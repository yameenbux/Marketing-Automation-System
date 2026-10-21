import json

from mas import ops
from mas.context import Context
from mas.marketing.calendar import build_calendar
from datetime import date


def test_state_roundtrip_excludes_personal_data(ctx, tmp_path):
    build_calendar(ctx, date(2026, 11, 2), weeks=1)
    ctx.store.conn.execute("INSERT INTO suppression(key, kind, reason, added_at) VALUES ('email:a@b.test','email','x','t')")
    ctx.store.conn.commit()
    p = ops.export_state(ctx, tmp_path / "s.json")
    data = json.loads(p.read_text())
    assert "suppression" not in data["tables"] and "leads" not in data["tables"]
    fresh = Context.create(root=ctx.root, db=":memory:")
    r = ops.import_state(fresh, p)
    assert r["imported"] and r["counts"]["content"] == ctx.store.q("SELECT COUNT(*) n FROM content")[0]["n"]


def test_desk_queue_and_decisions(ctx):
    build_calendar(ctx, date(2026, 11, 2), weeks=1)
    q = ops.desk_queue(ctx)
    assert q[0]["id"] == "profile:acme"                       # profiles come first
    content_ids = [i["id"] for i in q if i["id"].startswith("content:")]
    res = ops.apply_decisions(ctx, [{"id": content_ids[0], "decision": "approve", "by": "me"},
                                    {"id": "profile:acme", "decision": "approve", "by": "me"},
                                    {"id": content_ids[1], "decision": "reject", "by": "me"}])
    assert all(r["applied"] for r in res), res                # profile applied before the post
    assert ctx.store.get_content(content_ids[0].split(":", 1)[1])["status"] == "approved"
    assert ctx.store.get_content(content_ids[1].split(":", 1)[1])["status"] == "cancelled"
    assert not any(i["id"] == "profile:acme" for i in ops.desk_queue(ctx))


def test_decision_errors_are_reported_not_raised(ctx):
    res = ops.apply_decisions(ctx, [{"id": "content:nope", "decision": "approve"}])
    assert res[0]["applied"] is False and res[0]["error"]
