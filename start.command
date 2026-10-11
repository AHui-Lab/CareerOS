#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  echo "请先双击 install.command 安装运行环境。"
  exit 1
fi
.venv/bin/python mac_launcher.py start
