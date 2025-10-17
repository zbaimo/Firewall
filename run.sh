#!/bin/bash
# Linux/macOS启动脚本

echo "========================================"
echo "  Nginx日志智能防火墙系统"
echo "========================================"
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "正在创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 检查依赖
echo "正在检查依赖..."
pip install -r requirements.txt --quiet

# 启动系统
echo ""
echo "正在启动系统..."
python main.py

