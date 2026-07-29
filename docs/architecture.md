# Architecture

## Ownership model

Every reusable artifact belongs to exactly one canonical root. Projects may consume it through imports, commands, generated output, or a small bridge. A project must not silently become a second owner through copying.

```text
canonical/       authoritative reusable material
projects/        project-specific identity and content
backups/         historical recovery material
audits/          review evidence and manifests
```

## Copy decision

1. Is the material reusable across projects? Put it under `canonical/`.
2. Is it project identity, content, or state? Keep it under that project.
3. Is it generated and reproducible? Put it under the configured generated subpath.
4. Is it historical evidence? Put it under `backups/` or `audits/`.
5. Otherwise, stop and classify it before copying.

## Enforcement layers

- Registry: declares ownership and allowed destinations.
- Guard: detects exact canonical copies in target projects.
- Copy tool: permits only approved bootstrap copies and records provenance.
- GitHub Actions: runs tests and the guard on every change.
- Human review: confirms public-release privacy and scope.
