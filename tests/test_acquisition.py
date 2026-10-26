"""Customer-acquisition layer. Synthetic data only."""
import json
from datetime import date
from pathlib import Path

import pytest

from mas import acquisition as acq
from mas.context import Context
from mas.lead_generation.leads import Lead, add_lead, suppress
from mas.outreach import drafts
from mas.outreach.eligibility import assess

REPO = Path(__file__).resolve().parents[1]
START = "2026-11-02"                                   # a Monday


def plan(**acme):
    p = {"priority": 1, "mode": "active",
         "stages": {"contacted": "c", "conversation": "v", "demo": "d", "paying": "p"},
         "icp": {"who": "w", "where": "w", "buyer": "b", "disqualify": [], "evidence_fact_ids": ["overview"]},
         "value_proposition": {"headline": "h", "fact_ids": ["feat-swap"], "do_not_lead_with": []},
         "assumptions": [{"id": "A1", "risk": "high", "statement": "s", "test": "t", "min_sample": 4,
                          "success_ratio": 0.5, "if_contradicted": "change course"}],
         "prerequisites": [{"id": "P1", "blocks": "paying", "item": "later thing", "owner": "you", "done": False},
                           {"id": "P2", "blocks": "contacted", "item": "now thing", "owner": "you", "done": False}],
         "channels": [{"source": "in_person", "priority": 1, "who_acts": "you", "how": "h", "compliance": "c"},
                      {"source": "post", "priority": 2, "who_acts": "you", "how": "h", "compliance": "c"},
                      {"source": "email", "priority": 3, "who_acts": "you", "how": "h", "compliance": "c"}],
         "content": {"post_days": [1], "post_time": "12:30", "hypothesis": "A1", "why": "w"},
         "targets": {"contacted": [5, 5, 5, 5], "conversation": [2, 2, 2, 2], "demo": [1, 1, 1, 1], "paying": [0, 0, 0, 1]},
         "messages": [{"id": "m1", "use": "u", "platform": "email", "fact_ids": ["feat-swap"],
                       "text": "Staff swap shifts from their phone and the owner approves in one tap."}],
         "demo": {"assets": [], "flow": [], "never_show": []}, "discovery_questions": [], "pilot_offer": "p"}
    p |= acme
    return {"start": START, "days": 30, "sources": ["referral", "in_person", "post", "email", "phone", "other"],
            "products": {"acme": p, "later": {"priority": 5, "mode": "readiness", "launch_prerequisites": []}}}


@pytest.fixture
def actx(root):
    (root / "config" / "acquisition.json").write_text(json.dumps(plan()))
    return Context.create(root=root, db=":memory:")


def ev(**kw):
    base = {"product": "acme", "org": "Cafe One", "stage": "contacted", "source": "in_person", "date": "2026-11-03"}
    return base | kw


def clean(events, p=None):
    ok, bad = acq.clean_events(p or plan(), events)
    assert not bad, bad
    return ok


# --- the real plan ---------------------------------------------------------------------------
def test_real_plan_cites_verified_facts_and_messages_pass_validator():
    assert acq.check_plan(REPO) == []


def test_real_plan_priorities_and_readiness():
    p = acq.load_plan(REPO)
    assert acq.active(p) == ["masjidone", "domi", "bolton-vouched", "booked-in"]
    assert p["products"]["tidemark"]["mode"] == "readiness"
    bi = p["products"]["booked-in"]
    assert bi["targets"]["paying"] == [0, 0, 0, 0]                   # billing has never taken a real payment
    assert not next(x for x in bi["prerequisites"] if x["id"] == "K-P1")["done"]


def test_check_plan_flags_unsupported_message(root):
    bad = plan(messages=[{"id": "m", "use": "u", "platform": "email", "fact_ids": ["feat-swap"],
                          "text": "The best rota app in the UK, used by 500 cafés."}])
    (root / "config" / "acquisition.json").write_text(json.dumps(bad))
    problems = acq.check_plan(root)
    assert any("superlative" in x.lower() or "best" in x for x in problems)
    assert any("500" in x for x in problems)


# --- pipeline maths --------------------------------------------------------------------------------
def test_events_validated():
    _, bad = acq.clean_events(plan(), [ev(stage="nope"), ev(source="carrier pigeon"), ev(product="later"),
                                       ev(date="soon"), ev(evidence="maybe")])
    assert len(bad) == 5


