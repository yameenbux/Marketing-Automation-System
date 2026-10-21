"""Wires settings, store and policy together for CLI and workflows."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import Settings
from .policy import Policy
from .store import Store


@dataclass
class Context:
    settings: Settings
    store: Store
    policy: Policy

    @property
    def root(self) -> Path:
        return self.settings.root

    @classmethod
    def create(cls, root: Path | None = None, overrides: dict | None = None, db: str | None = None) -> "Context":
        settings = Settings.load(root, overrides)
        store = Store(db or settings.var_dir / "mas.sqlite")
        return cls(settings, store, Policy(settings, store))
