# Manual VM release acceptance

The guest-side `make test-vm` target executes the fixed cases through
[run_acceptance.py](run_acceptance.py) for
[EPIC-024](../../docs/roadmap/README.md#epic-024-restore-native-agent-workflows-and-add-manual-vm-release-acceptance).
A passing result requires the recorded upgrade and startup observations.

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
| Executable gate and test contract | [Makefile](../../Makefile), [TESTING.md](../../TESTING.md#manual-vm-release-acceptance) |
| Scenario steps and criteria | [Release acceptance](release-acceptance.md) |
| Implementation scope and task acceptance | [Canonical scope and outcomes](../../docs/roadmap/README.md#epic-024-restore-native-agent-workflows-and-add-manual-vm-release-acceptance) |
| Release and installation authority | [AGENTS.md](../../AGENTS.md#release-policy), installed release-handler |

## Manual preparation and execution

1. Identify the exact committed candidate, matching test sources and host's
   installed release combination. Use the dedicated VM; keep candidate
   installation off the host and use the separately authorized installation path.
   Verify the dedicated guest before fixture mutation, installation or agent
   dispatch. The driver requires Darwin, the native hypervisor-present flag and
   the expected hardware UUID supplied in the external runtime request. It
   rejects a physical host or another guest before writing files.
2. Before upgrading, observe meaningful released-version fixture state and
   record its baseline. Do not manufacture old state using the candidate.
3. Prepare the matching clean guest verification checkout, then install the
   candidate and required released dependencies through supported paths. Use
   the setup capture command below to invoke installed
   `aquarium:dev-setup` scoped to each fixture and Podway. Approve its concrete
   proposal normally. The driver records managed bytes before and after the
   native operation; it never copies Procedures. Preserve customized sources
   and immutable snapshots. Use synthetic data and existing authorized guest
   access rather than copying host secrets.
4. After the captured managed updates, run `make test-vm` inside the VM. The host workflow
   guides these steps and collects results; the guest must not recursively enqueue
   work or install on the host.
5. Execute the cases through fresh Codex sessions and installed skill discovery.
   Record actual native work and resulting artifacts. Pasted candidate skill
   prose or standalone subagent acknowledgements cannot prove handler startup.

Host transport and VM selection belong to the user's environment. The driver
contains no SSH, VM application command, provider-specific machine model or
personal connection details. A verification checkout in the guest does not
authorize developing there.

## Runtime request and commands

Keep the request and results outside the verification checkout. Use a physical
absolute `run_root`, without symlink ancestry. The request records existing
authority; it does not grant execution, installation or acceptance.

```json
{
  "schema": "aquarium.vm-acceptance-request/v1",
  "expected_guest_uuid": "<dedicated guest hardware UUID>",
  "run_root": "/path/to/owned-run",
  "released_plugin_root": "/path/to/released/installed-plugin",
  "released_marketplace_root": "/path/to/released/registered-marketplace",
  "tools": {
    "codex": "/path/to/codex",
    "podway": "/path/to/podway",
    "python": "/path/to/python3"
  },
  "baseline_combination": {
    "aquarium": "<released plugin version>",
    "codex": "<native CLI version>",
    "podway": "<native v-prefixed version>"
  },
  "authority": {
    "kind": "explicit-vm-test",
    "reference": "<actual user request or release-handler envelope>",
    "observer": "<authorized fixture operator>"
  },
  "baseline_setup": {
    "task": "<actual setup thread UUID or JSONL path>",
    "epic": "<actual setup thread UUID or JSONL path>",
    "preservation": "<actual setup thread UUID or JSONL path>"
  }
}
```

`authority.kind` is `explicit-vm-test` or `release-handler`. Include selected
Gaori or Mulgae executable paths and their versions in both `tools` and
`baseline_combination` when they belong to the observed host combination.
Optional `codex_args` contains the operator's supported native process arguments;
the driver changes no persistent Codex configuration.

```sh
python3 -B tests/vm/run_acceptance.py guard --request /path/to/request.json
python3 -B tests/vm/run_acceptance.py seed --request /path/to/request.json
```

`seed` creates the fixed greeting repositories at `run_root/task` and
`run_root/epic`. It preserves an existing path by refusing replacement. Prepare
`run_root/preservation` separately with meaningful synthetic Git work, settings,
a historical report, a custom managed source and a released admitted session.
Use the released installed setup skill for all three repositories. Install the
fixture's declared test dependencies before its checks, then track its approved
managed configuration and sources. Do not use candidate Procedures to create
old history.

```sh
python3 -B tests/vm/run_acceptance.py baseline --request /path/to/request.json
```

The baseline command checks released versions, native installed/enabled plugin
registration and source bytes, native-valid managed files, setup calls and fresh
installed discovery. It captures Git work
and file hashes, custom sources and admitted sessions in create-once
`baseline.json`. Preparation does not report acceptance PASS.
Released setup captures retain completed public turn and item identities,
selected installed source and managed-file hashes in immutable records. Existing
released setup threads remain usable for baseline observation without replay.
A missing tracked file or a symlink in captured state leaves capture incomplete;
the driver does not silently omit it.

After the separately authorized candidate installation, add a `candidate`
object to the external request before updating managed files:

```json
{
  "git_sha": "<exact committed candidate>",
  "source_root": "/path/to/clean/candidate-checkout",
  "artifact_root": "/path/to/matching/marketplace",
  "artifact_manifest": "/path/to/artifact-manifest.json",
  "installed_plugin_root": "/path/to/candidate/installed-plugin",
  "marketplace_root": "/path/to/candidate/registered-marketplace"
}
```

Build on the host from clean local `main` whose HEAD equals the exact candidate.
Choose an existing empty absolute output directory outside the checkout and a
manifest path outside both the checkout and output directory. Save the
producer's stdout JSON:

```sh
git branch --show-current
git rev-parse HEAD
git status --porcelain
AQUARIUM_DEV_OUTPUT=/absolute/empty/build-output make aquarium-dev-build > /absolute/artifact-manifest.json
```

The first command must report `main`, the second the selected candidate SHA and
the third no changes. The producer rejects other branches, a dirty checkout or
a nonempty output directory. Set `artifact_root` to the output directory joined
with the manifest's relative `artifact_path`. Copy the artifact
and manifest through the user's transport. Transfer Git objects or otherwise
prepare a clean guest verification checkout at that exact SHA, including its
committed tests. Do not install the artifact on the host.

The manifest binds artifact content and development version to `git_sha`;
the artifact excludes tests. The driver independently checks
the actual guest Git HEAD and cleanliness, committed plugin bytes, artifact
digest, native installed/enabled plugin registration, installed package bytes
and fresh skill paths. `marketplace_root` may be omitted when the native
registered marketplace is `artifact_root`; otherwise its entire payload must
match the artifact.
Installed-cache comparison excludes standard `__pycache__` bytecode associated
with an existing Python source file. Every shipped source byte and other cache
entry remains checked; generated bytecode is not distribution identity. Native
test invocations also disable bytecode writes for their process tree.

Capture each authorized managed update through the installed setup skill:

```sh
python3 -B tests/vm/run_acceptance.py setup --request /path/to/request.json --fixture task
python3 -B tests/vm/run_acceptance.py setup --request /path/to/request.json --fixture epic
python3 -B tests/vm/run_acceptance.py setup --request /path/to/request.json --fixture preservation
```

The command records actual managed-file preimages immediately before native
dispatch and postimages after it returns. Preimages must match the released
baseline or the previous captured native postimage. An unexplained earlier
manual copy leaves the case incomplete; a later comparison cannot establish
the missing update. Keep the fixture free of other mutators during this bounded
native operation. Required changes from released to candidate bytes must occur inside its
captured windows. When baseline and candidate source bytes already agree, an
actual current-source setup/check may establish a genuine no-op. Custom files
retain their baseline bytes.

If setup asks for a decision, read its concrete proposal and resume with an
actual operator reply:

```sh
python3 -B tests/vm/run_acceptance.py reply --request /path/to/request.json \
  --case task-setup --reply-file /path/to/actual-operator-reply.txt
```

Use `epic-setup` or `preservation-setup` for the other fixtures. The first setup
call may use `--resume-thread <actual released baseline setup UUID>` to continue
that existing thread. The candidate setup call establishes the installed setup
context; ordinary approval replies need not repeat its name. Public new-turn
evidence, current-source calls, captured byte transitions and final files
establish the result together. An external setup handle recorded afterward is
insufficient. Unknown operations remain incomplete and are retained without
automatic replay or resetting the fixture.

If invocation or public observation fails, the driver captures the managed
postimage and any available exit and native handle alongside the original preimage.
Reconcile that existing handle with a read-only public observation:

```sh
python3 -B tests/vm/run_acceptance.py reconcile --request /path/to/request.json --fixture task
```

Use the other fixture names as needed. Reconciliation records a separate
immutable observation; it never dispatches a provider turn or rewrites the
failed capture. A recovered successful operation can complete the setup case.
A settled failed or interrupted operation remains incomplete until an actual
operator reply produces a successful update through the same handle. Read its
current proposal and status before replying. Active or unknown work, a missing
handle, and unexplained changes after the captured postimage remain incomplete.
The final setup must succeed and verify the expected managed bytes; earlier
failures remain in the result's operation windows.

```sh
AQUARIUM_VM_REQUEST=/path/to/request.json make test-vm
```

The command records actual post-update files and session observations before
dispatching installed Task and Epic startup. It retains this candidate-bound
upgrade record across normal fixture progression, while rechecking the separate
preservation repository. When a handler needs a ready plan or exact-result
decision, the result remains incomplete and names its real native handle. The operator
reads the proposal or diff and writes the actual reply to a file, then resumes:

```sh
python3 -B tests/vm/run_acceptance.py reply --request /path/to/request.json \
  --case task-startup --reply-file /path/to/actual-operator-reply.txt
```

Use `epic-startup` for the other case. Rerun the Make target to assess the current
result and continue. It reuses existing invocation handles, preserving previous
input and result files. An uncertain invocation without a completed receipt
requires reconciliation before another dispatch; it is not automatically replayed.

## Native observations

The driver retains public CLI events and uses a bounded foreground native
app-server reader for the exact invocation and its descendants. Public
`subAgentActivity` records connect native paths to real child UUIDs. Actual
child execution, final results, role assignments, assessed source bytes,
fixture oracles and Podway progression establish the startup result together.
The reader starts no provider turn or daemon and exits after reading.

For these test cases, the Coordinator saves original ordinary v3 assignments and
role reports inside `run_root/task-startup` or `run_root/epic-startup`, with each
case's `startup-evidence.json` pointing only to files in that directory. Preserve
the other case's evidence during incomplete runs and resumes. Actual child final
results include their JSON report or its path
and digest. Reports identify `greet.py` bytes through `target.greet_sha256`;
Evaluator rows retain the original smoke IDs, sources, evidence and states. The
Evaluator remains report-only. Native role metadata may be null; child user messages,
model telemetry, full private history and formal accepted-task bindings are not
required. This collection protocol belongs to VM acceptance, not ordinary startup.

Use a cumulative delivery handoff that lists the Executor's actual implementation
changes and subsequent refinement and check results. Preserve a verification
phase's no-op result without dropping the earlier changes from that handoff.
Both reports use a 64-character lowercase SHA-256 hex digest for
`target.greet_sha256`, with an optional `sha256:` prefix. Both forms must match
the current source bytes exactly.
Return the complete report JSON in the native final result, or its original
absolute path and 64-character lowercase SHA-256 digest, with an optional
`sha256:` prefix. Point `startup-evidence.json` to that original report path. Preserve previous captures when reconciling a
collection reference or recovering report delivery.

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

The Python driver returns 0 for Pass, 1 for Fail and 2 for Incomplete. GNU Make
normally returns its own failure code, often 2, for either failing recipe. Read
`result.json` and command output for the classification; any nonzero Make result
is non-passing. A checklist, VM preparation or success sentence cannot substitute
for native work and required manual observations.

## Cleanup and reuse

Settle mutating agents before replacement or disposal. Stop partial smoke work
truthfully through supported native operations; do not mark an unfinished goal
achieved to clean it up. The default disposition retains owned fixture and
evidence directories for inspection, with provider invocations and native readers
ended and completed child work observed. Preserve the intentionally unfinished
workflow state and old baseline session. Remove only owned fixtures under
separately applicable cleanup authority and preserve unrelated work.
Restoring a VM baseline requires its applicable authority. Unresolved cleanup
leaves the run non-passing.

Reuse these definitions across releases; results apply only to their recorded
candidate and installed combination under the release policy. Future EPIC-019
Haepari host submission reuses this guest entrypoint and scenario catalog.

## Fixed profiles

`tests/vm/profiles/` holds immutable fixed test profiles as
`aquarium.vm-profile/v1` documents. A profile pins exact component identities
inside the tool catalog's support policy: the Haepari release archive,
executable and complete `use-haepari` tree digests with their provenance, the
controller service plan identity, the Aquarium plugin version with provenance
where it exists, and independently pinned native skills, plus effective
non-sensitive configuration identities, explicitly absent components,
abstract resource shape (`utm-macos`, capacity one), starting states, input
bindings and cleanup expectations. Machine-local bindings (VM identity, SSH
material, absolute homes, installation IDs, registered resource ids) never
enter a profile; they live in the private run directory of the admitting run.
The profile identity is the SHA-256 of the exact file bytes. A candidate
override replaces a whole declared component unit; a skill-only override
replaces the skill tree pin and retains every other pin. When candidate bytes
change, later tasks derive a new fully resolved profile file with no
placeholders and never edit an accepted one.

`tests/vm/profiles/validate_profiles.py` validates profiles and
`aquarium.vm-inventory/v1` documents offline, compares before, candidate
and post-cleanup inventories over complete trees, and computes the
`aquarium-skill-tree-sha256/v1` complete-tree digest; TASK-088 recipes call
`tree_digest_from_directory` on an installed tree to derive the same value a
profile pins. An inventory entry's identity is its installation scope together
with its relative path: the same path may appear in two scopes, a duplicate is
rejected only within one scope, and a comparison reports a file moved between
scopes as missing from one scope and added to the other, with every difference
named by scope and path. Guest-state inventories and the Codex component
digest walk the real guest layout with the symlink-aware inventory walk: a
regular file becomes an entry as usual, while a symlink becomes an entry with
`executable` `false` and a `sha256` over `aquarium-symlink/v1`, one NUL byte
and the link target (`os.readlink`), so a retargeted link or a file↔symlink
swap changes the entry. The walk itself may resolve a symlinked scope root;
below the root it never follows a link and never descends into a linked
directory, and a special file (FIFO, socket or device) in scope fails the
suite instead of being inventoried. Sealed-tree digests stay strict and still
refuse symlinks and special files. The `codex-plugin-cache` scope covers
`.codex/plugins/cache`, every marketplace's cache; Codex-internal state
beside it under `.codex/plugins/` (for example `.plugin-appserver` or
`.remote-plugin-install-staging`) belongs to the Codex component and stays
out of scope, and the narrow runtime allowance stays
`.codex/plugins/cache/root-kernel/`. During `stale-skill` only, native
`skills/list` updates under non-`root-kernel` marketplace caches
(`.codex/plugins/cache/<mkt>/...` where `<mkt>` is not `root-kernel`) are
recorded as `codex_owned_cache_observations` rather than restoration failures,
while `.codex/skills`, `.agents/skills`, `user-global` (including normalized
`config.toml`), `.codex/plugins/cache/root-kernel/`, and later
`consumer-cleanup` and successor starting-state checks remain strict. TASK-089
adds the `codex-home-skills` scope (`.codex/skills`) so the active per-home
skills a native client can load are inventoried beside the other scopes. The two full-combination
profiles below record the observed host Codex version, Podway (version and
executable digest) and the uv-managed Python 3.14.8 interpreter, and
existing guest per-home Codex rules are preserved starting state that
the combination adds nothing to. Recipes produce real inventories from TASK-088 on; the
release-acceptance transaction verifies the guest's observed versions
against the profile-derived baseline combination inside the Job at capture.
Profiles are reproducible test inputs: they claim no provisioned VM and no
passed migration.

| Profile | Digest | Status |
| --- | --- | --- |
| `proposed-stable-haepari-0.1.0-aquarium-0.1.21.json` | `930de6cbf2ae1468133f04f7519d201bb6d08927e807f18f2670f73c1bf553c4` | superseded |
| `proposed-candidate-haepari-0.1.0-aquarium-0.1.22.json` | `9d922eb4ee160dbdd5f966387b5754c0e5a5b54798cfba1195ee333ec05a25b4` | superseded |
| `proposed-stable-haepari-0.1.0-aquarium-0.1.21-codex-0.164.0.json` | `f128ff2c42c27b30d3265c17a3985de0850c1ab8457b23a2d9464647ccd7628b` | superseded |
| `proposed-candidate-haepari-0.1.0-aquarium-0.1.21-dev-b7c227e301a9.json` | `14618806de8ea6c0eb445a6098132f48b262e159f08747fa91fc287c2eff8edf` | superseded |
| `proposed-stable-haepari-0.1.0-aquarium-0.1.21-codex-0.164.0-podway-0.2.14.json` | `04df16201e8cff0f89d50082d162dcab00049da42aa9c1c5960e7f9a4e3e8b31` | verified prior baseline |
| `proposed-candidate-haepari-0.1.0-aquarium-0.1.21-codex-0.164.0-podway-0.2.14-dev-406f84cc58d1.json` | `09dcb4f1c599be77207d6af18752652d52bb6b0f2ecce28578ede6dbf9aa5d1c` | qualified installed pilot |

The two TASK-087 profiles are superseded because the host Codex release moved
to 0.164.0 after they were written and the candidate version axis is now bound
by sealed artifact bytes instead of the unreleased `0.1.22` number; the
TASK-088 pair is superseded because TASK-089 extended the stable profile to
the complete intended combination. Their bytes stay unchanged as immutable
history. The TASK-089 stable profile pins the full combination (Haepari and
`use-haepari`, Codex 0.164.0, the Aquarium plugin 0.1.21 with its
`aquarium-skill-tree-sha256/v1` pin computed from the v0.1.21 tag artifact,
`use-podway` with its measured skill-tree digest, Podway `v0.2.14` with its
observed executable digest, and the uv-managed Python 3.14.8
interpreter), and the release-acceptance request derives its
`baseline_combination` from the profile in the driver's reported shapes (Podway `v`-prefixed). The candidate
profile is generated at bundle-build time from the sealed candidate artifact
through `host_bundle.py`: the plugin's own skill-tree pin is recomputed from
the sealed artifact's skills tree, unchanged dependency pins stay verbatim,
the `prior_version` edge is the stable plugin release, and the profile id
derives from the stable id. It is committed with bytes equal to the sealed
copy at Task closeout. TASK-090 promotes the exact candidate profile sealed
for the tested commit `406f84cc58d14fbe827f81b138f6ffa268c9239b`; the earlier
TASK-089 seal remains historical evidence in Git. The profile identifier keeps
its generated `proposed-` prefix even after the pilot qualifies its bytes.
Committing the pair commits bytes already fixed at sealing. Promoting fixed bytes is not permission to
alter pins afterward.

## Qualified pilot and limits

TASK-090 qualified the installed policy-cutover artifact from commit
`406f84cc58d14fbe827f81b138f6ffa268c9239b`, development version
`v0.1.21-dev.406f84cc58d1`, using the full-combination profile above. Its sealed
plugin tree digest is
`899a278e42b9d5f35436bc076f1a5bffbd986855aaa3e0f702980f57d5e0d69a`;
the executable recipe tree digest is
`d375867673cc39f16f13f1ab095a690ef3f5fb35efcff259cfe7f723fa3cd9d7`.
The completion change promotes those exact profile bytes and noninstalled
documentation/test pins. It changes neither the qualified plugin payload nor
the executable recipes and does not claim installation of a newly stamped
completion artifact.

| Observation | Actual outcome and boundary |
| --- | --- |
| Baseline, install, upgrade and bounded migration failure/recovery | PASS with complete evidence and verified cleanup. Install restores product absence; the upgrade cases restore their declared prior stable. |
| Guard failure | Intentional FAIL, declared leftover and failed consumer cleanup; native Job cleanup is verified separately. |
| Manual hold and real observer disconnect | The same Job survives the owned host-observer signal. A deliberately unobserved discovery scenario yields INCOMPLETE; verified restoration does not turn that result into PASS. |
| Two callers, replay and queue handoff | Identical saved admission returns the same Job; a changed survivor receives native CONFLICT. Queued cancellation reaches CANCELLED, capacity-one ownership does not overlap, and a successor baseline passes. |
| Terminal cancellation | The settled PASS and its exported bytes remain unchanged after the native cancellation disposition. |
| Matched collection control/fault | Both Jobs intentionally remain INCOMPLETE. Withholding only the owned post-cleanup inventory adds a native required-output gap and removes exactly that artifact. The fault's delivered consumer cleanup stays unverified despite separately retained physical-restoration proof. A later baseline verifies its own starting state. |
| Uninterrupted release acceptance | All ten scenarios PASS in one manual Job, with complete evidence, verified native and consumer cleanup, all 44 exported files verified and all 376 members of nine bounded archives checked. |
| Actual stopped VM | Doctor reports a readiness gap; one admitted Job waits under `vm_not_started`, then the same Job returns PASS after Master's restart. A ready-VM admit-despite-gap attempt is refused without admission. |

The release transaction observes the pre-model ChatGPT identity, released setup
and meaningful prior state, the actual approved runtime update, prospective
approval before each terminal no-op setup record, upgrade/startup behavior and
stale-skill duplication followed by restoration across all inventoried scopes.
The Task startup needed external fixture-operator staging of its three declared
files after the native sandbox refused index writes. Genuine assignment-coverage
and report-selection corrections preserved original failures; a new native
cumulative handoff distinguished earlier implementation from current checks.
The Epic startup needed no external staging. These assisted observations retain
their actual scope.

The Task stopped at `document`; the Epic stopped at `record-evidence`. Their
remaining global criteria and selected technical review stayed unfinished.
Neither startup PASS establishes full fixture completion, future release-role
behavior or Master's overall EPIC-019 acceptance. A recurring observer teardown
`EPERM` produced an earlier `UNKNOWN` reconnect observation; its cause remains
unproven, and later same-Job terminal/export evidence does not rewrite it.
Haepari's advertised `qualified_backends` array remains empty, separately from
the observed producer and Aquarium combination evidence.

The original pre-implementation local baseline receipt is unavailable. A later
supported-toolchain rerun of the starting HEAD passed; it cannot establish when
the original baseline ran.

Earlier TASK-088/089 results retain their original artifact and harness scope.
They are not substituted for this final-harness pilot. Every later release
retains its exact-candidate verification and distribution-identity obligations.
Host activation, publication, producer rollout and shared legacy retirement
remain separate. [ADR-0010](../../docs/architecture-decision-records/0010-haepari-vm-verification-and-advisory-locks.md)
records the adopted architecture.

## Host-submitted managed VM suites

VM and SSH registration stay with the native operator. A new or replaced
Haepari binary may need macOS Automation approval for UTM access; registration
can return `PREREQUISITE_UNAVAILABLE` until the operator approves access. Report
that gap and follow the authorized native registration plan after approval.

TASK-088 adds the separate host wrapper `make test-vm-host HAEPARI=<absolute
CLI> RESOURCE=<registered id> MODE=auto|manual RUN_DIR=<private physical
0700 path> SUITE=<suite|all> GUEST_CONTEXT=<private guest-context json>` over
the installed Haepari release controller (`HAEPARI_HOME`). It is invoked only through explicit
VM-test or release-handler authority, never from ordinary `make test` or automatic Task/Epic
checks, and the guest-side `make test-vm` gate above keeps its own contract
unchanged when invoked directly or inside a held Job. Under the managed policy qualified by TASK-090
(see [Haepari VM operations](../../docs/ops/haepari-vm-verification.md)),
Aquarium-owned installation-dependent
checks targeting the registered shared `utm-macos` VM acquire one outer-boundary
managed Job on that controller and resource before guest mutation, while guest
entrypoints (`make test-vm`, `tests/vm/recipes/guest_entry.sh`, and nested
handler fixtures) run inside the held allocation without recursive resource
acquisition. `Makefile` defines `override PYTHON := .venv/bin/python` when
`.venv/bin/python` exists in the current working tree and `override PYTHON :=
python3` otherwise, so passing `PYTHON=<path>` on the `make` command line is
ignored. Callers in the primary checkout use `.venv/bin/python` automatically;
callers in a clean disposable clone (where `.venv` is absent) and
the nested `make aquarium-dev-build` in `tests/vm/host_bundle.py` resolve
`python3` from `PATH`. The producer
(`plugins/aquarium/tools/aquarium-dev/build_aquarium_artifact.py`) builds the
marketplace tree from a clean clone of `AQUARIUM_VM_CANDIDATE_SHA` and returns
`git_sha`, `development_version` `v<version>-dev.<sha12>` and `sha256` in its
manifest, saved as `bundle/artifact-manifest.json`.
Prepend the verified repository Python environment
(`<repo-root>/.venv/bin`) to process-local `PATH` before invoking `make test-vm-host` or
`<repo-root>/.venv/bin/python -B tests/vm/host_wrapper.py`. The wrapper refuses
to run inside a managed guest context, never performs a VM power operation
(Master alone operates `utmctl`), and never installs a candidate on the host.

The wrapper persists every request key and exact spec in `RUN_DIR/run.json`
before the first submission, submits each consumer-declared suite once as a
`haepari.job/v2` Job, observes through native blocking `wait` (`AQUARIUM_VM_WAIT_TIMEOUT`,
integer seconds, default `900`, and `AQUARIUM_VM_WAIT_ROUNDS`, default `480`) and the blocking
event path to `awaiting_manual`, and reconnects an existing Job from the saved
run directory without creating a replacement Job. Terminal verdicts map to
wrapper exits 0/1/3/4 with the native verdict cross-checked; a caller wait
timeout reports PENDING with exit 5 and never cancels the Job; transport or
storage uncertainty reports UNKNOWN while preserving the native exit; exit 2
is classified by envelope code (`RESULT_UNAVAILABLE`, `CONFLICT`,
`INVALID_REQUEST`) and kept distinct from exit-6 uncertainty; GNU `make`
collapses any non-zero recipe exit to `2` while captured stdout and the wrapper process exit preserve its exact disposition;
`RUN_DIR/run.json` retains per-Job observations. Each suite
result reports the native `workload_outcome`, `evidence_completeness`,
`cleanup_outcome` and the recipe's `consumer_cleanup` separately; missing
observations or failed consumer cleanup never produce PASS, and `SUITE=all`
selects all nine suites alphabetically using each suite's first declared mode,
without filtering by `MODE`; a nonzero result skips later suites. Select
explicit suites for a passing batch and retain deliberate failure or unobserved
cases separately. Suite phases are budgeted inside the registered resource-v2
ceilings, each queue budget satisfies the queue-deadline rule for
capacity-one resources that Haepari v0.1.0 documents in
`docs/contracts/configuration.md` ("Queue deadlines for capacity-one
resources"): `queue_seconds >= (jobs ahead + 1) * 26100` (checked against
the live queue before each fresh submission), and reconnection never
extends a deadline. The 26100 s multiplier is the resource's maximum Job
duration under its registered ceilings: the manual path's prepare 1800 +
manual 21600 + collect 900 + cleanup 1800, which is longer than the
automatic path with its 7200 s run ceiling.
Known behavior: a wrapper terminated by a signal stops observing only. A
native `haepari wait` or `events --follow` child it started may continue
until its own timeout or the Job's end; those children are read-only, change
no state, and reconnect never depends on them.

The live TASK-088 results were produced against the tested artifact from
`b7c227e`, development version `0.1.21-dev.b7c227e301a9`, with harness tree
`b27a75c2a5b96addfcfecb19304fef7ad8578c8eebc5f3ab6243f10246a398ab`. The final
Task commit differs from that tested artifact only in documentation bytes,
for example `plugins/aquarium/references/haepari-integration.md`, and an
artifact built from the final commit carries that commit's own development
version stamp; the results never describe the final commit as the
tested installed artifact, and TASK-089/090 re-verify the release candidate.
TASK-088's suites remain historical evidence on harness `b27a75c2…`:
TASK-089's changes to the shared snapshot scope, helpers and derivation are additive, no
recorded suite's control flow changes, and every changed path is exercised by
J-RA itself; TASK-090's pilot re-runs install/migration/regression/manual
evidence live on the final harness. TASK-089 seals its candidate artifact from
the committed `db13284` (development version `0.1.21-dev.db132845624c`) with
the harness again a labelled development snapshot, and the committed
candidate profile equals that seal's bytes.
Earlier runs on two superseded harness trees are preserved and disclosed as
records of the same demonstrations. The admit-despite-gap probe's record of
the doctor gap was added after its single live run, whose gap was observed
with doctor before submission and whose blocker Haepari recorded natively.

`GUEST_CONTEXT` is mandatory for a live submission and carries only
machine-local values that never enter tracked files: the expected guest UUID,
guest home and `PATH`, the uv-managed Python 3.14 interpreter path,
the driver interpreter chosen at the J-0 gate, and the guest Codex, Podway
and marketplace paths. A tracked example shape is
`{"schema": "aquarium.vm-guest-context/v1", "expected_guest_uuid": "<uuid>",
"guest_home": "<absolute>", "guest_path": "<absolute PATH>",
"guest_python": "<absolute>", "guest_codex": "<absolute>",
"guest_podway": "<absolute>", "guest_marketplace_name": "<name>"}`.

The declared suites are `baseline`, `install`, `upgrade` (which carries the
existing-behavior oracle, fixture gate and restart checks inside its
post-upgrade assertions), `migration-failure`, `manual-hold` (a minimal
offline hold carrying the manual-path demonstrations, including the
kill-and-reconnect reconnect proof), `release-acceptance` (TASK-089's one
uninterrupted release-acceptance Job) and the labelled probes
`guard-failure-probe`, `immutability-probe` and `vm-blocked-probe`; the
immutability probes must queue behind a Job that holds the resource long
enough to perform the mutation and replay steps, and the demonstrated live
choreography queued them behind `manual-hold`'s `awaiting_manual` hold,
because `migration-failure` finishes in under a minute. The recipe comments,
the manual-hold scenario and the tests use live-sequence labels for these
suites: J-BASE is `baseline`, J-A `install`, J-B `upgrade`, J-M
`migration-failure`, J-F `guard-failure-probe`, J-H `manual-hold`, J-Q
`immutability-probe` and J-V `vm-blocked-probe`; J-RA is
`release-acceptance`. The sealed bundle carries the candidate artifact and its build
manifest from a clean committed checkout, the prior v0.1.21 artifact from its
tag, the full-history candidate Git bundle, the harness recipes as a labelled
development snapshot, the profile files and the hash-locked fixture
requirements resolved before admission. The guest entrypoint `tests/vm/recipes/guest_entry.sh` refuses to
run without the managed runner's Job/lease context, and every recipe runs the
committed candidate's guest identity guard before any guest mutation,
captures real `aquarium.vm-inventory/v1` inventories over
`(installation_scope, relative_path)`, stages its declared outputs, and
finishes recipe-owned consumer cleanup with a verified post-cleanup inventory
before workload exit or `manual complete`. The `manual-hold` suite carries
every manual-path demonstration TASK-088 owns: the hold itself, evidence
staging, verified consumer cleanup before `manual complete`, one
deliberately `unobserved` scenario yielding native INCOMPLETE, and the
kill-and-reconnect demonstration — reconnecting the same `RUN_DIR` to the
same Job ID for a terminal verdict with receipt-verified export reuse. A
verified export consumes Haepari v0.1.0's real layout: Job-relative outputs
live under `artifacts/<path>` inside the export directory, the manifest's
`files[]` lists exactly `artifacts/…`, `output.log` and `recovery-…` entries
with matching digests, and the consumed suite result is
`artifacts/results/<suite>/result.json`.

The manual-hold operator run: `manual-hold` declares two manual scenarios
(`fixture-check` and `discovery-check`) and five required outputs
(`results/manual-hold/{result.json,inventories.json,smoke.json,consumer-cleanup.json,post-cleanup-inventory.json}`).
When the Job reaches `awaiting_manual`, take
the workspace root from the `manual_preparation_stopped` event's
`workspace`. Enter `<workspace>/harness` and invoke
`/bin/sh tests/vm/recipes/guest_entry.sh --suite manual-hold --phase
consumer-cleanup` there with the saved spec's `workload.environment`, plus
`HAEPARI_PARENT_CONTEXT` read from `../operator-parent-context.json`
relative to `harness` (that is, `<workspace>/operator-parent-context.json`;
mode 0600, written by the suite's setup, removed with the Job root, never
a declared output). Stage the evidence, then run `haepari manual complete
<job-id> --input <completion-json> --expected-revision <n> --json`. Never
print the context value in logs or reports.

The `release-acceptance` suite (J-RA) is the one uninterrupted
release-acceptance transaction: its `machine-prepare` phase runs inside
`prepare_seconds` (sealed-input verification, declared abort-residue
normalization with a preimage persisted before any effect, prior-stable
establishment, fixture seeding, locked dependencies, the non-secret guest
Codex identity and the prior-stage skill identity over content identities),
and every later phase is an operator step over the same held resource
invoked through `guest_entry.sh` with the saved environment and context, in
the order the [runbook](recipes/scenarios/release-acceptance.md) gives:
released setups, preservation prerequisites, baseline capture, candidate
install, skill identity over the five inventoried scopes, the
approval-based status-runtime update through the named `dev-setup-global`
continuation before any candidate repository setup, then managed updates,
the EPIC-024 startup smokes (VM-UPGRADE-01, VM-TASK-START-01 and
VM-EPIC-START-01 through `make test-vm`, bound to the current invocation),
the stale-skill failure and restoration scenario, evidence staging,
consumer cleanup and the manual completion. Evidence transport is fixed
before admission: one deterministic tar per case under
`results/release-acceptance/evidence/` with a content manifest whose
required record classes follow the producers' writers (the startup cases
archive the case directory with its referenced child reports, the native
observation and checks under the driver's own names). Baseline and setup
archives also carry native setup observations, including recovery captures,
with their recorded digest bindings checked. Every driver window requires
its input, JSONL and stderr originals; setup windows require before/after
records as well. Every case is attempted, existing originals travel in the
declared outputs, and each manifest names its missing required records.
`ok` stays false while a gap remains. A retry invalidates the earlier
success and withdraws its previous declared archives and working files
before rebuilding. Source originals and unrelated outputs remain in place.
Publication stays within the 32 MiB per-archive and 256 MiB aggregate bounds,
including interrupted retries; the controller pin is confirmed in preflight.
The suite's per-capture inventory files
(`inventory-prior-baseline`, `inventory-post-install`, `inventory-stale-pre`,
`inventory-stale-post`, `inventory-cleanup-before`, `inventory-post-cleanup`)
are declared outputs, and `inventories.json` aggregates every capture across
the phase processes. The suite's `manual.required_scenarios` are the ten
scenario ids of the completion record; missing observations stay
`unobserved` and prevent PASS. The queue budget is selected from the live
queue position before sealing (26100/52200/78300 for zero/one/two Jobs
ahead) and never silently clamped. Offline, the simulation drives every
fakeable phase for real and stops the smoke gate at its precise live-only
guest boundary; live results apply only to their recorded candidate, bundle
and installed combination.

Deliberate probes are labelled invocation paths, never production behavior:
`AQUARIUM_VM_PROBE=changed-survivor-replay` admits a Job, mutates a sealed
bundle copy and replays the same key to record the native `CONFLICT` while
the production reconnect guard stays intact; `identical-replay` records the
idempotent same-key admission; `admit-despite-gap` submits the VM-blocked
probe although `doctor --resource` reports the expected VM-not-started gap,
records doctor's gaps, or its error, in the run record, and refuses when
doctor reports neither.
`AQUARIUM_VM_CANCEL=1` cancels the admitted Job of an existing run through
the native revision-fenced cancel. On a first-ever resource the queue
projection may report `unknown_occupied_execution` because no
`managed_vm_observations` row exists yet; it is expected first-use state, not
an occupancy blocker, and preflight uses `doctor --resource`, not the queue
projection.

Host wrapper, bundle sealing, recipes and offline tests are covered by unit
tests built from real envelope shapes; they exercise guards, record-before-
submit ordering, reconnect, exit classification, queue sizing, probe paths
and inventory identity without a controller, VM, network or LLM. Live
results apply only to their recorded candidate, bundle and installed
combination, and remain separate from the release-QA contract and the
EPIC-024 historical manual results.

## Directory guidance development verification

[Directory guidance scenarios](directory-agent-guidance.md) define five manual
groups covering EPIC-029's 13 acceptance scenarios. The
[independent base fixture](fixtures/directory-guidance/) has two implementation
areas, existing local instructions, legacy and code-adjacent canonical contracts
and executable baseline checks. It starts without a directory-guide adoption
declaration. Separate empty greenfield and authority-free bootstrap repositories
are prepared only under the scenario operator's approved scope.

Installed results apply only to their recorded candidate and combination and
stay outside these definitions. Use the dedicated UTM VM and the
candidate, authority, preservation and evidence rules above. These manual groups
have no driver operation and are outside `make test-vm` and the adaptive suite.
Their outcomes and installed native-loading claims remain unverified until observed.

## Adaptive development verification

EPIC-026 extends this driver with committed
[case descriptors](fixtures/adaptive/cases.json),
[semantic checks](adaptive_cases.py) and an
[intermittent diagnosis fixture](fixtures/adaptive/diagnosis/sampler.py).
TASK-145 prepares these tools; actual installed observations belong to TASK-146.
The existing release `run` suite still verifies upgrade preservation and explicit
canonical Task/Epic startup. Its fixed node assertions apply only to those
source-selected regressions. Development cases exercise different actual
producer/evidence/Decision structures and their admitted mappings.

Use the same guarded external request, exact clean candidate and tools. Set
`"suite": "adaptive-development"` to identify development intent and use the
explicit guest commands below. `run` and `make test-vm` are release-only and
reject that suite; they never substitute adaptive results for release acceptance:

```sh
<supported-python> -B tests/vm/run_acceptance.py seed-development --request <request.json>
<supported-python> -B tests/vm/run_acceptance.py development --request <request.json>
```

`seed-development` creates seven separate case directories. It refuses existing
paths. Use installed approved repository setup for Git-backed cases; leave
`adaptive-project` without `.git` or `.podway`. Do not manufacture released
upgrade baselines with candidate sources. Development execution still verifies
clean matching candidate checkout, artifact and installed bytes, native plugin
registration, fresh installed skill discovery, exact tools and guest identity.
An existing per-case candidate/combination/authority binding prevents reusing old
results or handles as a pass for a different candidate. Public native collection
must complete and every started descendant must settle.

The default development run covers all seven entrypoints. Optional
`development_cases` selects explicit case names for affected re-verification;
report that subset as partial evidence. `case_leaves` may select additional
supported upstream leaves for a case while retaining its declared due leaves.
The selected current-home Ouroboros package/rules/skills/MCP prerequisites must
be configured; actual leaf results must link to completed public native
operations. Configuration alone does not prove live provider behavior. When PM
is selected, include actual `clipboard_authority` with `source: user`,
`replace: true` and its authority `reference` before invoking it. No clipboard
permission is required for cases that do not use PM. The driver never installs,
repairs, reads the previous clipboard or silently waives a missing prerequisite.
Select an existing compatible interpreter with YAML and `jsonschema`; system
Python and a repository-local development environment are not assumed. Invoke
`development` directly with that interpreter; the ordinary Make interpreter
selection remains unchanged. Development success and failure use
`aquarium.vm-adaptive-result/v1` at `adaptive-result.json`; release `run` uses
`aquarium.vm-acceptance-result/v1` at `result.json`.

Each case captures original assignments and actual returned ordinary v3 reports
inside its own `<case>-capture` directory, the only adaptive `--add-dir` scope.
Driver-owned original recursive product images and candidate bindings live outside
that agent capture, under `adaptive-state/<case>/`, including on same-thread
resume. Product images exclude only `.git`, `.venv`, Python caches,
`.podway/runtime`, local `.podway/procedures/.local` and `.candidates` bundles,
`.ouroboros/artifacts`, and `.gaori/runs`; tracked files remain included even
under an excluded directory.
All other product files, including ignored files, documents and managed sources,
are included. The entire changed path set and each before/after image must equal
the actual approved document proposal. These document-only fixtures permit
approved Markdown (`.md`) targets at custom roots as well as their existing
paths; consent cannot authorize edits to product code or new implementation.
This is fixture scope, not a production path policy. Reasoned no-change requires
an empty string diff, empty targets, unchanged bytes and a nonblank reason;
every proposal diff must be a string.
Reports identify assessed files as `target.files`, a relative-path to SHA-256 map. The driver correlates real native
Executor/Evaluator children and complete returned results; cold validation can use a
Evaluator without an unused corrective Executor. It compares every due original
criterion, current target bytes and the case oracle while preserving future
unverified rows. Synthetic unit reports prove only the checks, never installed
agent behavior.
Assessed-file and upstream-result digests accept the same optional `sha256:`
prefix; candidate and native binding identities retain their specified formats.

Git-backed adaptive cases recover the current exact source/binding through the
installed public context helper. Their family, source bytes, native tuple,
current role and selected producer/item values must agree. Adequate known reuse
requires the installed public context's `qualified-known` result and exact bytes
of the installed released family source. The collector reports `known-reuse`
separately from `structurally-adapted`, which requires an actual producer/evidence/
Decision difference. Edited bytes or renamed placements alone cannot establish
either claim. Fenced native evidence reads must include the real returned Evaluator
report or its exact content digest. This instrumentation belongs only to these
VM cases and adds no ordinary startup receipt or authentication protocol.
Non-Git project verification checks documents and absence of Git/Podway without
invoking a native observer on that branch.

The declared cold-validation fixture includes `original-epic-validation-completion`
alongside the three audit/process criteria. Its expected negative assessment keeps
that original completion row `unmet` or `unverified`, with current source and
evidence, while the three process rows remain met. The original report retains
`rework` or `evidence-needed` and `goal_outcome: not-achieved`; operation completion
and a passing negative-case oracle do not establish goal achievement. The live
native goal must retain all four obligations and cannot mark original completion
satisfied or determine achievement. Other cases retain their positive checkpoint
and met-row requirements. The later normal stopped completion must separately
establish native `not_achieved` in the installed observation. A terminal session
without live guidance remains incomplete for this semantic-checkpoint collector.

Document cases require a real operator reply through the existing `reply`
operation, using the actual case handle. For the test capture, send one JSON
object with `schema: aquarium.vm-document-decision/v1`, `decision: approved`,
an explicit decision `reference`, and the full exact `proposal` object.
The saved `application_approval` must match that actual public user message.
Rejected/request-changes decisions, agent messages and quoted proposals cannot
supply approval. Recheck current postimages after application. This capture
format is VM instrumentation, not a new product approval exchange.

The diagnosis oracle preserves product bytes and reproduces missing samples at
sequences 2 and 5. Capture original expected/observed evidence, competing isolated
experiments, actual raw QA and faithful incomplete/no-work or established
conclusions. No particular conclusion is forced to make the fixture pass.
Design cases preserve product code and require specifically approved documents;
non-Git planning cannot initialize a repository merely to run Podway. Missing
reports, prerequisites, approvals or selected evidence remain incomplete.
Failure preserves native handles and original observations for same-operation
recovery. Run results never grant final Task, Epic or release acceptance.

The development collector checks the first due semantic checkpoint. Continue
the same thread through `reply` for later delivery, review, actual acceptance
and finalization. Before re-collection, preserve `adaptive-result.json` and each
case's `native-observation.json`, which re-collection can overwrite. Classify the
new invocation from its actual stdout and exit status. Keep the original checkpoint
evidence: after progression or completion, native evidence selectors may no longer
expose that earlier consumer. Verify later effects against the original reports, native history,
current source and goal-assessment mapping rather than replaying work to restore
an old selector. Without live placement, collection reports `incomplete`; this
does not assess historical achievement. A completed lifecycle alone does not
prove achievement.

When integration requires a correction, retain each observation's original
candidate and tool basis. Install the committed correction and verify the
affected behavior with matching tools. A combined assessment may reuse unchanged
earlier evidence only with its applicability established; identify the observed
candidate, later runtime and evaluator separately. Do not rewrite an immutable
case binding, relabel an earlier result as a new candidate pass, or report a
partial or manual assessment as an automatic all-case pass. Preserve failed
collection results alongside any independently verified native evidence.


## Podway v0.2.15 adoption suite

The [Podway upgrade scenario](recipes/scenarios/podway-upgrade.md) owns the explicit manual `podway-upgrade` suite, its exact external release input, seven original-evidence cases and consumer restoration. The bundle retains stable v0.2.14 and creates a separate sealed v0.2.15 candidate profile. This is preparation for EPIC-034; it establishes no installed result before native manual completion and actual functional observation. Existing qualification records retain their original identities and limits.
