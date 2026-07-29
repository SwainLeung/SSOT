"""Dry-run-first execution of SSOT-approved copy modes."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from .hashing import tree_hash


class CopyPolicyError(RuntimeError):
    pass


def _inside(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _roots(base: Path, values: list[str]) -> list[Path]:
    return [(base / value).resolve() for value in values]


def _project_for(path: Path, base: Path, registry: dict) -> Path | None:
    for pattern in registry.get("target_roots", []):
        target_root = (base / str(pattern)).resolve()
        if not _inside(path, target_root):
            continue
        relative = path.relative_to(target_root)
        if relative.parts:
            return target_root / relative.parts[0]
    projects = []
    for pattern in registry.get("project_roots", []):
        projects.extend(item for item in base.glob(str(pattern)) if item.is_dir())
    candidates = [item.resolve() for item in projects if _inside(path, item)]
    return max(candidates, key=lambda item: len(item.parts), default=None)


def _manifest_path(owner: Path, registry: dict) -> Path:
    manifest = registry.get("manifest", {})
    return owner / str(manifest.get("directory", ".ssot")) / str(manifest.get("filename", "copy-manifest.json"))


def _record(mode: str, source: Path, destination: Path, base: Path) -> dict:
    return {
        "mode": mode,
        "source": source.relative_to(base).as_posix(),
        "destination": destination.relative_to(base).as_posix(),
        "source_sha256": tree_hash(source),
        "destination_sha256": tree_hash(destination),
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def _append_manifest(owner: Path, registry: dict, record: dict) -> str:
    manifest_path = _manifest_path(owner, registry)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    value = {"schema_version": 1, "entries": []}
    if manifest_path.is_file():
        value = json.loads(manifest_path.read_text(encoding="utf-8"))
    value.setdefault("entries", []).append(record)
    manifest_path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return str(manifest_path)


def _copy(source: Path, destination: Path) -> None:
    if source.is_dir():
        shutil.copytree(source, destination)
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def execute(mode: str, source: str | Path, destination: str | Path, root: str | Path, registry: dict, apply: bool = False) -> dict:
    base = Path(root).resolve()
    source_path = Path(source).resolve()
    destination_path = Path(destination).resolve()
    if mode == "reference":
        raise CopyPolicyError("reference mode forbids copying; import or call the canonical source")
    if not source_path.exists():
        raise CopyPolicyError("source does not exist")
    if destination_path.exists():
        raise CopyPolicyError(f"destination already exists: {destination_path}")

    if mode == "bootstrap":
        allowed_sources = _roots(base, registry.get("bootstrap_sources", []))
        if not any(_inside(source_path, item) for item in allowed_sources):
            raise CopyPolicyError("bootstrap source is outside configured bootstrap_sources")
        owner = _project_for(destination_path, base, registry)
        if owner is None:
            raise CopyPolicyError("bootstrap destination is outside configured project_roots")
    elif mode == "generated":
        owner = _project_for(destination_path, base, registry)
        if owner is None or not owner.is_dir():
            raise CopyPolicyError("generated destination is outside configured project_roots")
        allowed = [owner / item for item in registry.get("generated_subpaths", [])]
        if not any(_inside(destination_path, item) for item in allowed):
            raise CopyPolicyError("generated destination is outside generated_subpaths")
        if not _inside(source_path, base):
            raise CopyPolicyError("generated source must remain inside the repository root")
    elif mode == "archive":
        allowed_archives = _roots(base, registry.get("archive_roots", []))
        owner = next((item for item in allowed_archives if _inside(destination_path, item)), None)
        if owner is None:
            raise CopyPolicyError("archive destination is outside archive_roots")
        if not _inside(source_path, base):
            raise CopyPolicyError("archive source must remain inside the repository root")
    elif mode == "bridge":
        raise CopyPolicyError("bridge mode requires a language-specific adapter; use import/run bridge code, not a file copy")
    else:
        raise CopyPolicyError(f"unsupported copy mode: {mode}")

    preview = {
        "applied": False,
        "mode": mode,
        "source": source_path.relative_to(base).as_posix(),
        "destination": destination_path.relative_to(base).as_posix(),
    }
    if not apply:
        return preview
    _copy(source_path, destination_path)
    record = _record(mode, source_path, destination_path, base)
    preview.update({"applied": True, **record, "manifest": _append_manifest(owner, registry, record)})
    return preview


def bootstrap(source: str | Path, destination: str | Path, root: str | Path, registry: dict, apply: bool = False) -> dict:
    """Backward-compatible bootstrap helper."""

    return execute("bootstrap", source, destination, root, registry, apply=apply)
