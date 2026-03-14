# CODEBUDDY.md

This file provides guidance to CodeBuddy Code when working with code in this repository.

## 项目概述

newsup-solar 是一个 Python 新闻聚合器，专注于太阳能和可再生能源新闻。项目支持两种模式：
- **普通模式**：通用太阳能新闻抓取
- **工商业光伏模式（Commercial Solar）**：专门针对工商业（C&I）光伏领域的新闻、政策和市场分析

## 常用命令

### 环境设置
```bash
# 创建并激活虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt

# 安装 spaCy 语言模型（用于 NLP）
python -m spacy download en_core_web_sm
```

### 数据库操作
```bash
# 初始化数据库（SQLite，默认 data/news.db）
python scripts/init_db.py

# 或通过主程序初始化
python src/main.py --init-db
```

### 爬虫运行
```bash
# 普通模式爬取
python src/main.py --crawl --init-db

# 工商业光伏模式爬取（推荐）
python src/main.py --crawl --commercial --init-db

# 指定数据源爬取
python src/main.py --crawl --commercial --source pv_magazine
python src/main.py --crawl --commercial --source solar_power_world
python src/main.py --crawl --commercial --source commercial  # 仅商业模式爬虫

# 查看帮助
python src/main.py --help
```

### 代码质量
```bash
# 代码格式化
black src/ tests/

# 代码检查
flake8 src/ tests/

# 类型检查
mypy src/
```

### 测试
```bash
# 运行所有测试
pytest tests/

# 运行带覆盖率报告
pytest --cov=src tests/
```

### API 服务
```bash
# 启动 API 服务器
python src/main.py --serve

# 或直接运行
python src/api/server.py
```

## 架构概览

### 核心流程
```
爬虫(Crawlers) → 清洗器(Cleaners) → 分类器(Classifier) → 数据库(Database)
```

### 目录结构
```
src/
├── crawlers/           # 新闻源爬虫
│   ├── base.py         # 爬虫基类 (BaseCrawler)
│   ├── pv_magazine.py  # PV Magazine 通用爬虫
│   ├── solar_power_world.py
│   └── commercial/     # 工商业光伏专用爬虫
│       ├── pv_magazine_business.py
│       └── solar_power_world_commercial.py
├── processors/         # 数据处理模块
│   ├── cleaner.py      # 通用文章清洗器 (ArticleCleaner)
│   ├── commercial_cleaner.py  # 工商业光伏专用清洗器
│   └── classifier.py   # 文章分类器
├── storage/
│   └── database.py     # SQLAlchemy 数据库模型 (Article, DatabaseManager)
├── api/                # FastAPI 服务端点
└── utils/              # 工具函数

config/
└── commercial_solar_keywords.py  # 工商业光伏关键词配置

scripts/
└── init_db.py          # 数据库初始化脚本
```

### 关键类继承关系

**爬虫体系**：
- `BaseCrawler`（抽象基类）定义接口：
  - `fetch_article_urls()` - 获取文章URL列表
  - `parse_article(url)` - 解析单篇文章
  - `crawl()` - 主入口方法
- 具体爬虫继承 `BaseCrawler` 实现特定网站的抓取逻辑

**清洗器体系**：
- `ArticleCleaner` - 基础清洗：HTML清理、文本规范化、相关性评分
- `CommercialSolarCleaner` - 继承 `ArticleCleaner`，添加：
  - 工商业光伏关键词识别
  - 商业模式提取（PPA、租赁等）
  - 政策类型分类
  - 项目规模和地域识别

### 数据模型

Article 表主要字段：
- `article_id` - 主键（URL 的 SHA256 哈希前16位）
- `title`, `url`, `source`, `content`, `summary`
- `keywords`, `categories` - JSON 数组
- `sentiment_score`, `relevance_score` - 分析评分
- `processed` - 处理状态标志
- `article_metadata` - 额外元数据（JSON）

### 工商业光伏分析

`CommercialSolarCleaner` 产出以下分析维度：
- `content_type`: news / policy / market
- `business_models`: PPA、租赁、第三方所有权等
- `policy_types`: 税收优惠、补贴、监管等
- `project_scale`: small / medium / large
- `regions`: us / china / europe / apac
- `commercial_relevance_score`: 0-10 相关度评分

## 配置

### 环境变量
复制 `.env.example` 到 `.env` 并配置：
- `DATABASE_URL` - 数据库连接（默认 SQLite）
- `CRAWL_INTERVAL_HOURS` - 爬取间隔
- `LOG_LEVEL` - 日志级别

### 关键词定制
修改 `config/commercial_solar_keywords.py` 可：
- 添加/删除工商业光伏关键词
- 调整政策/市场分类关键词
- 修改地域识别规则

## 添加新爬虫

1. 在 `src/crawlers/` 或 `src/crawlers/commercial/` 创建新文件
2. 继承 `BaseCrawler` 类
3. 实现必需方法：
   - `source_url` 属性
   - `source_display_name` 属性
   - `fetch_article_urls()` 方法
   - `parse_article(url)` 方法
4. 在 `src/main.py` 的 `get_crawlers()` 函数中注册新爬虫

## 数据库查询示例

```bash
# 使用 sqlite3 查看数据
sqlite3 data/news.db

# 查询示例
SELECT COUNT(*) FROM articles;
SELECT title, source, content_type FROM articles LIMIT 5;
```

## 注意事项

- 爬虫默认限制每次最多抓取 10-20 篇文章（可在各爬虫中调整）
- 遵守网站 robots.txt，设置合理的请求间隔
- 反爬虫策略：使用配置的 User-Agent，避免短时间大量请求
