"""Synthetic data only — no real organisations or people."""
import json
from datetime import date, timedelta

import pytest

from mas.context import Context
from mas.lead_generation import companies_house
from mas.lead_generation.leads import Lead, LeadError, add_lead, import_csv, score, suppress
from mas.outreach import drafts, sender
from mas.outreach.eligibility import assess
from mas.github_sync.client import Response

ICP = {"criteria": [{"id": "uk", "label": "UK", "weight": 50, "field": "country", "equals": "GB"},
                    {"id": "web", "label": "has site", "weight": 50, "field": "website", "present": True}],
       "exclude": [{"field": "signals", "contains": "existing_customer"}]}

GOOD_SENDER = {"legal_name": "Test Ventures Ltd", "postal_address": "1 Test St, Testtown TT1 1TT",
               "reply_to": "hello@test.example", "opt_out_instructions": "Reply STOP to opt out."}


def cfg(**product):
    base = {"allowed_channels": ["email"], "lia_documented": False, "lia_reference": None}
    return {"sender": GOOD_SENDER, "research_max_age_days": 180, "products": {"acme": base | product}}


def lead(**kw):
    base = dict(company="Example Café Ltd", source_url="https://example.test/listing", qualification_reason="it runs "
                "three cafés with shift staff", research_date=date.today().isoformat(), website="https://excafe.test",
                country="GB", subscriber_type="corporate", contact_email="info@excafe.test")
    return Lead(**(base | kw))


def test_lead_requires_source_and_reason():
    with pytest.raises(LeadError):
        lead(source_url="").validate()
    with pytest.raises(LeadError):
        lead(qualification_reason=" ").validate()


def test_personal_webmail_rejected():
    with pytest.raises(LeadError, match="personal webmail"):
        lead(contact_email="someone@gmail.com").validate()


def test_dedupe_by_domain_and_number(ctx):
    a = add_lead(ctx.store, "acme", lead(), ICP)
    b = add_lead(ctx.store, "acme", lead(company="Example Cafe Limited"), ICP)
    assert a[1] == "new" and b == (a[0], "duplicate")
    c1 = add_lead(ctx.store, "acme", lead(website=None, company_number="01234567"), ICP)
    c2 = add_lead(ctx.store, "acme", lead(website="https://other.test", company_number="01234567"), ICP)
    assert c2 == (c1[0], "duplicate")


def test_score_is_transparent_and_respects_exclusion():
    s, why = score(lead(), ICP)
    assert s == 100 and len(why) == 2
    assert score(lead(signals=["existing_customer"]), ICP)[0] == 0


def test_csv_import_rejects_extra_personal_columns(ctx, tmp_path):
    p = tmp_path / "l.csv"
    p.write_text("company,source_url,research_date,qualification_reason,date_of_birth\nA,https://x.test,2026-01-01,r,1990-01-01\n")
    with pytest.raises(LeadError, match="not permitted"):
        import_csv(ctx.store, "acme", p, ICP)


def test_csv_import_counts(ctx, tmp_path):
    p = tmp_path / "l.csv"
    p.write_text("company,source_url,research_date,qualification_reason,website,contact_email,signals\n"
                 "A Ltd,https://x.test,2026-01-01,runs cafés,https://a.test,info@a.test,uk;cafe\n"
                 "A Ltd,https://x.test,2026-01-01,runs cafés,https://a.test,,\n"
                 "B,https://x.test,2026-01-01,runs cafés,https://b.test,b@gmail.com,\n"
                 "C,,2026-01-01,runs cafés,https://c.test,,\n")
    r = import_csv(ctx.store, "acme", p, ICP)
    assert r["counts"] == {"new": 1, "duplicate": 1, "suppressed": 0, "rejected": 2}


# --- eligibility --------------------------------------------------------------
def test_corporate_role_address_eligible(ctx):
    assert assess(ctx.store, cfg(), "acme", lead(), "email").status == "eligible"


@pytest.mark.parametrize("st", ["sole_trader", "individual", "partnership", "unincorporated"])
def test_individual_subscribers_blocked_without_consent(ctx, st):
    e = assess(ctx.store, cfg(), "acme", lead(subscriber_type=st), "email")
    assert e.status == "blocked" and "PECR_REG22" in e.rules


def test_individual_with_consent_eligible(ctx):
    e = assess(ctx.store, cfg(), "acme", lead(subscriber_type="sole_trader"), "email", consent_record="form-2026-01")
    assert e.status == "eligible"


def test_unknown_subscriber_needs_manual_review(ctx):
    assert assess(ctx.store, cfg(), "acme", lead(subscriber_type="unknown"), "email").status == "manual_review"


def test_named_contact_needs_lia(ctx):
    named = lead(contact_email="jane.doe@excafe.test")
    assert assess(ctx.store, cfg(), "acme", named, "email").rules == ["UKGDPR_LIA"]
    assert assess(ctx.store, cfg(lia_documented=True, lia_reference="LIA-1"), "acme", named, "email").status == "eligible"


def test_suppression_wins_over_everything(ctx):
    suppress(ctx.store, "dom:excafe.test", "asked not to be contacted")
    e = assess(ctx.store, cfg(), "acme", lead(), "email", consent_record="x")
    assert e.status == "blocked" and e.rules == ["SUPPRESSED"]


def test_email_suppression_case_insensitive(ctx):
    suppress(ctx.store, "email:INFO@excafe.test", "opt-out")
    assert assess(ctx.store, cfg(), "acme", lead(), "email").rules == ["SUPPRESSED"]


