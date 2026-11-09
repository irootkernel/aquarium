# Shared Python environment qualification

Two kinds of installed checks apply, both on the dedicated UTM macOS VM. Fixture
tests and this document do not establish installed results.

- **Recurring release acceptance:** the required scenario below, plus the
  existing Task/Epic startup scenarios, in every `release-acceptance` Job
  (J-RA).
- **Required development qualification:** the feature cases further down. They
  must pass before this change's first release, and again whenever a later
  change affects them.

The [release-acceptance runbook](release-acceptance.md) owns invocation,
ordering, evidence transport and cleanup for both.

## Required: `python-runtime-approval`

Runbook step f2 records this scenario after the status runtime update and
before managed updates and startup.

1. `python-runtime-update` runs the installed candidate's
   `tools/aquarium-python/runtime.py inspect` with `-I`. It records the initial
   status, the sealed requirements digest and the environments that already
   exist for that digest. Against the released baseline, the expected status is
   `missing-prerequisite` with the scoped `aquarium-python` continuation, and
   diagnosis creates no runtime path.
2. The same phase invokes the candidate `dev-setup-global` for only
   `aquarium-python`. Confirm from `NNN.last` that the proposal discloses the
   runtime target, pinned dependencies and PyPI endpoints before installation.
   `python-runtime-reply` continues the same thread with the actual reply.
   Approval completion requires one of two results, and diagnosis reporting
   `current` for the sealed digest. Either the reply created the selected
   environment, or an environment that existed at the start of the phase is
   reused. No environment may appear in the proposal turn or outside the
   windows, and no prior environment may be removed.

The existing `task-startup` and `epic-startup` scenarios then exercise actual
Task and Epic handler startup with that environment selected. `consumer-cleanup`
verifies the retained selection and prior environments.

## Required development qualification

These installed feature cases qualify this change before its first release.
Repeat them only when a later change affects these features; a J-RA PASS does
not imply them, and unchanged features need no automatic repetition in each
J-RA. Run them only under explicit, candidate-bound Haepari/UTM VM-test
authority, inside a held managed Job after step f2 has prepared the environment
and before evidence staging. Use run-owned temporary fixtures. Bind the result
to the exact candidate and retain the original evidence. Verified consumer
cleanup under the runbook's contract is required. A case not performed remains
unverified, and its absence blocks the first release of this change. These
cases are not J-RA required-scenario identities and do not change the
completion template.

3. In two separate non-Python fixtures, run a candidate helper through
   `runtime.py run`, using the bundle normalizer with a valid external manifest
   in a run-owned directory. Confirm that both invocations select the same
   interpreter and that repeated approved setup downloads nothing.
4. With an unrelated fixture environment carrying conflicting YAML and
   `jsonschema` modules, and with `PYTHONPATH` set to them, repeat the helper
   invocation. Confirm the imports come from the Aquarium environment and that
   the fixture's packages and files are intact.
5. Damage a dependency file only in the environment that this run created in
   step 2. Confirm that diagnosis refuses it. Continue the same thread through
   further `python-runtime-reply` windows. Confirm that setup proposes repair
   and that the approved repair selects a new environment while retaining the
   damaged one. An interrupted preparation must leave the previous selection
   unchanged. Cleanup accepts only the selection that the latest recorded reply
   names, so a selection changed outside a reply window fails. Cleanup allows changes only to the selection, the installer lock
   and environments created inside recorded reply windows. Any other new or
   changed file in the family, including in an environment that existed before
   the phase, fails cleanup.
6. Run bundle setup from its initial entrypoint with a valid manifest. Confirm
   that it prepares or reuses the environment once, before YAML parsing. Also
   exercise the missing-runtime and rejected-approval paths, with no fallback
   to a project environment.
7. Confirm that the opt-out and non-Git `new-project` branches return before
   runtime discovery, without the environment.

Retain the original case outputs, failed attempts, exact candidate identity and
final consumer inventory. Cleanup never removes prior environments and never
restores an older installed plugin. Master's functional acceptance remains
separate.
