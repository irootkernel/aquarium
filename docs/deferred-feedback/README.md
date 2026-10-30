# Deferred Feedback

This index owns small actionable findings intentionally postponed from current work. It is not a second roadmap, completion history, or runtime evidence store.

## DF-002: Replace the forgeable commit-gate authorization marker

- Actionable issue: the task commit gate accepts a caller-controlled environment marker and can be bypassed when Git is invoked through another shell interpreter, so it does not independently prove that the authorized commit workflow owns the commit.
- Owner: `task-commit` and its repository hook contract.
- Reason for deferral: the finding is independent of EPIC-003 runtime review correctness and does not change the isolated committed bytes or their verification.
- Re-entry condition: resolve before relying on the gate as an enforcement boundary by replacing the marker with authenticated workflow evidence and failing closed across supported shell invocation paths.

## DF-003: Tear down in-flight native observation children on wrapper signals

- Actionable issue: the host wrapper's signal teardown stops its own observer but leaves in-flight native `haepari wait` and `events --follow` children running until their own timeout or the Job's end.
- Owner: the VM host wrapper (`tests/vm/host_wrapper.py`).
- Reason for deferral: the children are read-only and self-ending, change no state, and do not affect results or reconnect.
- Re-entry condition: resolve before the wrapper is used unattended in automation that sends signals, by extending the observer's bounded teardown to those children.

## DF-004: Reconcile descriptive Goal-version guidance

- Actionable issue: descriptive Goal-version labels disagree. Epic Handler and Procedure node contracts name version 35, while Epic orchestration names version 37.
- Sources: [Epic Handler](../../plugins/aquarium/skills/epic-handler/SKILL.md), [Procedure node contracts](../../plugins/aquarium/references/procedure-node-contracts.md#goal-procedure), and [Epic orchestration](../../plugins/aquarium/references/epic-orchestration.md#ordinary-execution-and-handler-roles).
- Owner: workflow documentation for Epic Handler, Procedure node contracts and Epic orchestration.
- Reason for deferral: the descriptive drift predates TASK-148 and is independent of its collaboration instructions and display-role changes; no current TASK-148 runtime behavior defect is established by this wording mismatch.
- Re-entry condition: at the next maintenance of Goal-version guidance, reconcile the descriptions against current canonical Procedure sources while preserving admitted historical definitions, source identities and snapshots.

## DF-005: Reconcile the parent Epic lifecycle at Handler work start

- Actionable issue: a Handler fixture completed both member Tasks while its parent Epic remained in the target roadmap's not-started state. The parent record update was omitted, and both the reviewed base and candidate Handler instructions lack an explicit Epic-start reconciliation step.
- Owner: [Epic Handler](../../plugins/aquarium/skills/epic-handler/SKILL.md) lifecycle guidance, using each target repository's canonical roadmap vocabulary.
- Source: EPIC-027 whole-Epic review 1, F-4 (requirements review REQ-4 and verification review VER-3); original failed fixture and later record-only correction remain separate results.
- Reason for deferral: this is an independent preventive clarification of preexisting Handler guidance. EPIC-027 changes its role wording; no new display-role regression was established. The fixture correction repaired only its parent record.
- Re-entry condition: before the next applicable Handler lifecycle maintenance or use, define and verify parent-Epic reconciliation when actual work starts, preserving the target repository's allowed lifecycle transitions and terminal member records.

## DF-006: Review Squad composition boundaries before external-role extension

- Actionable issue: the composition and commit-handoff consumers in [adaptive_squad.py](../../plugins/aquarium/shared/adaptive_squad.py) combine evidence applicability, finding classification, acceptance and commit eligibility. Extending these consumers can make their contract boundaries harder to audit.
- Owner: Squad composition/commit maintenance before EPIC-028 TASK-154 and TASK-155 extend those concerns.
- Source: EPIC-027 whole-Epic review 1, F-7 (code review CODE-2).
- Reason for deferral: this is an independent maintainability improvement, with no additional current behavior defect established. The current unresolved-finding defect was repaired separately; broad decomposition is unnecessary for that correction.
- Re-entry condition: before TASK-154 or TASK-155 changes composition or commit eligibility, evaluate small extractions by concern and verify preserved contracts with the existing affected suite. The finding imposes no line-count limit, mandatory large refactor or new framework.
