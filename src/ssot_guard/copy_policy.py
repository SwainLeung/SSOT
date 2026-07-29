"""Dry-run-first bootstrap copy with provenance recording."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


class CopyPolicyError(RuntimeError):
    pass


def _inside(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _tree_hash(path: Path) -> str:
    digest = hashlib.sha256()
    files = [path] if path.is_file() else sorted(item for item in path.rglob("*") if item.is_file())
    for item in files:
        relative = item.name if path.is_file() else item.relative_to(path).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(item.read_bytes())
    return digest.hexdigest()


def bootstrap(source: str | Path, destination: str | Path, root: str | Path, registry: dict, apply: bool = False) -> dict:
    base = Path(root).resolve()
    source_path = Path(source).resolve()
    destination_path = Path(destination).resolve()
    allowed_sources = [base / item for item in registry.get("bootstrap_sources", [])]
    if not any(_inside(source_path, candidate) for candidate in allowed_sources):
        raise CopyPolicyError("source is outside the configured bootstrap sources")
    target_roots = [base / item for item in registry.get("target_roots", [])]
    target_root = next((item for item in target_roots if _inside(destination_path, item)), None)
    if target_root is None:
        raise CopyPolicyError("destination is outside the configured target roots")
    if destination_path.exists():
        raise CopyPolicyError(f"destination already exists: {destination_path}")
    record = {
        "mode": "bootstrap",
        "source": source_path.relative_to(base).as_posix(),
        "destination": destination_path.relative_to(base).as_posix(),
        "source_sha256": _tree_hash(source_path),
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    if not apply:
        return {"applied": False, **record}
    if source_path.is_dir():
        shutil.copytree(source_path, destination_path)
    else:
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination_path)
    manifest_path = destination_path / ".ssot/copy-manifest.json" if destination_path.is_dir() else target_root / ".ssot/copy-manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {"schema_version": 1, "entries": []}
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.setdefault("entries", []).append(record)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"applied": True, **record, "manifest": manifest_path.relative_to(base).as_posix()}
