"""Stable file and tree hashing used by the guard and copy policy."""

from __future__ import annotations

import hashlib
from pathlib import Path


HASH_SKIP_DIRECTORIES = {".git", ".ssot", "__pycache__"}


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tree_hash(path: Path) -> str:
    digest = hashlib.sha256()
    if path.is_file():
        files = [path]
    else:
        files = sorted(
            item for item in path.rglob("*")
            if item.is_file() and not any(part in HASH_SKIP_DIRECTORIES for part in item.relative_to(path).parts)
        )
    for item in files:
        relative = item.name if path.is_file() else item.relative_to(path).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(file_hash(item).encode("ascii"))
    return digest.hexdigest()
