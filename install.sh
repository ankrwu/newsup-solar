#!/bin/bash
# Solar News 一键安装脚本
# 使用方法: curl -sSL https://raw.githubusercontent.com/ankrwu/newsup-solar/main/install.sh | bash

set -e

echo "========================================"
echo "  Solar News 安装脚本"
echo "  全球太阳能行业新闻聚合器"
echo "========================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 Python 版本
check_python() {
    echo "检查 Python 版本..."
    if command -v python3 &> /dev/null; then
        PYTHON_CMD=python3
    elif command -v python &> /dev/null; then
        PYTHON_CMD=python
    else
        echo -e "${RED}错误: 未找到 Python，请先安装 Python 3.9+${NC}"
        exit 1
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    echo -e "${GREEN}发现 Python $PYTHON_VERSION${NC}"
    
    # 检查版本是否 >= 3.9
    MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 9 ]); then
        echo -e "${RED}错误: 需要 Python 3.9 或更高版本${NC}"
        exit 1
    fi
}

# 克隆仓库
clone_repo() {
    echo ""
    echo "克隆 Solar News 仓库..."
    
    if [ -d "newsup-solar" ]; then
        echo -e "${YELLOW}目录 newsup-solar 已存在，跳过克隆${NC}"
    else
        git clone https://github.com/ankrwu/newsup-solar.git
        echo -e "${GREEN}仓库克隆完成${NC}"
    fi
    
    cd newsup-solar
}

# 创建虚拟环境
create_venv() {
    echo ""
    echo "创建虚拟环境..."
    
    if [ -d "venv" ]; then
        echo -e "${YELLOW}虚拟环境已存在，跳过创建${NC}"
    else
        $PYTHON_CMD -m venv venv
        echo -e "${GREEN}虚拟环境创建完成${NC}"
    fi
}

# 安装依赖
install_deps() {
    echo ""
    echo "安装依赖包..."
    
    source venv/bin/activate
    
    # 升级 pip
    pip install --upgrade pip
    
    # 安装项目
    pip install -e .
    
    echo -e "${GREEN}依赖安装完成${NC}"
}

# 安装 Playwright 浏览器
install_playwright() {
    echo ""
    echo "安装 Playwright 浏览器（用于动态内容渲染）..."
    
    source venv/bin/activate
    playwright install chromium
    
    echo -e "${GREEN}Playwright 安装完成${NC}"
}

# 初始化数据库
init_db() {
    echo ""
    echo "初始化数据库..."
    
    source venv/bin/activate
    python -c "from src.storage.database import DatabaseManager; import asyncio; asyncio.run(DatabaseManager().initialize())"
    
    echo -e "${GREEN}数据库初始化完成${NC}"
}

# 显示完成信息
show_success() {
    echo ""
    echo "========================================"
    echo -e "${GREEN}  安装完成！${NC}"
    echo "========================================"
    echo ""
    echo "使用方法:"
    echo ""
    echo "  # 进入项目目录"
    echo "  cd newsup-solar"
    echo ""
    echo "  # 激活虚拟环境"
    echo "  source venv/bin/activate"
    echo ""
    echo "  # 爬取新闻（默认中英文）"
    echo "  solarnews crawl"
    echo ""
    echo "  # 只爬取中文源"
    echo "  solarnews crawl --chinese"
    echo ""
    echo "  # 只爬取英文源"
    echo "  solarnews crawl --english"
    echo ""
    echo "  # 启用智能摘要"
    echo "  solarnews crawl --smart"
    echo ""
    echo "  # 启动 API 服务"
    echo "  solarnews serve"
    echo ""
    echo "  # 查看帮助"
    echo "  solarnews --help"
    echo ""
    echo "更多信息: https://github.com/ankrwu/newsup-solar"
    echo ""
}

# 主流程
main() {
    check_python
    clone_repo
    create_venv
    install_deps
    install_playwright
    init_db
    show_success
}

# 运行主流程
main
