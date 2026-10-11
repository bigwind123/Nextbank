"""Run one or all public, offline examples: python examples/run_demo.py [gateway|ocr|mcp|all]."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

# Running as a file puts only examples/ on sys.path; include the portfolio root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from examples import gateway, mcp, ocr


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", choices=("gateway", "ocr", "mcp", "all"), nargs="?", default="all")
    args = parser.parse_args()
    selected = {"gateway": gateway.demo, "ocr": ocr.demo, "mcp": mcp.demo}
    for name in selected if args.scenario == "all" else (args.scenario,):
        print(f"=== {name.upper()} (offline fictional fixture) ===")
        print(selected[name]())


if __name__ == "__main__":
    main()
