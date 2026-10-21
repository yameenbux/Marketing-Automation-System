"""Time-gated dispatcher. Call `mas tick` every 15–30 minutes from any scheduler
(cron, systemd timer, GitHub Actions, a Claude scheduled task). It decides what is
due in Europe/London time — so UTC-only schedulers and BST/GMT changes don't matter —
and each workflow is idempotent per day, so extra ticks are harmless.
"""
from __future__ import annotations

from datetime import datetime, time

from .analytics import report
from .context import Context
from . import workflows


def due(ctx: Context, now: datetime | None = None) -> list[str]:
    now = (now or ctx.policy.london_now()).astimezone(ctx.policy.tz)
    if not ctx.policy.within_operating_hours(now):
        return []
    sched = ctx.settings["schedule"]
    today = now.date().isoformat()
    done = {r["idempotency_key"] for r in ctx.store.q("SELECT idempotency_key FROM runs WHERE status='ok'")}
    jobs = []
    if now.time() >= time.fromisoformat(sched["daily_planner"]) and f"planner:{today}" not in done:
        jobs.append("planner")
    if f"planner:{today}" in done and f"production:{today}" not in done:
        jobs.append("production")
    if now.time() >= time.fromisoformat(sched["daily_report"]) and f"report:{today}" not in done:
        jobs.append("report")
    return jobs


def tick(ctx: Context, now: datetime | None = None) -> dict:
    if ctx.policy.kill_switch_active():
        return {"ran": [], "reason": "kill switch active"}
    ran, errors = [], {}
    for job in due(ctx, now):
        today = (now or ctx.policy.london_now()).astimezone(ctx.policy.tz).date().isoformat()
        key = f"{job}:{today}"
        try:
            if job == "planner":
                workflows.run_planner(ctx)
                ran.append(job)
                ctx.store.start_run(f"production:{today}", "production")
                out = workflows.run_production(ctx)
                workflows.run_publishing(ctx)
                ctx.store.finish_run(f"production:{today}", "ok", {"items": len(out)})
                ran.append("production")
            elif job == "production":
                ctx.store.start_run(key, "production")
                out = workflows.run_production(ctx)
                workflows.run_publishing(ctx)
                ctx.store.finish_run(key, "ok", {"items": len(out)})
                ran.append(job)
            elif job == "report":
                ctx.store.start_run(key, "report")
                _, path = report.build(ctx)
                ctx.store.finish_run(key, "ok", {"path": str(path)})
                ran.append(job)
        except Exception as e:  # noqa: BLE001 — record, alert via report, continue with other jobs
            errors[job] = str(e)
            ctx.store.finish_run(key, "error", {"error": str(e)})
            ctx.store.audit("workflow", job, "error", str(e))
    return {"ran": ran, "errors": errors}
