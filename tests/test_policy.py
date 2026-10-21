from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from mas.config import Settings
from mas.context import Context
from mas.policy import Action, PolicyError


def test_defaults_are_safe(ctx):
    assert ctx.settings["dry_run"] is True
    assert ctx.settings["live"] == {"publishing": False, "outreach_sending": False}
    assert ctx.settings.limit("max_outreach_per_day") == 0


def test_publish_is_simulated_in_dry_run(ctx):
    d = ctx.policy.authorize(Action.PUBLISH, "metricool_outbox")
    assert d.mode == "simulate"


def test_live_publish_requires_both_flags(root):
    c = Context.create(root=root, db=":memory:", overrides={"live": {"publishing": True}})
    assert c.policy.authorize(Action.PUBLISH, "metricool_outbox").mode == "simulate"  # dry_run still on
    c = Context.create(root=root, db=":memory:", overrides={"dry_run": False, "live": {"publishing": True}})
    assert c.policy.authorize(Action.PUBLISH, "metricool_outbox").mode == "live"


def test_live_publish_daily_limit(root):
    c = Context.create(root=root, db=":memory:",
                       overrides={"dry_run": False, "live": {"publishing": True}, "limits": {"max_posts_per_day": 2}})
    modes = [c.policy.authorize(Action.PUBLISH, "metricool_outbox").mode for _ in range(3)]
    assert modes == ["live", "live", "blocked"]


def test_outreach_sending_blocked_even_when_live_flag_set_with_zero_limit(root):
    c = Context.create(root=root, db=":memory:", overrides={
        "dry_run": False, "live": {"outreach_sending": True}, "integrations": {"email_sending": {"enabled": True}}})
    assert c.policy.authorize(Action.SEND_OUTREACH, "email_sending").mode == "blocked"


def test_outreach_integration_disabled_by_default(ctx):
    assert ctx.policy.authorize(Action.SEND_OUTREACH, "email_sending").mode == "blocked"


@pytest.mark.parametrize("how", ["settings", "env", "file"])
def test_kill_switch_blocks_everything(root, monkeypatch, how):
    overrides = {"kill_switch": True} if how == "settings" else None
    if how == "env":
        monkeypatch.setenv("MAS_KILL_SWITCH", "1")
    c = Context.create(root=root, db=":memory:", overrides=overrides)
    if how == "file":
        c.policy.engage_kill_switch("test")
    for action, integ in [(Action.FETCH_EXTERNAL, "github_public"), (Action.RENDER, "local_render"),
                          (Action.PUBLISH, "metricool_outbox"), (Action.DRAFT_OUTREACH, "local_render")]:
        assert c.policy.authorize(action, integ).mode == "blocked"
    with pytest.raises(PolicyError):
        c.policy.require(Action.FETCH_EXTERNAL, "github_public")


def test_kill_switch_release(ctx):
    ctx.policy.engage_kill_switch("t")
    assert ctx.policy.kill_switch_active()
    ctx.policy.release_kill_switch()
    assert not ctx.policy.kill_switch_active()


def test_render_daily_limit(root):
    c = Context.create(root=root, db=":memory:", overrides={"limits": {"max_renders_per_day": 1}})
    assert c.policy.authorize(Action.RENDER, "local_render").allowed
    assert not c.policy.authorize(Action.RENDER, "local_render").allowed


def test_budget_blocks_spend(ctx):
    ctx.store.record_cost("anthropic_llm", 4.9)
    ctx.settings.data["integrations"]["anthropic_llm"]["enabled"] = True
    assert ctx.policy.authorize(Action.LLM_CALL, "anthropic_llm", estimated_cost_gbp=0.05).allowed
    assert not ctx.policy.authorize(Action.LLM_CALL, "anthropic_llm", estimated_cost_gbp=0.2).allowed


def test_every_decision_is_audited(ctx):
    ctx.policy.authorize(Action.PUBLISH, "metricool_outbox")
    ctx.policy.authorize(Action.SEND_OUTREACH, "email_sending")
    rows = ctx.store.q("SELECT action, outcome FROM audit")
    assert [(r["action"], r["outcome"]) for r in rows] == [("publish", "simulated"), ("send_outreach", "blocked")]


def test_operating_hours_london_dst(ctx):
    tz = ZoneInfo("Europe/London")
    assert ctx.policy.within_operating_hours(datetime(2026, 7, 1, 9, 30, tzinfo=tz))       # BST weekday
    assert not ctx.policy.within_operating_hours(datetime(2026, 7, 1, 8, 30, tzinfo=ZoneInfo("UTC")) .replace(hour=7))
    assert ctx.policy.within_operating_hours(datetime(2026, 1, 7, 9, 0, tzinfo=tz))        # GMT weekday
    assert not ctx.policy.within_operating_hours(datetime(2026, 1, 7, 17, 0, tzinfo=tz))
    assert not ctx.policy.within_operating_hours(datetime(2026, 1, 10, 12, 0, tzinfo=tz))  # Saturday


def test_secrets_in_settings_file_rejected(root):
    (root / "config" / "settings.json").write_text('{"integrations": {"x": {"api_key": "abc"}}}')
    with pytest.raises(ValueError):
        Settings.load(root)


def test_unregistered_secret_name_rejected():
    with pytest.raises(KeyError):
        Settings.secret("PATH")


def test_ops_settings_layer_and_local_override(root):
    import json as _j
    (root / "config" / "settings.ops.json").write_text(_j.dumps({"dry_run": False, "live": {"publishing": True}}))
    s = Settings.load(root)
    assert s["dry_run"] is False and s["live"]["publishing"] is True
    (root / "config" / "settings.json").write_text(_j.dumps({"dry_run": True}))
    assert Settings.load(root)["dry_run"] is True              # local file wins over ops


def test_env_dry_run_beats_ops(root, monkeypatch):
    import json as _j
    (root / "config" / "settings.ops.json").write_text(_j.dumps({"dry_run": False}))
    monkeypatch.setenv("MAS_DRY_RUN", "1")
    assert Settings.load(root)["dry_run"] is True
