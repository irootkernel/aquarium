# Production Setup Status Operations

`aquarium-status` owns the user-private setup ledger at
`~/.aquarium/status.yaml`. It supports Apple Silicon macOS with Python 3.11 or
newer. The ledger records terminal setup history; it is not repository authority
or a live tool-health check. The local operator owns routine diagnosis and
approved recovery; an Aquarium maintainer owns defects in the shipped contract
or installer.

## Diagnose and report

Run the global inspector with `--component aquarium-status` to inspect the
bundled and installed identities, selector, dependency tree, and launcher without
changing them. Run `aquarium-status show --format json` for a local-only report.
Add `--refresh` only after authorizing the documented GitHub latest-Release read,
or `--source-root` for one explicitly selected Aquarium checkout.

An absent ledger is healthy empty state. A partial report preserves valid rows
and names optional observations that failed. Unsafe owned paths or a corrupt
ledger fail closed. Do not edit the YAML or infer live readiness from a recorded
successful attempt.

## Install, update, or repair the runtime

Use `$aquarium:dev-setup-global` and approve the exact action separately. The
bundled installer contacts only PyPI's simple index and wheel host for the
hash-pinned PyYAML 6.0.3 binary wheel. It prepares and verifies a private
generation before atomically selecting it and installing the launcher. A failed
preparation leaves the previous runtime untouched; a failed activation restores
the prior selector and launcher. An unknown regular launcher is never replaced
automatically.

## Recover a recording failure

A successful setup remains successful if status recording fails. Use only the
returned closed `retry_request` with `aquarium-status record`; do not rerun setup
mutations. An exact replay of the current last attempt is a no-change success.
A stale revision, changed payload, or replay after a newer attempt is a conflict
that requires a fresh setup decision rather than request editing.

## Forget one row

Invoke `$aquarium:status`, inspect one exact row, and approve its displayed root,
file revision, row revision, and digest. The skill re-reads the ledger before
calling `forget` with every precondition. Any intervening change invalidates the
approval. Forgetting removes only local history; it does not delete a checkout,
change enrollment, uninstall tools, or modify Git.

## Escalate

Stop local recovery and escalate to an Aquarium maintainer when a verified
managed runtime cannot be classified, repair cannot preserve the prior selector
and launcher, valid ledger bytes are rejected, or the documented record/replay
contract produces inconsistent revisions. Escalate unsafe or unknown owned
paths to the local operator first because resolving or removing user-owned state
requires an explicit decision. Include only bounded error envelopes, versions,
and relative component names; do not attach ledger contents or absolute local
paths unless the owner explicitly requests them through an approved private
channel.
