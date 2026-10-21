import json

import pytest

from mas.marketing.validator import validate
from mas.marketing.writer import TemplateWriter
from mas.products.profile import load_profile
from mas.publishing.publisher import Publisher
from mas.store import TransitionError
from mas.workflows import approve_content, approve_profile, run_production, run_publishing, validate_content
from mas.marketing.planner import build_plan


def prof(ctx):
    return load_profile(ctx.root, "acme")


def test_profile_facts_verified(ctx):
    p = prof(ctx)
    assert {f.status for f in p.facts} == {"verified"}


def test_fact_goes_stale_when_source_changes(ctx):
    src = ctx.root / "data/products/acme/sources/README.md"
    src.write_text(src.read_text().replace("texts the next available person", "emails the manager"))
    assert prof(ctx).fact("feat-sick").status == "stale"
    assert not prof(ctx).fact("feat-sick").usable


def test_fact_with_unsupported_number_invalid(ctx):
    path = ctx.root / "data/products/acme/profile.json"
    d = json.loads(path.read_text())
    d["facts"][2]["text"] = "Staff swap shifts in 3 seconds."
    path.write_text(json.dumps(d))
    assert prof(ctx).fact("feat-swap").status == "invalid"


def test_unsynced_source_is_unverifiable(ctx):
    (ctx.root / "data/products/acme/sources/README.md").unlink()
    assert {f.status for f in prof(ctx).facts} == {"unverifiable"}


def test_writer_cites_only_usable_facts(ctx):
    p = prof(ctx)
    for pillar in ("problem_solution", "feature_spotlight", "how_it_works", "privacy_trust", "behind_the_build"):
        d = TemplateWriter().social_post(p, "instagram", pillar)
        assert d is not None
        assert "lim-payroll" not in d.fact_ids
        assert validate(d.text, product=p, platform="instagram", fact_ids=d.fact_ids).ok, (pillar, d.text)


def test_x_post_fits_limit(ctx):
    d = TemplateWriter().social_post(prof(ctx), "x", "how_it_works")
    assert len(d.text) <= 280


@pytest.mark.parametrize("text,needle", [
    ("Acme Rota is the best rota app. https://acmerota.example.co.uk", "superlative"),
    ("Trusted by thousands of cafés.", "social proof"),
    ("Saves 12 hours a week.", "numbers not supported"),
    ("We guarantee results.", "guarantee"),
    ("Visit https://evil.example.com now", "unverified host"),
    ("Lose weight fast with Acme.", "health outcome"),
])
def test_validator_blocks_claims(ctx, text, needle):
    r = validate(text, product=prof(ctx), platform="instagram", fact_ids=["feat-swap"])
    assert not r.ok and any(needle in e for e in r.errors), r.errors


def test_validator_blocks_limitations_and_missing_citations(ctx):
    p = prof(ctx)
    assert not validate("Payroll export.", product=p, platform="linkedin", fact_ids=["lim-payroll"]).ok
    assert not validate("Hello", product=p, platform="linkedin", fact_ids=[]).ok
    assert not validate("Hello", product=p, platform="linkedin", fact_ids=["nope"]).ok


def test_validator_allows_cited_price(ctx):
    r = validate("Acme Rota costs £9 a month per café. https://acmerota.example.co.uk",
                 product=prof(ctx), platform="linkedin", fact_ids=["price", "url"])
    assert r.ok, r.errors


def test_platform_limit(ctx):
    r = validate("a " * 200, product=prof(ctx), platform="x", fact_ids=["feat-swap"])
    assert any("exceeds" in e for e in r.errors)


def test_guardrail_tidemark_app_store():
    from mas.marketing.validator import GUARDRAILS
    import re
    assert any(re.search(p, "download now on your iphone") for p, _ in GUARDRAILS["tidemark"])


def test_duplicate_content_not_reinserted(ctx):
    a = ctx.store.add_content(product="acme", kind="k", platform="x", body={}, fingerprint="f1")
    b = ctx.store.add_content(product="acme", kind="k", platform="x", body={}, fingerprint="f1")
    assert a[0] == b[0] and a[1] and not b[1]


def test_status_machine(ctx):
    cid, _ = ctx.store.add_content(product="acme", kind="k", platform="x", body={}, fingerprint="f2")
    with pytest.raises(TransitionError):
        ctx.store.set_content_status(cid, "published")
    ctx.store.set_content_status(cid, "validated")
    ctx.store.set_content_status(cid, "approved")
    ctx.store.set_content_status(cid, "scheduled")
    ctx.store.set_content_status(cid, "published")
    with pytest.raises(TransitionError):
        ctx.store.set_content_status(cid, "draft")


def _produce(ctx):
    plan = build_plan(ctx.root, ctx.store, max_posts=1)
    return plan, run_production(ctx, plan)


def test_planner_prioritises_and_flags_approval(ctx):
    plan = build_plan(ctx.root, ctx.store, max_posts=1)
    acme = plan["products"][0]
    assert acme["slug"] == "acme"
    assert "needs_human_profile_approval" in acme["actions"]
    assert any(a.startswith("produce_post:") for a in acme["actions"])


