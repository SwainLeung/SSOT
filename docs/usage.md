# Usage

## Check a repository

```powershell
python scripts/ssot-guard.py --registry config/ssot-registry.json
```

The command is read-only and exits non-zero when a target project contains an exact copy of a canonical file covered by the registry.

It also validates every `.ssot/copy-manifest.json` under registered projects. A non-zero result means a source, destination, hash, or boundary no longer matches the recorded operation.

## Bootstrap a project

```powershell
python scripts/ssot-copy.py `
  --mode bootstrap `
  --source canonical/templates `
  --destination projects/example
```

Review the JSON preview. Apply only after review:

```powershell
python scripts/ssot-copy.py `
  --mode bootstrap `
  --source canonical/templates `
  --destination projects/example `
  --apply
```

The tool records source and destination paths, a deterministic source hash, and a timestamp in `projects/example/.ssot/copy-manifest.json`.

## Other copy modes

- `generated`: destination must be under a configured generated subpath such as `build/data` or `build/temp`.
- `archive`: destination must be under a configured archive root such as `backups` or `audits`.
- `reference`: always blocked because it is not a copy operation.
- `bridge`: intentionally blocked by the generic copier; create a small language-specific adapter that imports or invokes the canonical source.

Every applied operation records both `source_sha256` and `destination_sha256`. The guard detects drift on the next run.
