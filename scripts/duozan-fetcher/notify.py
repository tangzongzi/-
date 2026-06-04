#!/usr/bin/env python3
"""
notify.py - 多赞抓取任务飞书通知

用法：
  python3 notify.py success "2026-06-04" 442 10643.33 758.33
  python3 notify.py failure "2026-06-04" "API 返回 401"
  python3 notify.py token_expired
"""
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

# 读 config
CONFIG_FILE = Path.home() / ".config/duozan/config.json"
with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

CHAT_ID = CONFIG["feishu"]["chat_id"]
LARK_CLI = CONFIG["feishu"]["lark_cli"]


def send(message: str):
    """用 lark-cli 发消息到飞书群"""
    try:
        result = subprocess.run(
            [
                LARK_CLI, "im", "+messages-send",
                "--chat-id", CHAT_ID,
                "--markdown", message,
            ],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            print(f"❌ 飞书通知失败: {result.stderr}", file=sys.stderr)
            print(f"   stdout: {result.stdout}", file=sys.stderr)
        else:
            print(f"✅ 飞书通知已发: {message[:50]}...")
    except Exception as e:
        print(f"❌ 飞书通知异常: {e}", file=sys.stderr)


def fmt_success(date: str, count: int, pay: float, profit: float):
    return f"""✅ **多赞采购单抓取成功** · {date}

- 订单数: **{count}** 条
- 金额合计: **¥{pay:,.2f}**
- 利润合计: **¥{profit:,.2f}** (已剔除关闭订单)
- 文件: /多赞采购单/数据/按日期/{date}/
- 抓取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🤖 自动抓取 (Hanako 0:10 cron)"""


def fmt_failure(date: str, error: str):
    return f"""❌ **多赞采购单抓取失败** · {date}

- 错误: {error}
- 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🤖 自动抓取 (Hanako 0:10 cron)
👉 请检查 token.json 或重跑"""


def fmt_token_expired():
    return f"""⚠️ **多赞抓取 token 已失效**

- 状态: token 过期，无法继续抓取
- 解决: 在 HanaAgent 对话里说「重新登录多赞」，会用 browser 工具自动登录并更新 token.json
- 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🤖 自动抓取 (Hanako 0:10 cron)"""


def fmt_realtime(date: str, count: int, pay: float, profit: float, slot: str):
    """实时追踪通知：今天 0:00 到现在 累计订单"""
    return f"""🟢 **多赞实时追踪 · {date}**

- 时段: **{slot}**
- 累计订单: **{count}** 单
- 累计金额: **¥{pay:,.2f}**
- 累计利润: **¥{profit:,.2f}** (已剔除关闭订单)
- 快照时间: {datetime.now().strftime('%H:%M:%S')}

🤖 实时追踪 (Hanako 4h 一次)"""


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: notify.py success|failure|token_expired ...")
        sys.exit(1)

    kind = sys.argv[1]
    if kind == "success":
        if len(sys.argv) < 6:
            print("success 需要 4 个参数: date count pay profit")
            sys.exit(1)
        msg = fmt_success(sys.argv[2], int(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]))
    elif kind == "failure":
        if len(sys.argv) < 4:
            print("failure 需要 2 个参数: date error")
            sys.exit(1)
        msg = fmt_failure(sys.argv[2], sys.argv[3])
    elif kind == "token_expired":
        msg = fmt_token_expired()
    elif kind == "realtime":
        # python3 notify.py realtime YYYY-MM-DD count pay profit slot
        if len(sys.argv) < 7:
            print("realtime 需要 5 个参数: date count pay profit slot")
            sys.exit(1)
        msg = fmt_realtime(sys.argv[2], int(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]), sys.argv[6])
    else:
        print(f"未知类型: {kind}")
        sys.exit(1)

    send(msg)
