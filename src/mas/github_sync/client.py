"""Read-only GitHub client for public repositories.

Strategy, in order:
  1. GitHub REST API (unauthenticated by default; optional read-only token) — gives file blob SHAs,
     commit SHAs, ETag caching and pagination.
  2. If the REST API refuses (403 from a proxy, or rate-limited with a long reset), fall back to
     raw.githubusercontent.com for file content and `git ls-remote` for the commit SHA.
     The blob SHA is computed locally — it is identical to GitHub's.

This module never issues anything other than GET requests / ls-remote.
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Callable, Protocol

API = "https://api.github.com"
RAW = "https://raw.githubusercontent.com"
_NAME = re.compile(r"^[A-Za-z0-9_.-]{1,100}$")
_REF = re.compile(r"^[A-Za-z0-9_./-]{1,200}$")


@dataclass
class Response:
    status: int
    headers: dict[str, str]
    body: bytes


class Transport(Protocol):
    def __call__(self, url: str, headers: dict[str, str]) -> Response: ...


class GitHubError(RuntimeError):
    pass


class RateLimited(GitHubError):
    def __init__(self, reset_epoch: int | None):
        super().__init__(f"GitHub rate limit exhausted; resets at {reset_epoch}")
        self.reset_epoch = reset_epoch


class ApiUnavailable(GitHubError):
    """The REST API refused for a reason other than not-found (e.g. proxy policy)."""


def urllib_transport(url: str, headers: dict[str, str]) -> Response:
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:  # noqa: S310 — URL built from validated parts
            return Response(r.status, {k.lower(): v for k, v in r.headers.items()}, r.read(2_000_001))
    except urllib.error.HTTPError as e:
        return Response(e.code, {k.lower(): v for k, v in (e.headers or {}).items()}, e.read(65536) if e.fp else b"")


def git_blob_sha(content: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(content) + content).hexdigest()  # noqa: S324 — git's own scheme


def validate_name(value: str, kind: str = "name") -> str:
    if not _NAME.match(value) or value in {".", ".."}:
        raise ValueError(f"invalid GitHub {kind}: {value!r}")
    return value


def validate_ref(ref: str) -> str:
    if not _REF.match(ref) or ".." in ref:
        raise ValueError(f"invalid ref: {ref!r}")
    return ref


def validate_repo_path(path: str) -> str:
    """Approved paths must be relative, normalised and free of traversal."""
    if not path or path.startswith(("/", "\\")) or "\\" in path or "\x00" in path:
        raise ValueError(f"invalid path: {path!r}")
    parts = path.split("/")
    if any(p in {"", ".", ".."} for p in parts):
        raise ValueError(f"invalid path: {path!r}")
    return path


class GitHubClient:
    def __init__(self, transport: Transport = urllib_transport, token: str | None = None,
                 max_requests: int = 120, max_wait_s: int = 60, retries: int = 3,
                 sleep: Callable[[float], None] = time.sleep,
                 ls_remote: Callable[[str, str, str], str | None] | None = None):
        self.transport = transport
        self.token = token
        self.max_requests = max_requests
        self.max_wait_s = max_wait_s
        self.retries = retries
        self.sleep = sleep
        self.requests_made = 0
        self.etags: dict[str, tuple[str, bytes]] = {}
        self.api_available = True
        self._ls_remote = ls_remote or _git_ls_remote

    # --- low level ---------------------------------------------------------
    def _headers(self, url: str, accept: str) -> dict[str, str]:
        h = {"Accept": accept, "User-Agent": "ysb-marketing-automation/0.1", "X-GitHub-Api-Version": "2022-11-28"}
        if self.token and url.startswith(API):
            h["Authorization"] = f"Bearer {self.token}"
        if url in self.etags:
            h["If-None-Match"] = self.etags[url][0]
        return h

    def get(self, url: str, accept: str = "application/vnd.github+json") -> Response:
        attempt = 0
        while True:
            if self.requests_made >= self.max_requests:
                raise GitHubError(f"request budget for this run exhausted ({self.max_requests})")
            self.requests_made += 1
            try:
                resp = self.transport(url, self._headers(url, accept))
            except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
                resp = None
                err: Exception | None = e
            else:
                err = None

            if resp is not None:
                if resp.status == 304 and url in self.etags:
                    return Response(200, resp.headers, self.etags[url][1])
                if resp.status in (403, 429) and resp.headers.get("x-ratelimit-remaining") == "0":
                    reset = int(resp.headers.get("x-ratelimit-reset", "0") or 0)
                    wait = max(0, reset - int(time.time()))
                    if wait <= self.max_wait_s and attempt < self.retries:
                        self.sleep(wait + 1)
                        attempt += 1
                        continue
                    raise RateLimited(reset or None)
                if resp.status == 429 or resp.status >= 500:
                    err = GitHubError(f"HTTP {resp.status}")
                else:
                    if resp.status == 200 and "etag" in resp.headers:
                        self.etags[url] = (resp.headers["etag"], resp.body)
                    return resp
            if attempt >= self.retries:
                raise GitHubError(f"GET {url} failed after {attempt + 1} attempts: {err}")
            self.sleep(min(2 ** attempt, 16))
            attempt += 1

    def get_json(self, url: str) -> object:
        r = self.get(url)
        if r.status == 404:
            raise FileNotFoundError(url)
        if r.status == 403:
            raise ApiUnavailable(_short(r.body))
        if r.status != 200:
            raise GitHubError(f"HTTP {r.status} for {url}")
        return json.loads(r.body)

    def paginate(self, url: str, max_pages: int = 10) -> list:
        out: list = []
        for _ in range(max_pages):
            r = self.get(url)
            if r.status != 200:
                raise ApiUnavailable(_short(r.body)) if r.status == 403 else GitHubError(f"HTTP {r.status}")
            out.extend(json.loads(r.body))
            nxt = _next_link(r.headers.get("link", ""))
            if not nxt:
                break
            url = nxt
        return out

    # --- high level --------------------------------------------------------
    def list_public_repos(self, owner: str) -> list[dict]:
        owner = validate_name(owner, "owner")
        return self.paginate(f"{API}/users/{owner}/repos?per_page=100&type=owner&sort=pushed")

    def head_commit(self, owner: str, repo: str, branch: str) -> str | None:
        owner, repo, branch = validate_name(owner), validate_name(repo), validate_ref(branch)
        if self.api_available:
            try:
                data = self.get_json(f"{API}/repos/{owner}/{repo}/commits/{urllib.parse.quote(branch, safe='')}")
                return data["sha"]  # type: ignore[index]
            except (ApiUnavailable, RateLimited):
                self.api_available = False
        return self._ls_remote(owner, repo, branch)

    def get_file(self, owner: str, repo: str, path: str, ref: str, max_bytes: int = 400_000) -> tuple[bytes, str, str]:
        """Return (content, blob_sha, via). Raises FileNotFoundError if absent."""
        owner, repo, ref, path = validate_name(owner), validate_name(repo), validate_ref(ref), validate_repo_path(path)
        qpath = urllib.parse.quote(path)
        if self.api_available:
            try:
                data = self.get_json(f"{API}/repos/{owner}/{repo}/contents/{qpath}?ref={urllib.parse.quote(ref)}")
                if not isinstance(data, dict) or data.get("type") != "file":
                    raise FileNotFoundError(path)
                if int(data.get("size", 0)) > max_bytes:
                    raise GitHubError(f"{path} exceeds {max_bytes} bytes")
                content = base64.b64decode(data.get("content", ""))
                return content, data["sha"], "api"
            except (ApiUnavailable, RateLimited):
                self.api_available = False
        r = self.get(f"{RAW}/{owner}/{repo}/{urllib.parse.quote(ref)}/{qpath}", accept="text/plain")
        if r.status == 404:
            raise FileNotFoundError(path)
        if r.status != 200:
            raise GitHubError(f"raw fetch HTTP {r.status} for {path}")
        if len(r.body) > max_bytes:
            raise GitHubError(f"{path} exceeds {max_bytes} bytes")
        return r.body, git_blob_sha(r.body), "raw"


def _git_ls_remote(owner: str, repo: str, branch: str) -> str | None:
    try:
        out = subprocess.run(  # noqa: S603 — fixed argv, validated components, no shell
            ["git", "ls-remote", f"https://github.com/{owner}/{repo}", f"refs/heads/{branch}"],
            capture_output=True, text=True, timeout=30, check=False,
        ).stdout
    except (OSError, subprocess.TimeoutExpired):
        return None
    m = re.match(r"^([0-9a-f]{40})\s", out)
    return m.group(1) if m else None


def _next_link(link: str) -> str | None:
    for part in link.split(","):
        m = re.search(r'<([^>]+)>;\s*rel="next"', part)
        if m and m.group(1).startswith(API):
            return m.group(1)
    return None


def _short(body: bytes) -> str:
    try:
        return str(json.loads(body).get("message", ""))[:200]
    except (ValueError, AttributeError):
        return body[:200].decode("utf-8", "replace")
