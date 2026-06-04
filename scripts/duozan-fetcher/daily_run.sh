#!/bin/bash
# ============================================================
# daily_run.sh - 多赞采购单每日抓取 + dashboard 更新主控
#
# 流程：
#   [1] 跑 fetch_and_export.py 抓昨天数据 → 落 xlsx
#   [2] 解析输出（订单数/金额/利润） → 飞书通知
#   [3] 跑 update.sh（export_data + export_detail + refresh_dashboards）
#       → 23 个看板 json 刷新
#   [4] 跑 notify_dashboard.sh → 飞书新品日报
#
# 退出码：
#   0 = 全流程成功
#   1 = 抓取失败
#   2 = token 失效
#   3 = 抓取异常（API 错等）
#   4 = 抓取成功但 dashboard 更新失败
# ============================================================
set -e

# launchd 默认 PATH 不全，必须手动补
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DUOZAN_SCRIPTS="/Users/manba/Documents/OH-WorkSpace/多赞数据库/多赞采购单/scripts"
YESTERDAY="$(date -v-1d +%Y-%m-%d)"
LOG_FILE="/tmp/duozan-fetcher.log"

echo "========================================" | tee -a "$LOG_FILE"
echo "  多赞采购单抓取 + dashboard 更新 - $YESTERDAY" | tee -a "$LOG_FILE"
echo "  启动时间: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# ============================================================
# [1] 抓取数据
# ============================================================
cd "$SCRIPT_DIR"
OUTPUT=$(python3 fetch_and_export.py "$YESTERDAY" 2>&1)
EXIT_CODE=$?

echo "$OUTPUT" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# ============================================================
# [2] 解析输出，发抓取通知
# ============================================================
if [ $EXIT_CODE -ne 0 ]; then
    ERROR_MSG="抓取异常 (exit=$EXIT_CODE)"
    if [ $EXIT_CODE -eq 2 ]; then
        ERROR_MSG="token 失效或读取失败"
        python3 notify.py token_expired
        exit 2
    fi
    python3 notify.py failure "$YESTERDAY" "$ERROR_MSG"
    exit 1
fi

# 成功 - 提取订单数/金额/利润
COUNT=$(echo "$OUTPUT" | grep "订单条数:" | grep -oE "[0-9]+" | head -1)
PAY=$(echo "$OUTPUT" | grep "金额合计:" | grep -oE "¥[0-9,]+\.[0-9]+" | head -1 | sed 's/¥//;s/,//')
PROFIT=$(echo "$OUTPUT" | grep "利润合计:" | grep -oE "¥[0-9,]+\.[0-9]+" | head -1 | sed 's/¥//;s/,//')

if [ -z "$COUNT" ] || [ -z "$PAY" ] || [ -z "$PROFIT" ]; then
    python3 notify.py failure "$YESTERDAY" "解析输出失败 (count/pay/profit 缺失)"
    exit 1
fi

# 数据合理性检查
if [ "$COUNT" -lt 50 ]; then
    python3 notify.py failure "$YESTERDAY" "订单数 $COUNT 异常少（正常 350-500），可能抓取异常"
    exit 1
fi

python3 notify.py success "$YESTERDAY" "$COUNT" "$PAY" "$PROFIT"
echo "  ✅ 抓取完成: $COUNT 单, ¥$PAY, 利润 ¥$PROFIT" | tee -a "$LOG_FILE"

# ============================================================
# [3] 跑 dashboard 更新（26 汇总 + 10 明细 + 23 看板）
# ============================================================
echo "" | tee -a "$LOG_FILE"
echo "----------------------------------------" | tee -a "$LOG_FILE"
echo "  [3/5] 跑 dashboard 更新流水线" | tee -a "$LOG_FILE"
echo "----------------------------------------" | tee -a "$LOG_FILE"

DASH_START=$(date '+%s')
if bash "$DUOZAN_SCRIPTS/update.sh" 2>&1 | tee -a "$LOG_FILE"; then
    DASH_END=$(date '+%s')
    DASH_DUR=$((DASH_END - DASH_START))
    echo "  ✅ dashboard 更新完成（耗时 ${DASH_DUR}s）" | tee -a "$LOG_FILE"
else
    DASH_END=$(date '+%s')
    DASH_DUR=$((DASH_END - DASH_START))
    echo "  ❌ dashboard 更新失败（耗时 ${DASH_DUR}s）" | tee -a "$LOG_FILE"
    python3 notify.py failure "$YESTERDAY" "dashboard 更新失败（抓取数据已落盘），详见 /tmp/duozan_update.log"
    exit 4
fi

# ============================================================
# [4] 推送到 GitHub，触发 EdgeOne Pages 自动部署（→ 网页版刷新）
# ============================================================
echo "" | tee -a "$LOG_FILE"
echo "----------------------------------------" | tee -a "$LOG_FILE"
echo "  [4/5] 推送 GitHub + 触发 EdgeOne Pages 部署" | tee -a "$LOG_FILE"
echo "----------------------------------------" | tee -a "$LOG_FILE"

SYNC_START=$(date '+%s')
if bash "/Users/manba/Documents/OH-WorkSpace/多赞数据库/多赞采购单/sync.sh" 2>&1 | tee -a "$LOG_FILE"; then
    SYNC_END=$(date '+%s')
    SYNC_DUR=$((SYNC_END - SYNC_START))
    echo "  ✅ GitHub 推送完成（耗时 ${SYNC_DUR}s，1-2 分钟后网页版自动刷新）" | tee -a "$LOG_FILE"
else
    SYNC_END=$(date '+%s')
    SYNC_DUR=$((SYNC_END - SYNC_START))
    echo "  ❌ GitHub 推送失败（耗时 ${SYNC_DUR}s）" | tee -a "$LOG_FILE"
    python3 notify.py failure "$YESTERDAY" "GitHub 推送失败（数据已落盘，需手动 sync.sh），详见 /tmp/duozan-fetcher.log"
    exit 5
fi

# ============================================================
# [5] 最终汇总
# ============================================================
echo "" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "  ✅ 全流程完成" | tee -a "$LOG_FILE"
echo "  - 抓取: $COUNT 单 / ¥$PAY / 利润 ¥$PROFIT" | tee -a "$LOG_FILE"
echo "  - xlsx: /多赞采购单/数据/按日期/$YESTERDAY/" | tee -a "$LOG_FILE"
echo "  - 看板: 23 个 json 已刷新" | tee -a "$LOG_FILE"
echo "  - 完成时间: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
exit 0
