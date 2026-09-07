# Deferred Feedback

This index owns small actionable findings intentionally postponed from current work. It is not a second roadmap, completion history, or runtime evidence store.

## DF-002: Replace the forgeable commit-gate authorization marker

- Actionable issue: the task commit gate accepts a caller-controlled environment marker and can be bypassed when Git is invoked through another shell interpreter, so it does not independently prove that the authorized commit workflow owns the commit.
- Owner: `task-commit` and its repository hook contract.
- Reason for deferral: the finding is independent of EPIC-003 runtime review correctness and does not change the isolated committed bytes or their verification.
- Re-entry condition: resolve before relying on the gate as an enforcement boundary by replacing the marker with authenticated workflow evidence and failing closed across supported shell invocation paths.

## DF-004: Restore successful Podway workspace-removal replay

- Actionable issue: the official Podway v0.2.8 CLI resolves the deleted workspace configuration before reaching the daemon's `already_absent` path, so an identical post-success UUID-fenced replay returns nonretryable `WORKSPACE_CONFIG_INVALID` even though Podway's ADR, IPC schema, and daemon tests define `already_absent=true` convergence.
- Owner: the Podway compatibility gate and integration documentation.
- Reason for deferral: the first exact fenced removal succeeds, and Aquarium independently verifies that the isolated registry entry and `.podway` tree are absent while the Git worktree is preserved. The bounded v0.2.8 exception therefore does not weaken the initial destructive mutation boundary.
- Remaining qualification: the v0.2.9 compatibility implementation removes the v0.2.8 exception and requires `podway.workspace-removal-result/v1` with a null workspace UUID, `registry_entry_removed=false`, `podway_directory_removed=false`, and `already_absent=true`. Run the official checksum-verified artifact against the clean committed Aquarium candidate before removing this entry. The v5 receipt must prove successful replay and preserved Git worktree state; unit tests alone do not close this finding.

## DF-005: Separate non-output operational deviations from target findings

- Actionable issue: define how `orca-review` reports non-output operational deviations when target scope and integrity, repository state, reviewer identity, result completeness, and lifecycle settlement remain trustworthy. Report adjudicated target findings first and record those deviations separately; block the technical verdict when a deviation makes those guarantees untrustworthy.
- Owner: `orca-review`, the shared static review contract, and Orca supervision reporting.
- Reason for deferral: this remaining reporting policy concerns non-output deviations and is independent of the external review-file permission contract. Permitted external output is outside this item's scope.
- Re-entry condition: address when a concrete non-output deviation demonstrates misleading verdict reporting, or before adopting a general operational-deviation reporting policy. Cover both harmless deviations and violations that invalidate target integrity or authoritative settlement.
