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
