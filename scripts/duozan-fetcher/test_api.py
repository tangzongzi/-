#!/usr/bin/env python3
"""
第 1 步验证：用 Python + 抓到的 token 直接调 API
不依赖浏览器，看脚本能跑通
"""
import requests
import json
from datetime import datetime

# 从浏览器抓到的 token（直接用，不登录）
TENANT_ID = "93e4349a-aed8-b6b2-b576-3a0b308e1a79"
ACCESS_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjQ0MTY5MTU0NzcxMkVBQUZGNTk4NzRCRUQyMkMwM0QzQTFGOUExRjFSUzI1NiIsInR5cCI6ImF0K2p3dCIsIng1dCI6IlJCYVJWSGNTNnFfMW1IUy0waXdEMDZINW9mRSJ9.eyJuYmYiOjE3ODA1NjUyNzYsImV4cCI6MTc4MTg2MTI3NiwiaXNzIjoiaHR0cHM6Ly9hdXRoLmR1b3phbi5jb20iLCJhdWQiOlsiQmxvYlN0b3JpbmdBcGlTZXJ2ZXIiLCJFYXN5ZnhHb29kRWxhc3RpY1NlcnZlciIsIkVhc3lmeEdvb2RQdWh1b1NlcnZlciIsIkVhc3lmeEhvc3RXZWIiLCJTZW5kT3JkZXJBcGlTZXJ2ZXIiLCJTdGF0aXN0aWNzQXBpU2VydmVyIiwiVGVuYW50QXBpU2VydmVyIiwiV3hXb3JrQXBpU2VydmVyIl0sImNsaWVudF9pZCI6ImVhc3lmeC1wYy1jbGllbnQiLCJzdWIiOiI5M2U0MzQ5YS1hZWQ4LWI2YjItYjU3Ni0zYTBiMzA4ZTFhNzkiLCJhdXRoX3RpbWUiOjE3ODA1NjUyNzYsImlkcCI6ImxvY2FsIiwidGVuYW50aWQiOiI5M2U0MzQ5YS1hZWQ4LWI2YjItYjU3Ni0zYTBiMzA4ZTFhNzkiLCJzX3VzZXJJZCI6IjkzZTQzNDlhLWFlZDgtYjZiMi1iNTc2LTNhMGIzMDhlMWE3OSIsInJvbGUiOiJhZG1pbiIsImh0dHA6Ly9zY2hlbWFzLnhtbHNvYXAub3JnL3dzLzIwMDUvMDUvaWRlbnRpdHkvY2xhaW1zL2dpdmVubmFtZSI6ImFkbWluIiwicGhvbmVfbnVtYmVyIjoiMTMzNzU4NDU5MTUiLCJwaG9uZV9udW1iZXJfdmVyaWZpZWQiOiJGYWxzZSIsImVtYWlsIjoiMTMzNzU4NDU5MTVAZHVvemFuLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjoiRmFsc2UiLCJuYW1lIjoiMTMzNzU4NDU5MTUiLCJpYXQiOjE3ODA1NjUyNzYsInNjb3BlIjpbImFkZHJlc3MiLCJCbG9iU3RvcmluZ0FwaVNlcnZlciIsIkVhc3lmeEdvb2RFbGFzdGljU2VydmVyIiwiRWFzeWZ4R29vZFB1aHVvU2VydmVyIiwiRWFzeWZ4SG9zdFdlYiIsImVtYWlsIiwib3BlbmlkIiwicGhvbmUiLCJwcm9maWxlIiwicm9sZSIsIlNlbmRPcmRlckFwaVNlcnZlciIsIlN0YXRpc3RpY3NBcGlTZXJ2ZXIiLCJUZW5hbnRBcGlTZXJ2ZXIiLCJXeFdvcmtBcGlTZXJ2ZXIiLCJvZmZsaW5lX2FjY2VzcyJdLCJhbXIiOlsidGVuYW50X3Bhc3N3b3JkIl19.kfC7SVtHT8_6nj02AyG8ewsCWpOkX9JyRnOJ6zHzzv19zWFG-hplg-id6pI8M0ID-TdeDhQZpLwC3_UvPh7iiJ_EbCMy_MrdWXfcUozvqBPOdNNJ5g4Wy_YM_qdQPPsjUjzMmSWN19dYP54PDBR1i5wtVSZGCoPvhblPvUvnEwaz76J92CUcYfdAboRFfFSP3iRae67enREqzVeleR4Zy4qzRXBaDNtENXliVDpM2_6BfpxX5wOf1wtrOPeoG1A7jVJrWEjV_VDNl8OM8b6bN8gqMJDUAKJHAf3nJJoyH6mOuFvPDQ3Lho_x2f7zFshxjS2qmAtvqWo8u6pvq-RJIg"

# 调 API 拿 6/3 数据
url = "https://order.duozan.com/api/purchase-order"
params = {
    "orderType": 1,
    "dateTimeType": 1,  # 创建时间
    "skipCount": 0,
    "maxResultCount": 200,  # 一次拉完
    "startTime": "2026-06-03 00:00:00",
    "endTime": "2026-06-03 23:59:59"
}
headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "TenantId": TENANT_ID,
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.7339.249 Safari/537.36",
    "Referer": "https://easyfx.duozan.com/",
    "Origin": "https://easyfx.duozan.com",
}

print("=" * 60)
print("Step 1: Python 调 API 验证")
print("=" * 60)

resp = requests.get(url, params=params, headers=headers, timeout=15)
print(f"HTTP 状态码: {resp.status_code}")
print(f"返回长度: {len(resp.text)} 字节")

if resp.status_code != 200:
    print(f"❌ 失败: {resp.text[:500]}")
    exit(1)

data = resp.json()
print(f"\n总订单数 (totalCount): {data.get('totalCount')}")
print(f"本次返回条数 (items): {len(data.get('items', []))}")

if data.get('items'):
    first = data['items'][0]
    print(f"\n第一条订单关键字段:")
    print(f"  采购单号: {first.get('id')}")
    print(f"  创建时间: {first.get('creationTime')}")
    print(f"  金额 (payment): {first.get('payment')}")
    print(f"  利润 (profit): {first.get('profit')}")
    print(f"  采购单状态: {first.get('statusStr')}")
    print(f"  付款状态: {first.get('paidStatusStr')}")
    print(f"  供应商: {first.get('supplierName')}")
    if first.get('orderDetails'):
        d = first['orderDetails'][0]
        print(f"  商品名: {d.get('good', {}).get('title', '')[:40]}")
        print(f"  单价: {d.get('price')}")
        print(f"  数量: {d.get('number')}")
        print(f"  发货状态: {d.get('sendStatusStr')}")
    if first.get('customerOrder'):
        print(f"  店铺名: {first['customerOrder'].get('shopName')}")
        print(f"  店铺单号: {first['customerOrder'].get('shopOrderId')}")

# 把数据存到本地 JSON 备用
output_path = "/tmp/duozan-investigate/api_20260603.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"\n✅ 数据已存到: {output_path}")
