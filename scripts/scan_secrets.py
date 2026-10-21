#!/usr/bin/env python3
"""Fail if anything secret-shaped is tracked in git. Used in CI and as a pre-commit check."""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from mas.redact import scan  # noqa: E402

SKIP_SUFFIXES = (".png", ".jpg", ".jpeg", ".mp4", ".wav", ".onnx", ".gif", ".pdf")
ALLOW = {"tests/test_github_sync.py", "tests/test_policy.py"}  # contain deliberate synthetic fakes

files = subprocess.run(["git", "ls-files"], capture_output=True, text=True, check=True).stdout.split()
bad = []
for f in files:
    if f.endswith(SKIP_SUFFIXES) or f in ALLOW:
        continue
    if Path(f).name in (".env",) or (Path(f).name.startswith(".env.") and not f.endswith(".example")):
        bad.append(f"{f}: .env file must not be committed")
        continue
    try:
        text = Path(f).read_text(encoding="utf-8")
    except (UnicodeDecodeError, FileNotFoundError):
        continue
    bad += [f"{f}:{x.line}: {x.kind} {x.preview}" for x in scan(text)]
if bad:
    print("Possible secrets found:\n" + "\n".join(bad))
    sys.exit(1)
print(f"secret scan: {len(files)} tracked files clean")