def test_planner_rotates_pillar(ctx):
    _, out1 = _produce(ctx)
    plan2 = build_plan(ctx.root, ctx.store, max_posts=1)
    assert plan2["products"][0]["pillar"] != out1[0]["pillar"]
    assert plan2["products"][0]["avoid_fact_ids"]


def test_production_validates(ctx):
    _, out = _produce(ctx)
    assert out[0]["status"] == "validated", out


def test_approval_requires_profile_approval(ctx):
    _, out = _produce(ctx)
    with pytest.raises(PermissionError, match="not approved"):
        approve_content(ctx, out[0]["content_id"], "tester")


def test_end_to_end_dry_run_publish_and_idempotency(ctx):
    approve_profile(ctx, "acme", "tester")
    _, out = _produce(ctx)
    cid = out[0]["content_id"]
    approve_content(ctx, cid, "tester")
    r1 = run_publishing(ctx)
    assert r1[0]["status"] == "simulated"
    outbox = json.loads(open(r1[0]["path"]).read())
    assert outbox["tool"] == "createScheduledPostForReview"
    assert json.loads(outbox["args"]["info"])["providers"] == [{"network": "instagram"}]
    assert ctx.store.get_content(cid)["status"] == "approved"   # nothing actually scheduled
    assert not (ctx.root / "var/outbox/metricool").exists()


def test_live_handoff_once_only(root):
    from mas.context import Context
    c = Context.create(root=root, db=":memory:", overrides={"dry_run": False, "live": {"publishing": True}})
    approve_profile(c, "acme", "tester")
    _, out = _produce(c)
    approve_content(c, out[0]["content_id"], "tester")
    first = run_publishing(c)
    assert first[0]["status"] == "handed_off"
    assert c.store.get_content(out[0]["content_id"])["status"] == "scheduled"
    pub = Publisher(c.policy, c.store, c.root)
    again = pub.schedule(out[0]["content_id"], "metricool:instagram", first[0]["key"] and
                         c.store.q("SELECT scheduled_for FROM publications")[0]["scheduled_for"])
    assert again.status == "duplicate"


def test_unapproved_content_never_published(ctx):
    cid, _ = ctx.store.add_content(product="acme", kind="social_post", platform="instagram",
                                   body={"text": "x", "fact_ids": []}, fingerprint="f3")
    r = Publisher(ctx.policy, ctx.store, ctx.root).schedule(cid, "metricool:instagram", "2030-01-01T12:00:00+00:00")
    assert r.status == "blocked"


def test_stale_fact_blocks_revalidation(ctx):
    approve_profile(ctx, "acme", "tester")
    _, out = _produce(ctx)
    cid = out[0]["content_id"]
    src = ctx.root / "data/products/acme/sources/README.md"
    src.write_text("# replaced\n")
    assert validate_content(ctx, cid)["status"] == "rejected"
    with pytest.raises(PermissionError):
        approve_content(ctx, cid, "tester")


@pytest.mark.parametrize("text,blocked", [
    ("Upgrade to Pro for more enquiries.", True),
    ("Pro is coming soon.", False),
    ("Get a featured listing today.", True),
    ("Every trader is fully vetted.", True),
    ("All tradespeople are DBS-checked.", True),
    ("Reviews are coming soon.", True),
    ("Pick a trade and an area, then call or WhatsApp them in one tap.", False),
    ("Bolton's professional plumbers.", False),
])
def test_bolton_vouched_guardrails(text, blocked):
    import re
    from mas.marketing.validator import GUARDRAILS
    hit = any(re.search(p, text.lower(), re.I) for p, _ in GUARDRAILS["bolton-vouched"])
    assert hit == blocked, text


@pytest.mark.parametrize("text,blocked", [
    ("Join thousands of happy customers.", True),
    ("Used by hundreds of traders across Bolton.", True),
    ("Recommendations scroll away under hundreds of messages.", False),
])
def test_social_proof_rule_targets_customer_counts(ctx, text, blocked):
    r = validate(text, product=prof(ctx), platform="linkedin", fact_ids=["feat-swap"])
    assert any("social proof" in e for e in r.errors) == blocked, r.errors


def _second_product(root):
    """Add a second synthetic product so the calendar has a portfolio to rotate."""
    import shutil
    src, dst = root / "data/products/acme", root / "data/products/beta"
    shutil.copytree(src, dst)
    d = json.loads((dst / "profile.json").read_text())
    d["slug"], d["name"] = "beta", "Beta Rota"
    (dst / "profile.json").write_text(json.dumps(d))
    reg = json.loads((root / "config/repositories.json").read_text())
    reg["products"].append(dict(reg["products"][0], slug="beta", name="Beta Rota", repo="beta"))
    (root / "config/repositories.json").write_text(json.dumps(reg))
    ch = json.loads((root / "config/channels.json").read_text())
    ch["products"]["beta"] = []
    ch["primary_platform"] = {"acme": "instagram", "beta": "linkedin"}
    (root / "config/channels.json").write_text(json.dumps(ch))


