# EV Launch Intelligence V2：BMW iX3 海外上市情报看板

这是一个支持中英文切换、每日更新且证据可追溯的公开新闻情报看板，用于分析BMW iX3在海外市场中的媒体声量、核心信息触达、竞品定位和风险信号。

> 本项目为独立作品集项目，不隶属于BMW Group，也不代表其官方立场，且不包含任何宝马内部资料。

![第二版看板预览](assets/dashboard-preview.png)

## 第二版主要变化

- 中英文界面切换，覆盖筛选器、指标、图表、主题、风险标签、方法说明和CSV导出。
- 真实公开新闻窗口从2025年9月5日iX3全球首发开始，持续至最近一次成功采集。
- 当前仓库附带的2026年9月28日快照包含2,588条真实可追溯记录。
- 每条记录保留发布方、发布方主页、证据链接、发布时间、首次采集时间、最近发现时间和数据提供方式。
- 每日增量采集会重查过去48小时，避免遗漏延迟进入RSS的新闻。
- 数据源健康状态、最近更新时间和超过36小时未更新警告。
- GitHub Actions每日自动更新工作流。
- 合成演示数据继续保留，但与真实数据完全分离。

## 当前真实数据来源

### Google News RSS

历史回填和每日增量目前都使用带日期范围的Google News RSS查询。RSS负责发现文章，但看板同时保存其提供的真实媒体名称和媒体主页。

`market`字段表示发现文章时使用的Google News地区配置，不等同于发布方总部所在地，也不能被解释为完整的国家媒体样本。

### BMW Group PressClub

iX3全球首发日期与官方事件锚点来自BMW Group PressClub。官方事件保存在独立文件中，不参与默认的独立媒体声量指标。

### GDELT状态

开发期间对GDELT进行了真实接口验证，但请求返回HTTP 429。因此第二版没有假装已经接入GDELT，而是将其保留为未来可选数据源。

## 来源等级

| 等级 | 默认进入核心指标 | 说明 |
|---|---:|---|
| 官方来源 | 可选 | 经过确认的品牌新闻中心或官方媒体域名 |
| 可信独立媒体 | 是 | 具有编辑审核机制的汽车、科技、商业或新闻媒体 |
| 未验证公开来源 | 否 | 保留证据链接供检查，但默认不进入核心KPI |

默认看板只使用可信独立媒体。用户可以切换到“全部可信来源”或“全部已采集公开来源”。

## 指标边界

- 新闻声量不等于销量、需求或市场份额。
- Share of Voice只表示当前证据集中的报道数量占比。
- Message Pull-through表示iX3报道中命中透明主题词典的比例。
- 语气与风险信号只用于安排人工复核优先级，不代表消费者情绪。
- 同一篇文章如果分别出现在多个地区RSS结果中，可能作为不同地区发现记录保留。
- 本项目提供的是可追溯公开新闻样本，而不是完整全球媒体监测。

## 本地运行

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

真实公开新闻快照是默认数据源，本地启动后会自动打开浏览器。

## 手动更新数据

每日增量更新：

```bash
python -m scripts.collect_news --mode daily
python -m scripts.validate_dataset
```

从全球首发日重新回填：

```bash
python -m scripts.collect_news \
  --mode backfill \
  --start 2025-09-05 \
  --chunk-months 3 \
  --limit 100
python -m scripts.validate_dataset
```

## 每日自动更新

`.github/workflows/update-news.yml`设置为每天06:15 UTC运行，也支持手动触发。项目推送到GitHub、启用Actions并允许工作流写入仓库后，定时任务才会真正生效。

## 测试

```bash
pip install -r requirements-dev.txt
pytest -q
ruff check .
```

完整的架构、目录说明和浏览器测试方法见英文版 [README](README.md)。
