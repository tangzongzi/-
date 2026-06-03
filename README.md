# 多赞数据看板 · EdgeOne Pages 部署指南

## 部署方案：GitHub 集成（最简单）

EdgeOne Pages 原生支持 GitHub 集成，**不需要 CLI、不需要 API Key、不需要 GitHub Actions**。
push 一次 = 部署一次，全自动。

## 一次性配置（5 步，10 分钟）

### ① 创建 GitHub 私有仓库

浏览器开 https://github.com/new

- Repository name: `duozan-dashboard`
- Visibility: **Private** （私有仓库，看板是内部数据）
- 不要勾选 Initialize this repository with anything（本地已有 .gitignore）
- 点 Create repository

### ② 本地初始化 Git 并推送

```bash
cd /Users/manba/Documents/OH-WorkSpace/多赞数据库/多赞采购单

git init
git branch -M main
git add .
git commit -m "init: 多赞数据看板 v1"

# 替换 你的用户名 为你的 GitHub 用户名
git remote add origin https://github.com/你的用户名/duozan-dashboard.git
git push -u origin main
```

**首次推送可能要点 GitHub 凭据**（PAT Token 或 SSH key）。

### ③ 在 EdgeOne Pages 创建项目并连 GitHub

浏览器开 https://console.cloud.tencent.com/edgeone/pages

1. 点 **创建项目** → 选 **Git 仓库** → 选 **GitHub**
2. 授权 EdgeOne 访问你的 GitHub
3. 选仓库：`你的用户名/duozan-dashboard`
4. 分支：`main`
5. 构建命令：**留空**（纯静态，无构建）
6. 输出目录：**留空**（根目录就是）
7. 点 **开始部署**

**首次部署需要 1-2 分钟**。

### ④ 拿到部署地址

部署完成后 EdgeOne 会给一个地址：

```
https://duozan-dashboard-xxx.edgeone.app
```

或更短：

```
https://duozan-dashboard.edgeone.app
```

这就是公网可访问的地址，老板在外面用手机也能看。

### ⑤（可选）配自定义域名

1. EdgeOne Pages 项目 → **域名管理** → 添加域名
2. 按提示到你的 DNS 服务商配 CNAME 解析
3. EdgeOne 自动签发 HTTPS 证书

## 日常更新流程

```bash
# 1. 跑数据更新（本地 Mac）
cd /Users/manba/Documents/OH-WorkSpace/多赞数据库/多赞采购单
bash update.sh

# 2. 提交 + 推送
git add -A
git commit -m "data: 2026-06-03 数据更新"
git push
```

**结果**：EdgeOne 检测到 push → 自动部署 → 1-2 分钟后公网可访问。

## 自动化进阶（可选）

### 方案 A：Mac 端自动 git push（cron）

```bash
# 加到 /usr/local/bin/duozan-sync.sh
#!/bin/bash
cd /Users/manba/Documents/OH-WorkSpace/多赞数据库/多赞采购单
bash update.sh
git add -A
git commit -m "data: auto sync $(date +%Y-%m-%d)" 2>/dev/null
git push origin main 2>/dev/null

# chmod +x /usr/local/bin/duozan-sync.sh

# crontab -e 加：
# 0 3 * * * /usr/local/bin/duozan-sync.sh
# 每天凌晨 3 点跑（比 update.sh 02:00 慢 1h）
```

### 方案 B：GitHub Actions 定时拉数据（无需本地 cron）

```yaml
# .github/workflows/refresh-data.yml
name: Refresh Data Daily
on:
  schedule:
    - cron: '0 20 * * *'  # UTC 20:00 = 北京 04:00
  workflow_dispatch:
jobs:
  refresh:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install pandas openpyxl numpy
      - run: python scripts/export_data.py
      - run: python scripts/refresh_dashboards.py
      - run: |
          git config user.name "github-actions[bot]"
          git config user.email "actions@github.com"
          git add -A
          git commit -m "data: auto refresh" || exit 0
          git push
```

> 注：GitHub Actions 的 macOS runner 是临时的，**不保存 Excel 文件**，所以这个方案需要把 Excel 也存到仓库里（约 64KB，可接受），或换用 GitHub 仓库的 raw URL 在线读取。

## 数据同步策略

| 文件夹 | 大小 | 同步频率 |
|---|---|---|
| HTML/JS/CSS/charts/assets | ~2MB | 修改时增量 |
| 数据/看板数据/ | 808KB | **每日** |
| 数据/汇总/ | 576KB | **每日** |
| 数据/Excel/ | 64KB | 每周几次 |
| 数据/明细/ | 161MB | **首次全量**（增量靠 git） |

**首次推送**：~180MB
**每日更新**：~10MB（git 增量）

## 项目结构

```
多赞采购单/
├── 00_总览.html              # 入口
├── 销售业绩/  平台×店铺细分/  商品结构/  供货商分析/  风险监控/
├── assets/   # echarts.min.js 等
├── charts/   # 24 个图表 JS
├── 数据/
│   ├── 看板数据/   # 前端 fetch 用（1MB）
│   ├── 汇总/       # 中间数据（9MB）
│   ├── 明细/       # CSV 下载（161MB）
│   └── Excel/      # 原始 xlsx（64KB）
├── scripts/  # export_data.py + refresh_dashboards.py
└── .gitignore  # 排除 _archive 等
```

## 遇到问题

**Q: push 后 EdgeOne 没自动部署？**
A: EdgeOne 控制台 → 项目 → 部署历史，看最新状态。失败会显示错误日志。

**Q: 老板访问很慢？**
A: EdgeOne 在国内有 CDN 节点，速度应该 OK。如果卡，刷新一下（Ctrl+Shift+R 强制刷新缓存）。

**Q: 想改页面？**
A: 改完后 `git add . && git commit -m "fix: ..." && git push`，1 分钟自动上线。

**Q: 想回滚？**
A: EdgeOne 控制台 → 部署历史 → 选上一个版本 → 设为当前。

## 风险与备份

- **数据安全**：私有仓库，EdgeOne 也是私有部署，只有你能访问
- **代码备份**：GitHub 仓库本身就是备份
- **数据备份**：建议每周手动 git tag 一个版本（如 `v1.0`）
