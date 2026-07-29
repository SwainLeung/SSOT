import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ssot_guard import scan


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