@pytest.mark.parametrize("ch", ["phone", "linkedin", "sms"])
def test_other_channels_blocked(ctx, ch):
    c = cfg(allowed_channels=["email", "phone", "linkedin", "sms"])
    assert assess(ctx.store, c, "acme", lead(), ch).status == "blocked"


def test_channel_not_allowed_for_product(ctx):
    assert assess(ctx.store, cfg(allowed_channels=[]), "acme", lead(), "email").rules == ["CHANNEL_NOT_ALLOWED"]


def test_missing_sender_identity_blocks(ctx):
    c = cfg()
    c["sender"] = {}
    assert assess(ctx.store, c, "acme", lead(), "email").rules == ["SENDER_ID"]


def test_stale_research_needs_review(ctx):
    old = (date.today() - timedelta(days=400)).isoformat()
    assert assess(ctx.store, cfg(), "acme", lead(research_date=old), "email").status == "manual_review"


def test_fail_closed_on_error(ctx):
    e = assess(ctx.store, cfg(), "acme", lead(research_date="not-a-date"), "email")
    assert e.status == "blocked" and e.rules == ["FAIL_CLOSED"]


def test_unknown_product_blocked(ctx):
    assert assess(ctx.store, cfg(), "nope", lead(), "email").rules == ["NO_POLICY"]


# --- drafts and sending ---------------------------------------------------------
@pytest.fixture
def outreach_ctx(root):
    (root / "config" / "outreach.json").write_text(json.dumps(cfg()))
    return Context.create(root=root, db=":memory:")


def test_draft_contains_identity_optout_and_only_verified_claims(outreach_ctx):
    lid, _ = add_lead(outreach_ctx.store, "acme", lead(), ICP)
    r = drafts.prepare(outreach_ctx, lid)
    assert r["status"] == "draft"
    t = r["draft"]
    assert "Test Ventures Ltd" in t and "STOP" in t and "won't contact you again" in t
    assert "VALIDATION FAILED" not in t
    assert "three cafés" in t                              # personalisation = recorded reason only


def test_blocked_lead_gets_no_draft(outreach_ctx):
    lid, _ = add_lead(outreach_ctx.store, "acme", lead(subscriber_type="sole_trader"), ICP)
    r = drafts.prepare(outreach_ctx, lid)
    assert r["status"] == "blocked" and r["draft"] is None


def test_send_requires_approval_and_never_sends_in_dry_run(outreach_ctx):
    lid, _ = add_lead(outreach_ctx.store, "acme", lead(), ICP)
    oid = drafts.prepare(outreach_ctx, lid)["outreach_id"]
    assert sender.send(outreach_ctx, oid)["sent"] is False                 # not approved
    sender.approve(outreach_ctx, oid, "tester")
    r = sender.send(outreach_ctx, oid)
    assert r["sent"] is False and r["mode"] == "blocked"                    # integration disabled


def test_send_never_possible_even_fully_enabled(root):
    (root / "config" / "outreach.json").write_text(json.dumps(cfg()))
    c = Context.create(root=root, db=":memory:", overrides={
        "dry_run": False, "live": {"outreach_sending": True},
        "integrations": {"email_sending": {"enabled": True}}, "limits": {"max_outreach_per_day": 5}})
    lid, _ = add_lead(c.store, "acme", lead(), ICP)
    oid = drafts.prepare(c, lid)["outreach_id"]
    sender.approve(c, oid, "tester")
    with pytest.raises(sender.NoSendingIntegration):
        sender.send(c, oid)


def test_suppression_after_approval_blocks_send(outreach_ctx):
    lid, _ = add_lead(outreach_ctx.store, "acme", lead(), ICP)
    oid = drafts.prepare(outreach_ctx, lid)["outreach_id"]
    sender.approve(outreach_ctx, oid, "tester")
    suppress(outreach_ctx.store, "email:info@excafe.test", "opted out yesterday")
    r = sender.send(outreach_ctx, oid)
    assert r["sent"] is False and "no longer eligible" in r["reason"]


def test_manual_review_cannot_be_approved(outreach_ctx):
    lid, _ = add_lead(outreach_ctx.store, "acme", lead(subscriber_type="unknown"), ICP)
    oid = drafts.prepare(outreach_ctx, lid)["outreach_id"]
    with pytest.raises(PermissionError):
        sender.approve(outreach_ctx, oid, "tester")


# --- Companies House adapter (mocked) ---------------------------------------------
def test_companies_house_maps_legal_form(ctx, monkeypatch):
    monkeypatch.setenv("COMPANIES_HOUSE_API_KEY", "test-key-123456")
    ctx.settings.data["integrations"]["companies_house"]["enabled"] = True
    body = {"items": [
        {"title": "EXAMPLE OPTICIANS LTD", "company_number": "11111111", "company_type": "ltd", "company_status": "active"},
        {"title": "OLD CO LTD", "company_number": "22222222", "company_type": "ltd", "company_status": "dissolved"},
        {"title": "EXAMPLE PARTNERS", "company_number": "33333333", "company_type": "limited-partnership", "company_status": "active"},
    ]}
    seen = {}
    def transport(url, headers):
        seen["auth"] = headers["Authorization"]
        return Response(200, {}, json.dumps(body).encode())
    leads = companies_house.search(ctx.policy, "domiciliary optician", transport=transport)
    assert [l.subscriber_type for l in leads] == ["corporate", "unknown"]
    assert seen["auth"].startswith("Basic ")


def test_companies_house_disabled_by_default(ctx, monkeypatch):
    monkeypatch.setenv("COMPANIES_HOUSE_API_KEY", "test-key-123456")
    assert companies_house.search(ctx.policy, "x", transport=lambda u, h: 1 / 0) == []
