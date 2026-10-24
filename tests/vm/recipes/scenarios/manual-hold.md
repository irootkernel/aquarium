# Manual-hold scenario document

This labelled disposable suite demonstrates the manual hold with a minimal
offline workload. The setup installs nothing; the smoke phase creates only a
trivial job-local fixture. The operator then observes the declared scenarios
while the Job holds the VM in `awaiting_manual`:

- `fixture-check`: the trivial fixture document created by the smoke phase is
  present and readable.
- `discovery-check`: left deliberately unobserved for this demonstration; it
  is recorded as `unobserved` in the manual result.

The operator stages case evidence in the Job's declared output paths, then
finishes recipe consumer cleanup through the `consumer-cleanup` phase, which
removes the trivial fixture and leaves guest product state untouched. Only
then does the operator submit the closed manual-result record. The
`unobserved` scenario yields the native INCOMPLETE verdict — unobserved work
prevents PASS — which is the truthful outcome this suite exists to show.

## Kill-and-reconnect demonstration

This suite also carries the reconnect proof (moved from the J-RA
transaction by the S5 scope amendment). While the Job holds in
`awaiting_manual`:

1. Terminate the host wrapper process with a signal (SIGTERM or SIGKILL)
   while it waits; the killed wrapper dies on the signal (Python reports
   signal termination, e.g. exit −15/−9), which is distinct from the
   wrapper's normal observation-budget exit: PENDING exit 5 with the Job
   never cancelled. The Job itself is never cancelled by either.
2. Re-run `make test-vm-host` with the **same** `RUN_DIR`, `RESOURCE`,
   `SUITE` and `MODE`. The wrapper reconnects to the **same Job ID** from
   the saved run record — no replacement Job, no new request key.
3. Finish the scenario work, submit `manual complete`, and let the native
   terminal verdict settle.
4. On reconnect after settlement, the wrapper reuses the completed export
   only after verifying its manifest receipt (Job ID, every declared
   output's digest, and the consumed result's suite and candidate
   identity); otherwise it exports to a fresh destination.

The demonstration succeeds when the same Job ID yields the terminal verdict
and the reused export passes receipt verification.
