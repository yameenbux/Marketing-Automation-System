"""Settings loading. Defaults are safe: dry-run on, live actions off.

Precedence: built-in defaults < config/settings.json < environment variables.
Secrets are only ever read from the environment, never from JSON files.
"""
from __future__ import annotations

import copy
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(os.environ.get("MAS_ROOT", Path(__file__).resolve().parents[2]))

DEFAULTS: dict[str, Any] = {
    "timezone": "Europe/London",
    "operating_hours": {"days": [0, 1, 2, 3, 4], "start": "09:00", "end": "17:00"},
    "schedule": {"daily_planner": "09:00", "daily_report": "16:30"},
    "dry_run": True,
    "kill_switch": False,
    "integrations": {
        "github_public": {"enabled": True},
        "local_render": {"enabled": True},
        "piper_tts": {"enabled": True},
        "playwright_screenshots": {"enabled": True, "allowed_hosts": []},
        "anthropic_llm": {"enabled": False},
        "metricool_outbox": {"enabled": True},
        "companies_house": {"enabled": False},
        "email_sending": {"enabled": False},
    },
    "live": {"publishing": False, "outreach_sending": False},
    "limits": {
        "monthly_budget_gbp": 50,
        "monthly_llm_budget_gbp": 5,
        "max_github_requests_per_run": 120,
        "max_renders_per_day": 6,
        "max_posts_per_day": 3,
        "max_drafts_per_day": 20,
        "max_outreach_per_day": 0,
    },
    "github": {"owner": "yameenbux", "max_file_bytes": 400_000},
}

SECRET_ENV_VARS = ("GITHUB_TOKEN", "ANTHROPIC_API_KEY", "COMPANIES_HOUSE_API_KEY")
TRUTHY = {"1", "true", "yes", "on"}


def _merge(base: dict, override: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in override.items():
        if k.startswith("_"):
            continue
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


@dataclass
class Settings:
    data: dict[str, Any]
    root: Path = field(default=ROOT)

    @classmethod
    def load(cls, root: Path | None = None, overrides: dict | None = None) -> "Settings":
        root = Path(root or ROOT)
        data = copy.deepcopy(DEFAULTS)
        # settings.ops.json (committed: operating mode for scheduled runs) then settings.json (local, gitignored).
        for ops in [root / "config" / "settings.ops.json"]:
            if ops.exists():
                data = _merge(data, json.loads(ops.read_text(encoding="utf-8")))
        path = root / "config" / "settings.json"
        if path.exists():
            loaded = json.loads(path.read_text(encoding="utf-8"))
            for secret_key in ("token", "api_key", "password", "secret"):
                if _contains_key(loaded, secret_key):
                    raise ValueError(
                        f"config/settings.json contains a '{secret_key}' field; secrets belong in the environment"
                    )
            data = _merge(data, loaded)
        if overrides:
            data = _merge(data, overrides)
        if os.environ.get("MAS_KILL_SWITCH", "").strip().lower() in TRUTHY:
            data["kill_switch"] = True
        if os.environ.get("MAS_DRY_RUN", "").strip().lower() in TRUTHY:
            data["dry_run"] = True
        return cls(data=data, root=root)

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    def integration_enabled(self, name: str) -> bool:
        return bool(self.data["integrations"].get(name, {}).get("enabled", False))

    def limit(self, name: str) -> float:
        return self.data["limits"][name]

    @property
    def var_dir(self) -> Path:
        p = self.root / "var"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def kill_switch_file(self) -> Path:
        return self.root / "var" / "KILL_SWITCH"

    @staticmethod
    def secret(name: str) -> str | None:
        if name not in SECRET_ENV_VARS:
            raise KeyError(f"{name} is not a registered secret")
        value = os.environ.get(name, "").strip()
        return value or None


def _contains_key(obj: Any, needle: str) -> bool:
    if isinstance(obj, dict):
        return any(needle in str(k).lower() or _contains_key(v, needle) for k, v in obj.items())
    if isinstance(obj, list):
        return any(_contains_key(v, needle) for v in obj)
    return False
