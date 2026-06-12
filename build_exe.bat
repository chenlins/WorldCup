@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 构建一键启动 exe

echo 正在安装打包工具 PyInstaller...
python -m pip install pyinstaller -q

echo 正在生成独立版 StartServer.exe ...
python -m PyInstaller --onefile --console --name "StartServer" ^
  --distpath "." --workpath "build" --specpath "build" --clean ^
  --paths "." ^
  --add-data "%~dp0web;web" ^
  --add-data "%~dp0config.yaml;." ^
  --hidden-import uvicorn.logging ^
  --hidden-import uvicorn.loops ^
  --hidden-import uvicorn.loops.auto ^
  --hidden-import uvicorn.protocols ^
  --hidden-import uvicorn.protocols.http ^
  --hidden-import uvicorn.protocols.http.auto ^
  --hidden-import uvicorn.protocols.http.h11_impl ^
  --hidden-import uvicorn.protocols.websockets ^
  --hidden-import uvicorn.protocols.websockets.auto ^
  --hidden-import uvicorn.lifespan ^
  --hidden-import uvicorn.lifespan.on ^
  --collect-submodules uvicorn ^
  --collect-submodules fastapi ^
  --collect-submodules starlette ^
  launcher.py

if exist "StartServer.exe" (
    copy /y "StartServer.exe" "启动服务.exe" >nul
    echo.
    echo 构建成功:
    echo   %cd%\StartServer.exe
    echo   %cd%\启动服务.exe
) else (
    echo.
    echo 构建失败，请检查上方错误信息
)

pause
