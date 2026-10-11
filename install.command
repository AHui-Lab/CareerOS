#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
PYTHON="${CAREEROS_PYTHON:-python3}"
BUNDLED="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
if [ -z "${CAREEROS_PYTHON:-}" ] && [ -x "$BUNDLED" ]; then
  PYTHON="$BUNDLED"
fi
if [ ! -x .venv/bin/python ]; then
  "$PYTHON" -m venv .venv
fi
.venv/bin/python -m pip install -r JobPilot/requirements.txt -r CareerVault/requirements.txt
if [ ! -f JobPilot/.env ]; then
  cp JobPilot/.env.example JobPilot/.env
fi
echo "安装完成。双击 start.command 启动 CareerOS。"
