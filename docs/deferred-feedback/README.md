# Deferred Feedback

This index owns small actionable findings intentionally postponed from current work. It is not a second roadmap, completion history, or runtime evidence store.

## DF-001: Harden release confirmation evidence and attempt integrity

- Actionable issue: `release-qa` must bind final confirmation to an immutable exact claim and frozen attempt record, pair every finding with its exact scenario, consume confirmation claims once, and return structured errors for rejected or inconsistent evidence.
- Owner: `release-qa`.
- Reason for deferral: the finding is independent of EPIC-003 review activation and does not affect its candidate, capture, supervision, or settlement correctness.
- Re-entry condition: resolve before the next release QA confirmation and cover replacement, replay, finding-scenario mismatch, and rejected-evidence diagnostics with focused tests.

## DF-002: Replace the forgeable commit-gate authorization marker

- Actionable issue: the task commit gate accepts a caller-controlled environment marker and can be bypassed when Git is invoked through another shell interpreter, so it does not independently prove that the authorized commit workflow owns the commit.
- Owner: `task-commit` and its repository hook contract.
- Reason for deferral: the finding is independent of EPIC-003 runtime review correctness and does not change the isolated committed bytes or their verification.
- Re-entry condition: resolve before relying on the gate as an enforcement boundary by replacing the marker with authenticated workflow evidence and failing closed across supported shell invocation paths.

## DF-003: Delay new-project test setup until a testable foundation exists

- Actionable issue: `new-project` can place its required testing-foundation work unit first while a greenfield repository still contains only planning documents. Sequence that work after the language, toolchain, root test authority, and minimum executable public behavior exist: use the final task of EPIC-001 when that epic delivers a testable walking skeleton, otherwise place it immediately after the earliest vertical slice and before broader feature expansion. Make `test-setup` stop without creating empty handlers, placeholder tests, or a documentation-only facade when those prerequisites are absent.
- Owner: `new-project` and `test-setup`.
- Reason for deferral: the issue affects future greenfield roadmap quality but is independent of the current Aquarium implementation and active delivery work, so its contract and focused coverage can be changed separately.
- Re-entry condition: resolve before the next greenfield `$aquarium:new-project` roadmap is adopted, with focused cross-skill coverage for documentation-only, EPIC-001 walking-skeleton, and later-vertical-slice scenarios.

## DF-004: Restore successful Podway workspace-removal replay

- Actionable issue: the official Podway v0.2.8 CLI resolves the deleted workspace configuration before reaching the daemon's `already_absent` path, so an identical post-success UUID-fenced replay returns nonretryable `WORKSPACE_CONFIG_INVALID` even though Podway's ADR, IPC schema, and daemon tests define `already_absent=true` convergence.
- Owner: the Podway compatibility gate and integration documentation.
- Reason for deferral: the first exact fenced removal succeeds, and Aquarium independently verifies that the isolated registry entry and `.podway` tree are absent while the Git worktree is preserved. The bounded v0.2.8 exception therefore does not weaken the initial destructive mutation boundary.
- Re-entry condition: when an official Podway v0.2.9 artifact is available, require the replay to return `podway.workspace-removal-result/v1` with a null workspace UUID, `registry_entry_removed=false`, `podway_directory_removed=false`, and `already_absent=true`; then remove the v0.2.8 exception and its v4 error-terminal assertions and documentation.
