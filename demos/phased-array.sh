#!/usr/bin/env bash
# Lecture shortcuts
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/.venv/bin/activate"
exec teaching-sims demo phased-array "$@"
