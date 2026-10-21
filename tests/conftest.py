import json
import shutil
from pathlib import Path

import pytest

from mas.context import Context

REPO = Path(__file__).resolve().parents[1]

README = """# Acme Rota

**Shift rotas for small cafés, without the spreadsheet.**

Café owners rebuild the rota every week by hand and it breaks when someone calls in sick.
Staff swap shifts from their phone and the owner approves in one tap.
When someone calls in sick, Acme Rota texts the next available person.
Every café's data is kept separate by the database itself.
Pricing: £9 a month per café.
Live at https://acmerota.example.co.uk
Not built yet: payroll export.
"""


def fact(fid, kind, text, quote):
    return {"id": fid, "kind": kind, "text": text, "source": {"path": "README.md", "quote": quote}}


PROFILE = {
    "slug": "acme", "name": "Acme Rota", "repo": "example/acme", "maker": "Test Ltd",
    "product_type": "b2b_saas", "maturity": "test",
    "approval": {"status": "draft", "approved_by": None, "approved_at": None},
    "brand": {"primary_color": "#123456", "secondary_color": "#345678", "accent_color": "#E07B4F", "tone": "plain"},
    "facts": [
        fact("overview", "overview", "Acme Rota builds shift rotas for small cafés.",
             "Shift rotas for small cafés, without the spreadsheet."),
        fact("pain-manual", "pain_point", "Café owners rebuild the rota by hand every week.",
             "Café owners rebuild the rota every week by hand"),
        fact("feat-swap", "feature", "Staff swap shifts from their phone and the owner approves in one tap.",
             "Staff swap shifts from their phone and the owner approves in one tap."),
        fact("feat-sick", "feature", "When someone calls in sick, Acme Rota texts the next available person.",
             "When someone calls in sick, Acme Rota texts the next available person."),
        fact("feat-separate", "privacy", "Each café's data is kept separate by the database itself.",
             "Every café's data is kept separate by the database itself."),
        fact("value-time", "value_prop", "Owners stop rebuilding the rota every week.",
             "Café owners rebuild the rota every week by hand and it breaks"),
        fact("price", "pricing", "Acme Rota costs £9 a month per café.", "Pricing: £9 a month per café."),
        fact("url", "url", "Acme Rota is live at acmerota.example.co.uk.", "Live at https://acmerota.example.co.uk"),
        fact("lim-payroll", "limitation", "Payroll export is not built yet.", "Not built yet: payroll export."),
    ],
}


@pytest.fixture
def root(tmp_path):
    (tmp_path / "config").mkdir()
    shutil.copy(REPO / "config" / "settings.example.json", tmp_path / "config" / "settings.example.json")
    reg = {"owner": "example", "products": [{
        "slug": "acme", "name": "Acme Rota", "owner": "example", "repo": "acme", "default_branch": "main",
        "category": "saas_product", "enabled": True, "approved_paths": ["README.md"], "last_successful_sync": None}],
        "excluded": []}
    (tmp_path / "config" / "repositories.json").write_text(json.dumps(reg))
    (tmp_path / "config" / "channels.json").write_text(json.dumps(
        {"products": {"acme": [{"destination": "metricool:instagram", "account": "acme", "verified": True}]}}))
    pdir = tmp_path / "data" / "products" / "acme"
    (pdir / "sources").mkdir(parents=True)
    (pdir / "profile.json").write_text(json.dumps(PROFILE))
    (pdir / "sources" / "README.md").write_text(README)
    film = tmp_path / "assets" / "acme" / "film"
    film.mkdir(parents=True)
    (film / "still_01_hook.jpg").write_bytes(b"jpg")
    (tmp_path / "config" / "settings.json").write_text(json.dumps(
        {"media": {"base_url": "https://media.example.test/repo"}, "metricool": {"blog_id": "123"}}))
    return tmp_path


@pytest.fixture
def ctx(root, monkeypatch):
    monkeypatch.delenv("MAS_KILL_SWITCH", raising=False)
    return Context.create(root=root, db=":memory:")
