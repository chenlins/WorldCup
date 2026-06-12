@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 构建一键启动 exe

echo 正在安装打包工具 PyInstaller...
python -m pip install pyinstaller -q

echo 正在生成 StartServer.exe ...
python -m PyInstaller --onefile --console --name "StartServer" --distpath "." --workpath "build" --specpath "build" --clean launcher.py

if exist "StartServer.exe" (
    copy /y "StartServer.exe" "启动服务.exe" >nul
    echo.
    echo 构建成功:
    echo   %cd%\start.bat
    echo   %cd%\启动服务.exe
) else (
    echo.
    echo 构建失败，请检查上方错误信息
)

pause
