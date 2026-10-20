# Fixture roadmap

This file owns fixture work identity and lifecycle. The operator selects the
bounded work and supplies actual workflow approvals. These entries are initial
inputs, without recorded execution or acceptance.

## Lifecycle

| Status | Meaning |
| --- | --- |
| Planned | Adopted but implementation has not started |
| In Progress | Implementation is active |
| In Review | Implementation is complete and acceptance evidence is under review |
| Completed | The work unit passed its explicit acceptance and closeout |
| Deferred | Adopted work is intentionally postponed with a re-entry condition |
| Cancelled | Adopted work is withdrawn; its ID and decision remain recorded |
| Blocked | Progress cannot continue until a named condition changes |

`EPIC-000` stays `In Progress` and is never closed; each member task has its own
lifecycle.

## Epic summary

| Epic | Title | Status |
| --- | --- | --- |
| EPIC-000 | Independent tasks | In Progress |
| EPIC-001 | Extend text export | Planned |

## EPIC-000: Independent tasks

**Status:** `In Progress`

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-001 | Add optional label uppercasing | Add keyword-only `uppercase=False` to `normalize_label`; true uppercases the existing normalized result, while false preserves all current behavior. Update the canonical policy and affected guide before review. | Planned | None |

## EPIC-001: Extend text export

**Status:** `Planned`

Add optional output repetition, then move the existing export feature to a
different directory depth. Keep the two members' canonical contract, architecture,
tests and applicable guidance consistent through review and Epic integration.
The two behavior and move requirements fit this bounded roadmap scope; no
separate execution dossier is needed.

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-002 | Add optional export repetition | Add keyword-only `repeat=1` to `render_lines`; emit each label `repeat` times in input order, zero produces empty output and negative values raise `ValueError`. Keep the default unchanged and update its exact contract and affected guide before review. | Planned | None |
| TASK-003 | Move the export feature | Move `src/exports` to `src/output/text`, preserving existing instructions and contract; rebase links and imports, update architecture and keep all repeat behavior. This move does not expand directory-guide adoption coverage. | Planned | TASK-002 |
