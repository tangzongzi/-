"""
export_detail.py — 明细数据导出

从全量 xlsx 数据，按"状态"切片，生成 /数据/明细/ 下 10 个文件（5 对 csv/json）。

调用方式：
    python3 export_detail.py

输出：
- 明细_全部订单.csv/.json   - 已去关闭
- 明细_关闭订单.csv/.json   - 交易关闭
- 明细_售后订单.csv/.json   - 触发了售后
- 明细_完整版.csv/.json     - 全量（含关闭）
- 明细_待确认.csv/.json     - 待客户确认
"""

import json
import pandas as pd
from pathlib import Path
from data_loader import load_all

DATA_DIR = Path("/Users/manba/Documents/OH-WorkSpace/多赞数据库/多赞采购单/数据")
DETAIL_DIR = DATA_DIR / "明细"
DETAIL_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_COLS = [
    "采购单号", "创建时间", "付款时间", "发货时间",
    "供货商", "商品名称", "规格", "商品编码",
    "数量", "已发数量", "采购单状态", "售后状态",
    "小计金额", "运费", "物流单号", "物流公司",
    "收件人-姓名", "收件人-电话",
    "收件地址-省", "收件地址-市", "收件地址-区",
    "店铺平台", "店铺名称", "店铺单号", "店铺商品小计",
]


def write_pair(name, df):
    """写一对 csv/json"""
    df_out = df[OUTPUT_COLS].copy()
    # CSV：把时间转字符串
    df_csv = df_out.copy()
    for col in ["创建时间", "付款时间", "发货时间"]:
        df_csv[col] = df_csv[col].dt.strftime("%Y/%m/%d %H:%M:%S").fillna("")
    df_csv.to_csv(DETAIL_DIR / f"{name}.csv", index=False, encoding="utf-8-sig")
    # JSON：保留 datetime
    df_out["创建时间"] = df_out["创建时间"].dt.strftime("%Y-%m-%dT%H:%M:%S")
    df_out["付款时间"] = df_out["付款时间"].dt.strftime("%Y-%m-%dT%H:%M:%S")
    df_out["发货时间"] = df_out["发货时间"].dt.strftime("%Y-%m-%dT%H:%M:%S")
    df_out = df_out.where(pd.notna(df_out), None)
    records = df_out.to_dict("records")
    with open(DETAIL_DIR / f"{name}.json", "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False)
    print(f"  ✓ {name}: {len(df_out)} 行 (csv {DETAIL_DIR / f'{name}.csv'})")


def main():
    print("读数据中...")
    df = load_all()
    print(f"  ✓ {len(df)} 行")
    print()
    print("生成 5 对 csv/json...")
    # 全部（已去关闭）
    write_pair("明细_全部订单", df[~df["采购单状态"].astype(str).str.contains("关闭", na=False)])
    # 关闭
    write_pair("明细_关闭订单", df[df["采购单状态"].astype(str).str.contains("关闭", na=False)])
    # 售后（售后状态非空）
    write_pair("明细_售后订单", df[df["售后状态"].notna() & (df["售后状态"].astype(str) != "")])
    # 完整版
    write_pair("明细_完整版", df)
    # 待确认
    write_pair("明细_待确认", df[df["采购单状态"].astype(str).str.contains("待客户确认", na=False)])
    print()
    print(f"完成。10 个文件写入 {DETAIL_DIR}")


if __name__ == "__main__":
    main()
