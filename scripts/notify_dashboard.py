#!/usr/bin/env python3
"""
新品日报飞书通知（多赞售后群）
================================
数据源：多赞采购单/数据/汇总/
发送：lark-cli im +messages-send（bot 身份）
失败容错：单跑失败返回 1（便于调试）；shell 包装会兜底不中断上游

口径说明：
- 首日上架：first_seen == latest_date 的新品
- 风险品：「风险_供货商关闭率.json」中 close_rate_pct > 30% 的供货商
        （数据源限制：关闭率仅在供货商维度，商品维度未统计）
        显示为「高风险供货商（其下新品需关注）」，避免误读为商品关闭率
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ---------- 路径配置 ----------
SCRIPT_DIR = Path(__file__).resolve().parent
# notify_dashboard.py 位于 duozan-dashboard/scripts/
# 数据源位于 多赞采购单/数据/汇总/
DUOZAN_ROOT = SCRIPT_DIR.parent.parent  # 多赞数据库/
DATA_SUMMARY_DIR = DUOZAN_ROOT / "多赞采购单" / "数据" / "汇总"
NEW_PRODUCT_JSON = DATA_SUMMARY_DIR / "新品_追踪.json"
SUPPLIER_RISK_JSON = DATA_SUMMARY_DIR / "风险_供货商关闭率.json"

# ---------- 飞书配置 ----------
CHAT_ID = "oc_c368fff060e8b5095e434e1a481cb396"  # 多赞售后群
LARK_CLI = "/opt/homebrew/bin/lark-cli"
DASHBOARD_URL = "https://dy.zongzi.fun/new-product"

# ---------- 风险阈值 ----------
CLOSE_RATE_THRESHOLD = 30.0  # 关闭率 > 30% 视为高风险供货商
TOP_N = 5                    # 各类 Top N

# ---------- 平台缩写映射 ----------
PLATFORM_ABBR = {
    "拼多多": "拼",
    "抖店": "抖",
    "小红书": "红",
}


# ---------- 工具函数 ----------
def fmt_money(v):
    """金额格式化：千分位 + 2 位小数"""
    try:
        return f"{float(v):,.2f}"
    except (TypeError, ValueError):
        return str(v)


def short_name(s, maxlen=22):
    """商品名截断（避免在飞书里溢出）"""
    s = (s or "").strip()
    return s if len(s) <= maxlen else s[:maxlen - 1] + "…"


def load_json(path):
    if not path.exists():
        print(f"⚠️  文件不存在: {path}", file=sys.stderr)
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️  读取失败 {path.name}: {e}", file=sys.stderr)
        return None


# ---------- 数据提取 ----------
def pick_first_day_top(news, latest_date, n=TOP_N):
    """首日上架 = first_seen == latest_date，按 total_order 降序取前 n"""
    first_day = [it for it in (news or []) if it.get("first_seen") == latest_date]
    first_day.sort(key=lambda x: x.get("total_order", 0), reverse=True)
    return first_day[:n]


def pick_all_time_top(news, n=TOP_N):
    """累计 Top N：所有在追踪窗口（≤14 天）内的商品按 total_order 降序"""
    all_sorted = sorted(news or [], key=lambda x: x.get("total_order", 0), reverse=True)
    return all_sorted[:n]


def pick_high_risk_suppliers(supplier_data, threshold=CLOSE_RATE_THRESHOLD, n=TOP_N):
    """关闭率 > threshold 的供货商（最多 n 个）"""
    risks = [s for s in (supplier_data or [])
             if (s.get("close_rate_pct") or 0) > threshold]
    risks.sort(key=lambda x: x.get("close_rate_pct", 0), reverse=True)
    return risks[:n]


# ---------- 渲染辅助 ----------
def render_shop_breakdown(shop_details_by_shop, max_shops=3, shop_maxlen=10):
    """把 shop_details_by_shop 渲染成 '拼·xx 35单 / 抖·yy 5单' 格式

    shop_details_by_shop 形如:
        { "店名|平台": {"shop": "店名", "platform": "抖店", "orders": 5, "amount": 100} }
    已按 orders 倒序排列。
    """
    if not shop_details_by_shop:
        return ""
    items = list(shop_details_by_shop.values())
    if not items:
        return ""
    shown = items[:max_shops]
    parts = []
    for v in shown:
        abbr = PLATFORM_ABBR.get(v.get("platform", ""), (v.get("platform") or "?")[:1])
        sname = short_name(v.get("shop", ""), shop_maxlen)
        parts.append(f"{abbr}·{sname} {v.get('orders', 0)}单")
    if len(items) > max_shops:
        parts.append(f"等{len(items)}店")
    return " / ".join(parts)


def render_top_lines(items, latest_date, show_days=False, max_shops=3):
    """通用 Top N 行渲染：
    1. 商品名
       40单 ｜ ¥1,040 ｜ 拼·xx 35单 / 抖·yy 5单   (已上架 3 天)
    """
    if not items:
        return None
    lines = []
    for i, it in enumerate(items, 1):
        name = short_name(it.get("product", ""))
        order = it.get("total_order", 0)
        amount = it.get("total_amount", 0)
        breakdown = render_shop_breakdown(
            it.get("shop_details_by_shop", {}), max_shops=max_shops
        )
        # 第一行：商品 ID + 名字
        pid = it.get("product_id", "").strip()
        id_label = f"「{pid}」" if pid else ""
        # 主行：单量 ｜ 金额 ｜ 店铺分解
        main = f"   {order}单 ｜ ¥{fmt_money(amount)}"
        if breakdown:
            main += f" ｜ {breakdown}"
        # 累计 Top 5 时附 "已上架 N 天" 提示
        if show_days and it.get("days_since") is not None:
            ds = it.get("days_since", 0)
            if it.get("first_seen") == latest_date:
                main += f"   （首日）"
            else:
                main += f"   （已上架 {ds} 天）"
        lines.append(f"{i}. {id_label}{name}\n{main}")
    return "\n".join(lines)


# ---------- 卡片构造 ----------
def build_card_content(summary, top_first_day, top_all_time, risks, latest_date):
    """构造 post 类型消息卡片的 content JSON"""
    new_count = summary.get("new_product_count", 0)
    total_orders = summary.get("total_new_orders", 0)
    total_amount = summary.get("total_new_amount", 0)
    avg_price = (float(total_amount) / total_orders) if total_orders else 0.0

    # —— 首日 Top 5 文本 ——
    first_day_text = render_top_lines(top_first_day, latest_date, show_days=False)
    if first_day_text is None:
        first_day_text = "（首日无新品上架）"

    # —— 累计 Top 5 文本 ——
    all_time_text = render_top_lines(top_all_time, latest_date, show_days=True)
    if all_time_text is None:
        all_time_text = "（暂无在追踪的新品）"

    # —— 高风险供货商文本 ——
    if risks:
        lines = []
        for s in risks:
            name = short_name(s.get("supplier", ""), 20)
            rate = s.get("close_rate_pct", 0)
            closed = int(s.get("closed", 0) or 0)
            lines.append(f"· {name}\n   关闭率 {rate}% · 关闭 {closed} 单")
        risk_text = "\n".join(lines)
    else:
        risk_text = "（无高风险供货商）"

    # —— 拼装 content（每条是一行；行内是 inline 元素数组）——
    sep = [{"tag": "text", "text": "─────────────"}]
    content = {
        "zh_cn": {
            "title": f"🆕 新品日报 · {latest_date}",
            "content": [
                [{"tag": "text", "text": f"📊 核心数据（{latest_date}）"}],
                [{"tag": "text", "text":
                    f"新增新品：{new_count} 个\n"
                    f"新品订单：{total_orders} 单\n"
                    f"新品金额：¥{fmt_money(total_amount)}\n"
                    f"平均客单：¥{fmt_money(avg_price)}"}],
                sep,
                [{"tag": "text", "text": "🆕 今日首日上架 Top 5"}],
                [{"tag": "text", "text": first_day_text}],
                sep,
                [{"tag": "text", "text": "📈 新品累计 Top 5（≤14 天在追踪）"}],
                [{"tag": "text", "text": all_time_text}],
                sep,
                [{"tag": "text", "text": "⚠️ 高风险供货商（关闭率>30%，其下新品需关注）"}],
                [{"tag": "text", "text": risk_text}],
                sep,
                [{"tag": "a", "href": DASHBOARD_URL, "text": "🔗 查看新品追踪看板"}],
                [{"tag": "text", "text":
                    f"🤖 多赞看板 · {datetime.now().strftime('%H:%M')} 自动播报"}],
            ]
        }
    }
    return content


# ---------- 发送 ----------
def send_card(content, idempotency_key=None):
    """调 lark-cli 发消息卡片"""
    cmd = [
        LARK_CLI, "im", "+messages-send",
        "--as", "bot",
        "--chat-id", CHAT_ID,
        "--msg-type", "post",
        "--content", json.dumps(content, ensure_ascii=False),
        "--format", "json",
    ]
    if idempotency_key:
        cmd.extend(["--idempotency-key", idempotency_key])

    print(f"📤 目标：chat_id={CHAT_ID}")
    print(f"📤 类型：post（lark-cli bot 身份）")
    if idempotency_key:
        print(f"🔑 幂等键：{idempotency_key}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✅ 发送成功")
            stdout = (result.stdout or "").strip()
            message_id = None
            if stdout:
                # 尝试从返回 JSON 里抠 message_id
                try:
                    resp = json.loads(stdout)
                    message_id = (
                        resp.get("data", {}).get("message_id")
                        or resp.get("message_id")
                    )
                except json.JSONDecodeError:
                    pass
                # 只打印前 200 字符，避免日志太长
                print(f"📥 返回：{stdout[:200]}")
            if message_id:
                print(f"📨 message_id: {message_id}")
            else:
                print("⚠️  未能从返回中解析出 message_id")
            return message_id
        else:
            print(f"❌ 发送失败：returncode={result.returncode}")
            stderr = (result.stderr or "").strip()
            stdout = (result.stdout or "").strip()
            if stderr:
                print(f"📥 stderr：{stderr[:400]}")
            if stdout:
                print(f"📥 stdout：{stdout[:400]}")
            return None
    except subprocess.TimeoutExpired:
        print("❌ 发送超时（30s）")
        return None
    except FileNotFoundError:
        print(f"❌ 找不到 lark-cli: {LARK_CLI}")
        return None
    except Exception as e:
        print(f"❌ 发送异常：{e}")
        return None


# ---------- 主流程 ----------
def main():
    print(f"🆕 新品日报通知 · {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📂 数据源目录：{DATA_SUMMARY_DIR}")

    # 1. 加载数据
    new_data = load_json(NEW_PRODUCT_JSON)
    if not new_data:
        print("❌ 新品数据加载失败，跳过发送")
        return 1

    supplier_full = load_json(SUPPLIER_RISK_JSON)
    supplier_data = (supplier_full or {}).get("data", [])

    summary = new_data.get("summary") or {}
    latest_date = summary.get("latest_date")
    if not latest_date:
        print("❌ summary 缺少 latest_date，跳过发送")
        return 1

    # 2. 提取 Top + 风险
    top_first_day = pick_first_day_top(new_data.get("data", []), latest_date)
    top_all_time = pick_all_time_top(new_data.get("data", []))
    risks = pick_high_risk_suppliers(supplier_data)

    print(f"📅 数据日期：{latest_date}")
    print(f"📦 首日 Top：{len(top_first_day)} / "
          f"{sum(1 for it in new_data.get('data', []) if it.get('first_seen') == latest_date)}")
    print(f"📈 累计 Top：{len(top_all_time)}（在追踪新品 {len(new_data.get('data', []))} 个）")
    print(f"⚠️  高风险供货商：{len(risks)} 个")

    # 3. 构造 + 发送
    content = build_card_content(summary, top_first_day, top_all_time, risks, latest_date)
    # 幂等键：日期 + 当前 HHMMSS（同一分钟内重复调用会因 lark-cli 幂等键去重）
    idempotency_key = f"duozan-newproduct-{latest_date}-{datetime.now().strftime('%H%M%S')}"
    message_id = send_card(content, idempotency_key=idempotency_key)
    return 0 if message_id else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        # 兜底：任何未捕获异常都返回 1（shell 包装会兜底为 0）
        print(f"❌ 脚本未捕获异常：{e}", file=sys.stderr)
        sys.exit(1)
