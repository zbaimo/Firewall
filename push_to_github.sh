#!/bin/bash

echo "========================================"
echo "  推送到GitHub"
echo "========================================"
echo ""

# 检查Git
if ! command -v git &> /dev/null; then
    echo "错误: 未找到Git，请先安装"
    exit 1
fi

# 获取用户名
read -p "请输入你的GitHub用户名: " USERNAME

echo ""
echo "请确认以下信息:"
echo "- GitHub仓库: https://github.com/$USERNAME/Firewall.git"
echo ""
read -p "按Enter继续..."

# 初始化Git（如果需要）
if [ ! -d ".git" ]; then
    echo "初始化Git仓库..."
    git init
    git branch -M main
fi

# 添加远程仓库
git remote remove origin 2>/dev/null
git remote add origin https://github.com/$USERNAME/Firewall.git

echo ""
echo "正在添加文件..."
git add .

echo ""
read -p "请输入提交信息（直接回车使用默认信息）: " COMMIT_MSG
if [ -z "$COMMIT_MSG" ]; then
    COMMIT_MSG="Initial commit: 完整的Nginx智能防火墙系统"
fi

echo ""
echo "正在提交..."
git commit -m "$COMMIT_MSG"

echo ""
echo "正在推送到GitHub..."
git push -u origin main

echo ""
echo "========================================"
echo "  推送完成！"
echo "========================================"
echo ""
echo "下一步:"
echo "1. 访问 https://github.com/$USERNAME/Firewall"
echo "2. 配置Docker Hub Secrets（见 DEPLOY_TO_GITHUB.md）"
echo "3. 触发GitHub Actions构建"
echo ""

