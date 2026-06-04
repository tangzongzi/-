#!/bin/bash
# ============================================================
# realtime_run.sh - 多赞采购单 4h 一次实时追踪 + dashboard 推送
#
# 流程：
#   1. 跑 fetch_and_export.py --realtime 抓"今天" → 落 /按日期/
#   2. 跑 update.sh（生成 26 汇总 + 10 明细 + 23 看板 json）
#   3. 跑 sync.sh → 推 GitHub → EdgeOne Pages 自动部署
#   4. 飞书实时通知
#
# 用法：bash realtime_run.sh
# ============================================================
set -e

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DUOZAN_SCRIPTS="/Users/manba/Documents/OH-WorkSpace/多赞数据库/多赞采购单/scripts"
DUOZAN_ROOT="/Users/manba/Documents/OH-WorkSpace/多赞数据库/多赞采购单"
TODAY="$(date +%Y-%m-%d)"
SLOT="$(date +%H:%M)"
LOG_FILE="/tmp/duozan-fetcher.log"

echo "========================================" | tee -a "$LOG_FILE"
echo "  多赞实时追踪 - $TODAY $SLOT" | tee -a "$LOG_FILE"
echo "  启动时间: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

cd "$SCRIPT_DIR"

# ============================================================
# [1] 实时抓取（落 /按日期/YYYY-MM-DD/，覆盖同名 = 最新进度）
# ============================================================
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

# ============================================================
# [2] 跑 dashboard 更新（生成 23 个看板 json）
# ============================================================
echo "" | tee -a "$LOG_FILE"
echo "----------------------------------------" | tee -a "$LOG_FILE"
echo "  [2/4] 跑 dashboard 更新流水线" | tee -a "$LOG_FILE"
echo "----------------------------------------" | tee -a "$LOG_FILE"

DASH_START=$(date '+%s')
if bash "$DUOZAN_SCRIPTS/update.sh" 2>&1 | tee -a "$LOG_FILE"; then
    DASH_DUR=$(($(date '+%s') - DASH_START))
    echo "  ✅ dashboard 更新完成（耗时 ${DASH_DUR}s）" | tee -a "$LOG_FILE"
else
    echo "  ❌ dashboard 更新失败" | tee -a "$LOG_FILE"
    python3 notify.py failure "$TODAY" "实时 dashboard 更新失败"
    exit 4
fi

# ============================================================
# [3] 推 GitHub → EdgeOne Pages 自动部署（→ 网页版刷新）
# ============================================================
echo "" | tee -a "$LOG_FILE"
echo "----------------------------------------" | tee -a "$LOG_FILE"
echo "  [3/4] 推 GitHub + 触发 EdgeOne Pages 部署" | tee -a "$LOG_FILE"
echo "----------------------------------------" | tee -a "$LOG_FILE"

SYNC_START=$(date '+%s')
if bash "$DUOZAN_ROOT/sync.sh" 2>&1 | tee -a "$LOG_FILE"; then
    SYNC_DUR=$(($(date '+%s') - SYNC_START))
    echo "  ✅ GitHub 推送完成（耗时 ${SYNC_DUR}s，1-2 分钟后网页版刷新）" | tee -a "$LOG_FILE"
else
    echo "  ❌ GitHub 推送失败" | tee -a "$LOG_FILE"
    python3 notify.py failure "$TODAY" "实时 GitHub 推送失败（数据已落盘，需手动 sync.sh）"
    exit 5
fi

# ============================================================
# [4] 飞书实时通知
# ============================================================
python3 notify.py realtime "$TODAY" "$COUNT" "$PAY" "$PROFIT" "$SLOT"

echo "  ✅ 实时追踪完成: $COUNT 单 / ¥$PAY / 利润 ¥$PROFIT ($SLOT)" | tee -a "$LOG_FILE"
echo "  📡 已推 GitHub → 网页版 1-2 分钟后刷新" | tee -a "$LOG_FILE"
exit 0
