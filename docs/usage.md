# Usage

## Check a repository

```powershell
python scripts/ssot-guard.py --registry config/ssot-registry.json
```

The command is read-only and exits non-zero when a target project contains an exact copy of a canonical file covered by the registry.

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
