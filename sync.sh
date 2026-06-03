#!/bin/bash
# sync.sh — 一键同步到 GitHub（触发 EdgeOne Pages 自动部署）
#
# 用法：bash sync.sh
# 前置：先跑 bash update.sh 生成最新数据
#
# 流程：
# 1. 检查是否有变更
# 2. 自动 commit（带日期）
# 3. push 到 GitHub
# 4. EdgeOne Pages 自动拉取部署

set -e
cd "$(dirname "$0")"

echo "=== 多赞数据同步 ==="

# 检查是否有变更
if git diff --quiet && git diff --cached --quiet; then
  echo "没有变更，跳过"
  exit 0
fi

# 统计变更
changed=$(git diff --stat | tail -1)
echo "变更: $changed"

# commit
DATE=$(date +%Y-%m-%d)
git add -A
git commit -m "📊 数据更新 $DATE" || echo "没有新变更"

# push
echo "推送到 GitHub..."
git push origin main

echo ""
echo "✓ 同步完成。EdgeOne Pages 将自动部署。"
echo "  预计 1-2 分钟后生效。"
