#!/bin/bash
# sync.sh — 跑完 update.sh 后自动 git commit + push
set -e
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

bash update.sh

MSG="data: $(date '+%Y-%m-%d %H:%M') 自动同步"
git add -A
git diff --cached --quiet || git commit -m "$MSG"
git push origin main
echo "✓ 已同步到 GitHub → EdgeOne 1-2 分钟后自动部署"
