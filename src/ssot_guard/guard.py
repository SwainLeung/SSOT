"""Registry-driven exact-copy detection for SSOT-owned files."""

from __future__ import annotations

import fnmatch
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path


SKIP_DIRECTORIES = {".git", ".venv", "node_modules", "__pycache__", ".ssot"}


@dataclass(frozen=True)
class Finding:
    rule_id: str
    path: Path
    source: Path
    message: str


def _hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _files(root: Path, patterns: list[str]):
    if not root.is_dir():
        return
    for current, directories, filenames in os.walk(root, topdown=True):
        directories[:] = [name for name in directories if name not in SKIP_DIRECTORIES]
        current_path = Path(current)
        for filename in filenames:
            if any(fnmatch.fnmatch(filename, pattern) for pattern in patterns):
                yield current_path / filename


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("registry must be a JSON object")
    return value


def _target_roots(base: Path, registry: dict) -> list[Path]:
    result: list[Path] = []
    for pattern in registry.get("target_roots", []):
        for path in base.glob(str(pattern)):
            if path.is_dir():
                result.append(path)
    return result


def scan(base: str | Path, registry_path: str | Path) -> list[Finding]:
    root = Path(base).resolve()
    registry = _load(Path(registry_path).resolve())
    targets = _target_roots(root, registry)
    findings: list[Finding] = []
    for rule in registry.get("guard_rules", []):
        source_root = root / str(rule["source"])
        patterns = [str(item) for item in rule.get("patterns", [])]
        canonical: dict[str, list[tuple[Path, str]]] = {}
        for source in _files(source_root, patterns) or ():
            canonical.setdefault(source.name, []).append((source, _hash(source)))
        for target_root in targets:
            for candidate in _files(target_root, patterns) or ():
                for source, source_hash in canonical.get(candidate.name, []):
                    if _hash(candidate) == source_hash:
                        findings.append(Finding(
                            str(rule["id"]),
                            candidate,
                            source,
                            str(rule.get("message", "Canonical file copied into a target")),
                        ))
                        break
    return sorted(findings, key=lambda item: str(item.path).lower())
