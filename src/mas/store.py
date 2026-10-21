"""SQLite state store: campaigns, content, publications, leads, suppression, audit, costs, runs.

One file (var/mas.sqlite). Uniqueness constraints in the schema are the primary
duplicate-prevention mechanism — application checks are a second line.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

SCHEMA = """
CREATE TABLE IF NOT EXISTS audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    action TEXT NOT NULL,
    integration TEXT NOT NULL,
    outcome TEXT NOT NULL,          -- live | simulated | blocked | ok | error
    reason TEXT NOT NULL,
    detail TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS audit_ts ON audit(ts);

CREATE TABLE IF NOT EXISTS sync_state (
    repo TEXT NOT NULL,
    path TEXT NOT NULL,
    sha TEXT,
    etag TEXT,
    content_hash TEXT,
    fetched_at TEXT NOT NULL,
    PRIMARY KEY (repo, path)
);

CREATE TABLE IF NOT EXISTS campaigns (
    id TEXT PRIMARY KEY,
    product TEXT NOT NULL,
    objective TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    data TEXT NOT NULL DEFAULT '{}',
    UNIQUE (product, objective, created_at)
);

CREATE TABLE IF NOT EXISTS content (
    id TEXT PRIMARY KEY,
    campaign_id TEXT,
    product TEXT NOT NULL,
    kind TEXT NOT NULL,
    platform TEXT NOT NULL,
    status TEXT NOT NULL,
    fingerprint TEXT NOT NULL UNIQUE,
    body TEXT NOT NULL,
    validation TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS publications (
    idempotency_key TEXT PRIMARY KEY,
    content_id TEXT NOT NULL,
    destination TEXT NOT NULL,
    status TEXT NOT NULL,
    scheduled_for TEXT,
    ts TEXT NOT NULL,
    detail TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS leads (
    id TEXT PRIMARY KEY,
    product TEXT NOT NULL,
    company TEXT NOT NULL,
    domain TEXT,
    dedupe_key TEXT NOT NULL,
    score REAL,
    status TEXT NOT NULL,
    data TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (product, dedupe_key)
);

CREATE TABLE IF NOT EXISTS suppression (
    key TEXT PRIMARY KEY,           -- normalised email, domain, or company number
    kind TEXT NOT NULL,
    reason TEXT NOT NULL,
    added_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS outreach (
    id TEXT PRIMARY KEY,
    lead_id TEXT NOT NULL,
    product TEXT NOT NULL,
    channel TEXT NOT NULL,
    status TEXT NOT NULL,           -- blocked | manual_review | draft | approved | sent
    decision TEXT NOT NULL,
    draft TEXT,
    created_at TEXT NOT NULL,
    UNIQUE (lead_id, product, channel)
);

CREATE TABLE IF NOT EXISTS costs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    integration TEXT NOT NULL,
    amount_gbp REAL NOT NULL,
    units TEXT,
    note TEXT
);

CREATE TABLE IF NOT EXISTS runs (
    idempotency_key TEXT PRIMARY KEY,   -- e.g. planner:2026-10-21
    workflow TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL,
    summary TEXT NOT NULL DEFAULT '{}'
);
"""

# Allowed content status transitions. Anything else raises.
CONTENT_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"validated", "rejected", "cancelled"},
    "rejected": {"draft", "cancelled"},
    "validated": {"approved", "draft", "rejected", "cancelled"},
    "approved": {"scheduled", "draft", "cancelled"},
    "scheduled": {"published", "failed", "cancelled"},
    "failed": {"scheduled", "cancelled"},
    "published": set(),
    "cancelled": set(),
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class TransitionError(ValueError):
    pass


class Store:
    def __init__(self, path: Path | str):
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.execute("PRAGMA journal_mode=WAL") if self.path != ":memory:" else None
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    @contextmanager
    def tx(self) -> Iterator[sqlite3.Connection]:
        try:
            yield self.conn
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def q(self, sql: str, params: tuple | dict = ()) -> list[sqlite3.Row]:
        return list(self.conn.execute(sql, params))

    # --- audit -------------------------------------------------------------
    def audit(self, action: str, integration: str, outcome: str, reason: str, detail: dict | None = None) -> None:
        from .redact import redact

        with self.tx() as c:
            c.execute(
                "INSERT INTO audit(ts, action, integration, outcome, reason, detail) VALUES (?,?,?,?,?,?)",
                (now_iso(), action, integration, outcome, redact(reason), redact(json.dumps(detail or {}, default=str))),
            )

    def count_audit_since(self, action: str, since_iso: str, outcomes: tuple[str, ...] = ("live", "simulated", "ok")) -> int:
        marks = ",".join("?" * len(outcomes))
        row = self.conn.execute(
            f"SELECT COUNT(*) FROM audit WHERE action=? AND ts>=? AND outcome IN ({marks})",
            (action, since_iso, *outcomes),
        ).fetchone()
        return int(row[0])

    # --- content -----------------------------------------------------------
    def add_content(self, *, product: str, kind: str, platform: str, body: dict, fingerprint: str,
                    campaign_id: str | None = None) -> tuple[str, bool]:
        """Insert content; returns (id, created). Duplicate fingerprints are not re-inserted."""
        existing = self.conn.execute("SELECT id FROM content WHERE fingerprint=?", (fingerprint,)).fetchone()
        if existing:
            return existing["id"], False
        cid = new_id("cnt")
        ts = now_iso()
        with self.tx() as c:
            c.execute(
                "INSERT INTO content(id, campaign_id, product, kind, platform, status, fingerprint, body, created_at, updated_at)"
                " VALUES (?,?,?,?,?,?,?,?,?,?)",
                (cid, campaign_id, product, kind, platform, "draft", fingerprint, json.dumps(body), ts, ts),
            )
        return cid, True

    def get_content(self, cid: str) -> dict[str, Any] | None:
        row = self.conn.execute("SELECT * FROM content WHERE id=?", (cid,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["body"] = json.loads(d["body"])
        d["validation"] = json.loads(d["validation"])
        return d

    def set_content_status(self, cid: str, new: str, validation: dict | None = None) -> None:
        row = self.conn.execute("SELECT status FROM content WHERE id=?", (cid,)).fetchone()
        if not row:
            raise KeyError(cid)
        old = row["status"]
        if new != old and new not in CONTENT_TRANSITIONS[old]:
            raise TransitionError(f"content {cid}: {old} -> {new} not allowed")
        with self.tx() as c:
            if validation is not None:
                c.execute("UPDATE content SET status=?, validation=?, updated_at=? WHERE id=?",
                          (new, json.dumps(validation), now_iso(), cid))
            else:
                c.execute("UPDATE content SET status=?, updated_at=? WHERE id=?", (new, now_iso(), cid))

    # --- runs (workflow idempotency) --------------------------------------
    def start_run(self, key: str, workflow: str) -> bool:
        """Claim a run key. False if this run already completed (idempotent re-trigger)."""
        row = self.conn.execute("SELECT status FROM runs WHERE idempotency_key=?", (key,)).fetchone()
        if row and row["status"] == "ok":
            return False
        with self.tx() as c:
            c.execute(
                "INSERT INTO runs(idempotency_key, workflow, started_at, status) VALUES (?,?,?,?)"
                " ON CONFLICT(idempotency_key) DO UPDATE SET started_at=excluded.started_at, status='running'",
                (key, workflow, now_iso(), "running"),
            )
        return True

    def finish_run(self, key: str, status: str, summary: dict) -> None:
        with self.tx() as c:
            c.execute("UPDATE runs SET finished_at=?, status=?, summary=? WHERE idempotency_key=?",
                      (now_iso(), status, json.dumps(summary, default=str), key))

    # --- costs -------------------------------------------------------------
    def record_cost(self, integration: str, amount_gbp: float, units: str = "", note: str = "") -> None:
        with self.tx() as c:
            c.execute("INSERT INTO costs(ts, integration, amount_gbp, units, note) VALUES (?,?,?,?,?)",
                      (now_iso(), integration, amount_gbp, units, note))

    def spend_since(self, since_iso: str, integration: str | None = None) -> float:
        if integration:
            row = self.conn.execute("SELECT COALESCE(SUM(amount_gbp),0) FROM costs WHERE ts>=? AND integration=?",
                                    (since_iso, integration)).fetchone()
        else:
            row = self.conn.execute("SELECT COALESCE(SUM(amount_gbp),0) FROM costs WHERE ts>=?", (since_iso,)).fetchone()
        return float(row[0])
