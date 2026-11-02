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

## DF-007: Retire the Mulgae requirements omission workaround

- Actionable issue: Mulgae v0.1.26's requirements instruction requests provider output v3 with requirement assessments, while its later extraction instruction requires v1 finding output without them. Aquarium temporarily uses explicit, evidenced assessments in the assigned owner's accepted report for native derived `answer_omitted` rows, preserving those rows unchanged.
- Owner: Mulgae owns the producer correction and its stable release. Aquarium's Mulgae adoption owns removal of the [temporary consumer path](../../plugins/aquarium/references/mulgae-review-contract.md#assess-criteria-when-native-answers-are-omitted).
- Producer work: reconcile initial, extraction and applicable repair output contracts; verify that accepted report assessments survive as admissible native v3 answers with original IDs and evidence. Cover positive, partial, negative and genuinely unverified answers without changing extraction policy or invocation budgets to mask the issue. Aquarium's workaround does not complete this upstream work.
- Reason for deferral: the producer release has its own implementation, verification and publication lifecycle. Aquarium's bounded consumer workaround permits current v0.1.26 adoption; its own installed qualification remains required.
- Re-entry condition: when a stable Mulgae release with the verified correction is published, adopt that exact CLI and complete paired skill, raise Aquarium's minimum to the fixed version, remove the omission-specific report-based path and dependent guidance, and verify native assessments through Task, Epic, standalone and remediation-confirmation callers. Do not retain the workaround as a permanent alternate route or infer the correction from a version number. Preserve historical evidence and settle this entry only after the replacement adoption is verified.

## DF-008: Investigate terminal observer teardown EPERM on macOS

- Actionable issue: the host wrapper can report `UNKNOWN / OBSERVER_TEARDOWN_INCOMPLETE` after the native event stream ends because signaling its observer group returns `EPERM`. A later terminal query of the same Job can establish `PASS`, verified cleanup and successful export. The wrapper's earlier unknown observation must remain distinct from that native result.
- Owner: the VM host wrapper's observer lifecycle (`tests/vm/host_wrapper.py`).
- Reason for deferral: this is separate from the Mulgae consumer correction. Same-Job terminal reconnection recovered the authoritative result and export without another workload, consumer mutation or VM reservation.
- Re-entry condition: at the next observer-lifecycle maintenance, establish the cause with owned-child exit and reap evidence and verify the macOS terminal-exit boundary. Do not suppress permission errors, infer termination without proof, signal an unrelated process group or weaken the fail-closed unknown result.
