"""
2026 世界杯赛事分析预测工具

用法:
  python main.py serve    # 启动 Web 服务
"""

import argparse
import sys

import yaml


def load_config(path: str = "config.yaml") -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def cmd_serve(config: dict):
    import uvicorn
    from api.app import create_app

    api_cfg = config.get("api", {})
    host = api_cfg.get("host", "127.0.0.1")
    port = api_cfg.get("port", 8086)
    app = create_app()
    print(f"2026 世界杯分析服务已启动: http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)


def main():
    parser = argparse.ArgumentParser(description="2026 世界杯赛事分析预测")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("serve", help="启动 Web 服务")
    args = parser.parse_args()
    config = load_config()

    if args.command == "serve":
        cmd_serve(config)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
