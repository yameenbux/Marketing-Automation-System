"""Central permission and policy framework.

Every side-effecting action in the system calls `Policy.authorize()` first. No
module is allowed to publish, send, spend or call an external service any other
way. The rules are deliberately few and enforced in code, not in prompts:

1. Kill switch (settings, env MAS_KILL_SWITCH, or var/KILL_SWITCH file) blocks everything.
2. A disabled integration blocks its actions.
3. PUBLISH and SEND_OUTREACH are *live* only if dry_run is off AND the matching
   `live.*` flag is on AND the daily limit allows. Otherwise they are simulated
   (dry-run) — or blocked when the limit for live sends is 0.
4. Daily and monthly limits are counted from the audit table, so a crash/retry
   can't reset them.
5. Every decision, allowed or not, is written to the audit log.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from enum import Enum
from zoneinfo import ZoneInfo

from .config import Settings
from .store import Store


class Action(str, Enum):
    FETCH_EXTERNAL = "fetch_external"     # read-only network (GitHub, screenshots, research APIs)
    RENDER = "render"                     # local CPU video rendering (daily-limited)
    SYNTH_AUDIO = "synth_audio"           # local TTS (free, not limited)
    LLM_CALL = "llm_call"                 # paid API generation
    PUBLISH = "publish"                   # social posting / scheduling
    SEND_OUTREACH = "send_outreach"       # any message to a prospect
    DRAFT_OUTREACH = "draft_outreach"     # local drafts only


# Actions with an outward effect on the real world.
LIVE_GATED = {Action.PUBLISH: "publishing", Action.SEND_OUTREACH: "outreach_sending"}

DAILY_LIMIT_KEY = {
    Action.RENDER: "max_renders_per_day",
    Action.PUBLISH: "max_posts_per_day",
    Action.DRAFT_OUTREACH: "max_drafts_per_day",
    Action.SEND_OUTREACH: "max_outreach_per_day",
}


class PolicyError(PermissionError):
    pass


@dataclass(frozen=True)
class Decision:
    mode: str            # "live" | "simulate" | "blocked"
    reason: str

    @property
    def allowed(self) -> bool:
        return self.mode != "blocked"

    @property
    def live(self) -> bool:
        return self.mode == "live"


class Policy:
    def __init__(self, settings: Settings, store: Store):
        self.settings = settings
        self.store = store
        self.tz = ZoneInfo(settings["timezone"])

    # --- kill switch -------------------------------------------------------
    def kill_switch_active(self) -> bool:
        return bool(self.settings["kill_switch"]) or self.settings.kill_switch_file.exists()

    def engage_kill_switch(self, reason: str) -> None:
        self.settings.kill_switch_file.parent.mkdir(parents=True, exist_ok=True)
        self.settings.kill_switch_file.write_text(reason + "\n", encoding="utf-8")
        self.store.audit("kill_switch", "system", "ok", f"engaged: {reason}")

    def release_kill_switch(self) -> None:
        if self.settings.kill_switch_file.exists():
            self.settings.kill_switch_file.unlink()
        self.store.audit("kill_switch", "system", "ok", "released (file); settings/env flags still apply")

    # --- time helpers ------------------------------------------------------
    def london_now(self) -> datetime:
        return datetime.now(self.tz)

    def start_of_london_day_utc(self) -> str:
        n = self.london_now()
        start = datetime.combine(n.date(), time(0, 0), tzinfo=self.tz)
        return start.astimezone(ZoneInfo("UTC")).isoformat(timespec="seconds")

    def start_of_london_month_utc(self) -> str:
        n = self.london_now()
        start = datetime(n.year, n.month, 1, tzinfo=self.tz)
        return start.astimezone(ZoneInfo("UTC")).isoformat(timespec="seconds")

    # --- the one gate ------------------------------------------------------
    def authorize(self, action: Action, integration: str, *, detail: dict | None = None,
                  estimated_cost_gbp: float = 0.0) -> Decision:
        decision = self._decide(action, integration, estimated_cost_gbp)
        outcome = {"live": "live", "simulate": "simulated", "blocked": "blocked"}[decision.mode]
        self.store.audit(action.value, integration, outcome, decision.reason, detail)
        return decision

    def require(self, action: Action, integration: str, **kw) -> Decision:
        d = self.authorize(action, integration, **kw)
        if not d.allowed:
            raise PolicyError(f"{action.value} via {integration} blocked: {d.reason}")
        return d

    def _decide(self, action: Action, integration: str, cost: float) -> Decision:
        if self.kill_switch_active():
            return Decision("blocked", "kill switch is active")
        if not self.settings.integration_enabled(integration):
            return Decision("blocked", f"integration '{integration}' is disabled")

        limit_key = DAILY_LIMIT_KEY.get(action)
        if limit_key is not None:
            limit = self.settings.limit(limit_key)
            used = self.store.count_audit_since(action.value, self.start_of_london_day_utc(), outcomes=("live",)) \
                if action in LIVE_GATED else \
                self.store.count_audit_since(action.value, self.start_of_london_day_utc())
            if action not in LIVE_GATED and used >= limit:
                return Decision("blocked", f"daily limit {limit_key}={limit} reached")

        if cost > 0:
            month = self.start_of_london_month_utc()
            if self.store.spend_since(month) + cost > self.settings.limit("monthly_budget_gbp"):
                return Decision("blocked", "monthly budget would be exceeded")
            if action is Action.LLM_CALL and \
                    self.store.spend_since(month, integration) + cost > self.settings.limit("monthly_llm_budget_gbp"):
                return Decision("blocked", "monthly LLM budget would be exceeded")

        if action in LIVE_GATED:
            flag = LIVE_GATED[action]
            live_requested = (not self.settings["dry_run"]) and bool(self.settings["live"].get(flag))
            if not live_requested:
                return Decision("simulate", f"dry-run (dry_run={self.settings['dry_run']}, live.{flag}="
                                            f"{self.settings['live'].get(flag)})")
            limit = self.settings.limit(limit_key)
            if limit <= 0:
                return Decision("blocked", f"live {action.value} requested but {limit_key} is 0")
            used = self.store.count_audit_since(action.value, self.start_of_london_day_utc(), outcomes=("live",))
            if used >= limit:
                return Decision("blocked", f"daily limit {limit_key}={limit} reached")
            return Decision("live", f"live {flag} enabled by operator")

        return Decision("live", "allowed")

    # --- operating window --------------------------------------------------
    def within_operating_hours(self, at: datetime | None = None) -> bool:
        at = (at or self.london_now()).astimezone(self.tz)
        oh = self.settings["operating_hours"]
        if at.weekday() not in oh["days"]:
            return False
        start = time.fromisoformat(oh["start"])
        end = time.fromisoformat(oh["end"])
        return start <= at.time() < end
