import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ssot_guard import execute, scan
from ssot_guard.copy_policy import bootstrap


class GuardTests(unittest.TestCase):
    def test_exact_canonical_copy_is_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "canonical/shared").mkdir(parents=True)
            (root / "projects/example").mkdir(parents=True)
            (root / "canonical/shared/tool.py").write_text("CANONICAL = True\n", encoding="utf-8")
            (root / "projects/example/tool.py").write_text("CANONICAL = True\n", encoding="utf-8")
            registry = root / "registry.json"
            registry.write_text(json.dumps({
                "target_roots": ["projects"],
                "guard_rules": [{
                    "id": "shared-code",
                    "source": "canonical/shared",
                    "patterns": ["*.py"],
                    "message": "use the canonical source",
                }],
            }), encoding="utf-8")
            findings = scan(root, registry)
            self.assertEqual(len(findings), 1)

    def test_different_bridge_content_is_allowed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "canonical/shared").mkdir(parents=True)
            (root / "projects/example").mkdir(parents=True)
            (root / "canonical/shared/tool.py").write_text("CANONICAL = True\n", encoding="utf-8")
            (root / "projects/example/tool.py").write_text("from canonical.shared.tool import *\n", encoding="utf-8")
            registry = root / "registry.json"
            registry.write_text(json.dumps({
                "target_roots": ["projects"],
                "guard_rules": [{"id": "shared-code", "source": "canonical/shared", "patterns": ["*.py"]}],
            }), encoding="utf-8")
            self.assertEqual(scan(root, registry), [])

    def test_manifest_destination_drift_is_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "canonical/templates"
            source.mkdir(parents=True)
            (source / "README.md").write_text("canonical\n", encoding="utf-8")
            registry = {
                "target_roots": ["projects"],
                "project_roots": ["projects/*"],
                "bootstrap_sources": ["canonical/templates"],
                "guard_rules": [],
                "manifest": {"directory": ".ssot", "filename": "copy-manifest.json"},
            }
            destination = root / "projects/example"
            bootstrap(source, destination, root, registry, apply=True)
            (destination / "README.md").write_text("changed\n", encoding="utf-8")
            findings = scan(root, root / "registry.json") if (root / "registry.json").exists() else []
            if not findings:
                registry_path = root / "registry.json"
                registry_path.write_text(json.dumps(registry), encoding="utf-8")
                findings = scan(root, registry_path)
            self.assertTrue(any(item.code == "manifest-destination-drift" for item in findings))
