#!/usr/bin/env python3
"""Run a controlled SSOT bootstrap copy; dry-run by default."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from ssot_guard.copy_policy import CopyPolicyError, bootstrap  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["bootstrap"], default="bootstrap")
    parser.add_argument("--source", required=True)
    parser.add_argument("--destination", required=True)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--registry", default=str(ROOT / "config/ssot-registry.json"))
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    registry = json.loads(Path(args.registry).read_text(encoding="utf-8"))
    source = Path(args.source)
    destination = Path(args.destination)
    if not source.is_absolute():
        source = root / source
    if not destination.is_absolute():
        destination = root / destination
    try:
        result = bootstrap(source, destination, root, registry, apply=args.apply)
    except (OSError, ValueError, CopyPolicyError) as exc:
        print(f"SSOT copy blocked: {exc}")
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
