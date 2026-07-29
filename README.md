# SSOT Governance

A small, repository-friendly toolkit for enforcing the Single Source of Truth (SSOT) principle.

It separates canonical sources from generated output, bootstrap copies, bridges, and archives. The goal is simple: reusable code and documentation have one owner; consumers reference that owner instead of creating silent copies.

## What this repository provides

- A registry describing canonical roots, target roots, and allowed copy modes.
- A read-only guard that detects exact copies of SSOT-owned files inside target projects.
- Manifest validation for source drift, destination drift, missing artifacts, and boundary violations.
- A controlled copier for `bootstrap`, `generated`, and `archive` modes that records source and destination hashes.
- A governance report command suitable for local review and CI.
- Unit tests and GitHub Actions CI.

## Quick start

```powershell
python scripts/ssot-guard.py --registry config/ssot-registry.json
python scripts/ssot-report.py --registry config/ssot-registry.json
python -m unittest discover -s tests -v
python scripts/ssot-copy.py --mode bootstrap --source canonical/templates --destination projects/example
```

The copy command is a dry-run by default. Add `--apply` only after reviewing its JSON plan.

Enable the versioned local hook with:

```powershell
git config core.hooksPath .githooks
```

## SSOT rules

| Mode | Meaning | Typical destination |
|---|---|---|
| `reference` | Import or call the canonical source; do not copy it | Any project |
| `bootstrap` | One-time generation from an approved template | A new project |
| `generated` | Derived output that can be regenerated | `projects/*/build/data` or `build/temp` |
| `bridge` | Small adapter that points to the canonical implementation; never a full copy | Project adapter directory |
| `archive` | Historical evidence, not an active source | `backups` or `audits` |

## Public-repository boundary

This repository intentionally contains only generic tooling and examples. Do not add:

- credentials, API keys, tokens, cookies, or private certificates;
- real domains, emails, server addresses, customer data, or unpublished content;
- local absolute paths, private repository URLs, backups, audit exports, or site directories;
- generated project data that is not required to test the toolkit.

Before publishing, run the checklist in [CHECKLIST.md](CHECKLIST.md).

## License

MIT. See [LICENSE](LICENSE).
