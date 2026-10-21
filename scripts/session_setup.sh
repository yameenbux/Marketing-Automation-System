#!/usr/bin/env bash
# Prepare a fresh cloud session for scheduled marketing runs. Idempotent; safe to re-run.
#   scripts/session_setup.sh            core only (planning, approvals, publishing, report)
#   scripts/session_setup.sh --render   also voices + Playwright for film rendering
set -euo pipefail
cd "$(dirname "$0")/.."
pip install -q -e ".[dev]" 2>&1 | grep -v -i "warning" || true
if [[ "${1:-}" == "--render" ]]; then
  pip install -q "piper-tts>=1.2" "playwright==1.56.0" 2>&1 | grep -v -i "warning" || true
  mkdir -p models/piper
  for v in "alba/medium/en_GB-alba-medium" "cori/high/en_GB-cori-high" \
           "northern_english_male/medium/en_GB-northern_english_male-medium" "vctk/medium/en_GB-vctk-medium"; do
    f="models/piper/$(basename "$v").onnx"
    [[ -s "$f" ]] || curl -sSL -o "$f" "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/$v.onnx"
    [[ -s "$f.json" ]] || curl -sSL -o "$f.json" "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/$v.onnx.json"
  done
fi
mas state import
mas status | head -12
