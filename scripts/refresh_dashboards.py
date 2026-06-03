"""
refresh_dashboards.py — 看板消费层生成器

从 /数据/汇总/ 下 26 个 json + /数据/汇总/，重新生成 /数据/看板数据/ 下 23 个 json
（前端 ECharts 友好的 columnar 结构）。

调用方式：
    python3 refresh_dashboards.py

输出 23 个看板 json：
- 00_总览
- 供货商_综合
- 商品结构_综合/周度/月度
- 新增淘汰明细
- 小红书/抖店/拼多多 各 综合/日度/周度/月度（共 12）
- 销售业绩 综合/日度/周度/月度
- 风险监控_综合
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from data_loader import load_all

DATA_DIR = Path("/Users/manba/Documents/OH-WorkSpace/多赞数据库/多赞采购单/数据")
SUMMARY_DIR = DATA_DIR / "汇总"
DASH_DIR = DATA_DIR / "看板数据"
DASH_DIR.mkdir(parents=True, exist_ok=True)

PLATFORMS = ["抖店", "拼多多", "小红书"]
PLAT_DIRS = {"小红书": "小红书", "抖店": "抖店", "拼多多": "拼多多"}


# ===== 工具函数 =====

def read_summary(name):
    """读 /数据/汇总/xxx.json"""
    with open(SUMMARY_DIR / name) as f:
        return json.load(f)


def write_dash(name, payload):
    """写 /数据/看板数据/xxx.json"""
    with open(DASH_DIR / name, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def make_meta(period, days, filter_note, title, grain="总览"):
    """统一 meta 段"""
    return {
        "source": "采购单数据(导出后已过滤交易关闭订单)",
        "period": period,
        "days": days,
        "filter": filter_note,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "title": title,
        "grain": grain,
    }


def rows_to_columnar(rows, key_col, value_cols):
    """[{key, a, b, c}, ...] → {key: [...], a: [...], b: [...], c: [...]}"""
    out = {key_col: [], **{vc: [] for vc in value_cols}}
    for r in rows:
        out[key_col].append(r.get(key_col))
        for vc in value_cols:
            out[vc].append(r.get(vc))
    return out


def build_sales_block(period, days, filter_note, kpi=None, full_df=None, plat=None):
    """
    构造 sales 段（前端 ECharts 消费）。
    - kpi: 顶层 KPI（来自 汇总/KPI_总览.json）
    - full_df: 全量 DataFrame（用于计算 platforms/shops）
    - plat: 如果指定，只算该平台
    """
    out = {"meta": make_meta(period, days, filter_note, "销售业绩", "总览")}
    if kpi:
        out["kpi"] = kpi

    if full_df is not None:
        sub = full_df if plat is None else full_df[full_df["店铺平台"] == plat]
        # platforms
        plats = sub.groupby("店铺平台").agg(order=("采购单号", "count"), amount=("小计金额", "sum")).reset_index()
        plats["avg_price"] = (plats["amount"] / plats["order"]).round(2)
        out["platforms"] = plats.to_dict("records")
        # shops
        shops = sub.groupby(["店铺平台", "店铺名称"]).agg(order=("采购单号", "count"), amount=("小计金额", "sum")).reset_index()
        shops["avg_price"] = (shops["amount"] / shops["order"]).round(2)
        out["shops"] = shops.rename(columns={"店铺平台": "plat", "店铺名称": "name"})[["name", "plat", "order", "amount", "avg_price"]].to_dict("records")

    # 粒度数据（columnar 格式）
    grain_map = [("day", "日", "dates"), ("week", "周", "weeks"), ("month", "月", "months")]
    for grain, grain_zh, dates_key in grain_map:
        fn = f"销售业绩_{grain_zh}.json"
        s = read_summary(fn)
        rows = s.get("data", [])
        if grain == "day":
            out["daily"] = {
                "dates": [r.get("date") for r in rows],
                "order": [r.get("order") for r in rows],
                "amount": [r.get("amount") for r in rows],
            }
        elif grain == "week":
            out["weekly"] = {
                "weeks": [r.get("week_start") for r in rows],
                "order": [r.get("order") for r in rows],
                "amount": [r.get("amount") for r in rows],
            }
        else:
            out["monthly"] = {
                "months": [r.get("month") for r in rows],
                "order": [r.get("order") for r in rows],
                "amount": [r.get("amount") for r in rows],
                "avg_price": [r.get("avg_price") for r in rows],
            }

    # 平台×店铺 粒度（按平台拆分）
    for grain, grain_zh, dates_key in grain_map:
        plat_col = {}
        for p in PLATFORMS:
            if plat is not None and plat != p:
                continue
            fn = f"平台_{p}_{grain_zh}.json"
            try:
                s = read_summary(fn)
                rows = s.get("data", [])
                shop_keys = [k for k in rows[0].keys() if k.endswith("_order")] if rows else []
                plat_col[p] = {}
                for sk in shop_keys:
                    amt_key = sk.replace("_order", "_amount")
                    plat_col[p][sk.replace("_order", "")] = {
                        "order": [r.get(sk, 0) for r in rows],
                        "amount": [r.get(amt_key, 0) for r in rows],
                    }
            except FileNotFoundError:
                continue
        if grain == "day":
            out["plat_shop_daily"] = plat_col
        elif grain == "week":
            out["plat_shop_weekly"] = plat_col
        else:
            out["plat_shop_monthly"] = plat_col

    return out


def build_product_block(period, days, filter_note):
    """构造 product 段"""
    s_week = read_summary("商品_周度节奏.json")
    s_month = read_summary("商品_月度变化.json")
    s_top = read_summary("商品_销售排行Top50.json")
    s_keep = read_summary("商品_4月新增5月留存.json")
    s_dist = read_summary("商品_5月销量分布.json")
    out = {"meta": make_meta(period, days, filter_note, "商品结构", "总览")}
    weeks = s_week.get("data", [])
    months = s_month.get("data", [])
    out["weeks"] = [w.get("week_start") for w in weeks]
    out["week_prod_count"] = [w.get("pool_size") for w in weeks]
    out["week_new"] = [w.get("new_count") for w in weeks]
    out["week_gone"] = [w.get("gone_count") for w in weeks]
    out["months"] = [m.get("month") for m in months]
    out["month_changes"] = [
        {
            "month": m.get("month"),
            "pool_size": m.get("pool_size"),
            "new_count": m.get("new_count"),
            "gone_count": m.get("gone_count"),
            "kept_count": m.get("kept_count"),
            "net_change": m.get("net_change"),
            "days_with_data": m.get("days_with_data"),
            "incomplete": m.get("incomplete", False),
        }
        for m in months
    ]
    top = s_top.get("data", [])
    out["concentration"] = {
        "top10_pct": s_top.get("summary", {}).get("top10_concentration_pct", 0),
        "top20_pct": 0,  # 简单占位
    }
    out["distribution_5"] = s_dist.get("data", [])
    out["top_products"] = top
    out["keep"] = s_keep.get("data", {})
    return out


def build_supplier_block(period, days, filter_note):
    """构造 supplier 段"""
    s_rank = read_summary("供货商_排行.json")
    s_month = read_summary("供货商_月度明细.json")
    s_supp_risk = read_summary("风险_供货商关闭率.json")
    out = {"meta": make_meta(period, days, filter_note, "供货商", "总览")}
    # 为每条供货商记录补充风险标记（关闭率 20%+ 标红，10%+ 标黄）
    risk_map = {}
    for r in s_supp_risk.get("data", []):
        name = r.get("supplier") or r.get("name")
        if name:
            risk_map[name] = {
                "closed": r.get("closed", 0),
                "close_rate_pct": r.get("close_rate_pct", 0)
            }
    def attach_risk(item):
        name = item.get("name")
        rk = risk_map.get(name)
        if rk:
            item["closed"] = rk["closed"]
            item["close_rate_pct"] = rk["close_rate_pct"]
            rate = rk["close_rate_pct"]
            if rate >= 20:
                item["risk_tag"] = "高"
                item["risk_color"] = "red"
            elif rate >= 10:
                item["risk_tag"] = "中"
                item["risk_color"] = "yellow"
            else:
                item["risk_tag"] = "低"
                item["risk_color"] = "green"
        else:
            item["closed"] = 0
            item["close_rate_pct"] = 0
            item["risk_tag"] = "—"
            item["risk_color"] = "gray"
        return item
    out["top_suppliers"] = [attach_risk({**r}) for r in s_rank.get("data", [])[:30]]
    out["all_suppliers"] = [attach_risk({**r}) for r in s_rank.get("data", [])]
    out["supp_month"] = s_month.get("data", [])
    out["summary"] = s_rank.get("summary", {})
    return out


def build_risk_block(period, days, filter_note):
    """构造 risk 段"""
    s_status = read_summary("风险_状态分布.json")
    s_supp = read_summary("风险_供货商关闭率.json")
    s_shop = read_summary("风险_店铺关闭率.json")
    s_month = read_summary("风险_关闭率月度.json")
    s_close_top = read_summary("风险_关闭订单Top.json")
    s_wait = read_summary("风险_待确认订单.json")
    out = {"meta": make_meta(period, days, filter_note, "风险监控", "总览")}
    out["status_dist"] = s_status.get("data", [])
    out["close_rate_month"] = s_month.get("data", [])
    out["close_rate_monthly"] = s_month.get("data", [])
    out["shop_close_rate"] = s_shop.get("data", [])
    out["supp_close_rate"] = s_supp.get("data", [])
    out["close_top"] = s_close_top.get("data", {})
    out["wait"] = s_wait.get("data", {})
    return out


# ===== 23 个 json 生成函数 =====

def gen_00_overview(df, period, days, filter_note):
    kpi = read_summary("KPI_总览.json").get("summary", {})
    payload = {
        "meta": make_meta(period, days, filter_note, "采购单总览KPI", "总览"),
        "sales": build_sales_block(period, days, filter_note, kpi=kpi, full_df=df),
        "product": build_product_block(period, days, filter_note),
        "supplier": build_supplier_block(period, days, filter_note),
        "risk": build_risk_block(period, days, filter_note),
    }
    write_dash("00_总览.json", payload)


def gen_supplier_overall(df, period, days, filter_note):
    payload = {
        "meta": make_meta(period, days, filter_note, "供货商分析", "总览"),
        "supplier": build_supplier_block(period, days, filter_note),
    }
    write_dash("供货商_综合.json", payload)


def gen_product(df, period, days, filter_note):
    block = build_product_block(period, days, filter_note)
    write_dash("商品结构_综合.json", {"meta": block["meta"], "product": block})
    # 周度
    s_week = read_summary("商品_周度节奏.json")
    weeks = s_week.get("data", [])
    write_dash("商品结构_周度.json", {
        "meta": make_meta(period, days, filter_note, "商品结构 · 周度", "周"),
        "product": {
            "meta": make_meta(period, days, filter_note, "商品结构 · 周度", "周"),
            "weeks": [w.get("week_start") for w in weeks],
            "week_prod_count": [w.get("pool_size") for w in weeks],
            "week_new": [w.get("new_count") for w in weeks],
            "week_gone": [w.get("gone_count") for w in weeks],
        }
    })
    # 月度
    s_month = read_summary("商品_月度变化.json")
    months = s_month.get("data", [])
    write_dash("商品结构_月度.json", {
        "meta": make_meta(period, days, filter_note, "商品结构 · 月度", "月"),
        "product": {
            "meta": make_meta(period, days, filter_note, "商品结构 · 月度", "月"),
            "months": [m.get("month") for m in months],
            "month_changes": months,
        }
    })
    # 新增淘汰明细
    s_keep = read_summary("商品_4月新增5月留存.json")
    write_dash("新增淘汰明细.json", {
        "meta": make_meta(period, days, filter_note, "新增淘汰明细", "总览"),
        "product": {
            "meta": make_meta(period, days, filter_note, "新增淘汰明细", "总览"),
            **s_keep.get("data", {}),
        }
    })


def gen_platform(df, period, days, filter_note):
    """每个平台：综合 / 日度 / 周度 / 月度"""
    for plat, plat_zh in PLAT_DIRS.items():
        # 综合：复合 sales 段（只含本平台）
        block = build_sales_block(period, days, filter_note, kpi=None, full_df=df, plat=plat)
        write_dash(f"{plat_zh}_综合.json", {
            "meta": make_meta(period, days, filter_note, f"{plat_zh} 平台综合", "总览"),
            "sales": block,
            "shops": block.get("shops", []),
        })
        # 日度
        try:
            s = read_summary(f"平台_{plat_zh}_日.json")
            write_dash(f"{plat_zh}_日度.json", {
                "meta": make_meta(period, days, filter_note, f"{plat_zh} · 日度", "日"),
                "sales": {
                    "meta": make_meta(period, days, filter_note, f"{plat_zh} · 日度", "日"),
                    "daily": rows_to_columnar(s.get("data", []), "period", ["total_order", "total_amount", "avg_price"]),
                    "plat_shop_daily": {plat_zh: {k.replace("_order", ""): {"order": [r.get(k, 0) for r in s.get("data", [])], "amount": [r.get(k.replace("_order", "_amount"), 0) for r in s.get("data", [])]} for k in (s.get("data", [{}])[0].keys() if s.get("data") else []) if k.endswith("_order")}}
                }
            })
        except FileNotFoundError:
            pass
        # 周度
        try:
            s = read_summary(f"平台_{plat_zh}_周.json")
            write_dash(f"{plat_zh}_周度.json", {
                "meta": make_meta(period, days, filter_note, f"{plat_zh} · 周度", "周"),
                "sales": {
                    "meta": make_meta(period, days, filter_note, f"{plat_zh} · 周度", "周"),
                    "weekly": rows_to_columnar(s.get("data", []), "period", ["total_order", "total_amount", "avg_price"]),
                    "plat_shop_weekly": {plat_zh: {k.replace("_order", ""): {"order": [r.get(k, 0) for r in s.get("data", [])], "amount": [r.get(k.replace("_order", "_amount"), 0) for r in s.get("data", [])]} for k in (s.get("data", [{}])[0].keys() if s.get("data") else []) if k.endswith("_order")}}
                }
            })
        except FileNotFoundError:
            pass
        # 月度
        try:
            s = read_summary(f"平台_{plat_zh}_月.json")
            write_dash(f"{plat_zh}_月度.json", {
                "meta": make_meta(period, days, filter_note, f"{plat_zh} · 月度", "月"),
                "sales": {
                    "meta": make_meta(period, days, filter_note, f"{plat_zh} · 月度", "月"),
                    "monthly": rows_to_columnar(s.get("data", []), "period", ["total_order", "total_amount", "avg_price"]),
                    "plat_shop_monthly": {plat_zh: {k.replace("_order", ""): {"order": [r.get(k, 0) for r in s.get("data", [])], "amount": [r.get(k.replace("_order", "_amount"), 0) for r in s.get("data", [])]} for k in (s.get("data", [{}])[0].keys() if s.get("data") else []) if k.endswith("_order")}}
                }
            })
        except FileNotFoundError:
            pass


def gen_sales(df, period, days, filter_note):
    # 综合
    kpi = read_summary("KPI_总览.json").get("summary", {})
    write_dash("销售业绩_综合.json", {
        "meta": make_meta(period, days, filter_note, "销售业绩综合", "总览"),
        "sales": build_sales_block(period, days, filter_note, kpi=kpi, full_df=df),
        "product": build_product_block(period, days, filter_note),
        "supplier": build_supplier_block(period, days, filter_note),
        "risk": build_risk_block(period, days, filter_note),
    })
    # 日/周/月
    for grain, fn_in, fn_out, grain_zh in [
        ("day", "销售业绩_日.json", "销售业绩_日度.json", "日"),
        ("week", "销售业绩_周.json", "销售业绩_周度.json", "周"),
        ("month", "销售业绩_月.json", "销售业绩_月度.json", "月"),
    ]:
        s = read_summary(fn_in)
        rows = s.get("data", [])
        if grain == "day":
            write_dash(fn_out, {
                "meta": make_meta(period, days, filter_note, f"销售业绩 · {grain_zh}度", grain_zh),
                "sales": {
                    "meta": make_meta(period, days, filter_note, f"销售业绩 · {grain_zh}度", grain_zh),
                    "daily": rows_to_columnar(rows, "date", ["order", "amount", "avg_price"]),
                }
            })
        elif grain == "week":
            write_dash(fn_out, {
                "meta": make_meta(period, days, filter_note, f"销售业绩 · {grain_zh}度", grain_zh),
                "sales": {
                    "meta": make_meta(period, days, filter_note, f"销售业绩 · {grain_zh}度", grain_zh),
                    "weekly": rows_to_columnar(rows, "week_start", ["order", "amount", "avg_price"]),
                }
            })
        else:
            write_dash(fn_out, {
                "meta": make_meta(period, days, filter_note, f"销售业绩 · {grain_zh}度", grain_zh),
                "sales": {
                    "meta": make_meta(period, days, filter_note, f"销售业绩 · {grain_zh}度", grain_zh),
                    "monthly": rows_to_columnar(rows, "month", ["order", "amount", "avg_price", "mom_order_pct", "mom_amount_pct"]),
                }
            })


def gen_risk(df, period, days, filter_note):
    write_dash("风险监控_综合.json", {
        "meta": make_meta(period, days, filter_note, "风险监控综合", "总览"),
        "risk": build_risk_block(period, days, filter_note),
    })


# ===== 主入口 =====

def main():
    print("读数据中...")
    df = load_all()
    period = f"{df['创建时间'].min().strftime('%Y-%m-%d')} ~ {df['创建时间'].max().strftime('%Y-%m-%d')}"
    days = (df["创建时间"].max() - df["创建时间"].min()).days + 1
    closed_n = int(df["采购单状态"].astype(str).str.contains("关闭", na=False).sum())
    filter_note = f"已去除交易关闭订单 ({closed_n} 笔)"
    print(f"  ✓ {len(df)} 行，{period}（{days} 天）")
    print()
    print("生成 23 个看板 json...")
    funcs = [
        ("00_总览", gen_00_overview),
        ("供货商_综合", gen_supplier_overall),
        ("商品结构 4 个", gen_product),
        ("平台 × 4 粒度 × 3 平台（12 个）", gen_platform),
        ("销售业绩 4 个", gen_sales),
        ("风险监控_综合", gen_risk),
    ]
    for name, fn in funcs:
        try:
            if name == "商品结构 4 个":
                fn(df, period, days, filter_note)
            elif name == "平台 × 4 粒度 × 3 平台（12 个）":
                fn(df, period, days, filter_note)
            else:
                fn(df, period, days, filter_note)
            print(f"  ✓ {name}")
        except Exception as e:
            print(f"  ❌ {name}: {e}")
            import traceback; traceback.print_exc()
    print()
    print(f"完成。{len(list(DASH_DIR.glob('*.json')))} 个 json 写入 {DASH_DIR}")


if __name__ == "__main__":
    main()
