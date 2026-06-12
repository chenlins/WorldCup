"""一键启动器：供 PyInstaller 打包为 exe，或直接用 python launcher.py 运行。"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import threading
import time
import webbrowser


def get_root() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def read_port(root: str) -> int:
    config_path = os.path.join(root, "config.yaml")
    try:
        import yaml

        with open(config_path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        return int(cfg.get("api", {}).get("port", 8086))
    except Exception:
        return 8086


def find_python() -> str | None:
    for name in ("python", "python3", "py"):
        path = shutil.which(name)
        if path:
            return path
    return None


def open_browser_later(port: int) -> None:
    time.sleep(2)
    webbrowser.open(f"http://127.0.0.1:{port}")


def main() -> int:
    root = get_root()
    os.chdir(root)
    port = read_port(root)

    print("=" * 40)
    print("  2026 世界杯赛事分析 - 一键启动")
    print("=" * 40)
    print(f"  工作目录: {root}")
    print(f"  服务地址: http://127.0.0.1:{port}")
    print("=" * 40)
    print()

    if getattr(sys, "frozen", False):
        python = find_python()
        if not python:
            print("[错误] 未找到 Python，请先安装 Python 3.10+")
            input("按回车键退出...")
            return 1
        cmd = [python, os.path.join(root, "main.py"), "serve"]
    else:
        cmd = [sys.executable, os.path.join(root, "main.py"), "serve"]

    req = os.path.join(root, "requirements.txt")
    if os.path.isfile(req):
        print("正在检查依赖...")
        subprocess.run(
            [cmd[0], "-m", "pip", "install", "-r", req, "-q"],
            cwd=root,
            check=False,
        )

    threading.Thread(target=open_browser_later, args=(port,), daemon=True).start()

    print("正在启动服务，浏览器将自动打开...")
    print("关闭本窗口即可停止服务。")
    print()

    try:
        return subprocess.call(cmd, cwd=root)
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        print(f"[错误] 启动失败: {e}")
        input("按回车键退出...")
        return 1


if __name__ == "__main__":
    sys.exit(main())
