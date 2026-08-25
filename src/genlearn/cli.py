from __future__ import annotations

import argparse
import json
import sys

from .workflow import run_workflow


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate and self-evaluate a beginner lesson.")
    parser.add_argument("--topic", default="Introduction to RAG")
    parser.add_argument("--inject-fault", action="store_true")
    args = parser.parse_args(argv)

    result = run_workflow(args.topic, inject_fault=args.inject_fault)
    json.dump(result, sys.stdout, indent=2, ensure_ascii=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
