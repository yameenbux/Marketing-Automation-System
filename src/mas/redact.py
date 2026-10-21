"""Secret detection and redaction.

Used in two places: scrubbing anything we log, and flagging possible credential
exposures in synced public repository content (we flag, never use).
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass

SECRET_PATTERNS: dict[str, re.Pattern[str]] = {
    "anthropic_key": re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}"),
    "openai_key": re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9]{32,}"),
    "github_token": re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}"),
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "stripe_secret": re.compile(r"\b(?:sk|rk)_live_[A-Za-z0-9]{20,}"),
    "slack_token": re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"),
    "google_api_key": re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b"),
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "jwt": re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    "supabase_service_role": re.compile(r"service_role[\"']?\s*[:=]\s*[\"']eyJ"),
    "generic_assignment": re.compile(
        r"(?i)\b(?:api[_-]?key|secret|password|passwd|token)\b\s*[:=]\s*[\"'][^\"'\s]{12,}[\"']"
    ),
}

# Placeholders that look like secrets in docs but are not.
_PLACEHOLDER = re.compile(r"(?i)(x{6,}|\.\.\.|your[_-]|example|placeholder|<[^>]+>|changeme)")


@dataclass(frozen=True)
class SecretFinding:
    kind: str
    line: int
    preview: str  # already redacted — safe to log


def scan(text: str) -> list[SecretFinding]:
    findings: list[SecretFinding] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for kind, pat in SECRET_PATTERNS.items():
            for m in pat.finditer(line):
                if _PLACEHOLDER.search(m.group(0)):
                    continue
                findings.append(SecretFinding(kind, lineno, _mask(m.group(0))))
    return findings


def _mask(value: str) -> str:
    return value[:4] + "…[REDACTED]" if len(value) > 4 else "[REDACTED]"


def redact(text: str) -> str:
    """Replace anything secret-shaped, plus the live values of known secret env vars."""
    if not text:
        return text
    for env_name in ("GITHUB_TOKEN", "ANTHROPIC_API_KEY", "COMPANIES_HOUSE_API_KEY"):
        val = os.environ.get(env_name)
        if val and len(val) >= 8:
            text = text.replace(val, "[REDACTED]")
    for pat in SECRET_PATTERNS.values():
        text = pat.sub(lambda m: _mask(m.group(0)), text)
    return text
