#!/usr/bin/env python3
"""Run the public SSOT guard."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from ssot_guard import scan  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--registry", default=str(ROOT / "config/ssot-registry.json"))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    findings = scan(root, args.registry)
    payload = {
        "errors": len(findings),
        "findings": [
            {
                **asdict(item),
                "path": str(item.path.relative_to(root)),
                "source": str(item.source.relative_to(root)),
            }
            for item in findings
        ],
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif findings:
        print(f"SSOT guard: {len(findings)} finding(s)")
        for item in findings:
            print(f"[ERROR] {item.rule_id}: {item.message} ({item.path.relative_to(root)}; source={item.source.relative_to(root)})")
    else:
        print("SSOT guard: clean")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
