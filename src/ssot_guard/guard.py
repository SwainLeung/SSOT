"""Registry-driven SSOT copy, boundary, and manifest-drift detection."""

from __future__ import annotations

import fnmatch
import json
import os
from dataclasses import dataclass
from pathlib import Path

from .hashing import file_hash, tree_hash


DEFAULT_SKIP_DIRECTORIES = {".git", ".venv", "node_modules", "__pycache__", ".ssot"}


@dataclass(frozen=True)
class Finding:
    code: str
    path: Path
    source: Path | None
    message: str


def _inside(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _files(root: Path, patterns: list[str], skip: set[str]):
    if not root.is_dir():
        return
    for current, directories, filenames in os.walk(root, topdown=True):
        directories[:] = [name for name in directories if name not in skip]
        current_path = Path(current)
        for filename in filenames:
            if any(fnmatch.fnmatch(filename, pattern) for pattern in patterns):
                yield current_path / filename


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("registry must be a JSON object")
    return value


def _root_paths(base: Path, patterns: list[str]) -> list[Path]:
    result: list[Path] = []
    for pattern in patterns:
        for path in base.glob(str(pattern)):
            if path.is_dir():
                result.append(path.resolve())
    return sorted(set(result), key=lambda item: str(item).lower())


def _project_roots(base: Path, registry: dict) -> list[Path]:
    patterns = registry.get("project_roots") or registry.get("target_roots", [])
    return _root_paths(base, [str(item) for item in patterns])


def _skip(registry: dict) -> set[str]:
    configured = registry.get("scan", {}).get("skip_directories", DEFAULT_SKIP_DIRECTORIES)
    return {str(item) for item in configured}


def _canonical_index(base: Path, rule: dict, skip: set[str]) -> dict[str, list[tuple[Path, str]]]:
    source_root = base / str(rule.get("source", ""))
    patterns = [str(item) for item in rule.get("patterns", [])]
    index: dict[str, list[tuple[Path, str]]] = {}
    for source in _files(source_root, patterns, skip) or ():
        try:
            index.setdefault(source.name, []).append((source, file_hash(source)))
        except OSError:
            continue
    return index


def _exact_copy_findings(base: Path, registry: dict, projects: list[Path], skip: set[str]) -> list[Finding]:
    findings: list[Finding] = []
    for rule in registry.get("guard_rules", []):
        index = _canonical_index(base, rule, skip)
        patterns = [str(item) for item in rule.get("patterns", [])]
        for project in projects:
            for candidate in _files(project, patterns, skip) or ():
                for source, source_digest in index.get(candidate.name, []):
                    try:
                        same = file_hash(candidate) == source_digest
                    except OSError:
                        same = False
                    if same:
                        findings.append(Finding(
                            "ssot-duplicate",
                            candidate,
                            source,
                            str(rule.get("message", "Canonical file copied into a project")),
                        ))
                        break
    return findings


def _allowed_source(base: Path, mode: str, source: Path, registry: dict) -> bool:
    if mode == "bootstrap":
        roots = [base / item for item in registry.get("bootstrap_sources", [])]
        return any(_inside(source, root) for root in roots)
    return _inside(source, base)


def _manifest_findings(base: Path, registry: dict, projects: list[Path]) -> list[Finding]:
    findings: list[Finding] = []
    manifest_config = registry.get("manifest", {})
    manifest_name = str(manifest_config.get("filename", "copy-manifest.json"))
    for project in projects:
        manifest = project / str(manifest_config.get("directory", ".ssot")) / manifest_name
        if not manifest.is_file():
            continue
        try:
            value = json.loads(manifest.read_text(encoding="utf-8"))
            entries = value["entries"]
            if not isinstance(entries, list):
                raise ValueError("entries must be a list")
        except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
            findings.append(Finding("manifest-invalid", manifest, None, str(exc)))
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                findings.append(Finding("manifest-invalid", manifest, None, "manifest entry must be an object"))
                continue
            try:
                mode = str(entry["mode"])
                source = (base / str(entry["source"])).resolve()
                destination = (base / str(entry["destination"])).resolve()
                source_hash = str(entry["source_sha256"])
                destination_hash = str(entry["destination_sha256"])
            except KeyError as exc:
                findings.append(Finding("manifest-invalid", manifest, None, f"missing field: {exc.args[0]}"))
                continue
            if not _allowed_source(base, mode, source, registry):
                findings.append(Finding("manifest-source-boundary", manifest, source, "manifest source is outside the allowed source boundary"))
            if not _inside(destination, project) and mode not in {"archive"}:
                findings.append(Finding("manifest-destination-boundary", manifest, source, "manifest destination is outside its project"))
            if not source.exists():
                findings.append(Finding("manifest-source-missing", manifest, source, "manifest source no longer exists"))
            else:
                try:
                    if tree_hash(source) != source_hash:
                        findings.append(Finding("manifest-source-drift", manifest, source, "canonical source hash changed"))
                except OSError as exc:
                    findings.append(Finding("manifest-source-unreadable", manifest, source, str(exc)))
            if not destination.exists():
                findings.append(Finding("manifest-destination-missing", manifest, source, "copied destination no longer exists"))
            else:
                try:
                    if tree_hash(destination) != destination_hash:
                        findings.append(Finding("manifest-destination-drift", destination, source, "copied destination changed after the recorded operation"))
                except OSError as exc:
                    findings.append(Finding("manifest-destination-unreadable", destination, source, str(exc)))
    return findings


def scan(base: str | Path, registry_path: str | Path) -> list[Finding]:
    root = Path(base).resolve()
    registry_path = Path(registry_path).resolve()
    registry = _load(registry_path)
    projects = _project_roots(root, registry)
    skip = _skip(registry)
    findings = _exact_copy_findings(root, registry, projects, skip)
    findings.extend(_manifest_findings(root, registry, projects))
    return sorted(findings, key=lambda item: (str(item.path).lower(), item.code))
