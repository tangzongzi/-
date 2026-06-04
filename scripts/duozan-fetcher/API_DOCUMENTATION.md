# 多赞易分销 API 调研文档

> 调研时间：2026-06-05  
> 调研方式：浏览器操作各页面抓 Network + Python 直接调 API  
> 鉴权：JWT Bearer Token + TenantId Header  
> 调研账号：13375845915

---

## 0. 鉴权信息

```
Authorization: Bearer <JWT_TOKEN>
TenantId: 93e4349a-aed8-b6b2-b576-3a0b308e1a79
User-Agent: Mozilla/5.0 ...
Referer: https://easyfx.duozan.com/
Origin: https://easyfx.duozan.com
```

---

## 1. 采购单（已实现）

| 端点 | 用途 | 返回示例 | 业务价值 |
|---|---|---|---|
| `GET /api/purchase-order` | 采购单列表（分页） | `{totalCount, items[]}` 含 profit/payment/statusStr | ⭐⭐⭐ 核心数据 |
| `GET /api/purchase-order/order-count` | 待办数 | `{waitSend, waitConfirm, waitPay, postSaleing, timeoutDeliveryCount}` | ⭐⭐ dashboard |
| `GET /api/purchase-order/{dateTimeType}{skip/max}` | 列表（用 dateTimeType 维度） | 1=创建/2=付款/3=发货 | ⭐⭐⭐ 多维度 |
| `GET /api/purchase-order/{id}/detail` | 采购单详情 | 包含 orderDetails/收货地址 | ⭐⭐ 详情 |

### 待补（端点存在但需参数）
- `GET /api/purchase-order/page` (204)
- `GET /api/purchase-order/statistics` (204)
- `GET /api/purchase-order/summary` (204)
- `GET /api/purchase-order/dashboard` (204)
- `GET /api/purchase-order/todo-count` (204)
- `GET /api/purchase-order/daily` (204)
- `GET /api/purchase-order/monthly` (204)

---

## 2. 售后 / 退换 / 理赔

| 端点 | 用途 | 返回示例 | 业务价值 |
|---|---|---|---|
| `GET /api/purchase-postsale-order/count` | 售后待办 | `{postSaleingCount, waitMchCheckCount, waitMchRefundCount, waitProcessingCount, waitMchReceivingCount}` | ⭐⭐ 监控 |
| `GET /api/purchase-postsale-order/page` | 售后分页 | `{totalCount, items[]}` 含退款金额 | ⭐⭐⭐ 售后分析 |
| `GET /api/purchase-postsale-order/list` | 售后列表（同 page） | 同上 | ⭐⭐⭐ |
| `GET /api/order/my-compensation/statistics` | 理赔统计 | `{waitMchCheckCount, waitUserUpdateCount, waitMchRefundCount}` | ⭐⭐ 理赔监控 |
| `GET /api/order/my-compensation/page` | 理赔分页 | `{totalCount, items[]}` | ⭐⭐ 理赔明细 |

---

## 3. 商品 / 库存

| 端点 | 用途 | 返回示例 | 业务价值 |
|---|---|---|---|
| `GET /api/goods/good/count` | 商品总数 | `items=0/4192` (共 4192 个商品) | ⭐⭐ |
| `GET /api/goods/good/page` | 商品分页 | `{totalCount, items[]}` 含 artNo/title/levelPrice | ⭐⭐⭐ 选品 |
| `GET /api/goods/good/goods-collect-count` | 收藏数 | 0/1 | ⭐ |
| `GET /api/goods/good/1688-goods-count` | 1688 货源商品数 | items=0/1 | ⭐ |
| `GET /api/goods/good/supplier-goods/adjustment-list` | 商品调整列表 | items=20/11053 含调价/货源变更 | ⭐⭐⭐ 重要 |
| `GET /api/goods/good/supplier-goods/adjustment-unread` | 未读调整 | 同上 | ⭐⭐ |

---

## 4. 供货商（部分已实现）

| 端点 | 用途 | 返回示例 | 业务价值 |
|---|---|---|---|
| `GET /api/my-supplier` | 我的供货商 | items=192 个，含 name/phone/levelId/cooperationTime | ⭐⭐⭐ 风险分析 |
| `GET /api/my-supplier/valid` | 可用供货商 | 同上结构 | ⭐⭐ 选品 |
| `GET /api/my-supplier?supplierType=1&cooperationStatus=1` | 抖店合作 | 同上 | ⭐⭐ |
| `GET /api/my-supplier?supplierType=1&cooperationStatus=3` | 全合作 | 同上 | ⭐⭐ |
| `GET /api/my-supplier/tag/list` | 标签列表 | items[] | ⭐ |
| `GET /api/my-supplier/tag/statistics` | 标签统计 | items[] | ⭐ |
| `GET /api/my-supplier/new-online-tip` | 新上线提示 | `{isUnread, unreadCount, lastOnlineTime}` | ⭐⭐ 选品 |
| `GET /api/my-supplier/get-supplier-ids` | 供货商 ID 列表 | 字符串 ID 数组 | ⭐ |

