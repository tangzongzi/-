#!/usr/bin/env python3
"""
notify.py - 多赞抓取任务飞书通知（interactive card 格式）
=============================================================

跟 gen_daily_report.py 用同一套 E_* 元素工厂 + 视觉风格。

用法：
  python3 notify.py success "2026-06-04" 442 10643.33 758.33
  python3 notify.py failure "2026-06-04" "API 返回 401"
  python3 notify.py token_expired
  python3 notify.py realtime "2026-06-04" 442 10643.33 758.33 "13:00"
"""
import sys
import json
from datetime import datetime
from pathlib import Path

# 共享 helpers（同目录）
sys.path.insert(0, str(Path(__file__).resolve().parent))
from feishu_card import (
    E_md, E_hr, E_fields, E_actions, E_note, make_card, send_card, Tpl
)

# 读 config
CONFIG_FILE = Path.home() / ".config/duozan/config.json"
with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

CHAT_ID = CONFIG["feishu"]["chat_id"]
LARK_CLI = CONFIG["feishu"]["lark_cli"]
DASHBOARD_URL = "https://dy.zongzi.fun/daily-report"


# ---------- 各场景卡片构造 ----------
def build_success_card(date, count, pay, profit):
    """0:30 主任务：抓取成功（昨日完整数据）"""
    title = f"✅ 多赞采购单抓取成功 · {date}"
    elements = [
        E_md(
            f"📦 **{date}** 抓取完成 · 自动播报于 {datetime.now().strftime('%H:%M:%S')}"
        ),
        E_hr(),
        E_fields([
            ("📦 订单数", f"**{count}** 条"),
            ("💰 金额合计", f"**¥{pay:,.2f}**"),
            ("💎 利润合计", f"**¥{profit:,.2f}**"),
            ("🗂️ 数据文件", f"按日期/{date}/"),
        ]),
        E_note(f"⭐ 利润已剔除交易关闭订单 · 数据源：多赞易分销 API"),
    ]
    return make_card(title, elements, template=Tpl.GREEN)


def build_failure_card(date, error):
    """抓取失败（红色 header）"""
    title = f"❌ 多赞采购单抓取失败 · {date}"
    elements = [
        E_md(
            f"⏰ 失败时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"📅 抓取目标：{date}"
        ),
        E_hr(),
        E_md(
            f"**❌ 错误信息**\n"
            f"```\n{error}\n```"
        ),
        E_hr(),
        E_actions([
            ("🔧 检查 token.json 并重跑", "primary", "https://dy.zongzi.fun/"),
        ]),
        E_note("🤖 多赞自动抓取 · cron 0:30"),
    ]
    return make_card(title, elements, template=Tpl.RED)


def build_token_expired_card():
    """token 失效（红色 header，需手动处理）"""
    title = "⚠️ 多赞抓取 token 已失效"
    elements = [
        E_md(
            f"⏰ 失效时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"🔐 状态：token 过期，无法继续抓取"
        ),
        E_hr(),
        E_md(
            f"**🔧 解决步骤**\n"
            f"1. 在 HanaAgent 对话里说「重新登录多赞」\n"
            f"2. 系统会用 browser 工具自动登录并更新 token.json\n"
            f"3. 登录成功后自动恢复抓取"
        ),
        E_actions([
            ("🔄 立即重新登录", "primary", "https://dy.zongzi.fun/"),
        ]),
        E_note("🤖 多赞自动抓取 · cron 0:30"),
    ]
    return make_card(title, elements, template=Tpl.RED)


def build_realtime_card(date, count, pay, profit, slot):
    """实时追踪：今天 0:00 到现在累计"""
    title = f"🟢 多赞实时追踪 · {date}"
    elements = [
        E_md(
            f"⏰ 快照时段：**{slot}** · 自动播报于 {datetime.now().strftime('%H:%M')}"
        ),
        E_hr(),
        E_fields([
            ("📦 累计订单", f"**{count}** 单"),
            ("💰 累计金额", f"**¥{pay:,.2f}**"),
            ("💎 累计利润", f"**¥{profit:,.2f}**"),
            ("🕐 快照时间", f"**{datetime.now().strftime('%H:%M:%S')}**"),
        ]),
        E_hr(),
        E_md("⭐ 利润已剔除交易关闭订单 · 数据源：多赞易分销 API"),
        E_actions([
            ("📊 打开日报看板", "primary", DASHBOARD_URL),
            ("🏠 工作台", "default", "https://dy.zongzi.fun/"),
        ]),
        E_note(f"🤖 实时追踪 · cron 9/13/17/21/23:30 · slot={slot}"),
    ]
    return make_card(title, elements, template=Tpl.GREEN)


# ---------- 入口 ----------
def main():
    if len(sys.argv) < 2:
        print("用法: notify.py success|failure|token_expired|realtime ...")
        sys.exit(1)

    kind = sys.argv[1]
    if kind == "success":
        if len(sys.argv) < 6:
            print("success 需要 4 个参数: date count pay profit")
            sys.exit(1)
        card = build_success_card(sys.argv[2], int(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]))
    elif kind == "failure":
        if len(sys.argv) < 4:
            print("failure 需要 2 个参数: date error")
            sys.exit(1)
        card = build_failure_card(sys.argv[2], sys.argv[3])
    elif kind == "token_expired":
        card = build_token_expired_card()
    elif kind == "realtime":
        if len(sys.argv) < 7:
            print("realtime 需要 5 个参数: date count pay profit slot")
            sys.exit(1)
        card = build_realtime_card(sys.argv[2], int(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]), sys.argv[6])
    else:
        print(f"未知类型: {kind}")
        sys.exit(1)

    # 幂等键：日期 + HHMMSS（同一分钟内重复调用会被去重）
    date_part = sys.argv[2] if kind not in ("token_expired",) else datetime.now().strftime("%Y-%m-%d")
    idempotency_key = f"duozan-{kind}-{date_part}-{datetime.now().strftime('%H%M%S')}"
    message_id = send_card(card, CHAT_ID, LARK_CLI, as_user="bot", idempotency_key=idempotency_key)
    return 0 if message_id else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"❌ 脚本未捕获异常: {e}", file=sys.stderr)
        sys.exit(1)
