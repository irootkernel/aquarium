# Orca Review Supervision

This is the execution backend for `$aquarium:orca-review`. Review semantics belong to [review-contract.md](review-contract.md); Orca owns only its native Run, Task, Dispatch, reviewer, Delivery, acknowledgement, settlement, and recovery lifecycle.

Require the separately installed `$orca-cli` skill. Resolve one Orca command exactly as that skill requires, load its version-matched `orca-cli` and `orchestration` guides, and confirm a ready local runtime. Reject nonempty `ORCA_ENVIRONMENT` or `ORCA_PAIRING_CODE`; do not route review source to a paired or remote runtime.

Use the original registered checkout and its proven `current` worktree. Do not create or register a temporary repository, copied checkout, snapshot, or another Git worktree. The declared target and included paths define reviewer scope; current worktree bytes outside that target are excluded even though the same operating-system user can technically read them.

Require the user to select a reviewer before creating the Run or Task. Then start one fresh requested reviewer through the live guide's supervised `worker-start --task <task-id> --worktree current --agent <requested-reviewer>` path. Use `--agent claude` when Claude is requested. Do not default to or substitute another reviewer. Do not reuse a terminal, create a low-level provider terminal, or use Dolgorae.

The Task contains the complete Review Brief defined by
[review-intent-contract.md](review-intent-contract.md), including the purpose,
actual criteria, checkpoint, source basis, candidate boundary, included and
excluded state, verification provenance, and requested result. Do not include
suspected findings or intended fixes. Do not create a capture manifest, target
digest binding, repository fingerprint, or pre/post state comparison.

Every Dispatch, regardless of target, carries that complete Review Brief and the
purpose-specific result defined by [review-contract.md](review-contract.md).
Tell the reviewer that this is review only. Prohibit creating, editing,
deleting, moving, formatting, or generating source files or other tracked or
non-ignored files in the current registered worktree; changes to the Git index,
refs, configuration, or commits; and tests, builds, formatters, installers,
authentication, or unrelated network operations.

Require actionable target findings with severity, scenario, violated authority,
impact, and evidence. Use exact `path:line` evidence when implementation exists.
A supported omission instead cites the requirement, expected location, and
inspected evidence without inventing a line. For `completion`, require one
`met`, `unmet`, `unverified`, or `not-applicable` assessment for every applicable
criterion, with evidence provenance and remaining gaps. For `change`, require an
explicit statement that whole-work-unit completion was not assessed.

Treat only the declared target as candidate evidence. The reviewer may read its
relevant files plus the unchanged context and approved authority sources needed
to judge the brief. Unstaged or current-worktree authority bytes do not replace
a declared HEAD or other revision basis. Do not broaden into unrelated
current-worktree inspection. For `head`, `commit`, and `range`, require candidate
content and diffs from the resolved revisions through read-only Git commands and
prohibit substituting current index or worktree bytes.

