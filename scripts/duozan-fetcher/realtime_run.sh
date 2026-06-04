#!/bin/bash
# ============================================================
# realtime_run.sh - 多赞采购单 4h 一次实时追踪
#
# 流程：
#   1. 跑 fetch_and_export.py --realtime 抓"今天"数据
#   2. 落盘到 /tmp/_duozan_realtime/（不污染 dashboard）
#   3. 飞书通知"实时追踪 · {date}"
#
# 用法：bash realtime_run.sh
# ============================================================
set -e

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TODAY="$(date +%Y-%m-%d)"
SLOT="$(date +%H:%M)"  # 时段标签，如 09:00
LOG_FILE="/tmp/duozan-fetcher.log"

echo "========================================" | tee -a "$LOG_FILE"
echo "  多赞实时追踪 - $TODAY $SLOT" | tee -a "$LOG_FILE"
echo "  启动时间: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# 跑实时抓取
cd "$SCRIPT_DIR"
OUTPUT=$(python3 fetch_and_export.py "$TODAY" --realtime 2>&1)
EXIT_CODE=$?

echo "$OUTPUT" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

if [ $EXIT_CODE -ne 0 ]; then
    if [ $EXIT_CODE -eq 2 ]; then
        python3 notify.py token_expired
        exit 2
    fi
    python3 notify.py failure "$TODAY" "实时抓取异常 (exit=$EXIT_CODE)"
    exit 1
fi

# 解析
COUNT=$(echo "$OUTPUT" | grep "订单条数:" | grep -oE "[0-9]+" | head -1)
PAY=$(echo "$OUTPUT" | grep "金额合计:" | grep -oE "¥[0-9,]+\.[0-9]+" | head -1 | sed 's/¥//;s/,//')
PROFIT=$(echo "$OUTPUT" | grep "利润合计:" | grep -oE "¥[0-9,]+\.[0-9]+" | head -1 | sed 's/¥//;s/,//')

if [ -z "$COUNT" ] || [ -z "$PAY" ] || [ -z "$PROFIT" ]; then
    python3 notify.py failure "$TODAY" "实时追踪解析失败"
    exit 1
fi

# 飞书实时通知
python3 notify.py realtime "$TODAY" "$COUNT" "$PAY" "$PROFIT" "$SLOT"

echo "  ✅ 实时追踪完成: $COUNT 单 / ¥$PAY / 利润 ¥$PROFIT ($SLOT)" | tee -a "$LOG_FILE"
exit 0
