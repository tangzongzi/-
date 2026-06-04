#!/usr/bin/env python3
"""
auth.py - 多赞采购单抓取的 token 管理

职责：
  1. 读 ~/.config/duozan/token.json 拿 access_token + tenant_id
  2. 解析 JWT 拿 exp，判断是否还有效
  3. token 失效时抛错（让 daily_run.sh 发飞书告警）

未来扩展（2 周后 token 失效时）：
  - 调用 HanaAgent browser 工具自动登录
  - 或读 macOS 钥匙串里的 Safari/Chrome cookie
  - 重新写入 token.json
"""
import json
import base64
import sys
from datetime import datetime, timezone
from pathlib import Path

TOKEN_FILE = Path.home() / ".config/duozan/token.json"


def decode_jwt_exp(token: str) -> int:
    """解析 JWT 拿 exp 时间戳（秒）"""
    try:
        parts = token.split(".")
        payload = parts[1]
        # 补齐 base64 padding
        payload += "=" * (4 - len(payload) % 4)
        data = json.loads(base64.urlsafe_b64decode(payload))
        return int(data["exp"])
    except Exception as e:
        raise ValueError(f"JWT 解析失败: {e}")


def load_token() -> dict:
    """从 token.json 读 token，校验有效性"""
    if not TOKEN_FILE.exists():
        raise FileNotFoundError(
            f"token 文件不存在: {TOKEN_FILE}\n"
            "请先用 HanaAgent browser 工具登录 easyfx.duozan.com 拿 token"
        )

    with open(TOKEN_FILE, "r", encoding="utf-8") as f:
        tok = json.load(f)

    access_token = tok.get("access_token")
    tenant_id = tok.get("tenant_id")
    if not access_token or not tenant_id:
        raise ValueError("token.json 缺 access_token 或 tenant_id")

    # 解析 exp
    exp = tok.get("exp")
    if not exp:
        exp = decode_jwt_exp(access_token)
        tok["exp"] = exp

    now_ts = datetime.now(timezone.utc).timestamp()
    days_left = (exp - now_ts) / 86400

    if exp < now_ts:
        raise ValueError(
            f"token 已过期 {abs(days_left):.1f} 天。"
            f"需要用 HanaAgent browser 工具重新登录更新 token.json"
        )

    # 接近失效（< 1 天）抛警告
    if days_left < 1:
        print(f"⚠️  token 即将失效（剩 {days_left:.2f} 天）", file=sys.stderr)

    return {
        "access_token": access_token,
        "tenant_id": tenant_id,
        "exp": exp,
        "days_left": days_left,
        "phone": tok.get("phone", ""),
    }


if __name__ == "__main__":
    # 命令行直接跑：python3 auth.py
    try:
        info = load_token()
        print(f"✅ token 有效")
        print(f"   tenant: {info['tenant_id']}")
        print(f"   phone: {info['phone']}")
        print(f"   剩余: {info['days_left']:.1f} 天")
    except Exception as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
