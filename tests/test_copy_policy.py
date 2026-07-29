import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ssot_guard.copy_policy import CopyPolicyError, bootstrap, execute


class CopyPolicyTests(unittest.TestCase):
    def registry(self):
        return {"target_roots": ["projects"], "bootstrap_sources": ["canonical/templates"]}

    def test_bootstrap_is_dry_run_by_default_and_records_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "canonical/templates"
            source.mkdir(parents=True)
            (source / "README.md").write_text("generic\n", encoding="utf-8")
            destination = root / "projects/example"
            preview = bootstrap(source, destination, root, self.registry())
            self.assertFalse(preview["applied"])
            result = bootstrap(source, destination, root, self.registry(), apply=True)
            self.assertTrue(result["applied"])
            self.assertTrue((destination / ".ssot/copy-manifest.json").is_file())
            json.loads((destination / ".ssot/copy-manifest.json").read_text(encoding="utf-8"))

    def test_noncanonical_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "random/file.txt"
            source.parent.mkdir(parents=True)
            source.write_text("generic\n", encoding="utf-8")
            with self.assertRaises(CopyPolicyError):
                bootstrap(source, root / "projects/example", root, self.registry())

    def test_reference_mode_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "canonical/shared/tool.py"
            source.parent.mkdir(parents=True)
            source.write_text("generic\n", encoding="utf-8")
            with self.assertRaises(CopyPolicyError):
                execute("reference", source, root / "projects/example/tool.py", root, self.registry())

    def test_generated_mode_requires_generated_subpath(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "projects/example"
            (project / "build/data").mkdir(parents=True)
            source = root / "input.txt"
            source.write_text("generated\n", encoding="utf-8")
            registry = {**self.registry(), "generated_subpaths": ["build/data", "build/temp"]}
            result = execute("generated", source, project / "build/data/output.txt", root, registry, apply=True)
            self.assertTrue(result["applied"])
            self.assertTrue((project / ".ssot/copy-manifest.json").is_file())

    def test_archive_mode_requires_archive_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "input.txt"
            source.write_text("archive\n", encoding="utf-8")
            registry = {**self.registry(), "archive_roots": ["backups"]}
            result = execute("archive", source, root / "backups/run/input.txt", root, registry, apply=True)
            self.assertTrue(result["applied"])
