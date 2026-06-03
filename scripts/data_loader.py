"""
data_loader.py — 数据加载与合并

功能：
- 读 /数据/按日期/YYYY-MM-DD/ 下的所有 xlsx（每日新数据）
- 读 /数据/原始_采购单_*.xlsx（历史全量）
- 合并、去重、按"创建时间"排序
- 返回标准化 DataFrame

设计原则：
- 字段名跟历史 xlsx 完全一致（25 列）
- 用"采购单号"做去重 key
- 关闭订单的判定：采购单状态包含"关闭"二字
"""

import pandas as pd
import glob
import os
from pathlib import Path

# 数据根目录
DATA_DIR = Path("/Users/manba/Documents/OH-WorkSpace/多赞数据库/多赞采购单/数据")
BY_DATE_DIR = DATA_DIR / "按日期"
HISTORY_XLSX_GLOB = str(DATA_DIR / "原始_采购单_*.xlsx")

# 25 个标准字段（跟历史 xlsx 一致）
STANDARD_COLS = [
    "采购单号", "创建时间", "付款时间", "发货时间",
    "供货商", "商品名称", "规格", "商品编码",
    "数量", "已发数量", "采购单状态", "售后状态",
    "小计金额", "运费", "物流单号", "物流公司",
    "收件人-姓名", "收件人-电话",
    "收件地址-省", "收件地址-市", "收件地址-区",
    "店铺平台", "店铺名称", "店铺单号", "店铺商品小计",
]


def _read_xlsx(path: str) -> pd.DataFrame:
    """读一个 xlsx，标准化字段"""
    df = pd.read_excel(path, sheet_name=0)
    # 字段对齐
    df = df.reindex(columns=STANDARD_COLS)
    return df


def load_all() -> pd.DataFrame:
    """
    合并所有数据源：
    1. /数据/按日期/YYYY-MM-DD/*.xlsx（每日新数据）
    2. /数据/原始_采购单_*.xlsx（历史全量基线）
    返回去重、按"创建时间"排序的 DataFrame
    """
    frames = []

    # 1. 读每日按日期归档的 xlsx
    if BY_DATE_DIR.exists():
        for daily_dir in sorted(BY_DATE_DIR.iterdir()):
            if not daily_dir.is_dir():
                continue
            for xlsx in sorted(daily_dir.glob("*.xlsx")):
                frames.append(_read_xlsx(str(xlsx)))

    # 2. 读历史全量 xlsx
    for hist in glob.glob(HISTORY_XLSX_GLOB):
        frames.append(_read_xlsx(hist))

    if not frames:
        raise FileNotFoundError("没找到任何 xlsx 数据源")

    df = pd.concat(frames, ignore_index=True)

    # 标准化时间字段
    df["创建时间"] = pd.to_datetime(df["创建时间"], errors="coerce")
    df["付款时间"] = pd.to_datetime(df["付款时间"], errors="coerce")
    df["发货时间"] = pd.to_datetime(df["发货时间"], errors="coerce")

    # 标准化金额
    df["小计金额"] = pd.to_numeric(df["小计金额"], errors="coerce").fillna(0)

    # 按"采购单号"去重（保留创建时间最新的）
    df = df.dropna(subset=["采购单号"])
    df = df.sort_values("创建时间").drop_duplicates("采购单号", keep="last")

    # 按"创建时间"排序
    df = df.sort_values("创建时间").reset_index(drop=True)

    return df


def mark_closed(df: pd.DataFrame) -> pd.DataFrame:
    """标记'已关闭'订单（在原 df 上加 'is_closed' 列）"""
    df = df.copy()
    df["is_closed"] = df["采购单状态"].astype(str).str.contains("关闭", na=False)
    return df


if __name__ == "__main__":
    df = load_all()
    print(f"总行数：{len(df)}")
    print(f"时间范围：{df['创建时间'].min()} ~ {df['创建时间'].max()}")
    print(f"平台：{df['店铺平台'].unique()}")
    print(f"店铺数：{df['店铺名称'].nunique()}")
    print(f"供货商数：{df['供货商'].nunique()}")
    print(f"商品数：{df['商品名称'].nunique()}")
    print(f"关闭订单：{df['采购单状态'].astype(str).str.contains('关闭', na=False).sum()}")
