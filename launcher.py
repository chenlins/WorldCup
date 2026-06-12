"""一键启动器：供 PyInstaller 打包为独立 exe，或直接用 python launcher.py 运行。"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path


def get_exe_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_bundle_dir() -> str:
    if getattr(sys, "frozen", False):
        return sys._MEIPASS  # type: ignore[attr-defined]
    return os.path.dirname(os.path.abspath(__file__))


def resolve_config_path() -> str:
    local = Path(get_exe_dir()) / "config.yaml"
    if local.is_file():
        return str(local)
    bundled = Path(get_bundle_dir()) / "config.yaml"
    if bundled.is_file():
        return str(bundled)
    return str(local)


def read_port(config_path: str) -> int:
    try:
        import yaml

        with open(config_path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        return int(cfg.get("api", {}).get("port", 8086))
    except Exception:
        return 8086


def open_browser_later(port: int) -> None:
    time.sleep(2)
    webbrowser.open(f"http://127.0.0.1:{port}")


def run_server(config_path: str, port: int) -> int:
    import uvicorn
    from api.app import create_app

    with open(config_path, encoding="utf-8") as f:
        import yaml

        cfg = yaml.safe_load(f) or {}
    host = cfg.get("api", {}).get("host", "127.0.0.1")

    app = create_app(config_path)
    uvicorn.run(app, host=host, port=port)
    return 0


def main() -> int:
    root = get_exe_dir()
    os.chdir(root)
    config_path = resolve_config_path()
    port = read_port(config_path)

    print("=" * 40)
    print("  2026 世界杯赛事分析 - 一键启动")
    print("=" * 40)
    print(f"  工作目录: {root}")
    print(f"  服务地址: http://127.0.0.1:{port}")
    print("=" * 40)
    print()

    threading.Thread(target=open_browser_later, args=(port,), daemon=True).start()
    print("正在启动服务，浏览器将自动打开...")
    print("关闭本窗口即可停止服务。")
    print()

    try:
        if getattr(sys, "frozen", False):
            return run_server(config_path, port)

        req = os.path.join(root, "requirements.txt")
        if os.path.isfile(req):
            print("正在检查依赖...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", req, "-q"],
                cwd=root,
                check=False,
            )
        cmd = [sys.executable, os.path.join(root, "main.py"), "serve"]
        return subprocess.call(cmd, cwd=root)
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        print(f"[错误] 启动失败: {e}")
        input("按回车键退出...")
        return 1


if __name__ == "__main__":
    sys.exit(main())
