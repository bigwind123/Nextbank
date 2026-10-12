from __future__ import annotations

import argparse

from .app import create_app
from .config import load_config


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local portfolio application")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--data-dir")
    parser.add_argument("--allow-external-bind", action="store_true")
    args = parser.parse_args()
    if args.host not in {"127.0.0.1", "localhost", "::1"} and not args.allow_external_bind:
        parser.error("external binding is disabled; use loopback or pass --allow-external-bind explicitly")
    config = load_config()
    if args.data_dir:
        config["data_dir"] = args.data_dir
    app = create_app(config)
    app.run(host=args.host, port=args.port, threaded=True, use_reloader=False)


if __name__ == "__main__":
    main()
