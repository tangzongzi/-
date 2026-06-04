#!/bin/bash
# notify_dashboard.sh — 飞书新品日报通知包装
# 设计：
#   1. 调用 notify_dashboard.py
#   2. 无论成功失败，都不影响上游 update.sh（永远 exit 0）
#   3. 日志统一写到 /tmp/duozan_notify.log

set -u

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOG_FILE="/tmp/duozan_notify.log"
TS=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TS] === 飞书通知开始 ===" >> "$LOG_FILE"

cd "$SCRIPT_DIR"

python3 notify_dashboard.py >> "$LOG_FILE" 2>&1
EXIT=$?

if [ $EXIT -eq 0 ]; then
    echo "[$TS] ✅ 通知成功" >> "$LOG_FILE"
else
    echo "[$TS] ⚠️  通知失败（python exit=$EXIT），不影响数据流程" >> "$LOG_FILE"
fi

TS_END=$(date '+%Y-%m-%d %H:%M:%S')
echo "[$TS_END] === 飞书通知结束 ===" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# 永远返回 0，不影响上游 update.sh
exit 0
