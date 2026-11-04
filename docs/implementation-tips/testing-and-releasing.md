# Testing and Releasing

Choose verification by the claim being made. Start with the narrowest test that exercises the changed behavior, then run the repository-standard aggregate gate when its cost and effects are appropriate.

## Change-to-Check Map

| Change | Focused evidence |
| --- | --- |
| Markdown skill or shared contract | Link checks, relevant validator assertions, and scenario tests for changed behavior |
| Procedure asset | YAML and graph assertions, owning workflow scenarios, and applicable Podway compatibility tests |
| Inspector or normalizer | Targeted Python unit tests plus matching black-box or approved legacy integration suite |
| Public docs or canonical maintainer docs | Docs inspector where applicable, Ruby validator, and `git diff --check` |
| Release helper or release contract | Targeted helper tests, release scenarios, release-note reconciliation, and exact-candidate QA |

[`TESTING.md`](../../TESTING.md) owns the enrolled stages, frameworks, environment, diagnostics, and waivers. [`Makefile`](../../Makefile) owns their executable composition. Do not convert missing dependencies, failed effects, or stale waivers into successful skips.

## Complete Development Gate

For an ordinary release-affecting implementation candidate, the complete local development gate is `make test`, followed by the relevant diff check. `make test` begins with preparation and may run formatters, so inspect and preserve unrelated work before invoking it. For documentation-only work, use the focused non-writing checks when repository policy says the aggregate gate is disproportionate.

Gaori may summarize noisy test evidence. Its parser status and summary quality do not override the child process exit status or prove that an unsupported framework became supported.

## Release Modes

The release handler establishes `full` or `light` mode before metadata changes. Full mode runs the complete applicable gate. Light mode is restricted to release metadata and requires explicit confirmation of required results for the clean exact candidate after changelog settlement. Every later candidate change requires fresh confirmation or full mode before the next QA pass or metadata step.

Before either mode, reconcile all material changes since the previous release, or the complete reachable history for a confirmed first release, with the open changelog section. After release QA, preserve approved entry text byte-for-byte. A substantive edit creates a new candidate and requires QA again.

The [release target contract](../../plugins/aquarium/skills/release-handler/references/release-orchestration.md)
freezes both repository-defined gate orders without activating them in the current
handler. TASK-174 owns that integration. For gate-before-commit, bind tested bytes
to the actual post-hook tree, metadata delta and release-basis parent. For
commit-before-gate, inspect the clean post-hook release commit first and run the
gate on that commit. A later gate is not due at the commit boundary but remains
globally required before publication. A failed commit-first gate preserves the
unpushed commit and stops before unauthorized history changes.

[Preparation and QA readiness](../../plugins/aquarium/skills/release-handler/references/release-preparation.md)
retain original pre-QA results and exact-SHA light confirmation, including required
prior VM/compatibility evidence. Plan readiness precedes settlement/pre-QA effects;
QA readiness precedes full QA and confirmation claim creation. Verify that the
current assessed manifest path, helper-native canonical digest and unchanged bytes
reach begin unchanged, then check actual claim readback before scenario dispatch.
Keep helper rejection stops and legitimate exact-request recovery distinct.

Review failure paths for handler-called Coordinator self-remediation, stale or
superseded manifest selection, negative readiness before claim creation, missing
actual confirmation and retarget-only requests entering mandatory role dispatch.
Standalone QA and retarget-only heading edits keep their existing boundaries.
These are semantic verification duties; do not encode prose matching as tests.

Do not rerun omitted light checks or claim they ran. Full-mode VM timing follows target
policy. Structural checks and fixture preparation do not establish native role
progression, installed acceptance or user acceptance. TASK-175 prepares scenarios
and the bounded installed startup case; TASK-176 observes the exact candidate
in the dedicated UTM environment. Current post-QA release steps and gate-convergence
instructions remain authoritative pending TASK-174 integration. Finish active
releases with their installed workflow before updating.

Publication is ordered: commit, push `main`, create and push the annotated tag, create the GitHub Release, then re-observe remote `main`, the peeled tag, and the release. Recovery may skip the push when a fresh ancestry check proves that remote main includes the release commit, subject to repository policy; tag and Release targets remain the original release SHA. Local success never proves distribution readiness. Opening the next empty `Unreleased` section is a separate post-release change with separate approval.
