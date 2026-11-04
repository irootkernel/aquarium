# Haepari VM verification

Aquarium's managed VM adapter submits immutable suites through the installed
Haepari release controller. Haepari owns scheduling, manual occupancy, collection
and Job cleanup. Aquarium recipes own guest installation, assertions and consumer
restoration. The persistent guest is not reset.

The [consumer contract](../../plugins/aquarium/references/haepari-integration.md),
[VM guide](../../tests/vm/README.md) and [testing authority](../../TESTING.md)
own the interfaces and scenarios. [Release policy](../../AGENTS.md#release-policy)
selects one managed `release-acceptance` Job. TASK-090 qualified this path
against its exact installed candidate; the [VM guide](../../tests/vm/README.md#qualified-pilot-and-limits)
records the observed outcomes and limits. Each release retains its own
exact-candidate verification and distribution identity requirements.

## Prerequisites and diagnosis

Use the verified Haepari v0.1.0 release and complete same-release `use-haepari`
skill under the [tool catalog](../../plugins/aquarium/references/tool-catalog.md#haepari).
Select the shared per-user installation through explicit `HAEPARI_HOME` and its
registered capacity-one `utm-macos` resource. VM and SSH registration, host-key
pins and private machine identities belong to native operator configuration.
This runbook creates no controller or resource.

Execution requires release-handler authority or an explicit VM-test request;
ordinary local checks and offline release QA do not submit Jobs. Candidate
installation runs only in the dedicated guest. Master controls VM power.
Installation, managed updates, commits and publication retain their own authority.
Model or service use also requires the scenario's approved guest identity,
endpoint and budget; offline is the default. Never copy host authentication into
the guest or use production data as a fixture. Guest restoration does not undo
external writes or charges.

Read-only diagnosis uses these native surfaces:

```sh
HAEPARI_HOME="<selected-home>" "<haepari-bin>" version --json
HAEPARI_HOME="<selected-home>" "<haepari-bin>" capabilities --json
HAEPARI_HOME="<selected-home>" "<haepari-bin>" doctor --projection --section queue --limit 10 --json
HAEPARI_HOME="<selected-home>" "<haepari-bin>" resources list --json
HAEPARI_HOME="<selected-home>" "<haepari-bin>" doctor --resource "<resource-id>" --json
```

The projection establishes controller reachability and installation identity;
resource inventory and resource doctor establish registration and guest readiness
separately. A partial inventory cannot establish absence. Preserve native gap
codes and error/retry envelopes. These commands do not start or reset the VM.

## Prepare and submit a suite

Select the repository-supported Python environment before invocation. Make uses
`.venv/bin/python` when present in the caller root, otherwise `python3`; its
`override PYTHON` assignment ignores command-line `PYTHON=<path>`. Prepending the
verified source repository's `.venv/bin` to process-local `PATH` also binds the
nested artifact-build Make in its clean clone. Verify the actual interpreter;
local development checks additionally use the toolchain declared in `TESTING.md`.

Allocate a private physical parent and an empty run directory. Store caller logs
outside the empty run directory, since the wrapper rejects unfinished preparation:

```sh
CASE_ROOT="$(mktemp -d /tmp/aquarium-vm.XXXXXX)"
CASE_ROOT="$(cd "$CASE_ROOT" && pwd -P)"
mkdir "$CASE_ROOT/run"
chmod 0700 "$CASE_ROOT" "$CASE_ROOT/run"
RUN_DIR="$CASE_ROOT/run"
```

Supply the private `aquarium.vm-guest-context/v1` JSON file. Its required fields
are `expected_guest_uuid`, `guest_home`, `guest_path`, `guest_python`,
`guest_codex`, `guest_podway` and `guest_marketplace_name`; optional `driver_python`
defaults to `guest_python`. Keep the file private and its values out of tracked
documents. SSH settings remain in Haepari's resource configuration.

For the declared suite set, the queue budget must be at least
`(jobs ahead + 1) * 26100`, within the resource ceiling `86400`. Select
`26100`, `52200` or `78300` for zero, one or two Jobs ahead before sealing.
Use an accepted hash-locked fixture requirements file; the repository's ordinary
requirements file is not a substitute. Each new suite gets a new empty run
directory. A reconnect reuses the original one.

```sh
PATH="<verified-repo-root>/.venv/bin:$PATH" \
HAEPARI_HOME="<selected-home>" \
AQUARIUM_VM_CANDIDATE_SHA="<committed-candidate-sha>" \
AQUARIUM_VM_FIXTURE_REQUIREMENTS="<accepted-hash-locked-file>" \
AQUARIUM_VM_QUEUE_SECONDS="<calculated-seconds>" \
AQUARIUM_VM_WAIT_TIMEOUT=120 AQUARIUM_VM_WAIT_ROUNDS=1 \
make test-vm-host HAEPARI="<haepari-bin>" RESOURCE="<resource-id>" \
  MODE=auto SUITE=baseline RUN_DIR="$RUN_DIR" \
  GUEST_CONTEXT="<private-guest-context.json>"
```

The wrapper persists the request key and exact spec before admission, then saves
the returned Job ID in `run.json` (`aquarium.vm-host-run/v1`). Its bundle includes
`harness/inputs.json` (`aquarium.vm-host-inputs/v1`), the producer's
`artifact-manifest.json`, sealed profiles and recipe inputs. The plugin comes
from a clean clone of the selected committed SHA through `make aquarium-dev-build`;
a dirty policy edit cannot masquerade as that commit's artifact.

Select suites explicitly. `baseline`, `install`, `upgrade` and
`migration-failure` normally pass their assertions; install finishes in its
product-absent state, while upgrade restores its declared prior stable.
`guard-failure-probe` intentionally fails and leaves a declared residue.
`manual-hold` intentionally retains an unobserved discovery case.
`SUITE=all` selects every suite alphabetically using its first declared mode,
without filtering by `MODE`; a nonzero result skips later suites.

## Manual occupancy and completion

A PENDING return does not prove `awaiting_manual`. Use the original Job's native
observations to establish readiness and obtain its workspace and current revision.
The [manual-hold scenario](../../tests/vm/recipes/scenarios/manual-hold.md) also
owns the real host-observer signal/disconnect demonstration. Reconnect the same
run directory and Job; a caller timeout neither cancels it nor extends its budget.

Before every guest mutation, verify the dedicated guest identity. Operator phases
run from `<workspace>/harness` through the recipe entrypoint, with the saved
spec's `workload.environment` and persisted `operator-parent-context.json`:

```sh
cd "<workspace>/harness"
# Export the saved workload.environment without logging its private context.
HAEPARI_PARENT_CONTEXT="$(cat ../operator-parent-context.json)" \
/bin/sh tests/vm/recipes/guest_entry.sh --suite manual-hold --phase consumer-cleanup
```

Do not print the parent context or enable shell tracing. Preparation already ran
manual-hold's smoke phase; repeating it overwrites the original repair record.
Observe `fixture-check`, leave the demonstration's `discovery-check` unobserved,
then finish consumer cleanup and verify all five declared outputs before
completion. That truthful demonstration yields native INCOMPLETE, not PASS.

For release acceptance, supply `AQUARIUM_VM_PODWAY_RELEASE`, use
`MODE=manual SUITE=release-acceptance`, and follow the
[complete operator runbook](../../tests/vm/recipes/scenarios/release-acceptance.md).
It owns the phase commands, fixed profiles, model-use budget, actual proposal and
result decisions, eleven required scenarios, ten bounded evidence archives and
abort/recovery checkpoints. One Job holds the VM throughout. The guest-side
`make test-vm` and nested handler fixtures run inside that allocation.

Read each setup proposal before replying. A terminal no-op status record still
needs approval covering its concrete scope, recorder command and ledger/language
effects before attempt creation or recording. Carry an existing covering approval
forward; a required record alone supplies no authority. The startup smokes stop
after first-member delivery and semantic progression, with later criteria open.

Stage original case evidence incrementally at case checkpoints and before
restoration or an authorized cancellation/deadline/abort checkpoint. The
[epic-squad scenario](../../tests/vm/recipes/scenarios/epic-squad.md#incremental-evidence-and-abnormal-checkpoints)
uses its declared fixed archives even while staging is INCOMPLETE. Its six-hour
manual window and evidence/cleanup reserve are planning assumptions; actual
sufficiency and immutable Job pin fit remain installed-verification observations.
Automated termination before a checkpoint leaves only previously staged
declared snapshots available for native collection, not newer unstaged originals. Keep the same Job/key/run directory
and report gaps; positively absent outputs can release an incomplete Job, while
existing outputs that cannot be collected retain native protection.

Release acceptance retains the tested Aquarium, Podway v0.2.16, paired skill
and candidate status runtime in the dedicated VM. Verify this final installation
and finish run-owned consumer cleanup, then restage its actual immutable pass
receipt and restoration inventory in the same held Job. For epic-squad,
`consumer-cleanup` seals `consumer-result.json` before another phase can overwrite
aggregate `result.json`; `stage-evidence` consumes that receipt without executing
the restored writer or reinstalling the candidate. Verify current complete
staging as well as actual functional results before manual completion. Staging
preserves a malformed restoration inventory and returns INCOMPLETE; it does not
replace invalid failed-history bytes with an empty aggregate on retry. Then construct
the suite's closed `haepari.manual-result/v1` input from actual observations.
J-RA's `complete-template` phase creates it only after the required checks.
Persist the input and use the actual current revision:

```sh
HAEPARI_HOME="<selected-home>" "<haepari-bin>" manual complete "<job-id>" \
  --input "<completion.json>" --expected-revision "<revision>" --json
```

Native collection and Job cleanup follow completion. Reconnect the wrapper with
the same bindings and run directory to wait and export last. Verify the native
`result.json` and `manifest.json`, all declared file digests/sizes and the consumed
recipe result under `artifacts/results/<suite>/result.json`. Missing observations
or unverified consumer cleanup prevent acceptance.

## Results, handoff and recovery

The wrapper emits JSON-line stdout reports and persists per-Job `observation`,
`cancellation` and probe records in `run.json`. Capture the actual process exit:
`0` PASS, `1` FAIL, `3` INCOMPLETE, `4` CANCELLED, `5` PENDING, `6` uncertainty;
exit `2` is a classified refusal or error. GNU Make maps a failed recipe to its
own exit `2`; direct wrapper invocation preserves the wrapper exit. Keep native
workload outcome, evidence completeness, Job cleanup, consumer cleanup and final
verdict separate. A designed negative case is not a passing release transaction.

A reusable request handoff names the selected installation/resource, saved key
and spec, committed candidate, sealed artifact/harness/profile identities, suite,
budgets, allowed effects and cleanup owner. The completion handoff adds the
returned Job/revision, original observations, verified exports, actual native and
consumer outcomes, omissions and remaining recovery. Concrete machine identities,
Job IDs and paths stay in private evidence under the
[evidence contract](../../plugins/aquarium/references/evidence-residency.md).

Reconnect uncertain submission with its original key/spec and follow native
`error.retry`; never generate a replacement key speculatively. To cancel, reconnect
with `AQUARIUM_VM_CANCEL=1`, or persist the exact current revision and request key
before the native command:

```sh
HAEPARI_HOME="<selected-home>" "<haepari-bin>" cancel "<job-id>" \
  --expected-revision "<revision>" --request-key "<saved-key>" --json
```

The wrapper stores acknowledgment/refusal separately from the subsequent immutable
terminal observation in `run.json`. Await that observation; acknowledgment alone
returns no capacity and guarantees no CANCELLED verdict.

If guest readiness fails, escalate the actual gap to Master. For unknown execution,
inspect the same Job and the native read-only recovery plan through `use-haepari`;
apply only the authorized plan. For failed consumer restoration, preserve its
preimage and inventory and use the recipe's documented recovery before affected
reuse. Manual-hold repairs only its declared guard-probe leftover, and J-RA's
machine preparation handles its documented abort residues. Neither grants general
foreign-state cleanup. Haepari never restores arbitrary guest installations or
excludes direct callers that bypass its selected installation/resource.

The pilot also observed conservative wrapper `UNKNOWN` after
`OBSERVER_TEARDOWN_INCOMPLETE` reported local observer teardown `EPERM`. Preserve
that uncertain observation and reconcile the original native Job and owned
observer state. Reconnect with the original run directory to obtain its actual
terminal disposition and verified export; neither a new Job nor an assumed
successful teardown resolves the gap. The cause remains unproven. Separately,
private physical-restoration proof cannot replace missing required output in a
native export; delivered consumer cleanup remains unverified in that case.

Aquarium's own legacy-enrollment audit and TASK-101 retain the separate retirement
boundary. This runbook authorizes no `~/.aquarium-dev` mutation, host candidate
installation, controller replacement, VM power operation or publication.


## Explicit Podway upgrade qualification

Use `SUITE=podway-upgrade MODE=manual` only under the exact VM-test authority described by the [operator scenario](../../tests/vm/recipes/scenarios/podway-upgrade.md). Supply `AQUARIUM_VM_PODWAY_RELEASE` with its physical prepared release-input path in addition to the normal candidate, resource and private guest context. The selected Job retains the original v0.2.14 baseline and a separate v0.2.15 candidate profile. Seven native manual cases, actual installed skill observations and verified restoration remain required; the helper never installs tools or discards runtime state. Recover the original Job and phase captures after disconnect.
