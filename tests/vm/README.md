# Manual VM release acceptance

These are planned reusable methods for
[EPIC-024](../../docs/roadmap/README.md#epic-024-restore-native-agent-workflows-and-add-manual-vm-release-acceptance).
TASK-128 will add the guest-side `make test-vm` target, fixtures and helpers.
They are not implemented yet. These definitions are not execution results.

## Purpose and invocation

Verify whether the existing installed system can accept the exact candidate and
start actual work. Complete functional verification during development before
release preparation; the release gate checks upgrade and startup blockers.

Run VM acceptance only through release-handler or Master's explicit VM-test
request. Ordinary `make test` and automatic Task/Epic checks must not invoke it.
For EPIC-024, manually operate the dedicated UTM macOS VM and verify Codex only.
Haepari is not required.

| Concern | Owner |
| --- | --- |
| Executable gate and test contract | [Makefile](../../Makefile), [TESTING.md](../../TESTING.md#planned-manual-vm-release-acceptance) |
| Scenario steps and criteria | [Release acceptance](release-acceptance.md) |
| Implementation scope and task acceptance | [Recovery dossier](../../docs/todo/TODO-NATIVE-AGENT-WORKFLOW-RECOVERY.md) |
| Release and installation authority | [AGENTS.md](../../AGENTS.md#release-policy), installed release-handler |

## Manual preparation and execution

1. Identify the exact committed candidate, matching test sources and host's
   installed release combination. Use the dedicated VM; keep candidate
   installation off the host and use the separately authorized installation path.
   Verify the dedicated guest before fixture mutation, installation or agent
   dispatch. The future target must reject host execution without mutation.
2. Before upgrading, observe meaningful released-version fixture state and
   record its baseline. Do not manufacture old state using the candidate.
3. Install the candidate and required released dependencies through supported
   paths. Perform authorized managed updates, preserving customized sources and
   immutable snapshots. Use synthetic fixture data and existing authorized guest
   access rather than copying host secrets.
4. Use candidate-matched guest test sources. Once TASK-128 implements it, run
   `make test-vm` inside the VM. The host workflow guides these steps and collects
   results; the guest must not recursively enqueue work or install on the host.
5. Execute the cases through fresh Codex sessions and installed skill discovery.
   Record actual native work and resulting artifacts. Pasted candidate skill
   prose or standalone subagent acknowledgements cannot prove handler startup.

Before the target exists, an authorized manual run may follow the same cases
and report its observations. It cannot claim that `make test-vm` passed.

## Result record

Record candidate identity, installed combination, case IDs, actual steps,
fixture artifacts and check results, public native call/result observations,
applicable Podway state, observer and cleanup outcome. Keep any required Master's
acceptance pending until supplied. Use the existing
[evidence-residency contract](../../plugins/aquarium/references/evidence-residency.md);
raw private logs and runtime directories do not become tracked scenario authority.

| Outcome | Required meaning |
| --- | --- |
| Pass | Every required observation and cleanup succeeded for the recorded candidate and combination |
| Fail | Observed upgrade, preservation, discovery, startup, result or cleanup behavior violates a case criterion |
| Incomplete | Environment, access, authority, observations or cleanup cannot be established |

The future command must return nonzero for Fail or Incomplete. Printing a
checklist, preparing a VM or receiving a success sentence is insufficient.
Missing native work or required manual observations cannot pass.

## Cleanup and reuse

Settle mutating agents before replacement or disposal. Stop partial smoke work
truthfully through supported native operations; do not mark an unfinished goal
achieved to clean it up. Remove only owned fixtures and preserve unrelated work.
Restoring a VM baseline requires its applicable authority. Unresolved cleanup
leaves the run non-passing.

Reuse these definitions across releases; results apply only to their recorded
candidate and installed combination under the release policy. Future EPIC-019
Haepari host submission reuses this guest entrypoint and scenario catalog.
