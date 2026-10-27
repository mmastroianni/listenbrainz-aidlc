#!/usr/bin/env bash
# Pre-merge check: lint, format check, type check, and tests with the 80% coverage floor.
# Run as: bash scripts/check.sh
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

# NFR5.1 / BR6.1: data and built models must never be tracked by git.
if git rev-parse --git-dir >/dev/null 2>&1; then
    tracked="$(git ls-files -- data models '*.parquet' '*.faiss' '*.sqlite')"
    if [ -n "$tracked" ]; then
        echo "FAIL: data or model files are tracked by git:" >&2
        echo "$tracked" >&2
        exit 1
    fi
fi

echo "== ruff check =="
uv run ruff check .

echo "== ruff format --check =="
uv run ruff format --check .

echo "== ty =="
uv run ty check

echo "== pytest (coverage floor 80%) =="
uv run pytest tests -q --cov=listenbrainz_recs --cov-report=term-missing --cov-fail-under=80

echo "All checks passed."
