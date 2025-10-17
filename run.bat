@echo off
REM Windows启动脚本

echo ========================================
echo   Nginx日志智能防火墙系统
echo ========================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python
    pause
    exit /b 1
)

REM 检查虚拟环境
if not exist "venv" (
    echo 正在创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 检查依赖
echo 正在检查依赖...
pip install -r requirements.txt --quiet

REM 启动系统
echo.
echo 正在启动系统...
python main.py

pause

