#!/usr/bin/env python3
"""
duozan_fetcher - 多赞采购单自动抓取器

功能：
  1. 从 auth.py 拿 token（自动检查失效）
  2. 调 API 抓指定日期的采购单
  3. 落成 xlsx（对齐老板现有 25 字段格式 + 新增"利润"列）
  4. 输出到 /多赞数据库/多赞采购单/数据/按日期/YYYY-MM-DD/采购单_YYYYMMDD-YYYYMMDD.xlsx

用法：
  python3 fetch_and_export.py <YYYY-MM-DD>
  例如：python3 fetch_and_export.py 2026-06-03
  不传参数 = 抓昨天
"""
import sys
import os
import json
import requests
import openpyxl
from datetime import datetime, timedelta
from pathlib import Path

# 引入 auth
sys.path.insert(0, str(Path(__file__).parent))
import auth

# ============================================================
# 配置
# ============================================================
API_URL = "https://order.duozan.com/api/purchase-order"

# 25 字段 + 1 利润字段（老板现有格式 + 新增）
COLUMNS = [
    "采购单号", "创建时间", "付款时间", "发货时间",
    "供货商", "商品名称", "规格", "商品编码",
    "数量", "已发数量",
    "采购单状态", "售后状态",
    "小计金额", "运费", "物流单号", "物流公司",
    "收件人-姓名", "收件人-电话", "收件地址-省", "收件地址-市", "收件地址-区",
    "店铺平台", "店铺名称", "店铺单号", "店铺商品小计",
    "利润",  # ★ 新增，老板最关心的字段
]

# 输出根目录
OUTPUT_ROOT = Path("/Users/manba/Documents/OH-WorkSpace/多赞数据库/多赞采购单/数据/按日期")


