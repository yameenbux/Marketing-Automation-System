from datetime import datetime
from unittest import mock
from zoneinfo import ZoneInfo

from mas import scheduler, workflows
from mas.analytics import report

TZ = ZoneInfo("Europe/London")


def no_sync(ctx, only=None):
    return []


def test_nothing_due_outside_hours(ctx):
    assert scheduler.due(ctx, datetime(2026, 10, 24, 10, 0, tzinfo=TZ)) == []      # Saturday
    assert scheduler.due(ctx, datetime(2026, 10, 21, 8, 59, tzinfo=TZ)) == []      # before 09:00


def test_planner_due_at_nine_in_both_bst_and_gmt(ctx):
    assert scheduler.due(ctx, datetime(2026, 7, 1, 9, 5, tzinfo=TZ)) == ["planner"]
    # 09:05 GMT in winter == 09:05 UTC; a UTC scheduler firing at 09:05 UTC in summer is 10:05 BST — still due
    assert scheduler.due(ctx, datetime(2026, 7, 1, 9, 5, tzinfo=ZoneInfo("UTC"))) == ["planner"]


def test_tick_is_idempotent(ctx):
    with mock.patch.object(workflows, "run_sync", no_sync):
        now = datetime(2026, 10, 21, 9, 10, tzinfo=TZ)   # a Wednesday
        with mock.patch.object(ctx.policy, "london_now", return_value=now):
            first = scheduler.tick(ctx, now)
            assert first["ran"] == ["planner", "production"], first
            assert scheduler.tick(ctx, now)["ran"] == []
            later = now.replace(hour=16, minute=31)
            assert scheduler.tick(ctx, later)["ran"] == ["report"]
            assert scheduler.tick(ctx, later)["ran"] == []


def test_tick_respects_kill_switch(ctx):
    ctx.policy.engage_kill_switch("t")
    assert scheduler.tick(ctx, datetime(2026, 10, 21, 9, 30, tzinfo=TZ))["ran"] == []


def test_report_reflects_reality(ctx):
    with mock.patch.object(workflows, "run_sync", no_sync):
        workflows.run_planner(ctx)
        workflows.run_production(ctx)
    ctx.policy.authorize(__import__("mas.policy", fromlist=["Action"]).Action.SEND_OUTREACH, "email_sending")
    text, path = report.build(ctx)
    assert path.exists()
    assert "planner: **ok**" in text
    assert "Messages sent: 0" in text
    assert "send_outreach via email_sending" in text      # blocked action surfaced
    assert "acme" in text                                  # awaiting profile approval
