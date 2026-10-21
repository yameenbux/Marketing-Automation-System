"""Outreach sending — deliberately has NO live implementation.

`send()` re-runs eligibility at send time, then asks the policy engine. Even if an
operator enables `live.outreach_sending`, raises the daily limit and enables the
`email_sending` integration, this function stops at `NoSendingIntegration`: wiring
a real provider (e.g. the connected Resend account) is a separate, explicit change
that needs your written authorisation, operating limits, and a tested unsubscribe flow.
"""
from __future__ import annotations

import json

from ..context import Context
from ..lead_generation.leads import get_lead
from ..policy import Action
from .eligibility import assess, load_outreach_config


class NoSendingIntegration(RuntimeError):
    pass


def send(ctx: Context, outreach_id: str) -> dict:
    row = ctx.store.conn.execute("SELECT * FROM outreach WHERE id=?", (outreach_id,)).fetchone()
    if row is None:
        raise KeyError(outreach_id)
    if row["status"] != "approved":
        ctx.store.audit("send_outreach", "email_sending", "blocked", f"status is {row['status']}, not approved")
        return {"sent": False, "reason": f"outreach is '{row['status']}', must be human-approved"}
    lead, _ = get_lead(ctx.store, row["lead_id"])
    decision = assess(ctx.store, load_outreach_config(ctx.root), row["product"], lead, row["channel"])
    if decision.status != "eligible":
        ctx.store.audit("send_outreach", "email_sending", "blocked", "eligibility changed",
                        {"decision": decision.as_dict()})
        return {"sent": False, "reason": f"no longer eligible: {decision.reasons}"}
    d = ctx.policy.authorize(Action.SEND_OUTREACH, "email_sending", detail={"outreach_id": outreach_id})
    if not d.live:
        return {"sent": False, "reason": d.reason, "mode": d.mode}
    ctx.store.audit("send_outreach", "email_sending", "blocked", "no sending integration is implemented")
    raise NoSendingIntegration("no outbound email integration has been authorised or implemented")


def approve(ctx: Context, outreach_id: str, approver: str) -> None:
    row = ctx.store.conn.execute("SELECT status, draft, decision FROM outreach WHERE id=?", (outreach_id,)).fetchone()
    if row is None:
        raise KeyError(outreach_id)
    if row["status"] != "draft" or json.loads(row["decision"])["status"] != "eligible":
        raise PermissionError("only eligible drafts can be approved (manual_review items need the issue resolved first)")
    if row["draft"].startswith("[VALIDATION FAILED"):
        raise PermissionError("draft failed content validation")
    with ctx.store.tx() as c:
        c.execute("UPDATE outreach SET status='approved' WHERE id=?", (outreach_id,))
    ctx.store.audit("approve_outreach", "human", "ok", f"approved by {approver}", {"outreach_id": outreach_id})
