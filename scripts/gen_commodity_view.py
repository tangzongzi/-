#!/usr/bin/env python3
"""
gen_commodity_view.py — 商品全景数据生成器

从现有汇总 JSON（新品_追踪 / 商品_销售排行Top50 / 商品_日度追踪）拼出
"商品_全景.json"，供 CommodityView.jsx 看板使用。

不调 API（保持现有数据流不变）。
"""

import json
from pathlib import Path

SUMMARY_DIR = Path("/Users/manba/Documents/OH-WorkSpace/多赞数据库/多赞采购单/数据/汇总")
OUTPUT_DIR = Path("/Users/manba/Documents/OH-WorkSpace/多赞数据库/duozan-dashboard/数据/看板数据")
OUTPUT_FILE = OUTPUT_DIR / "商品_全景.json"


def load(name):
    with open(SUMMARY_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    # 加载源数据
    new = load("新品_追踪.json")
    top50 = load("商品_销售排行Top50.json")
    daily = load("商品_日度追踪.json")

    latest_date = new.get("summary", {}).get("latest_date", "")

    # 1) 新品专区：新品_追踪 全部（≤14 天的）
    new_products = []
    for it in new.get("data", []):
        if it.get("days_since", 0) <= 14:
            new_products.append({
                "good_id": it.get("product_id", ""),
                "title": it.get("product", ""),
                "first_seen": it.get("first_seen", ""),
                "days_since": it.get("days_since", 0),
                "orders_total": it.get("total_order", 0),
                "amount_total": it.get("total_amount", 0),
                "avg_daily": it.get("avg_daily", 0),
                "main_shop": it.get("main_shop", ""),
                "main_platform": it.get("main_shop_platform", ""),
                "platforms": it.get("shops", []),
            })
    new_products.sort(key=lambda x: x["first_seen"], reverse=True)

    # 2) 明星产品：商品_销售排行Top50 Top 20（按销量）
    star_products = []
    for it in top50.get("data", [])[:20]:
        star_products.append({
            "rank": it.get("rank", 0),
            "title": it.get("name", ""),
            "orders_total": it.get("order", 0),
            "amount_total": it.get("amount", 0),
            "avg_price": it.get("avg_price", 0),
        })

    # 3) 滞销产品：商品_日度追踪 里 total_order 少（≤10）且 age_days 较长
    stagnant = []
    for it in daily.get("data", []):
        age = it.get("age_days", 0)
        total = it.get("total_order", 0)
        if age >= 30 and total <= 10:
            stagnant.append({
                "title": it.get("product", ""),
                "orders_total": total,
                "age_days": age,
                "last_day_order": it.get("last_day_order", 0),
                "lifecycle": it.get("lifecycle", "mature"),
                "trend": it.get("trend", "down"),
            })
    stagnant.sort(key=lambda x: (x["orders_total"], -x["age_days"]))
    stagnant = stagnant[:20]

    # 4) 下降产品：mom_pct 显著为负的
    declining = []
    for it in daily.get("data", []):
        mom = it.get("mom_pct") or 0
        total = it.get("total_order") or 0
        if mom < -30 and total >= 5:
            declining.append({
                "title": it.get("product", ""),
                "orders_total": it.get("total_order", 0),
                "mom_pct": round(mom, 1),
                "last_day_order": it.get("last_day_order", 0),
                "prev_day_order": it.get("prev_day_order", 0),
                "trend": it.get("trend", "down"),
                "lifecycle": it.get("lifecycle", "mature"),
            })
    declining.sort(key=lambda x: x["mom_pct"])
    declining = declining[:20]

    # KPI 概览
    summary = {
        "total_products_tracked": len(daily.get("data", [])),
        "total_sales_rank": len(top50.get("data", [])),
        "new_products_14d": len(new_products),
        "stagnant_products": len(stagnant),
        "declining_products": len(declining),
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
        "new_products": new_products,
        "star_products": star_products,
        "stagnant_products": stagnant,
        "declining_products": declining,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"✅ 已生成 {OUTPUT_FILE}")
    print(f"  KPI: {summary}")
    print(f"  新品: {len(new_products)} | 明星: {len(star_products)} | 滞销: {len(stagnant)} | 下降: {len(declining)}")


if __name__ == "__main__":
    main()
