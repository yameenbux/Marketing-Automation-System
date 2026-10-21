"""Publishing.

Only `approved` content can be scheduled. Each (content, destination, time)
gets an idempotency key with a UNIQUE constraint, so retries cannot double-post.

Destinations
- dry_run: always available; writes the would-be request to var/outbox/dry-run/.
- metricool: writes a handoff file in the exact shape of Metricool's
  `createScheduledPostForReview` MCP call. Metricool is only reachable through the
  claude.ai connector (not from this Python process), so a Claude session or a
  human submits it. Using the *review* variant means Metricool itself holds the
  post for a human approval before it goes out.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from ..policy import Action, Policy
from ..store import Store, now_iso

DESTINATIONS = {
    # destination -> (integration name, network)
    "metricool:instagram": ("metricool_outbox", "instagram"),
    "metricool:linkedin": ("metricool_outbox", "linkedin"),
    "metricool:facebook": ("metricool_outbox", "facebook"),
    "metricool:x": ("metricool_outbox", "twitter"),
}


@dataclass
class PublishResult:
    status: str        # simulated | handed_off | duplicate | blocked | error
    key: str
    detail: str
    path: str | None = None


def idempotency_key(content_id: str, destination: str, scheduled_for: str) -> str:
    return hashlib.sha256(f"{content_id}|{destination}|{scheduled_for}".encode()).hexdigest()[:32]


def metricool_payload(text: str, network: str, scheduled_for: str, blog_id: str, reviewer: str,
                      media_urls: list[str] | None = None) -> dict:
    info = {
        "text": text,
        "providers": [{"network": network}],
        "autoPublish": True,
        "media": media_urls or [],
        "publicationDate": {"dateTime": scheduled_for[:19], "timezone": "Europe/London"},
    }
    return {"tool": "createScheduledPostForReview",
            "args": {"blogId": blog_id, "date": scheduled_for, "info": json.dumps(info),
                     "reviewers": reviewer, "approvalSystem": "any"},
            "note": "Media must be public HTTPS URLs; local render paths are listed in 'local_media' for upload first."}


class Publisher:
    def __init__(self, policy: Policy, store: Store, root: Path, metricool_blog_id: str | None = None,
                 reviewer: str | None = None):
        self.policy, self.store, self.root = policy, store, root
        self.blog_id = metricool_blog_id
        self.reviewer = reviewer

    def schedule(self, content_id: str, destination: str, scheduled_for: str,
                 local_media: list[str] | None = None) -> PublishResult:
        key = idempotency_key(content_id, destination, scheduled_for)
        existing = self.store.conn.execute("SELECT status FROM publications WHERE idempotency_key=?", (key,)).fetchone()
        # Simulated/blocked attempts don't count — only a real hand-off or publication is a duplicate.
        if existing and existing["status"] in ("handed_off", "published"):
            return PublishResult("duplicate", key, f"already {existing['status']}")

        item = self.store.get_content(content_id)
        if item is None:
            return PublishResult("error", key, "unknown content")
        if item["status"] != "approved":
            return PublishResult("blocked", key, f"content is '{item['status']}', must be 'approved'")
        if not item["validation"].get("ok"):
            return PublishResult("blocked", key, "content has no passing validation record")
        if destination not in DESTINATIONS:
            return PublishResult("blocked", key, f"unknown destination {destination}")
        integration, network = DESTINATIONS[destination]
        if item["platform"] != (network if network != "twitter" else "x"):
            return PublishResult("blocked", key, f"content written for {item['platform']}, not {network}")

        decision = self.policy.authorize(Action.PUBLISH, integration,
                                         detail={"content_id": content_id, "destination": destination, "key": key})
        if not decision.allowed:
            self._record(key, content_id, destination, "blocked", scheduled_for, {"reason": decision.reason})
            return PublishResult("blocked", key, decision.reason)

        payload = metricool_payload(item["body"]["text"], network, scheduled_for,
                                    self.blog_id or "<METRICOOL_BLOG_ID>", self.reviewer or "<REVIEWER_EMAIL>")
        payload["local_media"] = local_media or []
        payload["idempotency_key"] = key

        sub = "metricool" if decision.live else "dry-run"
        out = self.root / "var" / "outbox" / sub / f"{key}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        status = "handed_off" if decision.live else "simulated"
        self._record(key, content_id, destination, status, scheduled_for, {"outbox": str(out), "reason": decision.reason})
        if decision.live:
            self.store.set_content_status(content_id, "scheduled")
        return PublishResult(status, key, decision.reason, str(out))

    def _record(self, key: str, cid: str, dest: str, status: str, when: str, detail: dict) -> None:
        with self.store.tx() as c:
            c.execute("INSERT INTO publications(idempotency_key, content_id, destination, status, scheduled_for, ts, detail)"
                      " VALUES (?,?,?,?,?,?,?) ON CONFLICT(idempotency_key) DO UPDATE SET status=excluded.status,"
                      " ts=excluded.ts, detail=excluded.detail",
                      (key, cid, dest, status, when, now_iso(), json.dumps(detail)))
