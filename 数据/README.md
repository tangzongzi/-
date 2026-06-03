# 多赞采购单 · 数据文件清单

## 📁 目录结构

```
多赞数据库/
├── 采购单_20260301-20260601.xlsx    ← 老板原购 Excel（数据更新输入位置）
└── 多赞采购单/                      ← 项目主体
    ├── 00_总览.html / 00_总览_v2.html   ← 入口看板
    ├── 销售业绩/                   ← 4 个 HTML（fetch 模式）
    ├── 平台×店铺细分/              ← 12 个 HTML（fetch 模式）
    ├── 商品结构/                   ← 5 个 HTML（fetch 模式）
    ├── 供货商分析/                 ← 1 个 HTML（fetch 模式）
    ├── 风险监控/                   ← 1 个 HTML（fetch 模式）
    ├── feishu_bot/                 ← 飞书机器人代码
    │   ├── feishu_query.py         ← 命令行查询 + 飞书消息处理
    │   ├── feishu_server.py        ← HTTP 服务（Flask）
    │   └── requirements.txt
    │
    └── 数据/                       ← 全部数据独立存放
        ├── 原始_采购单_*.xlsx        ← 老板原购 Excel
        ├── _index.json               ← 数据字典
        ├── README.md                 ← 本文件
        ├── 汇总/                     ← 26 个汇总 json（按主题_子主题）
        ├── 明细/                     ← 10 个文件（5 对 csv/json，双"明细"对齐 fetch 引用）
        ├── Excel/                    ← 14 个 csv（按主题_子主题，Excel 友好）
        ├── 看板数据/          ← 23 个看板数据（HTML fetch 目标，保留原名）
        └── 按日期/                   ← 以后老板给的新文件按 YYYY-MM-DD 归档
```

## 🔑 三层数据

### 1. 原始数据
- `原始_采购单_20260301-20260601.xlsx` - 老板原购 Excel，未做修改

### 2. 明细数据（`明细/`）
- 一行一单，包含 25 个字段
- 全部订单：37,483 条 / 完整版：42,274 条
- 关闭订单：4,791 条 / 售后订单：72 条 / 待确认：1,949 条

### 3. 汇总数据（`汇总/` + `Excel/`）
- 26 个 JSON（按主题拆分：KPI/供货商/商品/平台/销售业绩/风险）
- 14 个 CSV（Excel 友好，主题/子主题命名）
- 23 个 dashboard JSON（`看板数据/` 下，HTML 看板用）

## 🚀 HTML 看板（fetch 模式）

23 个 HTML 看板**不携带任何数据**，全部从 `看板数据/*.json` 动态加载：

```html
<script>
async function loadDataAndRender() {
  const DATA = await fetch('看板数据/00_总览.json').then(r => r.json());
  renderDashboard(DATA);
}
loadDataAndRender();
</script>
```

**好处：**
- HTML 文件从 50-80KB 缩小到 10-15KB
- 改数据不动 HTML：更新 JSON 文件即可
- 数据/视图彻底分离
- 飞书机器人、API、Excel 都能用同一份数据

## 🤖 飞书机器人

### 命令行模式
```bash
python3 feishu_bot/feishu_query.py "总销售额多少"
python3 feishu_bot/feishu_query.py "5月卖了多少"
python3 feishu_bot/feishu_query.py "4月新增5月留存"
python3 feishu_bot/feishu_query.py "供货商集中度"
python3 feishu_bot/feishu_query.py "供货商 Top 10"
python3 feishu_bot/feishu_query.py "关闭率最高的供货商"
```

### HTTP 服务模式
```bash
cd feishu_bot
python3 feishu_server.py
# 默认端口 5001
```

### 支持的问题
| 问题 | 示例 |
|---|---|
| 总销售额 | "总销售额多少" |
| 月度销售 | "5月卖了多少" / "3月" / "4月" |
| 平台对比 | "平台对比" / "店铺明细" |
| 商品新增淘汰 | "5月新增商品" / "4月新增5月留存" |
| 供货商 | "供货商集中度" / "供货商 Top 10" |
| 风险 | "关闭率最高供货商" / "关闭率走势" |
| 长尾 | "5月销量分布" |

### 接入飞书机器人步骤
1. 在飞书开放平台创建自定义机器人
2. 启用"事件订阅" → 填入 `https://你的服务器/feishu_bot/feishu/webhook`
3. 订阅事件：`im.message.receive_v1`
4. 权限：`im:message` `im:message:receive_v1`
5. 飞书用户向机器人发消息 → 飞书 webhook → `feishu_query.py` → 答案

## 🔌 数据 API（HTTP）

老板也可以直接把 `数据/` 目录挂到任何 HTTP 服务器上（OSS/七牛/自建），然后用：
- `curl https://你的域名/数据/汇总/KPI_总览.json`
- 飞书机器人 fetch URL
- 小程序 fetch URL
- Excel Power Query

## 📊 文件统计

- HTML 看板：23 个（fetch 模式）
- Dashboard JSON：23 个（`看板数据/`）
- 汇总 JSON：26 个（`汇总/`）
- 明细 JSON/CSV：5/5 个（`明细/`）
- Excel 汇总 CSV：14 个（`Excel/`）
- 原始 Excel：1 个
- 索引：1 个
- 飞书机器人：3 个文件

**总大小：约 185MB**（明细占 169MB，其他 16MB）

## 📈 核心数据快速查询

| 问题 | 文件 | 字段 |
|---|---|---|
| 总销售额多少？ | `汇总/KPI_总览.json` | `summary.total_amount_wan` = ¥103.09万 |
| 抖店3-5月订单？ | `汇总/平台_抖店_月.json` | `summary.total_orders` = 26,492 |
| 5月新增多少商品？ | `汇总/商品_月度变化.json` | `data[-1].new_count` = 115 |
| 关闭率最高供货商？ | `汇总/风险_供货商关闭率.json` | `data[0].supplier` |
| 供货商集中度？ | `汇总/供货商_排行.json` | `summary.top1_concentration_pct` = 28.2% |
| 4月新增5月留存？ | `汇总/商品_4月新增5月留存.json` | `summary.keep_rate_pct` = 38.3% |
| 5月某个商品卖了多少？ | `明细/明细_全部订单.csv` | 筛选`商品名称`+`创建时间` |

## 🔄 数据更新流程

1. 老板给我新 Excel → 放 `/多赞数据库/` 根级
2. 我跑 `/tmp/export_data.py` + `/tmp/export_detail.py` → 刷新 `汇总/` 和 `明细/`
3. 我跑 `/tmp/refresh_dashboards.py` → 刷新 `看板数据/` 下 23 个 dashboard JSON
4. HTML 看板自动用新数据（fetch 时拿到的是最新 JSON）

## 📅 新文件归档规则

老板给新文件（如新一天的采购单 xlsx）时：
- 在 `数据/按日期/YYYY-MM-DD/` 下建子目录
- 按文件实际内容对应的业务日期归档
- 例：`数据/按日期/2026-06-02/采购单_20260602.xlsx`

## ⚠️ 注意事项

- 收件人和电话是**加密的**（源数据本身就脱敏，## 开头那种）— 不是我处理的问题
- 原始 Excel 的列名是中文，部分列名带 `-`（如"收件地址-省"），导出的 JSON 用下划线代替
- **数据-视图完全分离**：HTML 不带数据，全部从 JSON 加载
- 重新跑 `export_data.py` + `export_detail.py` + `refresh_dashboards.py` 就能刷新全部数据

更新于 2026-06-02（按日期归档 + 明细/汇总/Excel 子目录重构）
