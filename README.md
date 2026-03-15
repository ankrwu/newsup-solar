# Solar News 🌞

> 全球太阳能行业新闻聚合器 - 一键获取中英文太阳能行业资讯

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Project Status](https://img.shields.io/badge/Status-完成-83.3%25-green.svg)](#)
[![Data Articles](https://img.shields.io/badge/Articles-80+-blue.svg)](#)

## 📋 项目状态

**当前版本**: v1.0.0 (2026-03-14)  
**项目状态**: ✅ **基本完成** (83.3% 完成度)  
**数据状态**: 📊 **80+ 篇文章已收录**  
**功能状态**: 🚀 **工商业光伏专项模式已上线**

### ✅ 已完成功能
- 多源新闻聚合（中英文）
- 工商业光伏专项模式
- 智能分类和商业分析
- 数据库存储和查询
- 完整的命令行工具

### 🔧 核心特性
- **专注领域**: 工商业光伏（Commercial & Industrial Solar）
- **数据源**: PV Magazine、Solar Power World、中文源等
- **分析维度**: 商业模式、政策类型、项目规模、地域
- **技术架构**: 异步爬虫 + SQLAlchemy + 模块化设计

> 📝 详细项目状态报告请参见 [PROJECT_STATUS.md](PROJECT_STATUS.md)

## ✨ 功能特性

- 🌍 **多源聚合** - 同时支持中英文新闻源
- 📰 **RSS + 动态渲染** - 自动降级，突破反爬虫
- 🤖 **智能摘要** - 可选 LLM 智能摘要和分类
- 📊 **工商业专项** - 专注工商业光伏领域
- 🚀 **一键安装** - 快速部署，开箱即用

## 📦 快速安装

### 方式一：一键安装（推荐）

```bash
curl -sSL https://raw.githubusercontent.com/ankrwu/newsup-solar/main/install.sh | bash
```

### 方式二：手动安装

```bash
# 克隆仓库
git clone https://github.com/ankrwu/newsup-solar.git
cd newsup-solar

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装
pip install -e .

# 安装 Playwright 浏览器（可选，用于动态内容）
playwright install chromium

# 初始化数据库
solarnews init
```

## 🚀 使用方法

### 基本命令

```bash
# 爬取所有源（默认中英文）
solarnews crawl

# 只爬取中文源
solarnews crawl --chinese

# 只爬取英文源
solarnews crawl --english

# 启用智能摘要（需要 LLM API）
solarnews crawl --smart

# 工商业光伏专项模式
solarnews crawl --commercial

# 启动 API 服务
solarnews serve

# 查看统计
solarnews stats

# 查看帮助
solarnews --help
```

### 命令行参数

| 参数 | 说明 |
|------|------|
| `--chinese` | 只爬取中文源 |
| `--english` | 只爬取英文源 |
| `--commercial` | 工商业光伏专项模式 |
| `--smart` | 启用智能摘要和分类 |
| `--playwright` | 强制使用动态渲染 |

## 📰 数据源

### 英文源
| 来源 | 方式 | 状态 | 说明 |
|------|------|------|------|
| PV Magazine | RSS + 动态爬取 | ✅ | 通用太阳能新闻 |
| Solar Power World | RSS + 动态爬取 | ✅ | 通用太阳能新闻 |
| PV Magazine Business | 动态爬取 | ✅ | **工商业光伏专项** (finance/markets分类) |
| Solar Power World Commercial | 动态爬取 | ✅ | **工商业光伏专项** (commercial分类) |

### 中文源
| 来源 | 方式 | 状态 | 说明 |
|------|------|------|------|
| PV Magazine 中国 | RSS | ✅ | 中国市场新闻 |
| 北极星光伏网 | Playwright | ✅ | 中国光伏行业新闻 |

### 数据统计
- **总文章数**: 80+ 篇
- **商业光伏文章**: 包含专项分析标签
- **更新频率**: 支持定时爬取
- **数据完整性**: 标题、内容、分析结果完整存储

## 🤖 智能功能

### 智能摘要
支持多种 LLM 后端：
- OpenAI (GPT-3.5/4)
- DeepSeek
- 智谱 GLM

```bash
# 设置 API Key
export OPENAI_API_KEY=your_key
solarnews crawl --smart
```

### 智能分类
自动分类内容类型：
- 新闻资讯 (news)
- 政策法规 (policy)
- 市场分析 (market)
- 技术创新 (technology)
- 项目动态 (project)
- 金融投资 (finance)

## 📊 项目结构

```
newsup-solar/
├── solarnews/           # CLI 入口
│   ├── cli.py          # 命令行工具
│   └── __init__.py
├── src/
│   ├── crawlers/       # 爬虫模块
│   │   ├── base.py     # 基础爬虫
│   │   ├── dynamic_crawler.py  # Playwright 支持
│   │   ├── pv_magazine.py
│   │   ├── solar_power_world.py
│   │   ├── chinese/    # 中文源
│   │   └── commercial/ # 工商业专项
│   ├── processors/     # 数据处理
│   │   ├── smart_summarizer.py   # 智能摘要
│   │   ├── smart_classifier.py   # 智能分类
│   │   └── rss_parser.py         # RSS 解析
│   ├── storage/        # 数据存储
│   └── api/            # API 服务
├── pyproject.toml      # 项目配置
├── install.sh          # 一键安装脚本
└── README.md
```

## ⚙️ 配置

### 环境变量

```bash
# 数据库（默认 SQLite）
DATABASE_URL=sqlite:///./data/news.db

# LLM API（可选）
OPENAI_API_KEY=your_key
DEEPSEEK_API_KEY=your_key
ZHIPU_API_KEY=your_key
```

## 🔧 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化
black src/ solarnews/

# 类型检查
mypy src/
```

## 📝 更新日志

### v1.0.0 (2026-03)
- ✅ 支持中英文新闻源
- ✅ RSS + Playwright 自动降级
- ✅ 智能摘要和分类
- ✅ 工商业光伏专项模式
- ✅ 一键安装脚本

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**🌞 Solar News** - 让太阳能资讯触手可及
