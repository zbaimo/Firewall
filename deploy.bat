@echo off
REM ===================================================================
REM Nginx智能防火墙 - Windows快速部署脚本
REM ===================================================================

chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

echo ==================================================================
echo   Nginx智能防火墙 - 部署向导
echo ==================================================================
echo.

REM 检查Docker
echo 正在检查依赖...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Docker未安装
    echo 请先安装Docker Desktop: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)
echo [✓] Docker已安装

REM 检查Docker Compose
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Docker Compose未安装
    pause
    exit /b 1
)
echo [✓] Docker Compose已安装

echo.
echo ==================================================================
echo   选择部署模式
echo ==================================================================
echo.
echo 1) 简单模式 - 快速测试（推荐新手）
echo 2) 标准模式 - 日常使用
echo 3) 生产模式 - 企业部署（推荐）
echo 4) 高性能模式 - 最高性能
echo.
set /p mode="请选择 [1-4]: "

if "%mode%"=="1" (
    set COMPOSE_FILE=docker-compose.simple.yml
    set MODE_NAME=简单模式
) else if "%mode%"=="2" (
    set COMPOSE_FILE=docker-compose.yml
    set MODE_NAME=标准模式
) else if "%mode%"=="3" (
    set COMPOSE_FILE=docker-compose.deploy.yml
    set MODE_NAME=生产模式
) else if "%mode%"=="4" (
    set COMPOSE_FILE=docker-compose.prod.yml
    set MODE_NAME=高性能模式
) else (
    echo [错误] 无效选择
    pause
    exit /b 1
)

echo [✓] 已选择: %MODE_NAME% (%COMPOSE_FILE%)

REM 检查配置文件
echo.
echo 检查配置文件...

if not exist "config.yaml" (
    echo [错误] config.yaml 不存在
    echo 请先创建config.yaml配置文件
    pause
    exit /b 1
)
echo [✓] config.yaml 存在

if not exist "%COMPOSE_FILE%" (
    echo [错误] %COMPOSE_FILE% 不存在
    pause
    exit /b 1
)
echo [✓] %COMPOSE_FILE% 存在

REM 检查环境变量文件
if not exist ".env" (
    echo [警告] .env 文件不存在
    if exist ".env.example" (
        echo 从 .env.example 创建 .env
        copy .env.example .env >nul
        echo [✓] .env 已创建
        echo [警告] 请编辑 .env 文件修改配置
    )
)

REM 创建必要目录
echo.
echo 创建必要的目录...
if not exist "exports" mkdir exports
if not exist "logs" mkdir logs
if not exist "data" mkdir data
echo [✓] 目录创建完成

REM 拉取最新镜像
echo.
echo 拉取Docker镜像...
docker-compose -f %COMPOSE_FILE% pull
if errorlevel 1 (
    echo [错误] 镜像拉取失败
    pause
    exit /b 1
)
echo [✓] 镜像拉取完成

REM 启动服务
echo.
echo ==================================================================
echo   启动服务
echo ==================================================================
docker-compose -f %COMPOSE_FILE% up -d
if errorlevel 1 (
    echo [错误] 服务启动失败
    pause
    exit /b 1
)

REM 等待服务启动
echo.
echo 等待服务启动...
timeout /t 5 /nobreak >nul

REM 检查服务状态
echo.
echo ==================================================================
echo   服务状态
echo ==================================================================
docker-compose -f %COMPOSE_FILE% ps

REM 显示访问信息
echo.
echo ==================================================================
echo   部署完成！
echo ==================================================================
echo.
echo [✓] 服务已启动
echo.
echo 访问地址: http://localhost:8080
echo 默认账户: admin / admin
echo.
echo [警告] 首次登录会强制修改密码
echo.
echo 常用命令:
echo   查看日志: docker-compose -f %COMPOSE_FILE% logs -f
echo   停止服务: docker-compose -f %COMPOSE_FILE% down
echo   重启服务: docker-compose -f %COMPOSE_FILE% restart
echo.
echo ==================================================================

REM 询问是否查看日志
set /p show_logs="是否查看实时日志？[y/N]: "
if /i "%show_logs%"=="y" (
    docker-compose -f %COMPOSE_FILE% logs -f
)

pause


