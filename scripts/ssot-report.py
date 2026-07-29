#!/usr/bin/env python3
"""Produce a compact SSOT governance report."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
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
        "root": str(root),
        "finding_count": len(findings),
        "by_code": dict(Counter(item.code for item in findings)),
        "findings": [
            {
                **asdict(item),
                "path": str(item.path.relative_to(root)),
                "source": str(item.source.relative_to(root)) if item.source else None,
            }
            for item in findings
        ],
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"SSOT report: {payload['finding_count']} finding(s)")
        for code, count in sorted(payload["by_code"].items()):
            print(f"  {code}: {count}")
        for item in payload["findings"]:
            print(f"  - {item['code']}: {item['path']}")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
