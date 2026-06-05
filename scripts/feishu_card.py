#!/usr/bin/env python3
"""
feishu_card.py - 飞书 interactive card 共享构造器
====================================================

跟 duozan-dashboard/scripts/gen_daily_report.py 用同一套 E_* 元素工厂，
统一所有飞书推送（新品日报、实时追踪、token 失效等）的视觉风格。

发送方式：lark-cli im +messages-send --msg-type interactive --content <JSON>
"""

import json
import subprocess
import sys
from datetime import datetime


# ---------- 元素构造器（与 gen_daily_report.py 保持一致）----------
def E_md(content):
    """div + lark_md 文本块"""
    return {"tag": "div", "text": {"tag": "lark_md", "content": content}}


def E_hr():
    return {"tag": "hr"}


def E_fields(items):
    """fields 并排（is_short=True 两列）"""
    return {
        "tag": "div",
        "fields": [
            {"is_short": True, "text": {"tag": "lark_md", "content": f"**{k}**\n{v}"}}
            for k, v in items
        ],
    }


def E_actions(buttons):
    """按钮组（text, type, url）"""
    return {
        "tag": "action",
        "actions": [
            {
                "tag": "button",
                "text": {"tag": "plain_text", "content": text},
                "type": typ,
                "url": url,
            }
            for text, typ, url in buttons
        ],
    }


def E_note(content):
    return {"tag": "note", "elements": [{"tag": "plain_text", "content": content}]}


def make_card(title, elements, template="blue", wide=True):
    """组装完整 interactive card JSON（不含 msg_type 外壳）"""
    return {
        "config": {"wide_screen_mode": wide},
        "header": {
            "template": template,
            "title": {"tag": "plain_text", "content": title},
        },
        "elements": elements,
    }


# ---------- 发送 ----------
def send_card(card, chat_id, lark_cli, as_user="bot", idempotency_key=None, timeout=30):
    """通过 lark-cli 发 interactive card

    Args:
        card: make_card() 返回的 dict
        chat_id: oc_xxx
        lark_cli: lark-cli 绝对路径
        as_user: "bot"（默认，cron 用）| "user"
        idempotency_key: 可选，幂等键（HHMMSS 精度）
        timeout: 30s

    Returns:
        message_id (str) or None
    """
    content_json = json.dumps(card, ensure_ascii=False)
    cmd = [
        lark_cli, "im", "+messages-send",
        "--as", as_user,
        "--chat-id", chat_id,
        "--msg-type", "interactive",
        "--content", content_json,
    ]
    if idempotency_key:
        cmd.extend(["--idempotency-key", idempotency_key])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            stdout = (result.stdout or "").strip()
            message_id = None
            if stdout:
                try:
                    resp = json.loads(stdout)
                    message_id = (
                        resp.get("data", {}).get("message_id")
                        or resp.get("message_id")
                    )
                except json.JSONDecodeError:
                    pass
            print(f"✅ 飞书 interactive card 已发 (message_id={message_id})")
            return message_id
        else:
            print(f"❌ 发送失败: returncode={result.returncode}", file=sys.stderr)
            if result.stderr:
                print(f"   stderr: {result.stderr[:400]}", file=sys.stderr)
            if result.stdout:
                print(f"   stdout: {result.stdout[:400]}", file=sys.stderr)
            return None
    except subprocess.TimeoutExpired:
        print("❌ 发送超时", file=sys.stderr)
        return None
    except FileNotFoundError:
        print(f"❌ 找不到 lark-cli: {lark_cli}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"❌ 发送异常: {e}", file=sys.stderr)
        return None


# ---------- 常用模板（按 header 颜色分类）----------
class Tpl:
    """header template 颜色枚举"""
    BLUE = "blue"      # 常规播报
    GREEN = "green"    # 实时/成功
    RED = "red"        # 失败/告警
    ORANGE = "orange"  # 警告
    VIOLET = "violet"  # 特殊
    GREY = "grey"      # 中性