---

## 5. 店铺

| 端点 | 用途 | 返回示例 | 业务价值 |
|---|---|---|---|
| `GET /api/shop/count` | 店铺统计 | `{authCount: 19, expiredCount: 1, totalCount: 20}` | ⭐⭐ |
| `GET /api/shop/all?appTypes=1` | 抖店店铺 | items[] | ⭐⭐⭐ |
| `GET /api/shop/all?appTypes=2,1024` | 拼多多店铺 | items[] | ⭐⭐⭐ |
| `GET /api/shop/all?needVerification=true` | 需验证店铺 | items[] | ⭐⭐ |
| `GET /api/shop/buyapp?stationType=1` | 抖店 app | 204 (存在) | ⭐ |
| `GET /api/shop/buyapp?stationType=2` | 拼多多 app | 204 (存在) | ⭐ |

---

## 6. 控价 / 投诉

| 端点 | 用途 | 返回示例 | 业务价值 |
|---|---|---|---|
| `GET /api/price-control/my-complaint-bill/list?status=1` | 投诉中 | items[] 含渠道/价格/商品 | ⭐⭐ 监控 |
| `GET /api/price-control/my-complaint-bill/count` | 投诉数 | `{waitCheckCount, waitChannelProcessCount, involvedCount}` | ⭐⭐ |

---

## 7. 业务 / 消息

| 端点 | 用途 | 返回示例 | 业务价值 |
|---|---|---|---|
| `GET /api/business/messges` | 业务消息 | items=58390 (含货源变更/商品缺货/售罄) | ⭐⭐⭐ |
| `GET /api/business/get-cooperate-config` | 合作配置 | `{autoCooperate: ...}` | ⭐ |

---

## 8. 推荐 / 热卖

| 端点 | 用途 | 返回示例 | 业务价值 |
|---|---|---|---|
| `GET https://good-elastic.duozan.com/api/platform-goods/supplier-hot-sale-list?day=1` | 近 24H 热卖 | `{goodsList, groupIdList}` | ⭐⭐⭐ 选品 |
| `GET ?day=7` | 近 7 天热卖 | 同上 | ⭐⭐⭐ |
| `GET https://platform-good.duozan.com/api/platform/good/category/sub-list?parentId=0&stationType=66` | 商品类目 | items[] | ⭐⭐ |

---

## 9. 调拨 / WMS

| 端点 | 用途 | 返回示例 | 业务价值 |
|---|---|---|---|
| `GET https://wms.duozan.com/api/dispatch-bill/get-status-statistics?status=1&billType=1` | 待处理调拨单 | `{exceptionTotalCounts, mergeCount, splitCount, statusCount, exceptionCount}` | ⭐⭐ |
| `GET ?status=5&billType=1` | 已完成 | 同上 | ⭐⭐ |
| `GET ?status=10&billType=1` | 异常 | 同上 | ⭐⭐⭐ |

---

## 10. 财务 / 余额

| 端点 | 用途 | 返回示例 | 业务价值 |
|---|---|---|---|
| `GET https://balance.duozan.com/api/user/balance/account/list` | 余额账户 | 数组 | ⭐⭐ 财务 |
| `GET /api/user/balance` | 余额 | - | ⭐⭐ |
| `GET /api/alipay/get-tenant-payinfo` | 支付宝支付 | - | ⭐ |

---

## 11. CRM / 优数

| 端点 | 用途 | 返回示例 | 业务价值 |
|---|---|---|---|
| `GET https://youshu-crm-api.duozan.com/api/customer/channel/outer/get-follower?customerTenantId={tenantId}` | CRM 跟进人 | `{followerId, followerName, followerLogo, followerPhonenumber, followerWxQrCode}` | ⭐ 客户经理 |

---

## 12. 公共服务（host.duozan.com）

| 端点 | 用途 | 返回示例 | 业务价值 |
|---|---|---|---|
| `GET /api/multi-tenancy/tenants/get-full/{tenantId}` | 租户详情 | `{companyName, phoneNumber, logo, brand, brandLogo}` | ⭐⭐ |
| `GET /api/brand?includeImages=true&tenantId={tenantId}` | 品牌列表 | items[] | ⭐ |
| `GET /api/weixin/mp/mini-qr-code` | 微信小程序码 | 图片 | ⭐ |
| `GET /api/weixin/mp/mini-url` | 微信小程序链接 | URL | ⭐ |

---

## 13. 统计