def test_calendar_rotates_whole_portfolio(root):
    from datetime import date
    from mas.context import Context
    from mas.marketing.calendar import build_calendar
    _second_product(root)
    c = Context.create(root=root, db=":memory:", overrides={"limits": {"max_posts_per_day": 2}})
    cal = build_calendar(c, date(2026, 11, 2), weeks=1)          # Monday
    slots = cal["slots"]
    assert len(slots) == 10                                      # 5 weekdays × 2
    assert {s["date"] for s in slots} == {f"2026-11-0{d}" for d in range(2, 7)}   # no weekend
    for d in {s["date"] for s in slots}:
        assert len({s["product"] for s in slots if s["date"] == d}) == 2          # one post per product per day
    assert {s["product"] for s in slots} == {"acme", "beta"}
    beta = [s for s in slots if s["product"] == "beta"]
    assert all(s["platform"] == "linkedin" and s["publish_route"].startswith("draft-only") for s in beta)
    assert all(s["status"] in ("validated", "duplicate of existing draft") for s in slots), slots
    acme_items = [c.store.get_content(s["content_id"]) for s in slots if s["product"] == "acme"]
    assert acme_items[0]["body"]["scheduled_for"].startswith("2026-11-02T12:00")
    assert len({i["body"]["pillar"] for i in acme_items}) >= 3   # pillars rotate


def test_calendar_slot_time_used_when_publishing(root):
    from datetime import date
    from mas.context import Context
    from mas.marketing.calendar import build_calendar
    c = Context.create(root=root, db=":memory:")
    approve_profile(c, "acme", "tester")
    cal = build_calendar(c, date(2026, 11, 2), weeks=1)
    cid = cal["slots"][0]["content_id"]
    approve_content(c, cid, "tester")
    r = [x for x in run_publishing(c) if x["content_id"] == cid][0]
    row = c.store.q("SELECT scheduled_for FROM publications WHERE idempotency_key=?", (r["key"],))[0]
    assert row["scheduled_for"].startswith("2026-11-02T12:00")


@pytest.mark.parametrize("text", ["Track your Mounjaro dose", "Perfect for Wegovy users", "GLP-1 tracker"])
def test_tidemark_blocks_prescription_medicine_names(text):
    import re
    from mas.marketing.validator import GUARDRAILS
    assert any(re.search(p, text.lower(), re.I) for p, _ in GUARDRAILS["tidemark"])


@pytest.mark.parametrize("text,blocked", [
    ("Domi texts the best-matched person on the waiting list.", False),
    ("The best scheduling app for opticians.", True),
    ("The only weight tracker that shows the trend.", True),
    ("A uniquely simple booking page.", True),
])
def test_superlative_and_exclusivity_rules(ctx, text, blocked):
    r = validate(text, product=prof(ctx), platform="linkedin", fact_ids=["feat-swap"])
    hit = any(("superlative" in e or "exclusivity" in e) for e in r.errors)
    assert hit == blocked, r.errors


def test_excluded_fact_never_used_even_when_avoid_exhausts_kind(ctx):
    p = prof(ctx)
    all_overview = {f.id for f in p.by_kind("overview")}
    d = TemplateWriter().social_post(p, "instagram", "behind_the_build", avoid=all_overview, exclude={"overview"})
    assert d is None or "overview" not in d.fact_ids


def test_calendar_rerun_is_idempotent(root):
    from datetime import date
    from mas.context import Context
    from mas.marketing.calendar import build_calendar
    c = Context.create(root=root, db=":memory:")
    a = build_calendar(c, date(2026, 11, 2), weeks=1)
    n = c.store.q("SELECT COUNT(*) n FROM content")[0]["n"]
    b = build_calendar(c, date(2026, 11, 2), weeks=1)
    assert c.store.q("SELECT COUNT(*) n FROM content")[0]["n"] == n
    assert [s["content_id"] for s in a["slots"]] == [s["content_id"] for s in b["slots"]]


@pytest.mark.parametrize("sentence,expected", [
    ("Plenty of systems keep a diary; Domi acts on the gap by finding who fits it, asking them by text and booking the first yes.",
     "Domi acts on the gap by finding who fits it, asking them by text and booking the first yes"),
    ("A cancellation costs a home-visit practice more than a clinic, because the clinician is already on the road and the gap is too short to fill by ringing round.",
     "A cancellation costs a home-visit practice more than a clinic"),
    ("Staff swap shifts from their phone.", "Staff swap shifts from their phone"),
])
def test_headline_keeps_the_point(sentence, expected):
    from mas.marketing.writer import _headline
    assert _headline(sentence) == expected


def test_cta_narration_without_url_is_grammatical(ctx):
    p = prof(ctx)
    p.facts = [f for f in p.facts if f.kind not in ("url", "cta")]
    cta = TemplateWriter().video_script(p).meta["scenes"][-1]
    assert cta["narration"] == "Find out more about Acme Rota."