def test_funnel_counts_week_and_cumulative():
    events = clean([ev(date="2026-11-03"), ev(org="Cafe Two", date="2026-11-10"),
                    ev(org="Cafe Two", stage="conversation", date="2026-11-11"),
                    ev(stage="contacted", date="2026-11-20", count=3)])          # future: not counted
    f = acq.funnel(plan(), events, date(2026, 11, 12))
    assert f["week"] == 2
    rows = {r["stage"]: r for r in f["products"]["acme"]}
    assert (rows["contacted"]["week_actual"], rows["contacted"]["week_target"]) == (1, 5)
    assert (rows["contacted"]["total_actual"], rows["contacted"]["total_target"]) == (2, 10)
    assert rows["conversation"]["week_actual"] == 1


def test_first_touch_source_gets_the_credit():
    events = clean([ev(org="Cafe One", source="post", date="2026-11-02"),
                    ev(org="cafe one ", stage="conversation", source="phone", date="2026-11-04"),
                    ev(org="Cafe One", stage="demo", source="email", date="2026-11-05"),
                    ev(org="Cafe Two", source="in_person")])
    s = acq.sources(plan(), events)["acme"]
    assert s["post"]["orgs"] == 1 and s["post"]["conversation"] == 1 and s["post"]["demo"] == 1
    assert "phone" not in s and "email" not in s
    assert s["in_person"]["orgs"] == 1 and s["in_person"]["conversation"] == 0


@pytest.mark.parametrize("yes,no,status", [(0, 0, "untested"), (2, 1, "testing (3/4)"),
                                           (3, 1, "supported"), (1, 3, "contradicted")])
def test_hypothesis_status(yes, no, status):
    events = clean([ev(org=f"o{i}", hypothesis="A1", evidence="supports") for i in range(yes)] +
                   [ev(org=f"n{i}", hypothesis="A1", evidence="contradicts") for i in range(no)])
    assert acq.hypotheses(plan(), events)["acme"][0]["status"] == status


def test_next_actions_order_and_rules():
    acts = acq.next_actions(plan(), [], date(2026, 11, 3))
    text = [a["action"] for a in acts]
    assert text[0].startswith("Log every conversation")
    assert text.index("Unblock contacted: now thing") < text.index("Unblock paying: later thing")   # urgent first
    dead = clean([ev(org=f"o{i}", source="post") for i in range(5)])
    text = [a["action"] for a in acq.next_actions(plan(), dead, date(2026, 11, 3))]
    assert any(t.startswith("Pause 'post'") for t in text)
    contra = clean([ev(org=f"o{i}", hypothesis="A1", evidence="contradicts") for i in range(4)])
    assert any("A1 contradicted: change course" in a["action"] for a in acq.next_actions(plan(), contra, date(2026, 11, 3)))


def test_report_lists_actions_funnel_and_bad_rows(actx, tmp_path):
    f = tmp_path / "events.json"
    f.write_text(json.dumps([ev(), ev(stage="flying")]))
    text = acq.report(actx, f, date(2026, 11, 3))
    assert "Customer acquisition" in text and "| contacted | 1 | 5 |" in text and "unknown stage 'flying'" in text


def test_daily_report_leads_with_acquisition(actx):
    from mas.analytics import report
    text, _ = report.build(actx)
    assert text.index("Customer acquisition") < text.index("## Workflows run today")


def test_no_plan_no_acquisition_section(ctx):
    from mas.analytics import report
    assert "Customer acquisition" not in report.build(ctx)[0]


# --- content only when a hypothesis needs it ----------------------------------------------------
def test_calendar_only_posts_on_hypothesis_days(actx):
    from mas.marketing.calendar import build_calendar
    cal = build_calendar(actx, date(2026, 11, 2), weeks=2)
    days = {s["date"] for s in cal["slots"]}
    assert days == {"2026-11-03", "2026-11-10"}                           # Tuesdays only
    for s in cal["slots"]:
        item = actx.store.get_content(s["content_id"])
        assert item["body"]["hypothesis"] == "A1"
        assert item["body"]["scheduled_for"].endswith("12:30:00+00:00") or "T12:30" in item["body"]["scheduled_for"]
    n = actx.store.q("SELECT COUNT(*) n FROM content")[0]["n"]
    build_calendar(actx, date(2026, 11, 2), weeks=2)                      # re-run adds nothing
    assert actx.store.q("SELECT COUNT(*) n FROM content")[0]["n"] == n


