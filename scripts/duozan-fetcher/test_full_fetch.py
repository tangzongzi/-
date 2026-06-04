#!/usr/bin/env python3
"""
测试一次性拉完全部 376 条订单
"""
import requests
import json

TENANT_ID = "93e4349a-aed8-b6b2-b576-3a0b308e1a79"
ACCESS_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjQ0MTY5MTU0NzcxMkVBQUZGNTk4NzRCRUQyMkMwM0QzQTFGOUExRjFSUzI1NiIsInR5cCI6ImF0K2p3dCIsIng1dCI6IlJCYVJWSGNTNnFfMW1IUy0waXdEMDZINW9mRSJ9.eyJuYmYiOjE3ODA1NjUyNzYsImV4cCI6MTc4MTg2MTI3NiwiaXNzIjoiaHR0cHM6Ly9hdXRoLmR1b3phbi5jb20iLCJhdWQiOlsiQmxvYlN0b3JpbmdBcGlTZXJ2ZXIiLCJFYXN5ZnhHb29kRWxhc3RpY1NlcnZlciIsIkVhc3lmeEdvb2RQdWh1b1NlcnZlciIsIkVhc3lmeEhvc3RXZWIiLCJTZW5kT3JkZXJBcGlTZXJ2ZXIiLCJTdGF0aXN0aWNzQXBpU2VydmVyIiwiVGVuYW50QXBpU2VydmVyIiwiV3hXb3JrQXBpU2VydmVyIl0sImNsaWVudF9pZCI6ImVhc3lmeC1wYy1jbGllbnQiLCJzdWIiOiI5M2U0MzQ5YS1hZWQ4LWI2YjItYjU3Ni0zYTBiMzA4ZTFhNzkiLCJhdXRoX3RpbWUiOjE3ODA1NjUyNzYsImlkcCI6ImxvY2FsIiwidGVuYW50aWQiOiI5M2U0MzQ5YS1hZWQ4LWI2YjItYjU3Ni0zYTBiMzA4ZTFhNzkiLCJzX3VzZXJJZCI6IjkzZTQzNDlhLWFlZDgtYjZiMi1iNTc2LTNhMGIzMDhlMWE3OSIsInJvbGUiOiJhZG1pbiIsImh0dHA6Ly9zY2hlbWFzLnhtbHNvYXAub3JnL3dzLzIwMDUvMDUvaWRlbnRpdHkvY2xhaW1zL2dpdmVubmFtZSI6ImFkbWluIiwicGhvbmVfbnVtYmVyIjoiMTMzNzU4NDU5MTUiLCJwaG9uZV9udW1iZXJfdmVyaWZpZWQiOiJGYWxzZSIsImVtYWlsIjoiMTMzNzU4NDU5MTVAZHVvemFuLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjoiRmFsc2UiLCJuYW1lIjoiMTMzNzU4NDU5MTUiLCJpYXQiOjE3ODA1NjUyNzYsInNjb3BlIjpbImFkZHJlc3MiLCJCbG9iU3RvcmluZ0FwaVNlcnZlciIsIkVhc3lmeEdvb2RFbGFzdGljU2VydmVyIiwiRWFzeWZ4R29vZFB1aHVvU2VydmVyIiwiRWFzeWZ4SG9zdFdlYiIsImVtYWlsIiwib3BlbmlkIiwicGhvbmUiLCJwcm9maWxlIiwicm9sZSIsIlNlbmRPcmRlckFwaVNlcnZlciIsIlN0YXRpc3RpY3NBcGlTZXJ2ZXIiLCJUZW5hbnRBcGlTZXJ2ZXIiLCJXeFdvcmtBcGlTZXJ2ZXIiLCJvZmZsaW5lX2FjY2VzcyJdLCJhbXIiOlsidGVuYW50X3Bhc3N3b3JkIl19.kfC7SVtHT8_6nj02AyG8ewsCWpOkX9JyRnOJ6zHzzv19zWFG-hplg-id6pI8M0ID-TdeDhQZpLwC3_UvPh7iiJ_EbCMy_MrdWXfcUozvqBPOdNNJ5g4Wy_YM_qdQPPsjUjzMmSWN19dYP54PDBR1i5wtVSZGCoPvhblPvUvnEwaz76J92CUcYfdAboRFfFSP3iRae67enREqzVeleR4Zy4qzRXBaDNtENXliVDpM2_6BfpxX5wOf1wtrOPeoG1A7jVJrWEjV_VDNl8OM8b6bN8gqMJDUAKJHAf3nJJoyH6mOuFvPDQ3Lho_x2f7zFshxjS2qmAtvqWo8u6pvq-RJIg"

url = "https://order.duozan.com/api/purchase-order"
headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "TenantId": TENANT_ID,
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.7339.249 Safari/537.36",
    "Referer": "https://easyfx.duozan.com/",
    "Origin": "https://easyfx.duozan.com",
}

print("=" * 60)
print("测试一次性拉完 376 条")
print("=" * 60)

# 试试 maxResultCount=500
params = {
    "orderType": 1,
    "dateTimeType": 1,
    "skipCount": 0,
    "maxResultCount": 500,
    "startTime": "2026-06-03 00:00:00",
    "endTime": "2026-06-03 23:59:59"
}

resp = requests.get(url, params=params, headers=headers, timeout=15)
data = resp.json()
print(f"maxResultCount=500 → totalCount={data.get('totalCount')}, items={len(data.get('items', []))}")

# 试 maxResultCount=1000
params["maxResultCount"] = 1000
resp = requests.get(url, params=params, headers=headers, timeout=15)
data = resp.json()
print(f"maxResultCount=1000 → totalCount={data.get('totalCount')}, items={len(data.get('items', []))}")

# 翻页拿全 376 条
all_items = []
skip = 0
page_size = 200
while True:
    params["skipCount"] = skip
    params["maxResultCount"] = page_size
    resp = requests.get(url, params=params, headers=headers, timeout=15)
    data = resp.json()
    items = data.get("items", [])
    if not items:
        break
    all_items.extend(items)
    print(f"  翻页 skip={skip}, 拉到 {len(items)} 条, 累计 {len(all_items)}/{data.get('totalCount')}")
    if len(all_items) >= data.get("totalCount", 0):
        break
    skip += page_size

print(f"\n✅ 翻页拿全: 共 {len(all_items)} 条")
print(f"  总订单数: {data.get('totalCount')}")

# 简单校验
import collections
prof_sum = sum(float(item.get("profit", 0) or 0) for item in all_items)
pay_sum = sum(float(item.get("payment", 0) or 0) for item in all_items)
suppliers = collections.Counter(item.get("supplierName") for item in all_items)
shops = collections.Counter((item.get("customerOrder") or {}).get("shopName") for item in all_items)

print(f"\n📊 汇总:")
print(f"  金额合计: ¥{pay_sum:.2f}")
print(f"  利润合计: ¥{prof_sum:.2f}")
print(f"  平均利润率: {prof_sum/pay_sum*100:.2f}%" if pay_sum else "")
print(f"  供应商数: {len(suppliers)}")
print(f"  店铺数: {len(shops)}")
print(f"\n  Top 5 供应商:")
for name, cnt in suppliers.most_common(5):
    print(f"    {name}: {cnt} 单")
print(f"\n  Top 5 店铺:")
for name, cnt in shops.most_common(5):
    print(f"    {name}: {cnt} 单")

# 存全量数据
output_path = "/tmp/duozan-investigate/api_20260603_full.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump({"totalCount": data.get("totalCount"), "items": all_items}, f, ensure_ascii=False, indent=2)
print(f"\n✅ 全量数据存到: {output_path}")