# ============================================================
# 抓取
# ============================================================
def fetch_orders(date_str: str, token_info: dict) -> dict:
    """抓取指定日期的采购单。date_str 格式: YYYY-MM-DD"""
    headers = {
        "Authorization": f"Bearer {token_info['access_token']}",
        "TenantId": token_info['tenant_id'],
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.7339.249 Safari/537.36",
        "Referer": "https://easyfx.duozan.com/",
        "Origin": "https://easyfx.duozan.com",
    }
    params = {
        "orderType": 1,
        "dateTimeType": 1,  # 创建时间
        "skipCount": 0,
        "maxResultCount": 1000,  # 一天最多 1000 条，足够
        "startTime": f"{date_str} 00:00:00",
        "endTime": f"{date_str} 23:59:59",
    }
    resp = requests.get(API_URL, params=params, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.json()


# ============================================================
# 字段映射：API JSON → xlsx 行
# ============================================================
def map_to_row(item: dict) -> list:
    """把一条 API 订单转成 xlsx 行"""
    # 解 orderDetails（一个采购单可能多个商品 → 多行）
    details = item.get("orderDetails") or []
    if not details:
        return [map_one_detail(item, {})]
    return [map_one_detail(item, d) for d in details]


def map_one_detail(item: dict, detail: dict) -> list:
    """单行映射"""
    good = (detail or {}).get("good") or {}
    specs = good.get("goodSkuSpecs") or []
    spec_text = "，".join(
        f"{s.get('saleProperty', '')}：{s.get('salePropertyValue', '')}"
        for s in specs
    )

    # 售后状态：API 有 isPostSaleing + postSaleType
    is_post_saleing = detail.get("isPostSaleing", False)
    post_sale_type = detail.get("postSaleType", 0)
    if is_post_saleing:
        aftersale = "售后中" if post_sale_type == 1 else "退款中"
    else:
        aftersale = ""

    # ★ 利润口径：交易关闭订单不计入利润（货没真发出去/钱没收）
    # 关闭订单的 profit 字段后端有值，但业务上不能算"实际利润"，置 None
    is_closed = item.get("statusStr") == "交易关闭"
    profit_val = None if is_closed else item.get("profit", 0)

    # 店铺平台：stationType 是平台标识
    #   station=11 = 抖店, station=2 = 拼多多
    #   经验性映射（已对照老板 6/3 原文件验证：376/376 匹配）
    customer_order = item.get("customerOrder") or {}
    station_type = customer_order.get("stationType", 0)
    PLATFORM_MAP = {11: "抖店", 2: "拼多多"}
    platform = PLATFORM_MAP.get(station_type, "")

    # 收件地址（API 里是加密的 + 拼接好的明文）
    addr = (item.get("orderAddress") or {}).get("address", "") or ""

    # 拆省/市/区
    province, city, district = "", "", ""
    if addr:
        # 简单按空格拆："安徽省 马鞍山市 花山区 xxx"
        parts = addr.split(" ")
        if len(parts) >= 1: province = parts[0]
        if len(parts) >= 2: city = parts[1]
        if len(parts) >= 3: district = parts[2]

    # 付款时间（API 没明确字段，但 lastSendTime 是发货时间）
    # 实际可能从 buyerName / creationTime + 几秒推算，先空
    pay_time = ""  # API 没暴露

    return [
        item.get("id", ""),                              # 采购单号
        item.get("creationTime", ""),                    # 创建时间
        pay_time,                                        # 付款时间（API 无）
        (item.get("lastSendTime") or ""),                # 发货时间
        item.get("supplierName", ""),                    # 供货商
        good.get("title", ""),                           # 商品名称
        spec_text,                                       # 规格
        good.get("artNo", "") or good.get("specId", ""), # 商品编码
        detail.get("number", 0) if detail else item.get("goodCount", 0),  # 数量
        detail.get("hasSendNumber", 0) if detail else 0, # 已发数量
        item.get("statusStr", ""),                       # 采购单状态
        aftersale,                                       # 售后状态
        item.get("payment", 0),                          # 小计金额
        item.get("postFee", 0),                          # 运费
        "",                                              # 物流单号（API 无）
        "",                                              # 物流公司（API 无）
        "",                                              # 收件人-姓名（API 加密）
        "",                                              # 收件人-电话（API 加密）
        province,                                        # 收件地址-省
        city,                                            # 收件地址-市
        district,                                        # 收件地址-区
        platform,                                        # 店铺平台
        customer_order.get("shopName", ""),              # 店铺名称
        customer_order.get("shopOrderId", ""),           # 店铺单号
        "",                                              # 店铺商品小计（API 无）
        profit_val,                                      # ★ 利润（交易关闭订单为 None，不计入）
    ]


# ============================================================
# 落 xlsx
# ============================================================
def save_xlsx(date_str: str, rows: list) -> Path:
    """落 xlsx 到 /数据/按日期/YYYY-MM-DD/采购单_YYYYMMDD-YYYYMMDD.xlsx"""
    # 创建日期目录
    day_dir = OUTPUT_ROOT / date_str
    day_dir.mkdir(parents=True, exist_ok=True)

    # 文件名：采购单_20260603-20260603.xlsx
    compact = date_str.replace("-", "")
    filename = f"采购单_{compact}-{compact}.xlsx"
    filepath = day_dir / filename

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "采购单"
    ws.append(COLUMNS)
    for row in rows:
        ws.append(row)
    wb.save(filepath)

    return filepath


# ============================================================
# 主流程
# ============================================================
def main():
    # 参数解析：
    #   python3 fetch_and_export.py              → 抓昨天，落盘到 /按日期/
    #   python3 fetch_and_export.py YYYY-MM-DD   → 抓指定日期，落盘到 /按日期/
    #   python3 fetch_and_export.py YYYY-MM-DD --realtime  → 抓指定日期，落盘到 /tmp/_realtime/（不更新 dashboard）
    args = sys.argv[1:]
    is_realtime = "--realtime" in args
    args = [a for a in args if not a.startswith("--")]

    if not args:
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        date_str = yesterday
        print(f"未传日期，默认抓昨天: {yesterday}")
    else:
        date_str = args[0]

    print("=" * 60)
    mode = "实时追踪" if is_realtime else "全量抓取"
    print(f"多赞采购单抓取 - {date_str} ({mode})")
    print("=" * 60)

    # 0. 拿 token
    try:
        token_info = auth.load_token()
        print(f"\n[0/3] Token 有效（剩 {token_info['days_left']:.1f} 天）")
    except Exception as e:
        print(f"\n❌ Token 错误: {e}")
        sys.exit(2)

    # 1. 抓数据
    print(f"\n[1/3] 抓取 {date_str} 的采购单...")
    try:
        data = fetch_orders(date_str, token_info)
    except requests.exceptions.HTTPError as e:
        print(f"      ❌ API 错误: {e}")
        sys.exit(3)
    except Exception as e:
        print(f"      ❌ 抓取失败: {e}")
        sys.exit(3)
    items = data.get("items", [])
    total = data.get("totalCount", 0)
    print(f"      抓到 {len(items)} / {total} 条")

    # 2. 字段映射
    print(f"\n[2/3] 字段映射 (利润 = 后端权威计算)...")
    all_rows = []
    for item in items:
        all_rows.extend(map_to_row(item))
    print(f"      生成 {len(all_rows)} 行 (含多商品拆分)")

    # 3. 落 xlsx
    print(f"\n[3/3] 落 xlsx...")
    if is_realtime:
        # 实时模式：落盘到 /tmp/_realtime/，不污染 dashboard
        import shutil
        tmp_dir = Path("/tmp/_duozan_realtime")
        tmp_dir.mkdir(parents=True, exist_ok=True)
        compact = date_str.replace("-", "")
        ts = datetime.now().strftime("%H%M%S")
        filepath = tmp_dir / f"采购单_{compact}_{ts}.xlsx"
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "采购单"
        ws.append(COLUMNS)
        for row in all_rows:
            ws.append(row)
        wb.save(filepath)
        print(f"      ✅ 临时存到: {filepath}")
    else:
        filepath = save_xlsx(date_str, all_rows)
        print(f"      ✅ 存到: {filepath}")

    # 汇总
    # ★ 利润只计非关闭订单（用 None 跳过关闭的）
    profit_sum = sum(float(r[25]) for r in all_rows if r[25] is not None)
    payment_sum = sum(float(r[12] or 0) for r in all_rows)
    closed_pay = sum(float(r[12] or 0) for r in all_rows if r[10] == "交易关闭")
    closed_count = sum(1 for r in all_rows if r[10] == "交易关闭")
    print(f"\n📊 {date_str} 数据汇总 (口径：交易关闭订单利润不计入):")
    print(f"   订单条数: {len(items)} (采购单)")
    print(f"   数据行数: {len(all_rows)} (含商品拆分)")
    print(f"   金额合计: ¥{payment_sum:.2f}")
    print(f"   利润合计: ¥{profit_sum:.2f}  (★ 已剔除 {closed_count} 单交易关闭订单)")
    if payment_sum > 0:
        print(f"   平均利润率: {profit_sum/payment_sum*100:.2f}%")
    if closed_pay > 0:
        print(f"   (供参考) 关闭订单金额: ¥{closed_pay:.2f} / {closed_count} 单")

    return filepath


if __name__ == "__main__":
    main()