def test_calendar_skips_products_without_route_or_hypothesis(root):
    (root / "config" / "acquisition.json").write_text(json.dumps(plan(content={"post_days": [], "hypothesis": None, "why": "w"})))
    from mas.marketing.calendar import build_calendar
    c = Context.create(root=root, db=":memory:")
    assert build_calendar(c, date(2026, 11, 2), weeks=1)["slots"] == []


def test_production_skips_products_outside_the_plan(actx):
    from mas.workflows import run_production
    out = run_production(actx, {"products": [{"slug": "acme", "actions": ["produce_post:feature"],
                                              "destinations": [], "avoid_fact_ids": []}]})
    assert out and all(o["status"].startswith("skipped") for o in out)
    assert actx.store.q("SELECT COUNT(*) n FROM content")[0]["n"] == 0


# --- post channel and prospects ------------------------------------------------------------------
def outreach_cfg(sender=True):
    s = {"legal_name": "Test Ventures Ltd", "postal_address": "1 Test St", "reply_to": "hi@test.example",
         "opt_out_instructions": "Reply STOP."} if sender else {}
    return {"sender": s, "research_max_age_days": 180,
            "products": {"acme": {"allowed_channels": ["email", "post"], "lia_documented": False,
                                  "post_addressee": "The Committee"}}}


def lead(**kw):
    base = dict(company="Example Café Trust", source_url="https://example.test/l", qualification_reason="its website "
                "lists evening classes", research_date=date.today().isoformat(), country="GB", region="Bolton, England",
                subscriber_type="unincorporated", contact_email="info@excafe.test")
    return Lead(**(base | kw))


def test_post_allowed_for_individual_subscriber_where_email_is_not(ctx):
    assert assess(ctx.store, outreach_cfg(), "acme", lead(), "email").rules == ["PECR_REG22"]
    e = assess(ctx.store, outreach_cfg(), "acme", lead(), "post")
    assert e.status == "eligible" and "POST_ROLE_ADDRESSED" in e.rules


def test_post_respects_suppression_and_sender_gate(ctx):
    no_sender = assess(ctx.store, outreach_cfg(sender=False), "acme", lead(), "post")
    assert no_sender.status == "blocked" and no_sender.lead_status == "eligible"
    suppress(ctx.store, "dom:excafe.test", "asked us to stop")
    assert assess(ctx.store, outreach_cfg(), "acme", lead(), "post").rules == ["SUPPRESSED"]


def test_post_draft_is_a_role_addressed_letter(root):
    (root / "config" / "outreach.json").write_text(json.dumps(outreach_cfg()))
    c = Context.create(root=root, db=":memory:")
    lid, _ = add_lead(c.store, "acme", lead(), None)
    r = drafts.prepare(c, lid, channel="post")
    assert r["status"] == "draft"
    assert r["draft"].startswith("To: The Committee, Example Café Trust")
    assert "Dear committee," in r["draft"] and "your website lists evening classes" in r["draft"]
    assert "Subject:" not in r["draft"] and "Test Ventures Ltd" in r["draft"]


def test_prospects_rank_and_permitted_methods(root):
    (root / "config" / "acquisition.json").write_text(json.dumps(plan()))
    (root / "config" / "outreach.json").write_text(json.dumps(outreach_cfg(sender=False)))
    c = Context.create(root=root, db=":memory:")
    near, _ = add_lead(c.store, "acme", lead(), None)
    far, _ = add_lead(c.store, "acme", lead(company="Far Ltd", region="Kent, England", subscriber_type="corporate",
                                             contact_email="info@far.test", source_url="https://example.test/f"), None)
    for lid in (near, far):
        drafts.prepare(c, lid, channel="email")
    rows = {r["org"]: r for r in acq.prospects(c, "acme")}
    m = {x["method"]: x["status"] for x in rows["Example Café Trust"]["methods"]}
    assert m["email"].startswith("not permitted (PECR_REG22")
    assert m["post"].startswith("allowed") and m["in_person"] == "allowed"
    far_m = {x["method"]: x["status"] for x in rows["Far Ltd"]["methods"]}
    assert far_m["email"] == "allowed once sender identity is set"
    assert [x["method"] for x in rows["Far Ltd"]["methods"]] == ["in_person", "post", "email"]   # plan channel order
    assert all(r["source_url"] and r["reason"] for r in rows.values())


