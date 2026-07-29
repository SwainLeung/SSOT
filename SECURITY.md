# Security Policy

Do not report or commit secrets in issues, pull requests, fixtures, logs, or examples.

If sensitive material is found in a working copy:

1. Remove it from active files immediately.
2. Revoke or rotate the affected credential.
3. Check Git history and remove the secret from reachable history using the repository owner's approved process.
4. Report the incident privately to the repository owner.

The SSOT guard checks file ownership and hashes. It is not a secret scanner and does not replace credential rotation or a dedicated secret-scanning service.
