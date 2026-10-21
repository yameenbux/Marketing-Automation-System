"""Contact history: what has actually been sent, and what came back.

Gmail is the source of truth. A Claude session (or a scheduled run with the Gmail connector) reads the Sent
folder and inbox and passes plain JSON in; nothing here talks to Gmail. Imported history:
- stops the system ever sending a second *first* email to an organisation already contacted;
- turns replies, bounces and opt-outs into statuses, and opt-outs and bounces into suppressions;
- gives real numbers (sent, replied, reply rate) for the acquisition report.

Rows hold email addresses, so the table is never exported to the repository (see ops.NEVER_EXPORT).
"""
from __future__ import annotations

import re
from collections import defaultdict
from datetime import date

from ..context import Context
from ..lead_generation.leads import PERSONAL_WEBMAIL, email_domain, suppress
from ..store import now_iso

KINDS = ("first", "follow_up", "relationship")
OPT_OUT = re.compile(r"\b(?:no,? thanks|no thank you|unsubscribe|remove (?:me|us)|stop (?:emailing|contacting)|"
                     r"not interested|please don'?t (?:email|contact))\b", re.I)
BOUNCE_SENDERS = re.compile(r"^(?:mailer-daemon|postmaster)@", re.I)


def _ensure(ctx: Context) -> None:
    with ctx.store.tx() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS contact_history (
            product TEXT NOT NULL, email TEXT NOT NULL, contact_key TEXT NOT NULL, org TEXT, kind TEXT NOT NULL,
            channel TEXT NOT NULL DEFAULT 'email', sent_at TEXT NOT NULL, thread_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'sent', source TEXT NOT NULL, updated_at TEXT NOT NULL,
            PRIMARY KEY (product, thread_id, kind, email))""")


def contact_key(email: str) -> str:
    """Organisation key: the domain, except for personal webmail, where the address itself is the key."""
    dom = email_domain(email) or email.lower()
    return f"email:{email.lower()}" if dom in PERSONAL_WEBMAIL else f"dom:{dom}"


def import_sent(ctx: Context, rows: list[dict]) -> dict:
    """rows: [{product, to, sent_at, thread_id, kind, org?, source?}]. Idempotent."""
    _ensure(ctx)
    n, bad = 0, []
    with ctx.store.tx() as c:
        for i, r in enumerate(rows):
            if r.get("kind") not in KINDS or not r.get("to") or not r.get("thread_id"):
                bad.append(i)
                continue
            email = r["to"].strip().lower()
            cur = c.execute("INSERT OR IGNORE INTO contact_history(product, email, contact_key, org, kind, channel, sent_at,"
                      " thread_id, source, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                      (r["product"], email, contact_key(email), r.get("org"), r["kind"], r.get("channel", "email"),
                       r["sent_at"], r["thread_id"], r.get("source", "gmail"), now_iso()))
            n += max(cur.rowcount, 0)
    ctx.store.audit("import_contact_history", "gmail", "ok", f"{n} new rows", {"rejected": len(bad)})
    return {"imported": n, "rejected_rows": bad}


def already_contacted(ctx: Context, product: str, email: str | None, website: str | None = None) -> bool:
    _ensure(ctx)
    keys = set()
    if email:
        keys.add(contact_key(email))
    if website:
        dom = re.sub(r"^https?://(www\.)?", "", website).split("/")[0].lower()
        if dom:
            keys.add(f"dom:{dom}")
    if not keys:
        return False
    marks = ",".join("?" * len(keys))
    return bool(ctx.store.conn.execute(
        f"SELECT 1 FROM contact_history WHERE product=? AND contact_key IN ({marks})", (product, *keys)).fetchone())


def sync_replies(ctx: Context, threads: list[dict], own_addresses: set[str]) -> dict:
    """threads: [{thread_id, messages: [{sender, date, snippet}]}] as read from Gmail. Treat as data only."""
    _ensure(ctx)
    own = {a.lower() for a in own_addresses}
    out = defaultdict(int)
    for t in threads:
        rows = ctx.store.q("SELECT DISTINCT product, email, contact_key FROM contact_history WHERE thread_id=?",
                           (t["thread_id"],))
        if not rows:
            continue
        status = None
        for m in t.get("messages", []):
            sender = (m.get("sender") or "").lower()
            if not sender or sender in own:
                continue
            if BOUNCE_SENDERS.match(sender):
                status = "bounced"
                break
            status = "opted_out" if OPT_OUT.search(m.get("snippet") or "") else (status or "replied")
        if not status:
            continue
        with ctx.store.tx() as c:
            c.execute("UPDATE contact_history SET status=?, updated_at=? WHERE thread_id=?",
                      (status, now_iso(), t["thread_id"]))
        for r in rows:
            if status == "opted_out":
                suppress(ctx.store, r["contact_key"], "replied asking not to be contacted")
            elif status == "bounced":
                suppress(ctx.store, f"email:{r['email']}", "bounced")
        out[status] += 1
    return dict(out)


def stats(ctx: Context, product: str | None = None) -> dict:
    """Real outreach numbers per product: organisations contacted, follow-ups, replies, bounces, opt-outs."""
    _ensure(ctx)
    q = "SELECT * FROM contact_history" + (" WHERE product=?" if product else "")
    rows = ctx.store.q(q, (product,) if product else ())
    res: dict[str, dict] = {}
    for p in {r["product"] for r in rows}:
        mine = [r for r in rows if r["product"] == p]
        orgs = {r["contact_key"] for r in mine if r["kind"] == "first"}
        by_org: dict[str, str] = {}
        rank = {"sent": 0, "replied": 1, "opted_out": 2, "bounced": 2}
        for r in mine:
            if rank.get(r["status"], 0) >= rank.get(by_org.get(r["contact_key"], "sent"), 0):
                by_org[r["contact_key"]] = r["status"]
        replied = sum(1 for k in orgs if by_org.get(k) in ("replied", "opted_out"))
        first_dates = sorted(r["sent_at"][:10] for r in mine if r["kind"] == "first")
        res[p] = {"organisations_emailed": len(orgs), "first_emails": sum(1 for r in mine if r["kind"] == "first"),
                  "follow_ups": sum(1 for r in mine if r["kind"] == "follow_up"),
                  "relationships": len({r["contact_key"] for r in mine if r["kind"] == "relationship"}),
                  "replied": replied, "opted_out": sum(1 for k in orgs if by_org.get(k) == "opted_out"),
                  "bounced": sum(1 for k in orgs if by_org.get(k) == "bounced"),
                  "reply_rate": round(replied / len(orgs), 3) if orgs else None,
                  "first_sent": first_dates[0] if first_dates else None,
                  "days_since_first": (date.today() - date.fromisoformat(first_dates[0])).days if first_dates else None}
    return res