def test_docs_render_every_section(root):
    (root / "config" / "acquisition.json").write_text(json.dumps(plan()))
    text = acq.render_doc(root, "acme")
    for h in ("Ideal customer", "Value proposition", "assumptions", "Prerequisites", "Channels", "Weekly targets",
              "Messages", "Discovery questions", "Demo", "Pilot offer"):
        assert h in text
    assert "not stored in this repository" in text


def test_desk_docs_seed_plan_prospects_and_actions(actx):
    docs = acq.desk_docs(actx, today=date(2026, 11, 3))
    cols = {d["collection"] for d in docs}
    assert cols == {"plan", "report"}                                 # no leads in this synthetic store
    planned = [d for d in docs if d["collection"] == "plan"][0]["data"]
    assert planned["stages"] and planned["targets"] and planned["assumptions"][0]["id"] == "A1"
    rep = [d for d in docs if d["collection"] == "report"][0]["data"]
    assert rep["actions"][0]["action"].startswith("Log every conversation")


def test_cold_email_with_no_replies_triggers_channel_change():
    email = {"acme": {"organisations_emailed": 40, "days_since_first": 8, "reply_rate": 0.0, "replied": 0}}
    acts = [a["action"] for a in acq.next_actions(plan(), [], date(2026, 11, 3), email)]
    assert any(a.startswith("Cold email isn't working: 0 replies from 40") for a in acts)
    quiet = {"acme": {"organisations_emailed": 40, "days_since_first": 3, "reply_rate": 0.0, "replied": 0}}
    assert not any("Cold email" in a["action"] for a in acq.next_actions(plan(), [], date(2026, 11, 3), quiet))


def test_report_shows_email_table():
    email = {"acme": {"organisations_emailed": 10, "follow_ups": 2, "replied": 1, "reply_rate": 0.1, "opted_out": 0,
                      "bounced": 0, "first_sent": "2026-10-13", "days_since_first": 8}}
    text = acq.report_markdown(plan(), [], [], date(2026, 11, 3), email=email)
    assert "| acme | 10 | 2 | 1 | 10% | 0 | 0 | 2026-10-13 |" in text


def test_dated_commitments_lead_the_actions():
    p = plan(commitments=[{"date": "2026-11-05", "item": "demo with a real prospect"}])
    acts = [a["action"] for a in acq.next_actions(p, clean([ev()], p), date(2026, 11, 3))]
    assert acts[0] == "By 2026-11-05: demo with a real prospect"
    assert not any("demo with" in a["action"] for a in acq.next_actions(p, clean([ev()], p), date(2026, 11, 20)))


def test_private_commitments_merge_from_var_not_config(tmp_path):
    (tmp_path / "config").mkdir(); (tmp_path / "var" / "pipeline").mkdir(parents=True)
    (tmp_path / "config" / "acquisition.json").write_text(json.dumps(plan()))
    assert "commitments" not in acq.load_plan(tmp_path)["products"]["acme"]
    (tmp_path / "var" / "pipeline" / "commitments.json").write_text(
        json.dumps({"acme": [{"date": "2026-11-05", "item": "x"}], "unknown": [{"date": "2026-11-05", "item": "y"}]}))
    p = acq.load_plan(tmp_path)
    assert p["products"]["acme"]["commitments"] == [{"date": "2026-11-05", "item": "x"}] and "unknown" not in p["products"]


def test_email_stats_fall_back_to_desk_copy_when_no_local_history(actx):
    assert acq.email_stats(actx) == {}
    p = actx.root / "var" / "pipeline"; p.mkdir(parents=True, exist_ok=True)
    (p / "email_stats.json").write_text(json.dumps({"by_brand": {"acme": {"organisations_emailed": 3,
                                                                         "first_sent": "2020-01-01", "days_since_first": 1}}}))
    st = acq.email_stats(actx)["acme"]
    assert st["organisations_emailed"] == 3 and st["days_since_first"] > 1000


def test_short_public_report_leaves_out_email_numbers(actx):
    p = actx.root / "var" / "pipeline"; p.mkdir(parents=True, exist_ok=True)
    (p / "email_stats.json").write_text(json.dumps({"by_brand": {"acme": {
        "organisations_emailed": 40, "follow_ups": 0, "replied": 0, "reply_rate": 0.0, "opted_out": 0, "bounced": 0,
        "first_sent": "2020-01-01", "days_since_first": 9}}}))
    full, short = acq.report(actx, today=date(2026, 11, 3)), acq.report(actx, today=date(2026, 11, 3), short=True)
    assert "Email outreach" in full and "Cold email" in full
    assert short and "Email outreach" not in short and "Cold email" not in short
