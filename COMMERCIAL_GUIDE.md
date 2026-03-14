# 工商业光伏新闻聚合器 - 使用指南

## 项目概述

这是一个专门针对工商业光伏（Commercial & Industrial Solar）新闻、政策和市场信息的智能聚合系统。系统可以自动抓取、分析和分类相关新闻，为投资者、企业和研究人员提供精准情报。

## 核心功能

### 1. 专项数据源
- **PV Magazine Business**: 工商业光伏新闻、项目、技术
- **Solar Power World Commercial**: 商业光伏安装、案例研究
- **未来扩展**: 更多英文、中文和市场数据源

### 2. 智能分析
- **内容分类**: 自动识别新闻、政策、市场报告
- **商业分析**: 识别商业模式（PPA、租赁等）、项目规模、地域
- **关键词过滤**: 59个工商业光伏专项关键词
- **情感分析**: 基础情感评分（可扩展）

### 3. 数据存储
- **标准化存储**: SQLite/PostgreSQL 数据库
- **完整元数据**: 文章、分类、分析结果
- **扩展性**: 模块化设计，易于添加新字段

## 快速开始

### 1. 环境设置
```bash
# 克隆项目
git clone git@github.com:ankrwu/newsup-solar.git
cd newsup-solar

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Linux/Mac:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 数据库初始化
```bash
python scripts/init_db.py
```
这将创建 SQLite 数据库文件 `data/news.db`。

### 3. 运行爬虫

#### 模式选择
- **普通模式**: 通用太阳能新闻
- **工商业光伏模式**: 专注工商业光伏内容

#### 命令示例
```bash
# 1. 普通模式爬取（通用太阳能新闻）
python src/main.py --crawl --init-db

# 2. 工商业光伏模式爬取（推荐）
python src/main.py --crawl --commercial --init-db

# 3. 指定数据源爬取
python src/main.py --crawl --commercial --source pv_magazine
python src/main.py --crawl --commercial --source solar_power_world

# 4. 只初始化数据库
python src/main.py --init-db

# 5. 查看帮助
python src/main.py --help
```

#### 参数说明
- `--crawl`: 运行爬取
- `--commercial`: 使用工商业光伏模式（专用爬虫+分析器）
- `--init-db`: 初始化数据库（如果不存在）
- `--source`: 指定数据源：`pv_magazine`, `solar_power_world`, `commercial`, `all`（默认）

### 4. 查看结果

#### 数据库查看
```bash
# 使用 sqlite3 命令行查看
sqlite3 data/news.db

# SQLite 命令示例
.tables
SELECT COUNT(*) FROM articles;
SELECT title, source, content_type FROM articles LIMIT 5;
```

#### 日志输出
爬虫运行时会在控制台输出详细信息：
- 找到的文章数量
- 处理状态
- 错误信息（如果有）

## 高级配置

### 1. 环境变量
复制示例配置文件并修改：
```bash
cp .env.example .env
```
编辑 `.env` 文件配置数据库、日志等。

### 2. 关键词定制
修改 `config/commercial_solar_keywords.py`：
- 添加/删除关键词
- 调整分类规则
- 修改地域识别规则

### 3. 添加新数据源
1. 在 `src/crawlers/commercial/` 创建新爬虫
2. 继承 `BaseCrawler` 类
3. 实现 `fetch_article_urls()` 和 `parse_article()` 方法
4. 在主程序 `get_crawlers()` 中添加新爬虫

### 4. 自定义分析规则
修改 `src/processors/commercial_cleaner.py`：
- 调整商业分析逻辑
- 添加新的分类规则
- 修改评分算法

## 项目结构
```
newsup-solar/
├── config/
│   └── commercial_solar_keywords.py    # 工商业光伏关键词
├── src/
│   ├── crawlers/
│   │   ├── commercial/                 # 工商业光伏专用爬虫
│   │   │   ├── pv_magazine_business.py
│   │   │   └── solar_power_world_commercial.py
│   │   └── base.py                     # 爬虫基类
│   ├── processors/
│   │   ├── commercial_cleaner.py       # 工商业光伏清洗器
│   │   ├── cleaner.py                  # 通用清洗器
│   │   └── classifier.py               # 分类器
│   └── storage/
│       └── database.py                 # 数据库模型
├── scripts/
│   └── init_db.py                      # 数据库初始化
└── data/                               # 数据存储目录
```

## 扩展计划

### 短期扩展（1-2周）
1. **添加更多数据源**:
   - Solar Industry Magazine
   - Renewable Energy World - Solar
   - SEIA 政策更新
   - 北极星太阳能光伏网（中文）

2. **增强分析功能**:
   - LLM 集成（摘要生成）
   - 情感分析改进
   - 实体识别（公司、项目、人物）

3. **API 服务**:
   - RESTful API 提供数据查询
   - 数据导出功能
   - 实时通知

### 中期扩展（1-2月）
1. **市场数据集成**:
   - 价格趋势数据
   - 投资分析报告
   - 政策影响评估

2. **可视化仪表板**:
   - 新闻热度图
   - 政策时间线
   - 市场趋势图表

3. **预警系统**:
   - 重要政策变化预警
   - 市场机会发现
   - 竞争情报分析

## 注意事项

### 1. 反爬虫策略
- 设置合理的请求间隔
- 使用 User-Agent 标识
- 遵守网站的 robots.txt
- 避免短时间内大量请求

### 2. 数据质量
- 定期验证数据源有效性
- 监控爬取成功率
- 清理无效/重复数据

### 3. 性能优化
- 使用异步请求提高效率
- 数据库索引优化
- 缓存常用查询结果

### 4. 法律合规
- 仅用于个人学习/研究
- 遵守数据使用条款
- 注明数据来源

## 故障排除

### 常见问题
1. **导入错误**: 确保所有依赖已安装
2. **数据库错误**: 检查数据库文件权限
3. **网络错误**: 检查网络连接和代理设置
4. **爬取失败**: 网站结构可能已更新

### 日志查看
- 控制台输出详细日志
- 日志级别可在代码中调整
- 错误信息包含详细堆栈跟踪

## 贡献指南
欢迎提交 Issue 和 Pull Request：
1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 创建 Pull Request

## 许可证
MIT License - 详见 LICENSE 文件

## 联系方式
- 项目地址: https://github.com/ankrwu/newsup-solar
- 问题反馈: GitHub Issues

---

**提示**: 首次运行建议先测试单个数据源，确认功能正常后再进行完整爬取。