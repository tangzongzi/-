#!/usr/bin/env python3
"""
gen_commodity_view.py — 商品全景数据生成器（v2，6 卡片网格风格）

从现有汇总 JSON（新品_追踪 / 商品_销售排行Top50 / 商品_日度追踪）拼出
"商品_全景.json"，供 CommodityView.jsx 看板使用。

不调 API（保持现有数据流不变）。
"""

import json
from collections import defaultdict
from pathlib import Path

SUMMARY_DIR = Path("/Users/manba/Documents/OH-WorkSpace/多赞数据库/多赞采购单/数据/汇总")
OUTPUT_DIR = Path("/Users/manba/Documents/OH-WorkSpace/多赞数据库/duozan-dashboard/数据/看板数据")
OUTPUT_FILE = OUTPUT_DIR / "商品_全景.json"


def load(name):
    with open(SUMMARY_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)


def short(s, n=30):
    s = (s or "").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def main():
    new = load("新品_追踪.json")
    top50 = load("商品_销售排行Top50.json")
    daily = load("商品_日度追踪.json")

    latest_date = new.get("summary", {}).get("latest_date", "")

    # ---------- 0. 商品详情字典（供 Drawer 按需查） ----------
    # key = title，去重后所有商品都可点击查详情
    detail_map = {}
    for it in daily.get("data", []):
        detail_map[it["product"]] = {
            "title": it["product"],
            "total_order": it.get("total_order", 0),
            "total_amount": it.get("total_amount", 0),
            "last_day_order": it.get("last_day_order", 0),
            "prev_day_order": it.get("prev_day_order", 0),
            "mom_pct": it.get("mom_pct"),
            "trend": it.get("trend", "flat"),
            "lifecycle": it.get("lifecycle", "mature"),
            "age_days": it.get("age_days", 0),
            "decline_days": it.get("decline_days", 0),
            "daily": it.get("daily", {}),
        }

    # ---------- 1. 新品 (≤14 天) ----------
    new_today = []  # first_seen == today
    new_7d = []
    new_14d = []
    for it in new.get("data", []):
        ds = it.get("days_since", 0)
        if ds > 14:
            continue
        rec = {
            "good_id": it.get("product_id", ""),
            "title": short(it.get("product", ""), 26),
            "first_seen": it.get("first_seen", ""),
            "days_since": ds,
            "orders_total": it.get("total_order", 0),
            "amount_total": it.get("total_amount", 0),
            "main_shop": short(it.get("main_shop", ""), 14),
            "main_platform": it.get("main_shop_platform", ""),
        }
        if ds <= 1:
            new_today.append(rec)
        if ds <= 7:
            new_7d.append(rec)
        new_14d.append(rec)

    new_today.sort(key=lambda x: x["first_seen"], reverse=True)
    new_7d.sort(key=lambda x: x["first_seen"], reverse=True)
    new_14d.sort(key=lambda x: x["first_seen"], reverse=True)

    # ---------- 2. 销售排名 (Top 50) ----------
    sales_today = []  # 按今日订单排序
    sales_total = []  # 累计销量
    for it in top50.get("data", []):
        title = it.get("name", "")
        rec = {
            "title": short(title, 26),
            "orders_total": it.get("order", 0),
            "amount_total": it.get("amount", 0),
            "avg_price": it.get("avg_price", 0),
        }
        sales_total.append(rec)

    # ---------- 3 & 4. 涨幅榜 / 跌幅榜 ----------
    # 涨幅榜 = 今日有单 + 累计达标（反映近期高热）
    # 跌幅榜 = 环比 < 0 的商品
    # 零动销 = last_day_order == 0 且 age >= 30
    up_trend = []  # 今日活跃
    down_trend = []  # 跌幅
    stagnant = []  # 零动销
    for it in daily.get("data", []):
        mom = it.get("mom_pct") or 0
        last = it.get("last_day_order") or 0
        prev = it.get("prev_day_order") or 0
        total = it.get("total_order") or 0
        age = it.get("age_days") or 0
        title = short(it.get("product", ""), 26)

        # 今日活跃（last > 0 且总单量足够）
        if last > 0 and total >= 3:
            up_trend.append({
                "title": title,
                "orders_total": total,
                "last_day_order": last,
                "prev_day_order": prev,
                "lifecycle": it.get("lifecycle", "mature"),
            })
        # 跌幅
        if mom < 0 and total >= 3:
            down_trend.append({
                "title": title,
                "orders_total": total,
                "last_day_order": last,
                "prev_day_order": prev,
                "mom_pct": round(mom, 1),
                "trend": it.get("trend", "down"),
                "lifecycle": it.get("lifecycle", "mature"),
            })
        # 零动销
        if last == 0 and age >= 30 and total <= 10:
            stagnant.append({
                "title": title,
                "orders_total": total,
                "age_days": age,
                "lifecycle": it.get("lifecycle", "mature"),
            })

    up_trend.sort(key=lambda x: -x["last_day_order"])  # 今日高→低
    down_trend.sort(key=lambda x: x["mom_pct"])  # 跌幅低→高
    stagnant.sort(key=lambda x: (x["orders_total"], -x["age_days"]))

    # ---------- 6. 新店铺 (从 new_7d 聚合) ----------
    shop_counter = defaultdict(lambda: {"orders": 0, "amount": 0, "first_seen": "", "platform": "", "items": 0})
    for it in new_7d:
        shop = it.get("main_shop", "")
        if not shop:
            continue
        shop_counter[shop]["orders"] += it.get("orders_total", 0)
        shop_counter[shop]["amount"] += it.get("amount_total", 0)
        shop_counter[shop]["items"] += 1
        shop_counter[shop]["platform"] = it.get("main_platform", "")
        fs = it.get("first_seen", "")
        if fs > shop_counter[shop]["first_seen"]:
            shop_counter[shop]["first_seen"] = fs

    new_shops = []
    for name, info in shop_counter.items():
        new_shops.append({
            "name": short(name, 20),
            "items": info["items"],
            "orders": info["orders"],
            "amount": round(info["amount"], 2),
            "platform": info["platform"],
            "first_seen": info["first_seen"],
        })
    new_shops.sort(key=lambda x: -x["items"])

    # ---------- KPI ----------
    summary = {
        "total_products_tracked": len(daily.get("data", [])),
        "new_products_7d": len(new_7d),
        "new_products_14d": len(new_14d),
        "up_trend": len(up_trend),
        "down_trend": len(down_trend),
        "stagnant": len(stagnant),
        "new_shops": len(new_shops),
        "latest_date": latest_date,
    }

    output = {
        "meta": {
            "title": "商品全景 · 老板专用",
            "data_date": latest_date,
            "fetched_at": latest_date,
            "data_source": "现有汇总 JSON（新品_追踪 / 商品_销售排行Top50 / 商品_日度追踪）",
            "update_freq": "每次跑 export_data.py 后自动更新",
        },
        "summary": summary,
        "new_products": {
            "today": new_today,
            "7d": new_7d,
            "14d": new_14d,
        },
        "sales_total": sales_total,
        "up_trend": up_trend,
        "down_trend": down_trend,
        "stagnant": stagnant,
        "new_shops": new_shops,
        "details": detail_map,  # 按 title 查商品详情（供 Drawer 使用）
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"✅ 已生成 {OUTPUT_FILE}")
    print(f"  KPI: {summary}")
    print(f"  新品: 今日 {len(new_today)} | 7天 {len(new_7d)} | 14天 {len(new_14d)}")
    print(f"  涨 {len(up_trend)} | 跌 {len(down_trend)} | 零动销 {len(stagnant)} | 新店铺 {len(new_shops)}")


if __name__ == "__main__":
    main()
