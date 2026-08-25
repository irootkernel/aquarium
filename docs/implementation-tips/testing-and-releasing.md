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

The release handler establishes `full` or `light` mode before metadata changes. Full mode runs the complete applicable gate. Light mode is restricted to release metadata and requires explicit confirmation of required results for the exact current HEAD; any later functional change invalidates that confirmation.

Before either mode, reconcile all material changes since the previous release with the open changelog section. After release QA, preserve approved entry text byte-for-byte. A substantive edit creates a new candidate and requires QA again.

Publication is ordered: commit, push `main`, create and push the annotated tag, create the GitHub Release, then re-observe remote `main`, the peeled tag, and the release. Local success never proves distribution readiness. Opening the next empty `Unreleased` section is a separate post-release change with separate approval.
