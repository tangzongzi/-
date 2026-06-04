#!/bin/bash
# update.sh — 多赞数据每日更新入口
# 跑 3 个脚本：export_data + export_detail + refresh_dashboards
# 设计：幂等（可重复跑）；失败不会破坏已有数据（先输出到临时文件再 mv）

set -e

SCRIPTS_DIR="/Users/manba/Documents/OH-WorkSpace/多赞数据库/多赞采购单/scripts"
LOG_FILE="/tmp/duozan_update.log"
TS=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TS] === 多赞数据更新开始 ===" >> "$LOG_FILE"

cd "$SCRIPTS_DIR"

echo "[$TS] [1/3] export_data.py（26 个汇总 json）..." >> "$LOG_FILE"
python3 export_data.py >> "$LOG_FILE" 2>&1

echo "[$TS] [2/3] export_detail.py（10 个明细文件）..." >> "$LOG_FILE"
python3 export_detail.py >> "$LOG_FILE" 2>&1

echo "[$TS] [3/3] refresh_dashboards.py（23 个看板 json）..." >> "$LOG_FILE"
python3 refresh_dashboards.py >> "$LOG_FILE" 2>&1

echo "[$TS] [4/4] notify_dashboard.sh（飞书新品日报，失败不影响数据流程）..." >> "$LOG_FILE"
bash "$SCRIPTS_DIR/notify_dashboard.sh" >> "$LOG_FILE" 2>&1

TS_END=$(date '+%Y-%m-%d %H:%M:%S')
echo "[$TS_END] === 多赞数据更新完成 ===" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
