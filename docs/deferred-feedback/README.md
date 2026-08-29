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
