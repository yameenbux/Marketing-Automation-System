"""Contact history, reply sync, legal identity. Synthetic data only."""
import json
import shutil
from datetime import date
from pathlib import Path

from mas import company
from mas.context import Context
from mas.lead_generation.leads import Lead, add_lead
from mas.ops import export_state
from mas.outreach import drafts, history
from mas.outreach.eligibility import assess

REPO = Path(__file__).resolve().parents[1]


def rows():
    return [{"product": "acme", "to": "info@cafe.test", "sent_at": "2026-10-14T16:00:00Z", "thread_id": "t1", "kind": "first",
             "org": "Cafe"},
            {"product": "acme", "to": "info@cafe.test", "sent_at": "2026-10-21T14:00:00Z", "thread_id": "t1", "kind": "follow_up"},
            {"product": "acme", "to": "owner@outlook.com", "sent_at": "2026-10-14T16:01:00Z", "thread_id": "t2", "kind": "first"},
            {"product": "acme", "to": "hello@bistro.test", "sent_at": "2026-10-15T09:00:00Z", "thread_id": "t3", "kind": "first"}]


def cfg_with_sender(root):
    (root / "config" / "outreach.json").write_text(json.dumps({
        "sender": {"legal_name": "Test Ventures Ltd", "postal_address": "1 Test St", "reply_to": "me@test.example",
                   "opt_out_instructions": "Reply STOP."}, "research_max_age_days": 180,
        "products": {"acme": {"allowed_channels": ["email"], "lia_documented": False}}}))


def lead(**kw):
    base = dict(company="Cafe Ltd", source_url="https://example.test/l", qualification_reason="it runs three cafés",
                research_date=date.today().isoformat(), country="GB", subscriber_type="corporate",
                contact_email="info@cafe.test", website="https://www.cafe.test")
    return Lead(**(base | kw))


def test_import_is_idempotent_and_rejects_bad_rows(ctx):
    assert history.import_sent(ctx, rows())["imported"] == 4
    assert history.import_sent(ctx, rows())["imported"] == 0
    assert history.import_sent(ctx, [{"product": "acme", "to": "x@y.test", "kind": "spam"}])["rejected_rows"] == [0]


def test_contact_key_uses_address_for_webmail():
    assert history.contact_key("Info@Cafe.test") == "dom:cafe.test"
    assert history.contact_key("owner@outlook.com") == "email:owner@outlook.com"


def test_already_contacted_blocks_a_second_first_email(root):
    cfg_with_sender(root)
    c = Context.create(root=root, db=":memory:")
    history.import_sent(c, rows())
    lid, _ = add_lead(c.store, "acme", lead(contact_email="bookings@cafe.test"), None)   # other address, same domain
    r = drafts.prepare(c, lid)
    assert r["status"] == "blocked" and r["draft"] is None and "ALREADY_CONTACTED" in r["decision"]["rules"]
    fresh, _ = add_lead(c.store, "acme", lead(company="New Ltd", contact_email="info@new.test", website="https://new.test",
                                               source_url="https://example.test/n"), None)
    assert drafts.prepare(c, fresh)["status"] == "draft"


def test_replies_opt_outs_and_bounces(ctx):
    history.import_sent(ctx, rows())
    threads = [{"thread_id": "t1", "messages": [{"sender": "me@ysb.test", "snippet": "hi"},
                                                 {"sender": "info@cafe.test", "snippet": "Interested, call me Tuesday"}]},
               {"thread_id": "t2", "messages": [{"sender": "owner@outlook.com", "snippet": "No thanks, please remove me"}]},
               {"thread_id": "t3", "messages": [{"sender": "mailer-daemon@googlemail.com", "snippet": "Address not found"}]},
               {"thread_id": "unknown", "messages": [{"sender": "a@b.test", "snippet": "hello"}]}]
    assert history.sync_replies(ctx, threads, {"me@ysb.test"}) == {"replied": 1, "opted_out": 1, "bounced": 1}
    keys = {r["key"] for r in ctx.store.q("SELECT key FROM suppression")}
    assert {"email:owner@outlook.com", "email:hello@bistro.test"} <= keys
    s = history.stats(ctx)["acme"]
    assert (s["organisations_emailed"], s["follow_ups"], s["replied"], s["opted_out"], s["bounced"]) == (3, 1, 2, 1, 1)
    assert s["reply_rate"] == round(2 / 3, 3)


def test_own_messages_are_not_replies(ctx):
    history.import_sent(ctx, rows())
    assert history.sync_replies(ctx, [{"thread_id": "t1", "messages": [{"sender": "ME@ysb.test", "snippet": "bump"}]}],
                                {"me@ysb.test"}) == {}


def test_opt_out_suppression_blocks_future_outreach(ctx):
    history.import_sent(ctx, rows())
    history.sync_replies(ctx, [{"thread_id": "t1", "messages": [{"sender": "info@cafe.test", "snippet": "not interested"}]}], set())
    cfg = {"sender": {"legal_name": "x", "postal_address": "y", "reply_to": "z@t.test", "opt_out_instructions": "o"},
           "products": {"acme": {"allowed_channels": ["email", "post"]}}}
    assert assess(ctx.store, cfg, "acme", lead(contact_email="new@cafe.test"), "post").rules == ["SUPPRESSED"]


def test_contact_history_never_exported(ctx, tmp_path):
    history.import_sent(ctx, rows())
    text = export_state(ctx, tmp_path / "s.json").read_text()
    assert "cafe.test" not in text and "outlook.com" not in text


# --- legal identity -------------------------------------------------------------------------
def test_company_footer_has_statutory_details_and_trading_name():
    company._load.cache_clear()
    f = company.email_footer(REPO, "domi")
    for must in ("Domi is a trading name of YSB Ventures Ltd.", "registered in England and Wales",
                 "company number 16022339", "Registered office: 711 Crompton Way, Bolton, England, BL1 8TL",
                 "won't email again"):
        assert must in f
    assert all(b in company.company(REPO)["brands"] for b in ("masjidone", "domi", "booked-in", "tidemark", "bolton-vouched"))


def test_real_brand_emails_cite_verified_facts_and_pass_validator(tmp_path):
    root = tmp_path / "r"
    for d in ("config", "data"):
        shutil.copytree(REPO / d, root / d, ignore=shutil.ignore_patterns("settings.json"))
    for slug in ("masjidone", "domi"):
        src = REPO / "data" / "products" / slug / "sources"
        if src.exists():
            shutil.copytree(src, root / "data" / "products" / slug / "sources", dirs_exist_ok=True)
    c = Context.create(root=root, db=":memory:")
    company._load.cache_clear()
    for slug, org, email in (("masjidone", "Example Masjid Trust", "info@masjid.test"), ("domi", "Example Eyecare Ltd", "info@eyes.test")):
        lid, _ = add_lead(c.store, slug, lead(company=org, contact_email=email, website=f"https://{email.split('@')[1]}"), None)
        r = drafts.prepare(c, lid)
        t = r["draft"]
        assert r["status"] == "draft", r["decision"]
        assert "VALIDATION FAILED" not in t and "phone call" in t and "16022339" in t and "trading name of YSB Ventures Ltd" in t
        assert t.startswith("Subject: ") and org in t.splitlines()[0]
        assert any(x.startswith("evidence: facts") for x in r["decision"]["reasons"])
