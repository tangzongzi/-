"""
export_data.py — 汇总数据生成器

从合并后的全量 xlsx 数据，生成 /数据/汇总/ 下 26 个 json。

调用方式：
    python3 export_data.py

设计原则：
- 每个 json 一个函数
- 通用辅助：按粒度聚合、按状态聚合、按维度聚合
- 输出 schema 跟现状完全一致（meta/summary/data 三段）
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from data_loader import load_all

DATA_DIR = Path("/Users/manba/Documents/OH-WorkSpace/多赞数据库/多赞采购单/数据")
SUMMARY_DIR = DATA_DIR / "汇总"
SUMMARY_DIR.mkdir(parents=True, exist_ok=True)


# ===== 通用辅助 =====

def write_json(path, meta, summary, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({"meta": meta, "summary": summary, "data": data}, f, ensure_ascii=False, indent=2)


def period_of(ts, grain):
    """按粒度返回 period key"""
    if pd.isna(ts):
        return None
    if grain == "day":
        return ts.strftime("%Y-%m-%d")
    elif grain == "week":
        start = ts - pd.Timedelta(days=ts.weekday())
        return start.strftime("%Y-%m-%d")
    elif grain == "month":
        return ts.strftime("%Y-%m")


def is_closed(s):
    return s.astype(str).str.contains("关闭", na=False)


def pivot_shop_period(df, grain):
    """按 [店铺平台, 店铺名称] × period 透视：每个店铺一列（order/amount）"""
    df = df.copy()
    df["_period"] = df["创建时间"].apply(lambda t: period_of(t, grain))
    df = df.dropna(subset=["_period"])
    # 透视前先算每个 period 的 total（避免 pivot 后重复列）
    period_total = df.groupby("_period").agg(
        _total_order=("采购单号", "count"),
        _total_amount=("小计金额", "sum"),
    ).reset_index()
    grouped = df.groupby(["_period", "店铺平台", "店铺名称"]).agg(
        order=("采购单号", "count"),
        amount=("小计金额", "sum")
    ).reset_index()
    pivot = grouped.pivot_table(index="_period", columns=["店铺平台", "店铺名称"], values=["order", "amount"], fill_value=0)
    pivot.columns = [f"{shop}_{agg}" for (_, shop, agg) in pivot.columns]
    pivot = pivot.reset_index().rename(columns={"_period": "period"})
    pivot = pivot.merge(period_total, left_on="period", right_on="_period").drop(columns=["_period"])
    pivot = pivot.rename(columns={"_total_order": "total_order", "_total_amount": "total_amount"})
    pivot["avg_price"] = (pivot["total_amount"] / pivot["total_order"]).round(2).fillna(0)
    return pivot.sort_values("period").to_dict("records")


# ===== 1. KPI 总览 =====

def gen_kpi(df):
    active = df[~is_closed(df["采购单状态"])].copy()
    days = max((df["创建时间"].max() - df["创建时间"].min()).days + 1, 1)
    summary = {
        "total_orders": int(len(active)),
        "total_amount": round(float(active["小计金额"].sum()), 2),
        "avg_price": round(float(active["小计金额"].mean()), 2) if len(active) > 0 else 0,
        "total_amount_wan": round(float(active["小计金额"].sum() / 10000), 2),
        "shop_count": int(df["店铺名称"].nunique()),
        "platform_count": int(df["店铺平台"].nunique()),
        "product_count": int(df["商品名称"].nunique()),
        "supplier_count": int(df["供货商"].nunique()),
        "orders_per_day": round(len(active) / days, 2),
        "amount_per_day": round(float(active["小计金额"].sum() / days), 2),
    }
    platforms = active.groupby("店铺平台").agg(orders=("采购单号", "count"), amount=("小计金额", "sum")).reset_index()
    shops = active.groupby(["店铺平台", "店铺名称"]).agg(orders=("采购单号", "count"), amount=("小计金额", "sum")).reset_index()
    data = {
        "platforms": platforms.to_dict("records"),
        "shops": shops.to_dict("records"),
    }
    meta = {
        "title": "采购单总览KPI",
        "period": f"{df['创建时间'].min().strftime('%Y-%m-%d')} ~ {df['创建时间'].max().strftime('%Y-%m-%d')}",
        "filter": f"已去除交易关闭订单 ({int(is_closed(df['采购单状态']).sum())} 笔)",
    }
    write_json(SUMMARY_DIR / "KPI_总览.json", meta, summary, data)


# ===== 2. 供货商（2 个）=====

def gen_supplier_ranking(df):
    active = df[~is_closed(df["采购单状态"])].copy()
    grouped = active.groupby("供货商").agg(
        order=("采购单号", "count"),
        amount=("小计金额", "sum")
    ).reset_index().sort_values("amount", ascending=False).reset_index(drop=True)
    grouped["rank"] = grouped.index + 1
    grouped["avg_price"] = (grouped["amount"] / grouped["order"]).round(2)
    grouped["platforms"] = grouped["供货商"].apply(lambda s: sorted(df.loc[df["供货商"] == s, "店铺平台"].dropna().unique().tolist()))
    total = grouped["amount"].sum()
    grouped = grouped.rename(columns={"供货商": "name"})
    data = grouped[["rank", "name", "platforms", "order", "amount", "avg_price"]].to_dict("records")
    summary = {
        "total_suppliers": int(len(grouped)),
        "total_amount": round(float(total), 2),
        "top1_concentration_pct": round(float(grouped.iloc[0]["amount"] / total * 100), 2) if total else 0,
        "top3_concentration_pct": round(float(grouped.iloc[:3]["amount"].sum() / total * 100), 2) if total else 0,
        "top5_concentration_pct": round(float(grouped.iloc[:5]["amount"].sum() / total * 100), 2) if total else 0,
        "top10_concentration_pct": round(float(grouped.iloc[:10]["amount"].sum() / total * 100), 2) if total else 0,
        "long_tail_count": int((grouped["order"] < 50).sum()),
    }
    meta = {"title": "供货商排行（按金额）", "grain": "3个月累计", "filter": "已去除交易关闭订单"}
    write_json(SUMMARY_DIR / "供货商_排行.json", meta, summary, data)


def gen_supplier_monthly(df):
    active = df[~is_closed(df["采购单状态"])].copy()
    active["month"] = active["创建时间"].dt.strftime("%Y-%m")
    months = sorted(active["month"].dropna().unique())
    suppliers = sorted(active["供货商"].dropna().unique())
    grouped = active.groupby(["供货商", "month"]).agg(
        order=("采购单号", "count"),
        amount=("小计金额", "sum")
    ).reset_index()
    rows = []
    for sup in suppliers:
        row = {"supplier": sup}
        sub = grouped[grouped["供货商"] == sup]
        for m in months:
            mm = sub[sub["month"] == m]
            row[f"{m}_order"] = int(mm["order"].sum()) if len(mm) else 0
            row[f"{m}_amount"] = round(float(mm["amount"].sum()), 2) if len(mm) else 0
        rows.append(row)
    summary = {"suppliers": len(suppliers), "months": len(months)}
    meta = {"title": "供货商月度明细", "grain": "月"}
    write_json(SUMMARY_DIR / "供货商_月度明细.json", meta, summary, rows)


# ===== 3. 平台 × 店铺 × 粒度（9 个）=====

PLATFORMS = ["小红书", "抖店", "拼多多"]
GRAINS = ["day", "week", "month"]
GRAIN_ZH = {"day": "日", "week": "周", "month": "月"}

def gen_platforms(df):
    for plat in PLATFORMS:
        sub = df[df["店铺平台"] == plat]
        sub_active = sub[~is_closed(sub["采购单状态"])].copy()
        if len(sub_active) == 0:
            continue
        for grain in GRAINS:
            data = pivot_shop_period(sub_active, grain)
            total_orders = int(sub_active["采购单号"].count())
            total_amount = round(float(sub_active["小计金额"].sum()), 2)
            summary = {
                "total_orders": total_orders,
                "total_amount": total_amount,
                "avg_price": round(total_amount / total_orders, 2) if total_orders else 0,
                "periods": len(data),
            }
            fn = f"平台_{plat}_{GRAIN_ZH[grain]}.json"
            meta = {"title": f"{plat} · 店铺{GRAIN_ZH[grain]}度销售", "grain": GRAIN_ZH[grain]}
            write_json(SUMMARY_DIR / fn, meta, summary, data)


# ===== 4. 销售业绩 日/周/月（3 个）=====

def gen_sales(df):
    active = df[~is_closed(df["采购单状态"])].copy()
    # 日
    daily = active.groupby(active["创建时间"].dt.strftime("%Y-%m-%d")).agg(
        order=("采购单号", "count"),
        amount=("小计金额", "sum")
    ).reset_index().rename(columns={"创建时间": "date"})
    daily["avg_price"] = (daily["amount"] / daily["order"]).round(2)
    daily = daily.sort_values("date").to_dict("records")
    summary_d = {
        "days": len(daily),
        "total_orders": sum(d["order"] for d in daily),
        "total_amount": round(sum(d["amount"] for d in daily), 2),
        "avg_daily_orders": round(np.mean([d["order"] for d in daily]), 2) if daily else 0,
        "avg_daily_amount": round(np.mean([d["amount"] for d in daily]), 2) if daily else 0,
    }
    write_json(SUMMARY_DIR / "销售业绩_日.json", {"title": "销售业绩 · 日度"}, summary_d, daily)
    # 周
    active["_week"] = active["创建时间"].apply(lambda t: period_of(t, "week"))
    weekly = active.groupby("_week").agg(order=("采购单号", "count"), amount=("小计金额", "sum")).reset_index().rename(columns={"_week": "week_start"})
    weekly["avg_price"] = (weekly["amount"] / weekly["order"]).round(2)
    weekly = weekly.sort_values("week_start").to_dict("records")
    summary_w = {
        "weeks": len(weekly),
        "total_orders": sum(w["order"] for w in weekly),
        "total_amount": round(sum(w["amount"] for w in weekly), 2),
        "avg_weekly_orders": round(np.mean([w["order"] for w in weekly]), 2) if weekly else 0,
    }
    write_json(SUMMARY_DIR / "销售业绩_周.json", {"title": "销售业绩 · 周度"}, summary_w, weekly)
    # 月（含环比）
    active["_month"] = active["创建时间"].dt.strftime("%Y-%m")
    monthly = active.groupby("_month").agg(order=("采购单号", "count"), amount=("小计金额", "sum")).reset_index().rename(columns={"_month": "month"})
    monthly["avg_price"] = (monthly["amount"] / monthly["order"]).round(2)
    monthly["mom_order_pct"] = monthly["order"].pct_change().fillna(0).round(4) * 100
    monthly["mom_amount_pct"] = monthly["amount"].pct_change().fillna(0).round(4) * 100
    monthly = monthly.sort_values("month").to_dict("records")
    summary_m = {
        "months": len(monthly),
        "total_orders": sum(m["order"] for m in monthly),
        "total_amount": round(sum(m["amount"] for m in monthly), 2),
    }
    write_json(SUMMARY_DIR / "销售业绩_月.json", {"title": "销售业绩 · 月度"}, summary_m, monthly)


# ===== 5. 商品（5 个）=====

def gen_products(df):
    active = df[~is_closed(df["采购单状态"])].copy()
    # 销售排行 Top50
    top = active.groupby("商品名称").agg(
        order=("采购单号", "count"),
        amount=("小计金额", "sum")
    ).reset_index().sort_values("order", ascending=False).head(50).reset_index(drop=True)
    top["rank"] = top.index + 1
    top["avg_price"] = (top["amount"] / top["order"]).round(2)
    data = top.rename(columns={"商品名称": "name"})[["rank", "name", "order", "amount", "avg_price"]].to_dict("records")
    summary = {
        "top50_orders": int(top["order"].sum()),
        "top50_orders_pct": round(top["order"].sum() / len(active) * 100, 2),
        "top50_amounts": round(float(top["amount"].sum()), 2),
        "top10_concentration_pct": round(float(top.iloc[:10]["order"].sum() / top["order"].sum() * 100), 2),
    }
    write_json(SUMMARY_DIR / "商品_销售排行Top50.json", {"title": "商品销售排行 Top 50"}, summary, data)

    # 5月销量分布
    may = active[active["创建时间"].dt.month == 5]
    may_dist = may.groupby("商品名称").size().reset_index(name="count")
    bins = [(1, 1), (2, 5), (6, 20), (21, 100), (101, 99999)]
    labels = ["1", "2-5", "6-20", "21-100", "100+"]
    dist = []
    for (lo, hi), lab in zip(bins, labels):
        n = int(((may_dist["count"] >= lo) & (may_dist["count"] <= hi)).sum())
        dist.append({"range": lab, "count": n})
    long_tail = sum(d["count"] for d in dist[2:])  # 6 以下
    summary = {
        "total_5_products": int(len(may_dist)),
        "long_tail_pct": round(long_tail / len(may_dist) * 100, 2) if len(may_dist) else 0,
    }
    write_json(SUMMARY_DIR / "商品_5月销量分布.json", {"title": "5月销量分布", "note": "已去关闭"}, summary, dist)

    # 周度节奏
    active["_week"] = active["创建时间"].apply(lambda t: period_of(t, "week"))
    weeks = sorted(active["_week"].dropna().unique())
    rows = []
    for w in weeks:
        in_w = set(active.loc[active["_week"] == w, "商品名称"].dropna().unique())
        # pool_size = 当周出现过的商品数（活跃池）
        # new_count = 当周新增的商品（之前没出现过）
        prev_products = set()
        for w2 in weeks:
            if w2 < w:
                prev_products |= set(active.loc[active["_week"] == w2, "商品名称"].dropna().unique())
        new = in_w - prev_products
        gone = prev_products - in_w
        rows.append({"week_start": w, "pool_size": len(in_w), "new_count": len(new), "gone_count": len(gone), "net_change": len(new) - len(gone)})
    summary = {
        "weeks": len(rows),
        "max_pool": max((r["pool_size"] for r in rows), default=0),
        "min_pool": min((r["pool_size"] for r in rows), default=0),
        "total_new": sum(r["new_count"] for r in rows),
        "total_gone": sum(r["gone_count"] for r in rows),
    }
    write_json(SUMMARY_DIR / "商品_周度节奏.json", {"title": "周度选品节奏"}, summary, rows)

    # 月度变化
    active["_month"] = active["创建时间"].dt.strftime("%Y-%m")
    active["_date"] = active["创建时间"].dt.date
    months = sorted(active["_month"].dropna().unique())
    rows = []
    for m in months:
        # 当月出现的所有商品
        in_m = set(active.loc[active["_month"] == m, "商品名称"].dropna().unique())
        # 当月实际有多少天有数据（用于判断是否完整月）
        days_in_month = active.loc[active["_month"] == m, "_date"].nunique()
        prev = set()
        for m2 in months:
            if m2 < m:
                prev |= set(active.loc[active["_month"] == m2, "商品名称"].dropna().unique())
        new = in_m - prev
        kept = in_m & prev
        gone = prev - in_m
        # 数据完整性标记：月内天数 < 20 视为不完整（不计入淘汰/净变化）
        # 避免当月初几天因为"老商品未出现"被误判为淘汰
        incomplete = days_in_month < 20
        if incomplete:
            gone = set()  # 不完整月不淘汰
            net = len(new)  # 净变化 = 新增数（因为不淘汰）
        else:
            net = len(new) - len(gone)
        rows.append({"month": m, "pool_size": len(in_m), "new_count": len(new), "gone_count": len(gone), "kept_count": len(kept), "net_change": net, "days_with_data": days_in_month, "incomplete": incomplete})
    summary = {
        "months": len(months),
        "avg_new_per_month": round(np.mean([r["new_count"] for r in rows]), 2) if rows else 0,
        "avg_gone_per_month": round(np.mean([r["gone_count"] for r in rows]), 2) if rows else 0,
    }
    write_json(SUMMARY_DIR / "商品_月度变化.json", {"title": "月度新增淘汰"}, summary, rows)

    # 4月新增5月留存
    apr = active[active["_month"] == "2026-04"]
    may = active[active["_month"] == "2026-05"]
    apr_products = set(apr["商品名称"].dropna().unique())
    may_products = set(may["商品名称"].dropna().unique())
    new_in_4 = apr_products
    kept_in_5 = new_in_4 & may_products
    dropped = new_in_4 - may_products
    keep_rate = round(len(kept_in_5) / len(new_in_4) * 100, 2) if new_in_4 else 0
    summary = {
        "new_in_4": len(new_in_4),
        "kept_in_5": len(kept_in_5),
        "keep_rate_pct": keep_rate,
    }
    data = {
        "new_products_4": sorted(new_in_4),
        "kept_products_5": sorted(kept_in_5),
        "dropped_products": sorted(dropped),
    }
    write_json(SUMMARY_DIR / "商品_4月新增5月留存.json", {"title": "4月新增5月留存分析"}, summary, data)


# ===== 6. 风险（6 个）=====

def gen_risk(df):
    # 状态分布（全量，含关闭）
    status = df.groupby("采购单状态").size().reset_index(name="count")
    status["pct"] = (status["count"] / status["count"].sum() * 100).round(2)
    data = status.sort_values("count", ascending=False).to_dict("records")
    closed_n = int(df["采购单状态"].astype(str).str.contains("关闭", na=False).sum())
    summary = {
        "total": int(len(df)),
        "closed": closed_n,
        "closed_rate_pct": round(closed_n / len(df) * 100, 2),
    }
    write_json(SUMMARY_DIR / "风险_状态分布.json", {"title": "采购单状态分布", "note": "包含交易关闭订单"}, summary, data)

    # 供货商关闭率（订单>=100）
    sup_total = df.groupby("供货商").size().reset_index(name="total")
    sup_closed = df[is_closed(df["采购单状态"])].groupby("供货商").size().reset_index(name="closed")
    sup_merge = sup_total.merge(sup_closed, on="供货商", how="left").fillna(0)
    sup_merge["close_rate_pct"] = (sup_merge["closed"] / sup_merge["total"] * 100).round(2)
    sup_merge = sup_merge[sup_merge["total"] >= 100].sort_values("close_rate_pct", ascending=False)
    # 风险标记
    def risk_tag(pct):
        if pct >= 20: return "高风险"
        if pct >= 10: return "中风险"
        return "正常"
    def risk_color(pct):
        if pct >= 20: return "red"
        if pct >= 10: return "orange"
        return "green"
    sup_merge["risk_tag"] = sup_merge["close_rate_pct"].apply(risk_tag)
    sup_merge["risk_color"] = sup_merge["close_rate_pct"].apply(risk_color)
    sup_data = sup_merge.rename(columns={"供货商": "supplier"}).to_dict("records")
    summary = {
        "supplier_count": len(sup_data),
        "highest": sup_data[0] if sup_data else None,
    }
    write_json(SUMMARY_DIR / "风险_供货商关闭率.json", {"title": "供货商关闭率排行", "note": "订单数>=100"}, summary, sup_data)

    # 店铺关闭率（订单>=50）
    shop_total = df.groupby("店铺名称").size().reset_index(name="total")
    shop_closed = df[is_closed(df["采购单状态"])].groupby("店铺名称").size().reset_index(name="closed")
    shop_merge = shop_total.merge(shop_closed, on="店铺名称", how="left").fillna(0)
    shop_merge["close_rate_pct"] = (shop_merge["closed"] / shop_merge["total"] * 100).round(2)
    shop_merge = shop_merge[shop_merge["total"] >= 50].sort_values("close_rate_pct", ascending=False)
    shop_data = shop_merge.rename(columns={"店铺名称": "shop"}).to_dict("records")
    summary = {
        "shop_count": len(shop_data),
        "highest": shop_data[0] if shop_data else None,
    }
    write_json(SUMMARY_DIR / "风险_店铺关闭率.json", {"title": "店铺关闭率排行", "note": "订单数>=50"}, summary, shop_data)

    # 关闭率月度走势
    df = df.copy()
    df["_month"] = df["创建时间"].dt.strftime("%Y-%m")
    m_total = df.groupby("_month").size().reset_index(name="total")
    m_closed = df[is_closed(df["采购单状态"])].groupby("_month").size().reset_index(name="closed")
    m_merge = m_total.merge(m_closed, on="_month", how="left").fillna(0)
    m_merge["close_rate_pct"] = (m_merge["closed"] / m_merge["total"] * 100).round(2)
    m_data = m_merge.sort_values("_month").rename(columns={"_month": "month"}).to_dict("records")
    summary = {
        "avg_close_rate_pct": round(float(m_merge["close_rate_pct"].mean()), 2) if len(m_merge) else 0,
        "max_close_rate_pct": round(float(m_merge["close_rate_pct"].max()), 2) if len(m_merge) else 0,
        "min_close_rate_pct": round(float(m_merge["close_rate_pct"].min()), 2) if len(m_merge) else 0,
    }
    write_json(SUMMARY_DIR / "风险_关闭率月度.json", {"title": "关闭率月度走势"}, summary, m_data)

    # 关闭订单 Top
    closed = df[is_closed(df["采购单状态"])]
    by_supplier = closed.groupby("供货商").size().reset_index(name="count").sort_values("count", ascending=False).head(20).rename(columns={"供货商": "name"}).to_dict("records")
    by_shop = closed.groupby("店铺名称").size().reset_index(name="count").sort_values("count", ascending=False).head(20).rename(columns={"店铺名称": "name"}).to_dict("records")
    by_platform = closed.groupby("店铺平台").size().reset_index(name="count").sort_values("count", ascending=False).head(20).rename(columns={"店铺平台": "name"}).to_dict("records")
    write_json(SUMMARY_DIR / "风险_关闭订单Top.json", {"title": "关闭订单分布 Top"}, {}, {"by_supplier": by_supplier, "by_shop": by_shop, "by_platform": by_platform})

    # 待确认订单
    pending = df[df["采购单状态"].astype(str).str.contains("待客户确认", na=False)].copy()
    if "创建时间" in pending.columns and len(pending) > 0:
        # 转 datetime
        pending["_ct"] = pd.to_datetime(pending["创建时间"], errors="coerce")
        # 现在时间取数据中最大创建时间 + 1天（避免 0 小时全部归到 >7d）
        now_ref = pending["_ct"].max() + pd.Timedelta(days=1) if pending["_ct"].notna().any() else pd.Timestamp.now()
        pending["_hours"] = (now_ref - pending["_ct"]).dt.total_seconds() / 3600
        # 时效分桶
        buckets = [
            ("0-24小时", 0, 24),
            ("24-72小时", 24, 72),
            ("3-7天", 72, 168),
            ("7天以上", 168, 99999),
        ]
        aging = []
        for name, lo, hi in buckets:
            n = int(((pending["_hours"] >= lo) & (pending["_hours"] < hi)).sum())
            aging.append({"range": name, "count": n, "min_hours": lo, "max_hours": hi})
        # 店铺维度（待确认>5的）
        by_shop = pending.groupby("店铺名称").size().reset_index(name="count").sort_values("count", ascending=False).head(10).rename(columns={"店铺名称": "name"}).to_dict("records")
        # 供货商维度
        by_supplier = pending.groupby("供货商").size().reset_index(name="count").sort_values("count", ascending=False).head(10).rename(columns={"供货商": "name"}).to_dict("records")
        # 金额总待
        total_amount = float(pending["小计金额"].astype(str).str.replace(",", "").apply(pd.to_numeric, errors="coerce").sum())
    else:
        aging = []
        by_shop = []
        by_supplier = []
        total_amount = 0
    summary = {
        "total": int(len(pending)),
        "pct": round(len(pending) / len(df) * 100, 2) if len(df) else 0,
        "total_amount": round(total_amount, 2),
        "aging_over_24h": sum(a["count"] for a in aging if a["min_hours"] >= 24),
        "aging_over_72h": sum(a["count"] for a in aging if a["min_hours"] >= 72),
    }
    write_json(SUMMARY_DIR / "风险_待确认订单.json", {"title": "待客户确认订单"}, summary, {
        "count": int(len(pending)),
        "aging": aging,
        "by_shop": by_shop,
        "by_supplier": by_supplier,
    })


# ===== 7. 商品日度追踪 =====

def gen_product_daily_tracker(df):
    """商品日度追踪：每个商品近 N 天每天的订单数和金额 + 生命周期 + 衰退预警"""
    active = df[~is_closed(df["采购单状态"])].copy()
    active["_date"] = active["创建时间"].dt.strftime("%Y-%m-%d")
    
    all_dates = sorted(active["_date"].unique())
    recent_dates = all_dates[-14:] if len(all_dates) >= 14 else all_dates
    recent = active[active["_date"].isin(recent_dates)]
    
    # 每个商品首次出现日期（全量）
    first_seen_all = active.groupby("商品名称")["_date"].min().to_dict()
    latest_date = all_dates[-1]
    
    from datetime import datetime as dt
    latest_dt = dt.strptime(latest_date, "%Y-%m-%d")
    
    grouped = recent.groupby(["商品名称", "_date"]).agg(
        order=("采购单号", "count"), amount=("小计金额", "sum")
    ).reset_index()
    
    products = sorted(recent.groupby("商品名称")["采购单号"].count().sort_values(ascending=False).head(80).index)
    
    rows = []
    for prod in products:
        sub = grouped[grouped["商品名称"] == prod]
        daily = {r["_date"]: {"order": int(r["order"]), "amount": round(float(r["amount"]), 2)} for _, r in sub.iterrows()}
        
        # 趋势判断（最近 3 天）
        last3 = [daily.get(d, {}).get("order", 0) for d in recent_dates[-3:]]
        if len(last3) >= 3 and last3[2] > last3[1] > last3[0]:
            trend = "up"
        elif len(last3) >= 3 and last3[2] < last3[1] < last3[0]:
            trend = "down"
        else:
            trend = "flat"
        
        # 生命周期
        first_dt = dt.strptime(first_seen_all.get(prod, latest_date), "%Y-%m-%d")
        age_days = (latest_dt - first_dt).days
        if age_days <= 7:
            lifecycle = "new"  # 新品
        elif age_days <= 30:
            lifecycle = "growth"  # 成长
        else:
            lifecycle = "mature"  # 成熟
        
        # 衰退预警：连续 3 天下降
        decline_days = 0
        for i in range(len(recent_dates) - 1, 0, -1):
            cur = daily.get(recent_dates[i], {}).get("order", 0)
            prev = daily.get(recent_dates[i-1], {}).get("order", 0)
            if cur < prev and cur > 0:
                decline_days += 1
            else:
                break
        if decline_days >= 3:
            lifecycle = "decline"  # 衰退
        
        total_order = sum(daily.get(d, {}).get("order", 0) for d in recent_dates)
        total_amount = sum(daily.get(d, {}).get("amount", 0) for d in recent_dates)
        last_day_order = daily.get(recent_dates[-1], {}).get("order", 0)
        prev_day_order = daily.get(recent_dates[-2], {}).get("order", 0) if len(recent_dates) >= 2 else 0
        mom = round((last_day_order - prev_day_order) / prev_day_order * 100, 1) if prev_day_order > 0 else None
        
        rows.append({
            "product": prod,
            "total_order": total_order,
            "total_amount": round(total_amount, 2),
            "last_day_order": last_day_order,
            "prev_day_order": prev_day_order,
            "mom_pct": mom,
            "trend": trend,
            "lifecycle": lifecycle,
            "age_days": age_days,
            "decline_days": decline_days,
            "daily": {d: daily.get(d, {}).get("order", 0) for d in recent_dates},
        })
    
    summary = {
        "product_count": len(rows),
        "dates": recent_dates,
        "up_count": sum(1 for r in rows if r["trend"] == "up"),
        "down_count": sum(1 for r in rows if r["trend"] == "down"),
        "new_count": sum(1 for r in rows if r["lifecycle"] == "new"),
        "growth_count": sum(1 for r in rows if r["lifecycle"] == "growth"),
        "mature_count": sum(1 for r in rows if r["lifecycle"] == "mature"),
        "decline_count": sum(1 for r in rows if r["lifecycle"] == "decline"),
    }
    write_json(SUMMARY_DIR / "商品_日度追踪.json", {"title": "商品日度追踪", "grain": "日"}, summary, rows)


# ===== 8. 新品追踪 =====

def gen_new_product_tracker(df):
    """新品追踪：自动识别首次出现 ≤7 天的商品"""
    active = df[~is_closed(df["采购单状态"])].copy()
    active["_date"] = active["创建时间"].dt.strftime("%Y-%m-%d")
    
    # 每个商品首次出现日期
    first_seen = active.groupby("商品名称")["_date"].min().to_dict()
    
    # 最近日期
    latest_date = active["_date"].max()
    
    from datetime import datetime as dt
    latest_dt = dt.strptime(latest_date, "%Y-%m-%d")
    
    rows = []
    for prod, first_date in first_seen.items():
        first_dt = dt.strptime(first_date, "%Y-%m-%d")
        days_since = (latest_dt - first_dt).days
        
        if days_since > 14:  # 只看最近 14 天内上新的
            continue
        
        sub = active[active["商品名称"] == prod]
        total_order = len(sub)
        total_amount = round(float(sub["小计金额"].sum()), 2)
        
        # 每天订单数
        daily = sub.groupby("_date").size().to_dict()
        daily_series = {d: daily.get(d, 0) for d in sorted(set(active["_date"])) if d >= first_date}
        
        rows.append({
            "product": prod,
            "first_seen": first_date,
            "days_since": days_since,
            "total_order": total_order,
            "total_amount": total_amount,
            "avg_daily": round(total_order / max(days_since, 1), 2),
            "daily": daily_series,
        })
    
    rows.sort(key=lambda x: x["first_seen"], reverse=True)
    
    summary = {
        "new_product_count": len(rows),
        "latest_date": latest_date,
        "total_new_orders": sum(r["total_order"] for r in rows),
        "total_new_amount": sum(r["total_amount"] for r in rows),
    }
    write_json(SUMMARY_DIR / "新品_追踪.json", {"title": "新品追踪", "grain": "日"}, summary, rows)


# ===== 9. 每日经营日报 =====

def gen_daily_report(df):
    """每日经营日报：销售额/售后额/增长商品/售后率"""
    df = df.copy()
    df["_date"] = df["创建时间"].dt.strftime("%Y-%m-%d")

    # 成功订单
    active = df[~is_closed(df["采购单状态"])]
    # 关闭订单
    closed = df[is_closed(df["采购单状态"])]
    # 售后订单：商家收货 / 商家退款 / 修改申请 / 寄回商品 / 商家审核
    aftersale_statuses = ["商家收货", "商家退款", "修改申请", "寄回商品", "商家审核"]
    aftersale = df[df["售后状态"].astype(str).isin(aftersale_statuses)]

    all_dates = sorted(active["_date"].unique())

    rows = []
    for d in all_dates:
        day_active = active[active["_date"] == d]
        day_closed = closed[closed["_date"] == d]
        day_aftersale = aftersale[aftersale["_date"] == d]

        sales_amount = round(float(day_active["小计金额"].sum()), 2)
        close_amount = round(float(day_closed["小计金额"].sum()), 2) if len(day_closed) > 0 else 0
        aftersale_amount = round(float(day_aftersale["小计金额"].sum()), 2) if len(day_aftersale) > 0 else 0
        
        # 按商品聚合
        prod_stats = day_active.groupby("商品名称").agg(
            order=("采购单号", "count"),
            amount=("小计金额", "sum")
        ).reset_index()
        
        # 前一天数据（用于算环比）
        prev_date = all_dates[all_dates.index(d) - 1] if all_dates.index(d) > 0 else None
        if prev_date:
            prev_active = active[active["_date"] == prev_date]
            prev_prod = prev_active.groupby("商品名称").agg(prev_order=("采购单号", "count")).reset_index()
            merged = prod_stats.merge(prev_prod, on="商品名称", how="left").fillna(0)
            merged["mom_pct"] = ((merged["order"] - merged["prev_order"]) / merged["prev_order"].replace(0, float("nan")) * 100).round(1)
        else:
            merged = prod_stats
            merged["mom_pct"] = None
        
        # Top5 增长
        growth = merged[merged["mom_pct"] > 0].sort_values("mom_pct", ascending=False).head(5)
        growth_list = [{"product": r["商品名称"], "order": int(r["order"]), "mom_pct": float(r["mom_pct"])} for _, r in growth.iterrows()] if "mom_pct" in merged.columns else []
        
        # Top5 下降
        decline = merged[merged["mom_pct"] < 0].sort_values("mom_pct").head(5)
        decline_list = [{"product": r["商品名称"], "order": int(r["order"]), "mom_pct": float(r["mom_pct"])} for _, r in decline.iterrows()] if "mom_pct" in merged.columns else []
        
        rows.append({
            "date": d,
            "orders": len(day_active),
            "sales_amount": sales_amount,
            "close_orders": len(day_closed),
            "close_amount": close_amount,
            "aftersale_orders": len(day_aftersale),
            "aftersale_amount": aftersale_amount,
            "product_count": len(prod_stats),
            "growth_top5": growth_list,
            "decline_top5": decline_list,
        })
    
    # 最近 7 天汇总
    recent = rows[-7:] if len(rows) >= 7 else rows
    summary = {
        "latest_date": all_dates[-1],
        "total_days": len(rows),
        "recent_7d_sales": sum(r["sales_amount"] for r in recent),
        "recent_7d_orders": sum(r["orders"] for r in recent),
        "recent_7d_aftersale": sum(r["aftersale_amount"] for r in recent),
    }
    write_json(SUMMARY_DIR / "经营_每日日报.json", {"title": "每日经营日报", "grain": "日"}, summary, rows)


# ===== 主入口 =====

def main():
    print("读数据中...")
    df = load_all()
    print(f"  ✓ {len(df)} 行")
    print()
    print("生成汇总 json...")
    funcs = [
        ("KPI 总览", gen_kpi),
        ("供货商排行", gen_supplier_ranking),
        ("供货商月度明细", gen_supplier_monthly),
        ("平台 × 店铺 × 粒度", gen_platforms),
        ("销售业绩 日/周/月", gen_sales),
        ("商品（5 个）", gen_products),
        ("风险（6 个）", gen_risk),
        ("商品日度追踪", gen_product_daily_tracker),
        ("新品追踪", gen_new_product_tracker),
        ("每日经营日报", gen_daily_report),
    ]
    for name, fn in funcs:
        try:
            fn(df)
            print(f"  ✓ {name}")
        except Exception as e:
            print(f"  ❌ {name}: {e}")
            import traceback; traceback.print_exc()
    print()
    print(f"完成。{len(list(SUMMARY_DIR.glob('*.json')))} 个 json 写入 {SUMMARY_DIR}")


if __name__ == "__main__":
    main()