| 端点 | 用途 | 返回示例 | 业务价值 |
|---|---|---|---|
| `GET https://statistic.duozan.com/api/statistics/goods/publish/batch-check-published` | 商品发布统计 | - | ⭐ |

---

## 14. 代理 / 用户

| 端点 | 用途 | 返回示例 | 业务价值 |
|---|---|---|---|
| `GET /api/agent-level/all` | 代理等级 | - | ⭐ |

---

## 15. 下载 / 任务

| 端点 | 用途 | 返回示例 | 业务价值 |
|---|---|---|---|
| `GET /api/download-task/list` | 下载任务 | items=366 个历史导出 | ⭐⭐ 复用 |
| `GET /api/download-task/{taskId}/url` | 下载预签名 URL | OSS URL | ⭐⭐ |
| `GET /api/purchase-order/export?dateTimeType=1&...` | 触发异步导出 | taskId | ⭐⭐ |

---

## 16. 完整数据流（首页 dashboard 触发的 20+ 个 API）

boss 一次首页加载，触发了这些调用：

| 业务域 | API | 用途 |
|---|---|---|
| 调拨单 | `wms/dispatch-bill/get-status-statistics` × 多次 | 调拨单各状态统计 |
| 采购单 | `purchase-order/order-count` | 待办（待发/待付/售后等）|
| 售后 | `purchase-postsale-order/count` | 售后各状态数 |
| 商品 | `goods/good/count` | 商品总数 |
| 理赔 | `order/my-compensation/statistics` | 理赔各状态数 |
| 控价 | `price-control/my-complaint-bill/list` + `count` | 控价投诉 |
| 业务消息 | `business/messges` | 货源变更/缺货/售罄 |
| 热卖 | `good-elastic/supplier-hot-sale-list?day=1` | 24H 热卖 |
| 购物车 | `goods/cart/good-ids` + `cart/sku-count` | 购物车商品数 |
| 租户 | `host/multi-tenancy/tenants/get-full` | 租户信息 |
| 品牌 | `host/brand` | 品牌列表 |
| 商品类目 | `platform-good/category/sub-list` | 类目树 |
| 财务 | `alipay/get-tenant-payinfo` | 支付信息 |
| CRM | `youshu-crm-api/customer/channel/outer/get-follower` | 客户经理 |
| 店铺 | `shop/all?needVerification=true` | 全部店铺 |
| 微信 | `weixin/mp/mini-qr-code` | 小程序码 |
| 余额 | `balance/user/balance/account/list` | 余额账户 |
| 商品发布统计 | `statistic/goods/publish/batch-check-published` | 发布统计 |

---

## 17. 待挖掘的（端点存在但需更多测试）

| 模块 | 端点提示 | 备注 |
|---|---|---|
| 推单 | `/api/push-order/*` | 首页有"待推单"tab |
| 推送单 | `/api/pushorder/*` | 旧命名 |
| 理赔详情 | `/api/compensation/*` | 不在 my- 前缀下 |
| 财务账单 | `/api/bill/*` | 没用 /api/finance/ |
| 财务钱包 | `/api/wallet/*` | 没用 /api/finance/ |
| 商品详情 | `/api/goods/good/{id}` | 单品详情 |
| 库存预警 | `/api/inventory/warning` | 类似 |
| 供货商详情 | `/api/my-supplier/{id}` | 供货商详情 |
| 通知/消息 | `/api/business/messges` | 已有 |
| 推荐分类 | `/api/recommend/category` | 分类推荐 |
| 优惠券 | `/api/coupon/*` | 营销 |
| 活动 | `/api/activity/*` | 营销 |

---

## 18. 调研结论

✅ **可自动抓取的数据**（从 easyfx.duozan.com）：

1. **采购单全量数据**（已有，21 字段 + 利润）
2. **采购单统计**（待办数、各状态分布）
3. **售后/理赔数据**（按状态分类）
4. **供货商全量**（192 个含合作时间、等级）
5. **店铺统计**（抖店/拼多多/小红书）
6. **商品总数 + 1688 商品 + 调整**
7. **业务消息**（货源变更/缺货/售罄）
8. **热卖商品**（24H 销量、利润率、供货价）
9. **品牌列表 / 类目树 / 调拨单统计**
10. **CRM 跟进人 / 余额账户**

❌ **不可获取的**：
- 真正的销售数据（抖店/拼多多后台，需要各自商家后台）
- 流量、转化率、ROI
- 客服聊天记录
- 财务流水（支付宝/微信支付）

🎯 **下一步建议**：
1. **优先**：补 4 个缺字段（付款时间/物流/收件人/店铺商品小计），调详情接口
2. **其次**：抓"采购单 order-count"补充到首页 dashboard
3. **可选**：抓"售后/理赔"做售后监控
4. **可选**：抓"业务消息"做异常告警（缺货/售罄即时通知）
