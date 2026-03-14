# newsup-solar - Solar Power News Aggregator

A Python-based news aggregator focused on solar power and renewable energy news.

## Features

- **Multi-source crawling**: Collect news from various solar power news sources
- **Content extraction**: Clean and structure news articles
- **Topic classification**: Categorize articles by topic and relevance
- **Sentiment analysis**: Analyze sentiment towards solar power developments
- **Search & filtering**: Advanced search capabilities
- **API access**: RESTful API for programmatic access
- **Web dashboard**: Visual dashboard for news monitoring

## Project Structure

```
newsup-solar/
├── src/                    # Source code
│   ├── crawlers/          # News source crawlers
│   ├── processors/        # Data processing modules
│   ├── storage/           # Database and storage modules
│   ├── api/               # API server
│   └── utils/             # Utility functions
├── config/                # Configuration files
├── tests/                 # Test suite
├── docs/                  # Documentation
├── data/                  # Data storage (excluded from git)
├── logs/                  # Log files (excluded from git)
├── requirements.txt       # Python dependencies
├── .env.example          # Example environment variables
├── .gitignore            # Git ignore rules
├── docker-compose.yml    # Docker orchestration
└── Dockerfile            # Docker container definition
```

## Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL 13+ (or SQLite for development)
- Redis (optional, for caching)

### Installation

1. Clone the repository:
```bash
git clone git@github.com:ankrwu/newsup-solar.git
cd newsup-solar
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize database:
```bash
python scripts/init_db.py
```

6. Run the crawler:
```bash
python src/main.py --crawl
```

7. Start the API server:
```bash
python src/api/server.py
```

## Configuration

Edit `.env` file to configure:

- Database connection
- News sources to crawl
- Crawling frequency
- API settings
- Logging levels

## Data Sources

Planned news sources:
- PV Magazine
- Solar Power World
- Renewable Energy World
- CleanTechnica
- Solar Industry Magazine
- National Renewable Energy Laboratory (NREL) news
- International Solar Energy Society (ISES) updates

## Commercial & Industrial Solar Focus

本项目专门提供了工商业光伏（C&I Solar）专项功能，专注于商业和工业光伏领域的新闻、政策和市场分析。

### 工商业光伏专项功能
- **专用爬虫**: PV Magazine Business, Solar Power World Commercial
- **智能分析**: 商业模式识别、项目规模分类、地域分析
- **关键词过滤**: 59个工商业光伏专项关键词
- **分类系统**: 新闻/政策/市场三级分类

### 快速开始（工商业光伏模式）
```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 初始化数据库
python scripts/init_db.py

# 3. 运行工商业光伏爬虫
python src/main.py --crawl --commercial --init-db
```

### 详细指南
详见 [COMMERCIAL_GUIDE.md](COMMERCIAL_GUIDE.md) 获取完整使用说明和扩展指南。

## Development

### Running Tests
```bash
pytest tests/
```

### Code Style
```bash
black src/ tests/
flake8 src/ tests/
```

### Building Documentation
```bash
cd docs && make html
```

## API Documentation

Once running, visit `http://localhost:8000/docs` for interactive API documentation.

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please read CONTRIBUTING.md for guidelines.

## Acknowledgments

- Built with Python and FastAPI
- Uses BeautifulSoup4 for HTML parsing
- PostgreSQL for data persistence
- Redis for caching (optional)