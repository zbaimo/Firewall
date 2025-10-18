#!/bin/bash

# ===================================================================
# Nginx智能防火墙 - 快速部署脚本
# ===================================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
print_header() {
    echo -e "${BLUE}===================================================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}===================================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 未安装"
        return 1
    fi
    print_success "$1 已安装"
    return 0
}

# 主函数
main() {
    print_header "Nginx智能防火墙 - 部署向导"
    
    echo ""
    print_info "正在检查依赖..."
    
    # 检查Docker
    if ! check_command docker; then
        print_error "请先安装Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    # 检查Docker Compose
    if ! check_command docker-compose; then
        print_error "请先安装Docker Compose: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    echo ""
    print_header "选择部署模式"
    echo ""
    echo "1) 简单模式 - 快速测试（推荐新手）"
    echo "2) 标准模式 - 日常使用"
    echo "3) 生产模式 - 企业部署（推荐）"
    echo "4) 高性能模式 - 最高性能"
    echo ""
    read -p "请选择 [1-4]: " mode
    
    case $mode in
        1)
            COMPOSE_FILE="docker-compose.simple.yml"
            MODE_NAME="简单模式"
            ;;
        2)
            COMPOSE_FILE="docker-compose.yml"
            MODE_NAME="标准模式"
            ;;
        3)
            COMPOSE_FILE="docker-compose.deploy.yml"
            MODE_NAME="生产模式"
            ;;
        4)
            COMPOSE_FILE="docker-compose.prod.yml"
            MODE_NAME="高性能模式"
            ;;
        *)
            print_error "无效选择"
            exit 1
            ;;
    esac
    
    print_success "已选择: $MODE_NAME ($COMPOSE_FILE)"
    
    # 检查配置文件
    echo ""
    print_info "检查配置文件..."
    
    if [ ! -f "config.yaml" ]; then
        print_error "config.yaml 不存在"
        print_info "请先创建config.yaml配置文件"
        exit 1
    fi
    print_success "config.yaml 存在"
    
    if [ ! -f "$COMPOSE_FILE" ]; then
        print_error "$COMPOSE_FILE 不存在"
        exit 1
    fi
    print_success "$COMPOSE_FILE 存在"
    
    # 检查环境变量文件
    if [ ! -f ".env" ]; then
        print_warning ".env 文件不存在"
        if [ -f ".env.example" ]; then
            print_info "从 .env.example 创建 .env"
            cp .env.example .env
            print_success ".env 已创建"
            print_warning "请编辑 .env 文件修改配置"
        fi
    fi
    
    # 创建必要目录
    echo ""
    print_info "创建必要的目录..."
    mkdir -p exports logs data
    print_success "目录创建完成"
    
    # 拉取最新镜像
    echo ""
    print_info "拉取Docker镜像..."
    docker-compose -f $COMPOSE_FILE pull
    print_success "镜像拉取完成"
    
    # 启动服务
    echo ""
    print_header "启动服务"
    docker-compose -f $COMPOSE_FILE up -d
    
    # 等待服务启动
    echo ""
    print_info "等待服务启动..."
    sleep 5
    
    # 检查服务状态
    echo ""
    print_header "服务状态"
    docker-compose -f $COMPOSE_FILE ps
    
    # 获取访问地址
    echo ""
    print_header "部署完成！"
    echo ""
    
    # 检查端口
    if [ "$mode" = "3" ] || [ "$mode" = "4" ]; then
        PORT=$(grep -oP 'WEB_PORT=\K\d+' .env 2>/dev/null || echo "8080")
    else
        PORT="8080"
    fi
    
    print_success "服务已启动"
    echo ""
    echo -e "${GREEN}访问地址:${NC} http://localhost:$PORT"
    echo -e "${GREEN}默认账户:${NC} admin / admin"
    echo ""
    print_warning "首次登录会强制修改密码"
    echo ""
    
    # 显示日志
    print_info "查看实时日志："
    echo "  docker-compose -f $COMPOSE_FILE logs -f"
    echo ""
    print_info "停止服务："
    echo "  docker-compose -f $COMPOSE_FILE down"
    echo ""
    print_info "重启服务："
    echo "  docker-compose -f $COMPOSE_FILE restart"
    echo ""
    
    # 询问是否查看日志
    read -p "是否查看实时日志？[y/N]: " show_logs
    if [ "$show_logs" = "y" ] || [ "$show_logs" = "Y" ]; then
        docker-compose -f $COMPOSE_FILE logs -f
    fi
}

# 运行主函数
main


