"""Synchronise approved documentation paths from public product repositories.

Writes data/products/<slug>/sources/<path> (secret-redacted copy) and
sources/_sync.json (commit SHA, blob SHAs, timestamps, flags). Read-only towards GitHub.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from ..policy import Action, Policy
from ..redact import redact, scan
from ..store import now_iso
from .client import GitHubClient, GitHubError, validate_repo_path
from .untrusted import injection_flags

ALLOWED_SUFFIXES = (".md", ".mdx", ".markdown", ".txt", ".rst")


@dataclass
class RepoSyncResult:
    slug: str
    commit: str | None = None
    changed: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    secret_flags: list[dict] = field(default_factory=list)
    injection_flags: list[dict] = field(default_factory=list)
    via: set[str] = field(default_factory=set)

    @property
    def ok(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict:
        d = self.__dict__.copy()
        d["via"] = sorted(self.via)
        return d


def load_registry(root: Path) -> dict:
    return json.loads((root / "config" / "repositories.json").read_text(encoding="utf-8"))


def save_registry(root: Path, reg: dict) -> None:
    (root / "config" / "repositories.json").write_text(json.dumps(reg, indent=2) + "\n", encoding="utf-8")


def safe_dest(base: Path, rel: str) -> Path:
    rel = validate_repo_path(rel)
    dest = (base / rel).resolve()
    if base.resolve() not in dest.parents:
        raise ValueError(f"path escapes sources dir: {rel}")
    return dest


def sync_product(entry: dict, client: GitHubClient, policy: Policy, root: Path,
                 max_bytes: int = 400_000) -> RepoSyncResult:
    res = RepoSyncResult(entry["slug"])
    decision = policy.authorize(Action.FETCH_EXTERNAL, "github_public", detail={"repo": entry["repo"]})
    if not decision.allowed:
        res.errors.append(decision.reason)
        return res

    owner, repo, branch = entry["owner"], entry["repo"], entry.get("default_branch", "main")
    base = root / "data" / "products" / entry["slug"] / "sources"
    base.mkdir(parents=True, exist_ok=True)
    meta_path = base / "_sync.json"
    prev = json.loads(meta_path.read_text()) if meta_path.exists() else {"files": {}}

    try:
        res.commit = client.head_commit(owner, repo, branch)
    except GitHubError as e:
        res.errors.append(f"commit lookup: {e}")

    files_meta = dict(prev.get("files", {}))
    for path in entry.get("approved_paths", []):
        try:
            validate_repo_path(path)
            if not path.lower().endswith(ALLOWED_SUFFIXES):
                res.errors.append(f"{path}: only documentation files may be synced")
                continue
            content, sha, via = client.get_file(owner, repo, path, branch, max_bytes=max_bytes)
        except FileNotFoundError:
            res.missing.append(path)
            continue
        except (GitHubError, ValueError) as e:
            res.errors.append(f"{path}: {e}")
            continue
        res.via.add(via)
        text = content.decode("utf-8", "replace")
        secrets = scan(text)
        inj = injection_flags(text)
        res.secret_flags += [{"path": path, "kind": s.kind, "line": s.line, "preview": s.preview} for s in secrets]
        res.injection_flags += [{"path": path, **f} for f in inj]
        if files_meta.get(path, {}).get("sha") == sha and safe_dest(base, path).exists():
            res.unchanged.append(path)
        else:
            dest = safe_dest(base, path)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(redact(text) if secrets else text, encoding="utf-8")
            res.changed.append(path)
        files_meta[path] = {"sha": sha, "via": via, "fetched_at": now_iso(),
                            "secret_flags": len(secrets), "injection_flags": len(inj)}
        policy.store.conn.execute(
            "INSERT INTO sync_state(repo, path, sha, fetched_at) VALUES (?,?,?,?) "
            "ON CONFLICT(repo, path) DO UPDATE SET sha=excluded.sha, fetched_at=excluded.fetched_at",
            (f"{owner}/{repo}", path, sha, now_iso()))
        policy.store.conn.commit()

    meta = {"repo": f"{owner}/{repo}", "branch": branch, "commit": res.commit or prev.get("commit"),
            "synced_at": now_iso(), "files": files_meta,
            "secret_flags": res.secret_flags, "injection_flags": res.injection_flags}
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    if res.secret_flags:
        policy.store.audit("secret_exposure_flag", "github_public", "ok",
                           f"{len(res.secret_flags)} possible secret(s) in {owner}/{repo} — manual review",
                           {"flags": res.secret_flags})
    return res


def sync_all(client: GitHubClient, policy: Policy, root: Path, only: str | None = None) -> list[RepoSyncResult]:
    reg = load_registry(root)
    results = []
    for entry in reg["products"]:
        if only and entry["slug"] != only:
            continue
        if not entry.get("enabled") and not only:
            continue
        r = sync_product(entry, client, policy, root, policy.settings["github"]["max_file_bytes"])
        if r.ok and (r.changed or r.unchanged):
            entry["last_successful_sync"] = now_iso()
            if r.commit:
                entry["last_synced_commit"] = r.commit
        results.append(r)
    save_registry(root, reg)
    return results
