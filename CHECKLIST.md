# Public Repository Checklist

Run this checklist before giving the repository URL to the owner for public GitHub setup.

## Content boundary

- [ ] No real domain names, site names, emails, usernames, server addresses, or private URLs.
- [ ] No credentials, API keys, tokens, cookies, certificates, or authentication headers.
- [ ] No site content, drafts, vaults, exports, screenshots, backups, audit dumps, or customer data.
- [ ] No local machine paths such as `C:\...`, `D:\...`, home directories, or workspace identifiers.
- [ ] No private repository names, remotes, commit messages, or personal account identifiers.

## Repository quality

- [ ] `README.md` explains scope, setup, copy modes, and the public boundary.
- [ ] `CHANGELOG.md` records the initial release.
- [ ] `LICENSE` is present and appropriate.
- [ ] `config/ssot-registry.json` contains only generic paths and rules.
- [ ] `.gitignore` excludes secrets, local manifests, caches, and build output.
- [ ] Tests pass with `python -m unittest discover -s tests -v`.
- [ ] `python scripts/ssot-guard.py --registry config/ssot-registry.json` exits cleanly.

## GitHub handoff

- [ ] No remote has been added until the repository owner provides the destination URL.
- [ ] No push or public visibility change has been performed by this preparation step.
- [ ] Review `git status --short` and `git diff --cached --check` before the first push.