For `change`, require the proportional inspection defined by
[review-contract.md](review-contract.md#proportional-change-inspection). Start
with the exact diff and changed implementation, and expand into unchanged
callers, contracts, tests, or dependents only along a plausible affected path.
Do not inventory callers, inspect adjacent modules for other defects, or spend
remaining time on a broader audit. Omit pre-existing issues that the target does
not introduce, worsen, or make newly reachable. Require the reviewer to return
the result as soon as the intended effect and plausible affected paths have been
assessed and no evidence-backed concern remains. Do not apply this stopping rule
to `completion` criterion coverage.

Require an advisory technical conclusion and separate reporting of operational
deviations under [the shared policy](review-contract.md#orca-operational-deviations).
Advisory `APPROVE` means the reviewer found no actionable target findings in the
evidence it could assess; require disclosure of any known compromise or
uncertainty. Tell the reviewer to deliver that result and complete its required
native lifecycle without waiting for or certifying the coordinator's later
settlement. Only the coordinator issues the final technical verdict.

For `staged`, additionally require inspection of `git diff --cached` and the relevant staged files, plus only the unchanged context required by the proportional `change` rule or the applicable `completion` criteria. Apply the corresponding target-specific read instructions to `head`, `commit`, and `range` without weakening the common restrictions.

Include the shared output permission in every Dispatch: All Orca reviewers may create or update review-related temporary files, native session state, tool output, and reports outside the current registered worktree or in Git-ignored runtime paths within it, such as ignored files under `.omc/`. `/tmp`, `/private/tmp`, `$TMPDIR`, and `~/.claude` are external examples, not an allowlist. This permission does not cover tracked files, non-ignored worktree files, or changes to Git state, including through symbolic links.

Include this distinction in every Dispatch: External tool output and reports may contain bytes of the declared target, including redirected `git diff --cached` or `git show` output read in pieces. These files are review aids; they do not replace the live index or resolved Git revisions as target authority.

Tell the reviewer to return the complete result through the Orca lifecycle message when it fits. Any reviewer may deliver a large report through external files with a concise lifecycle result and the paths of retained report files used to deliver the result. Read those reports before adjudication. Routine temporary files need no inventory. Aquarium does not automatically remove reviewer-owned files or treat them as repository state, capture evidence, or lifecycle authority. Permitted external review files and Git-ignored runtime files alone must not trigger a warning, an operational deviation, an approval request, additional checks, a withheld verdict, or another review.

Use event-driven waits for `worker_done`, `escalation`, and `question`, with a cumulative 30-minute default liveness budget and a user update at least once per minute. A checkpoint timeout inside the budget is not failure. At budget exhaustion inspect authoritative worker state once, keep an active or unproven worker intact, and require explicit user direction for more waiting or cancellation.

After one accepted `worker_done`, read the complete authoritative transcript, settle the worker through the current guide, process the complete Delivery, and acknowledge it only after required release or retention succeeds. Follow the live guide's current recovery and FIFO rules rather than duplicating a fixed batch-drain protocol here. Never retry, replace, switch reviewer, release an active worker, or turn backend failure, incomplete settlement, or compromised or unproven review guarantees into a final technical verdict. Assess other observed deviations under [the shared policy](review-contract.md#orca-operational-deviations).

## Output adjudication examples

External-path examples assume the declared worktree is elsewhere. File location does not replace finding adjudication or Orca lifecycle checks.

| Scenario | Required treatment |
| --- | --- |
| Claude writes tool output under `/tmp` or `/private/tmp`. | Allow it without an output-location warning or failure. |
| A reviewer redirects `git diff --cached` or `git show` into an external file and reads it in pieces. | Allow it as a review aid containing declared target bytes; the live index or resolved revisions remain authoritative. |
| Another requested reviewer writes a report under an external `$TMPDIR` or provider-owned directory. | Read the returned report and apply the same verdict rules as for Claude. |
| A reviewer writes scratch files in another external directory. | Allow it; the example paths are not an allowlist. |
| Claude updates Git-ignored runtime files under `.omc/` in the current worktree. | Allow it without warnings, approval requests, runtime-file inventories, or pre/post comparisons. |
| A reviewer creates a report or temporary file in another Git-ignored runtime path inside the current worktree. | Apply the same permission as for ignored `.omc/` files. |
| A reviewer modifies a tracked file under `.omc/` or writes a non-ignored worktree file. | Treat it as a worktree-write violation; a directory name alone does not grant permission. |
| An external path follows a symbolic link to a tracked or non-ignored worktree file. | Treat the actual write as a worktree-write violation. |
| External files exist, the complete result has no actionable findings, and the Orca lifecycle is authoritative. | Permit `APPROVE` without an output-location warning or another review. |
| An external report needed for the result is missing, or the Orca lifecycle is incomplete. | Report the missing output or lifecycle evidence; do not return `APPROVE`. |

## Operational deviation examples

Apply [Orca operational deviations](review-contract.md#orca-operational-deviations) to the complete available evidence. These examples describe how to report an observed violation; they do not permit the action or authorize another review.

| Scenario | Required treatment |
| --- | --- |
| A reviewer violates a report-format or delivery-order instruction, but the complete result and all review guarantees are established. | Report target findings first, decide the technical verdict from those findings, and report the instruction violation separately. Technical `APPROVE` does not imply instruction compliance. |
| A reviewer finds no actionable target findings and is ready to deliver its result before coordinator settlement. | Return advisory `APPROVE` with any observed deviations or uncertainty and complete the required native lifecycle. The coordinator decides the final verdict after settlement and acknowledgement; pending settlement alone does not block the reviewer's report. |
| A reviewer runs a prohibited test, but existing authorized evidence establishes that all review guarantees remain intact. | Report the test execution as a deviation. Exclude its results from the static technical verdict and decide that verdict from adjudicated target findings. |
| The side effects of a prohibited test or command cannot be established from existing authorized evidence. | Withhold the final technical verdict and identify the missing evidence. Do not launch checks or create a snapshot to fill the gap. |
| A reviewer changes the target or Git state, reviews a different target, or does not match the requested identity. | Withhold the final technical verdict and identify the compromised guarantee. Report only findings supported by the available evidence. |
| Required output is missing, the backend fails, or lifecycle settlement is incomplete. | Withhold the final technical verdict and report the output or native lifecycle failure. Follow Orca's existing recovery rules. |
| A reviewer creates a permitted external report and all review guarantees hold. | Apply the normal technical verdict rules without a deviation warning. |
