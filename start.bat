@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 2026世界杯赛事分析

echo ========================================
echo   2026 世界杯赛事分析 - 一键启动
echo ========================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.10 或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] 检查并安装依赖...
python -m pip install -r requirements.txt -q
if errorlevel 1 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)

echo [2/3] 读取端口配置...
for /f "tokens=2 delims=: " %%a in ('findstr /r "port:" config.yaml') do set PORT=%%a
if not defined PORT set PORT=8086

echo [3/3] 启动服务 http://127.0.0.1:%PORT%
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:%PORT%"

python main.py serve

echo.
echo 服务已停止
pause
