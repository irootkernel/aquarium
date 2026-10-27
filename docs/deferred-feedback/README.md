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
