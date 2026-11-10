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

Release acceptance requires the sealed `AQUARIUM_VM_PODWAY_RELEASE` input and
uses `podway-candidate`. Its successful final state retains the tested Aquarium,
Podway v0.2.16, paired skill and candidate status runtime in the dedicated VM.
Original baseline fixtures remain separate from fresh generation-2 candidate
workspaces. Consumer cleanup verifies the retained installation and settles
run-owned temporary effects. Other suites keep their declared cleanup contracts.

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
selects every configured suite alphabetically using each suite's first declared
mode, without filtering by `MODE`; a nonzero result skips later suites. Select
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
continuation before any candidate repository setup, the separate
approval-based shared `aquarium-python` environment preparation through
the same continuation, then managed updates,
the EPIC-024 startup smokes (VM-UPGRADE-01, VM-TASK-START-01 and
VM-EPIC-START-01 through `make test-vm`, bound to the current invocation),
the bounded release-handler plan-readiness startup, the stale-skill failure
and restoration scenario, evidence staging,
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
Consumer cleanup checks the final inventory against the released baseline.
It allows the retained installation, approved setup status records, native
plugin-cache updates, and the candidate digest's shared Python selection,
installer lock and environments created in recorded reply windows. Prior
environments must remain unchanged. It reports unrelated changes, missing entries and leftovers.
The upgraded installation remains in place.
The suite's per-capture inventory files
(`inventory-prior-baseline`, `inventory-post-install`, `inventory-stale-pre`,
`inventory-stale-post`, `inventory-cleanup-before`, `inventory-post-cleanup`)
are declared outputs, and `inventories.json` aggregates every capture across
the phase processes. The suite's `manual.required_scenarios` are the twelve
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

The [Podway upgrade scenario](recipes/scenarios/podway-upgrade.md) owns the explicit manual `podway-upgrade` suite, its exact external release input, seven original-evidence cases and consumer restoration. The bundle retains stable v0.2.14 and creates a separate sealed v0.2.15 candidate profile. Preparation alone establishes no installed result; native manual completion and actual functional observation are required.

EPIC-034's installed qualification passed on Aquarium candidate
`fd1e40e5304ff9f4bde6920bf0188a6a7c3b7268` with the official Podway v0.2.15 CLI
and complete release-pinned skill. All seven cases passed: released baseline,
writer refusal, approved runtime reset, fresh skill discovery, actual Task and
Epic startup with initial Executor/Evaluator progression, and consumer
restoration. Native evidence collection was complete, consumer and Job cleanup
were verified, and the shared resource was released. The earlier failed run
remains a separate failed result.

Master accepted the overall Podway adoption after this qualification and the
complete local test gate. The later test-fixture formatting correction preserves
Python semantics; it and the closeout documentation do not constitute another
installed run. This result retains its exact candidate binding and covers the
observed Codex paths. Each release still requires its own exact-candidate
release-acceptance result; existing qualification records keep their original
identities and limits.


## Native Squad installed cases

The [Squad scenario](recipes/scenarios/epic-squad.md) owns the separately
authorized manual `epic-squad` suite. It uses the existing sealed official Podway
dependency and baseline/candidate/restoration recipe, retaining the ordinary
profiles and suites. Its [inventory](fixtures/squad/cases.json) maps every original
native/shared scenario to finite grouped cases while keeping each observation
separately due. Record actual Codex/Claude results and the observed candidate for
multi-Task delivery, Handler continuity, negative evidence and recovery. Reuse of
earlier originals requires an explicit unchanged-branch applicability basis and
its limits; changed behavior requires its own installed observation. Source
checks do not establish those results.

`native_observation.py` captures an existing Codex operation and its public
descendants without another provider turn; it reuses the adaptive product-image
collector. Capture files establish neither semantic passage nor settlement. Keep
original reports/configuration and actual available counts/durations, with
unobserved harnesses and costs explicit. Separate functional verification records
actual installed behavior under the executor Master selects. TASK-151 assigned
the historical SSH/UTM verification to the coordinating agent. TASK-156 assigns
current mixed verification to that agent using the exact committed candidate and
matching harness. Historical TASK-151 observations retain their recorded candidate
and scope. Setup, source checks and a native Job verdict alone do not establish
the current functional result.

The current thirteen-case suite declares 34 collected outputs: thirteen fixed
case archives, thirteen content manifests and eight JSON files. The complete
output set is `suites.epic-squad.required_outputs` in `host_suites.json`. After
actual consumer restoration and its receipt/inventory
capture, the same held Job runs `--phase stage-evidence`; no candidate reinstall
is needed. Original role/capture/check bytes live in the case archives rather
than only in metadata references. Partial or unsafe evidence keeps staging
incomplete, and native collection/export digests remain separately required.

The Squad scenario stages declared original evidence at case checkpoints and
before restoration or an authorized early stop. Pre-cleanup staging can remain
INCOMPLETE while preserving available originals. Cleanup seals its pass receipt
immediately; final staging adds that receipt and the actual inventory. A failed
or interrupted staging attempt retains its progress and the last complete
archives for same-Job retry. The six-hour window and cleanup reserve are planning
assumptions. Historical collection timing and capacity observations below apply
only to their recorded candidates and collected output sets; current TASK-156
fit remains to be observed.

### TASK-151 candidate observations

Campaign records attribute the historical member and Master observations to the
`536a53dbc83306a436f7dde3b31e3219b2609255` source line. The two later campaigns
installed `a545c2b3065e981d8db003fbcfe1dbe9408e2a7f` with Codex and official
Podway `0.2.15`, after observing the released Aquarium `0.1.21` / Podway `0.2.14`
baseline. The historical Master interaction's candidate binding comes from its
campaign records; its public turn does not identify an installed Git commit.

The `536a53d` to `a545c2b` production change adds Task-owned pre-validation
remediation to the existing assessed member-scope predicate. Ordinary member
and Validation paths are unchanged. Earlier observations apply only to those
unchanged guarantees. Historical Squad Evaluator continuity includes a logical
replacement and inherited conversation context; physically uninterrupted
execution was not established. Imported product baselines do not restore the
historical commits or sessions.

Runtime identifiers and original records for the historical and both
`a545c2b` campaigns remain with the producing tools and workflow handoff, under
the evidence-residency contract.

| Area | Observed candidate and campaign | Established scope and remaining limit |
| --- | --- | --- |
| Native Squad delivery | Historical `536a53d` member campaign; first `a545c2b` campaign | The historical campaign supplied both member plans, independent assessments, checks, accepted commits and native handoffs. The first `a545c2b` campaign completed a Task-owned pre-validation correction and assembled integration, including a correction inside the same Validation, whole-fixture review and fixture-operator-accepted closeout. |
| Contract defects and local closure | Historical `536a53d` closures; first and followup `a545c2b` campaigns | Historical editorial and display-expectation repairs retain their original scope. In the first `a545c2b` campaign, a repeat cap and empty-name fallback survived green tests; direct probes and independent judgments exposed them and repairs added regressions. The followup's false numeric expectation retained its false green. Restoring the oracle produced a strict red at an intermediate Milestone before product repair; the final 17 direct CLI cases and full Make gate each ran once. |
| Handler continuity | First `a545c2b` campaign; followup parent-record correction | Two committed member deliveries retained one logical Epic Evaluator, Task Operator assignments and original schemas, with no separate Task Evaluator or mandatory support. The original lifecycle result failed: both Tasks were Completed while their parent Epic remained Planned. The followup corrected only the parent record and completed its commit and native handoff. Its actual dirty review target and the earlier review-ordering incident remain assurance limits. |
| Cold validation | First and followup `a545c2b` campaigns | The first cold case stopped on a Goal that required later acceptance and terminal effects too early. The followup retained a failed record-only re-entry as a separate failure. A distinct fresh cold fixture then used a fresh Coordinator, Evaluator and three technical views on unchanged imported product bytes; actual fixture-user acceptance preceded achieved completion and not_required finalization, with no empty commit. |
| Requested record changes | Followup `a545c2b` campaign | A genuine fixture-user request followed the normal changes-requested route into a local record clarification. Renewed exact-content acceptance preceded one authorized correction commit and native handoff, reusing applicable product checks and technical review. The original inconclusive EE result, original TO's targeted result-representation recovery and Coordinator's finite closure remain separate. |
| Design continuation | Followup `a545c2b` campaign | The missing dossier triggered Design. An actual Seed and one QA pass preceded separate Design, document-diff and result approvals. The predecessor produced the canonical input commit. After its missing final-assessment route was disclosed, an approved qualified successor refreshed the original criteria and recorded handoff without another commit, QA run or technical team. A genuinely new Squad conversation produced an initial plan before an execution envelope or product work; its first capacity failure and same-thread recovery remain recorded. |
| Input resolution and opt-out | Followup `a545c2b` campaign | Four invalid profile/input classes were rejected before affected-role or Design dispatch; the inputs remained unresolved. A separate fresh pre-session Podway opt-out produced ordinary native first-plan responses and stopped before product work. These cases do not establish refusal of a valid explicit profile or supplied-profile preservation through Design return. Both are required native-phase EPIC-027 observations; external role execution belongs to EPIC-028. |
| Retained Goal and Validation sources | Followup `a545c2b` campaign | Goal 37 and Validation 36 fixtures were admitted under released Aquarium with the supported Podway `0.2.15` writer. After the caller update, native session, source, binding and pending duties were preserved, and the installed candidate helper returned `dispatch-ready` for each retained source. This proves that bounded caller update and recovery; the earlier failed engine-Store migration and admission-order incident remain separate. |
| Harness coverage | Both `a545c2b` campaigns | Codex observations remain bounded by the applicable cases. Guest-native Claude cases remain unverified; its observed guest CLI was logged out. Host static review supplies no guest functional result. Public controls establish neither private backend identity nor technical isolation. |
| Master functional result | Historical `536a53d` status/ownership interaction | The completed read-only interaction and the response Master supplied are retained. Master's own assessment of whether it worked remains unverified. The unchanged Validation behavior permits bounded historical applicability, but an agent judgment or approval to continue cannot supply that human outcome or overall Epic acceptance. |

TASK-151's current functional verification is agent-executed in UTM through SSH,
using the exact committed Aquarium candidate and version-matched tools. Retain
the missing historical personal appraisal separately from that actual installed
result and Master's later overall Epic acceptance.

The first and followup `a545c2b` campaigns used disclosed host-only harness
snapshots, separately from the clean committed plugin payload. Their harness
content identities and effective phase budgets were:

| Campaign | Harness tree SHA-256 | Prepare / manual / collect / cleanup budgets (seconds) |
| --- | --- | --- |
| First `a545c2b` campaign | `4c469880a02df72c003555b0d2eada0090bf6c44866aaddd8f0ba3799eb02da0` | 900 / 21600 / 900 / 1800 |
| Followup `a545c2b` campaign | `f78b68ee4afe594b478fe21279c42be044ad8e4575c9ee405c2c274983c4bd85` | 1800 / 21600 / 900 / 1800 |

Both used a 26100-second queue budget. The followup actually ran scenario guide
SHA-256 `845db2901fc3cba015eeeaddb4d7e46c5b99a6689db8804e749a71dff609fa1f`;
the first campaign used an earlier guide. Their collection phases took 726.894
and 725.183 seconds respectively, within the declared 900 seconds. The committed
suite's former 600-second collection default was below both observations. It
now declares 900 seconds; the campaign-specific prepare and cleanup overrides
remain distinct from the suite's unchanged defaults. These observations bind the
recorded snapshots and effective budgets, not every later harness revision.

The historical native-phase inventory contained 68 rows with `observed: false`.
The current [inventory](fixtures/squad/cases.json) retains those rows and adds
mixed scenarios, for 94 rows. Historical observations, applicability and
per-harness outcomes remain in the workflow's 68-row evidence projection with
the producing tools. Conditional variants, unavailable measurements and
unobserved Claude cases remain explicit. No all-scenarios or all-harness pass
was established.

The followup exercised the revised cold-scenario Goal guidance: decision
readiness was assessed before acceptance and terminal effects, which remained
mandatory later postconditions. The original contradictory Goal and failed
paths remain unchanged. The superseded Design session's archive renders its
criteria unassessed; original pre-transition outputs retain those assessments.
The successor freshly assessed the unchanged criteria, so the archive view is
not proof that earlier statuses were preserved.

Both native campaign results remain `INCOMPLETE`, with failed workloads and
partial functional evidence. The followup's actual manual form records baseline
and consumer restoration as pass, integration closeout as fail, and seven other
groups as unobserved. These group outcomes remain separate from the bounded
positive paths above. All 28 declared outputs and the empty native log were
exported, with 10 opaque TARs containing 3,216 regular members in total. The
largest TAR contains 1,388 members; native whole-file collection limits do not
apply that count to opaque TAR contents. Native collection and cleanup were
verified, and the Job released its resource.

#### Corrected findings and profile-bearing Design return

A later campaign installed Aquarium candidate
`92d3d3d05545d181412ecf75548ba7dd9714c9ce` with Codex `0.164.0` and the official
Podway `0.2.15` binary and complete paired skill. It first observed released
Aquarium `0.1.21` / Podway `0.2.14` and saved fresh consumer preimages. The full
installed payload matched the sealed candidate artifact.

Fifteen controlled calls used the installed composition consumer. Ten cases with
unresolved named findings blocked readiness, including missing or unknown states,
required/blocking markers, conflicting optional labels and Task Operator or Epic
Evaluator findings. Five positive controls retained readiness: the original Task
and Epic plans, a supported settlement, explicit optional advice and attributed
future scope. Every plan outcome remained `not-achieved`. These observations
cover the installed pure consumer; source regressions separately cover result
assessment and commit eligibility.

A fresh native invocation supplied the complete Task Evaluator profile
`codex / gpt-6.1-terra / low`, leaving other profiles omitted. It identified the
unsupported Herdr role before launch, preserved the profile and selected the
authorized unaffected Design continuation for the missing dossier. Current
fixture-user Design and document approvals preceded the exact document addition;
all 15 original files remained unchanged. The installed Design consumer retained
the caller, profile, omissions and pending commit boundary. An independent
ordinary application Evaluator passed all six current application criteria.

The fixture user accepted the applied result before one nonempty Design input
commit.
The installed consumer then emitted `new-conversation-required` with
`automatic_delivery=false`. A genuinely new native conversation received only
that exact request and retained the supplied profile and external-role blocker,
without Task delivery or native substitution. This was a bounded application
and return probe using unchanged historical Design content and quality evidence;
it established no fresh whole Design cycle or whole-fixture delivery.

The campaign used the clean committed harness, SHA-256
`445a30e00fc45caa68d61e5c63910daf15503a0d54df5ddc349d6d7b95ee8653`,
with effective prepare/manual/collect/cleanup budgets of
1800/21600/900/1800 seconds and a 26100-second queue budget. After all owned
actors settled, restoration preserved all 5,757 entries across the nine declared
consumer roots, including the released plugin and Podway binary/paired skill.
Native collection took 125.863 seconds and cleanup took 6.310 seconds; both
completed and the resource was released.

The native aggregate remains `INCOMPLETE`, with an inconclusive workload,
partial functional evidence and verified cleanup. Its manual form records nine
full groups as unobserved and consumer restoration as pass. The case index
separately records the selected observations above and earlier evidence's bounded
applicability. All 28 declared outputs and the empty log were exported; all 216
regular members of the ten case archives matched their manifests. This supplies
no all-scenarios or all-harness pass.

Checkpoint originals were delivered to the host during execution. The first
canonical evidence-staging phase ran after restoration, omitting the required
earlier staging checkpoints. The export preserves the final case originals;
the earlier caller-receipt version and operator records remain
separate host originals. That receipt's sole change appended verified precommit
activity; its original caller, profile and response fields remained unchanged.

The [Squad scenario](recipes/scenarios/epic-squad.md) defines future execution,
consumer restoration and collection. Required source checks, agent-executed
installed functional verification and Master's actual overall Epic acceptance
retain their separate boundaries.

### Disposition of earlier execution incidents

The Handler fixture left its parent Epic in the roadmap's not-started state
while both member Tasks were Completed. The observed cause was the omitted
parent record update. The reviewed base and candidate Handler instructions both
lack an explicit Epic-start reconciliation step; this is a preexisting guidance
gap, with no new role-mapping regression established. The followup repaired the
fixture record only. [DF-005](../../docs/deferred-feedback/README.md#df-005-reconcile-the-parent-epic-lifecycle-at-handler-work-start)
owns the independent preventive clarification.

The failed cold fixture took broad manual rework from record-outcome at revision
47 to prepare-validation-pass at revision 48, although revision 47 advertised a
narrower prepare-validation-assessment target. The selected pass-preparation
route could not truthfully represent record-only re-entry. This was an operator
routing error; it does not establish a new current-source defect. The original
NOT_ACCEPTED result remains. Before rework, select a currently advertised target
that supports the actual record-handling purpose. The separate fresh cold
fixture and later requested-record-change case do not change this failed result.

### TASK-156 candidate observations

Installed observations used Aquarium candidate
`d7b88d902099453c0a10a6a5ad6453533460ca5a`, official Podway `0.2.15`,
Codex `0.164.0` and Herdr `0.9.5`. They cover named configurations using the
same CLI. Guest Claude authentication was unavailable; Gemini and OpenCode were
absent from the declared guest PATH. Cross-CLI delivery remains unverified.

| Configuration | Actual observation |
| --- | --- |
| External Task Operators with native Evaluators | The first Task used separate Herdr authoring and independent reviewing Operators with native Task and Epic Evaluators. Actual member acceptance, commit and native handoff followed its required gates. |
| Native Task Operators with external Evaluators | The dependent Task used distinct direct Herdr Epic and Task Evaluators with a common explicit profile. Both plan scopes and first full result assessments were observed. A later directed profile change retained these original assignments and reports. |
| Native Epic Evaluator with explicit external Task Evaluator | The later phase retained native Operators and Epic evaluation with an explicit Herdr Task Evaluator. Original finding closure and current evidence composition preceded the dependent Task's actual member commit and native handoff. |

In that campaign, the explicit Task Evaluator used
`codex / gpt-6.1-sol / low`, a `read-only`
sandbox and `on-request` approval. Public launch records and the UI confirmed
the selected profile. Native inherited model and effort telemetry remained
unconfirmed. Assignment read-only scope establishes no operating-system
isolation, and public settings supply no private backend attestation.

An exact README spelling repair used document and integrity checks without a
Make rerun or product Evaluator recall. A separate controlled contract fault
broke repeated uppercase output and eight integration checks. Strict composition
rejected the old green candidate. The original affected producers retained their
negative judgments and supplied current finding-ID coverage after restoration.
Phase and report-binding corrections preserved original judgments, source
priorities and future obligations. Before the dependent Task was accepted, its
current composition had no outstanding finding or applicability gaps.

Recovery reused original public Coordinator and Evaluator conversations after
observations timed out or were truncated. It preserved all 23 tracked fixture files,
Git references, accepted history and grant consumption. The earlier native
database was absent. Supported preparation created a distinct physical Goal
from the exact retained source and binding; the verified member commit then
reached completed/achieved/handed-off in that new Goal. The absent historical
session remains unfinished history.

A controlled complete-name fault was assigned to the already completed first
Task. Its owner reopened the Task through a disclosed new physical Goal. Two
independent plan reviewers found that a combined Make invocation would stop
before capturing the CLI failure after the expected unit failure. The author
separated those commands before receiving Writer authority. The new guards
then exposed the fault in the renderer and both CLI paths; exact renderer
restoration passed the full serial Make gate with 41 tests. Four regression
cases made the separate correction commit substantive. The original member
grants remained consumed and were not reused. The owner Goal reached completed
with an actual handed-off result before the Coordinator restored the Task's
Completed status.

A bounded native Support Operator inventoried the last dossier's live references,
source captures and proposed file hashes. The Coordinator used those facts in
the exact disposition proposal. Separate original Epic and Task judgments closed
the integration findings, and a substantive Epic Evaluator assessment covered
the final record proposal. The fixture operator then accepted that exact result
and conditional proposal. This supplies no Master functional or production
acceptance.

The earlier campaign remains `INCOMPLETE`. Its unchanged cleanup check rejected
a raw configuration digest mismatch even after all eight later consumer
preimages matched. Its two missing recipe-owned cleanup receipts and transient
system-skill differences retain their original meaning. A separately approved
fresh baseline matched canonical preparation and exact consumer preimages before
candidate installation.

The exact final fixture records were committed once under the matured conditional
grant. The same Validation reached completed/achieved with an actual handed-off
result. All eight declared consumer roots then matched their saved preimages,
including file modes. The unchanged consumer-cleanup recipe returned
pass/verified and wrote both original cleanup receipts. Native collection and
resource cleanup have separate receipts; those operational results establish no
functional acceptance. At that campaign's close, Master's separate functional
verification remained unverified. The 94 scenario rows retain their individual
applicability and evidence gaps; these observations establish no all-scenarios or
all-harness pass.

A separately approved status fixture exercised profile validation and the
omitted-effort default on the same installed payload. Missing model, empty
profile, empty Task Operator list and conflicting common/scoped Evaluator
profiles were refused before the affected role launched. An unsupported effort
was rejected against the installed supported-control catalog; native diagnostic
commands themselves accepted that value, so no native CLI rejection is claimed.
The explicit Task Evaluator profile omitted effort and ran through Herdr with
HIGH reasoning. Whole-profile omission kept the native Epic Evaluator and Task
Operators on the current LOW Coordinator settings. Public controls were
confirmed where available; private backend telemetry remains unknown.

The committed status requirement established the intended display before the
Writer changed it. The source-only change from `Status: ready` to
`Status: complete` preserved newline, exit, stderr, import and working-directory
behavior. The original unit and integration tests then failed at their old
exact display literals. Required E2E cases skipped by the aggregate failure
were run separately. Independent first assessments covered the original product
meaning and retained these failures. The author changed only the two obsolete
literal occurrences. Referring tests and the previously skipped stage passed,
followed by the full serial Make gate with four unique tests. The source and
E2E bytes, inputs and assertion strength stayed unchanged.

The same first review also found stale Planned lifecycle records. A separately
scoped record correction and the original nonauthoring Task Evaluator's focused
confirmation resolved that finding. Current composition combined the preserved
first reports, verified literal closures, focused record judgment and green
checks. The native correction route therefore included affected confirmation;
it supplies no claim that the entire mixed issue set used only local closure.

A read-only comparison of the preceding campaign's retained outer-operator
supervision records counted
162 native waits returning 120,639 bytes and 226 visible main-pane inspections
returning 428,038 redacted bytes. Fifty-eight retained exact UI/control pairs
had intervals of 4.937 to 141.42 seconds, with a median of 19.4625 seconds,
from the first matching retained UI read to its control receipt. These intervals
are not event-onset detection latency. Event onset, exhaustive missed or false
recoveries, provider cost and a matched controlled baseline were unavailable;
the records establish no efficiency or savings result.

Under Master's delegated verification authority, the Coordinator completed a
separate installed ordinary Handler fixture in a fresh Codex context. It delivered
two dependent Tasks, paused after the first actual commit before native
finalization, and resumed the same conversation and Task session before delivering
the second Task. One continuous Epic Evaluator and the ordinary Task Operator
retained their roles; no Task Evaluator or Support Operator was added.

The integrated product passed the full serial Make gate with 32 tests and ten
separate Coordinator CLI checks covering exact positive output and invalid counts.
Three fresh whole-Epic technical reviewers returned complete reports without
findings. Internal Validation and the final readiness assessment passed. The
fixture operator accepted the exact final record proposal, after which the final
commit and same-session completed/achieved/handed-off result were verified. Both
member grants and the conditional closeout grant were consumed once. Original
negative reports and earlier unverified states remain intact alongside the later
actual effects. Complete public records account for the main conversation and all
eleven descendants, with completed latest turns and no nonterminal commands.
These are the Coordinator's actual Handler results; Master's final overall
EPIC-028 acceptance remains separate.

The separate native-only Squad fixture delivered two dependent Tasks with fresh
Task teams and one continuous Epic Evaluator. Both plan scopes preceded each
Writer assignment, and each Task had independent result assessments, exact
delegated acceptance, a separate actual commit and a verified native handoff.
The first Task also delivered a function milestone before CLI completion. The
integrated product passed 32 tests and ten separate Coordinator CLI checks.

Source suitability rejected an initial Validation definition whose whole
criterion required later overall acceptance and final effects before integration
could finish. That rejection occurred before retention or native Validation
admission. The original first report and corrected High finding remain intact.
The Coordinator then adopted a distinct integration-readiness Goal using the
installed structured JSON basis contract. Its six criteria retain every original
product clause and current integration duty. The original whole criterion remains
globally unverified in the reports and parent-duty ledger, with explicit
`future_criteria` attribution. A fresh independent suitability assessment and
actual qualification passed for the new definition. This establishes source fit;
actual integration and final closeout require their own execution evidence.

The same Epic Evaluator and two fresh nonauthoring Task Operators then formed
independent first assembled views. Product behavior, traceability and member
history passed; the reports retained missing cohort and handoff evidence as
unverified. The first strict composition preserved those negatives. After the
complete original reports and actual evidence were available, the same owners
gave focused confirmations. Nine exact closures produced a ready integration
composition with no current gap or pending judgment, followed by the actual
native readiness judgment and retained integration result.

A separate first substantive closeout assessment reviewed the complete prospective
record changes and dossier retirement. The fixture operator accepted that exact
proposal before application and the final conditional commit. The same native
session then reached completed/achieved/handed-off to the verified commit. Both
member grants and the conditional final grant were consumed once. Earlier
unverified parent rows and rejected definitions remain unchanged historical
reports; a separate reconciliation records the later actual effects. This
completed the Coordinator's native-only Squad verification.

Complete public records account for ten Squad conversations and twelve Handler
conversations. Every latest turn completed without a pending command. The declared
candidate and harness sources, original reports and complete owned fixture Git
history were preserved before consumer restoration. All eight declared consumer
roots then matched their saved preimages, including file modes. The unchanged
consumer-cleanup recipe returned pass/verified and produced both original
receipts.

The initial native collection exceeded its 900-second deadline and retained the
guest originals. Its immutable result remains `INCOMPLETE`, with partial evidence
and failed cleanup. A separate native recovery collected all 34 required outputs
before verifying and completing the same Job's cleanup. The host export contained
35 files. Every required output matched the size and digest frozen in the guest,
and all 6,637 members of the 13 evidence archives matched their manifests and
required sets. The recovered outputs total 235,001,600 bytes. Supplementary
recovery preserves the original failure; resource-health verification governs
reuse separately. The three named groups passed and the other ten remain
unobserved.

Requested native `on-request` approval was not established as applied; the observed
policy was `never`, and protected Git writes were refused. The outer fixture
operator executed the exact authorized commit scripts and verified their actual
results. A process-local `--disable apps` continuation followed an optional
connector refusal. The two fixture trust registrations and generated bytecode
were included in restoration. Private model, effort and operating-system
isolation remain unconfirmed. These results supply no all-scenarios or all-harness
pass, and Master's final overall EPIC-028 acceptance remains separate.

## Sorage v0.1.4 adoption suite

The [manual scenario](recipes/scenarios/sorage-adoption.md) defines the managed
`sorage-adoption` suite for old-binary backup/restore, explicit upgrade, MCP and
skill behavior, v0.1.3 update without migration, actual Plan Mode communication,
and consumer restoration. Qualification is pending. Submit only
with exact candidate and guest installation authority; local checks do not establish
an installed result.

## Podway v0.2.16 adoption suite

The current [upgrade scenario](recipes/scenarios/podway-upgrade.md) targets the
official v0.2.16 CLI and its release-pinned skill. It preserves historical stable
profiles and adds a separately sealed authentic v0.2.15 input for writer-refusal
and original-request replay checks. The v0.2.15 observations above retain their
original candidate and limits. Source checks and release-input preparation do
not establish a v0.2.16 installed result.

### Podway v0.2.16 direct SSH observations

Under Master's explicit direction to proceed without Haepari, the operator ran
the installed checks over `ssh UTM` on 2026-11-03. The installed candidate was
built from verification snapshot `bee2e50f3be585793d07e2a095fe51ee2dc30783`.
All 200 tracked plugin payload files match the working implementation, allowing
only the declared development-version stamp. The official Podway release source
is `e9f4b41d1d09573b7acd443b91fbfb8f378fb8e1`; the installed CLI and complete
paired skill matched the sealed release inputs.

| Case | Observed result |
| --- | --- |
| Released baseline | Authentic v0.2.14 and v0.2.15 CLIs created and began sessions, then cancelled them before replacement. Custom Procedure content, tracked configuration, staged and unstaged work, and a sentinel were retained. |
| Writer refusal | v0.2.16 refused reads, fresh writes, original-request replay and UUID-fenced reset for both authentic Stores without changing their Store or source images. The original v0.2.14 generation-1 replay retained its original error-detail shape. |
| Explicit fixture reset | Each owned fixture acquired a fresh UUID and no current session. Successful outcome lookup and exact envelope replay passed; configuration, custom source, Git index and unrelated work were preserved. |
| Installed source discovery | Fresh Codex contexts resolved the candidate plugin root and loaded the installed Task/Epic sources and complete paired skill. Native filesystem discovery was used; this does not qualify the unavailable workspace-discovery connector or automatic advertisement of every handler in the initial skill catalog. |
| Task startup | Actual Executor plan delivery and independent Evaluator assessment advanced the session to `prepare-implementation`. The scoped startup checkpoint passed; the original global `rework` result, three unmet implementation obligations and intentionally failing baseline tests remain separate. |
| Epic startup | The first Task Operator corrected the addition fixture and passed three tests. Independent evaluation passed the due work checkpoint while retaining global `evidence-needed` and three future gaps. The Coordinator advanced to `record-evidence`. |
| Consumer restoration | Run-owned startup sessions were observed and cancelled after the bounded stop. The original Podway v0.2.14 binary, paired skill, plugin cache and registration, configuration, skills and rules matched their recorded bytes, modes and symlinks after native registration readback. Foreign plugin cache changes were recorded rather than rolled back. |

The initial ephemeral Codex calls and a pre-launch path error did not qualify
startup. Their original records remain separate from the successful persistent
calls. Codex 0.164.0 required a persisted parent rollout for native child context;
explicit write access to the disposable fixture's `.git` allowed Podway's local
retention lock. No installed executable or global configuration was patched.

These are bounded installed upgrade and initial orchestration observations.
Task/Epic completion, later technical review, final acceptance, other producer
paths and the release's separate acceptance gate were not exercised. The original
Haepari attempt remains `INCOMPLETE`; these direct SSH results do not rewrite it
or establish a managed Job PASS. Original requests, native responses, complete
child reports, observations and restoration inventories are retained outside Git.

### Full workflow follow-up

A second direct SSH campaign on 2026-11-03 used the same installed payload and
official v0.2.16 inputs in separate disposable addition fixtures. The standalone
Task completed planning, implementation, Deslop refinement, verification,
documentation, three fresh technical reviews and final independent evaluation.
All three behavior checks passed; the final assessment had no unmet or unverified
criteria. After Master's actual acceptance, the same native session reached
`completed`, goal outcome `achieved` and disposition `handed_off` to the verified
no-commit result. The Task became `Completed`; its parent remained `In Progress`.
The existing HEAD and index were preserved, with only the approved status change
added to the worktree.

The Epic completed its sole member Task, including three fresh technical reviews,
independent evaluation and a fixture-only member commit.
Internal whole-Epic Validation used another three fresh technical reviewers and
reached native `completed`, goal outcome `achieved` and disposition `not_required`.
The unchanged implementation and exact proposed Epic status-only closeout passed
focused checks and final independent evaluation, with no unmet or unverified
criteria. After Master's actual overall acceptance, the approved Epic status-only
change was committed in the fixture. The same closeout session reached
`completed`, goal outcome `achieved` and disposition `handed_off` to that verified
commit, with both Task and Epic `Completed` and a clean fixture worktree.

During closeout preparation, the Executor ran `git write-tree` despite its
read-only Git assignment. Independent checks confirmed unchanged source and
staged content; no earlier physical index snapshot existed, so index-byte
identity remains unverified. The command outputs were excluded from required
proof, and the independent assessment found no product blocker. The original
incident and its adjudication remain in the evidence.

Before awaiting the real final decision, the operator restored the original
controlled consumers and native plugin registration. Byte, mode and symlink
checks after native readback passed. Both pending fixture images, including
their native sessions, retained sources and Git state, remained unchanged for
resumption after reinstalling the same candidate. Finalization reused those exact
sessions and source/binding identities. A second restoration after completion
passed the same checks and preserved both completed fixture images.

These follow-up results cover the exercised one-Task fixtures through actual
acceptance, final repository results, native terminal completion and disposition.
Other workflows and producer paths still need their own applicable evidence;
release acceptance remains separate. The earlier startup-only assessments and
failed attempts retain their original scope.

### Podway v0.2.16 managed qualification and EPIC-032 reuse

The recovered managed `release-acceptance` allocation on Aquarium candidate
`8bd3e3e9283f1e234694920bde80c58af86a87c9` (`utm-macos` capacity `1`, runner
configuration digest
`9225ae4f819bf3b1b0dbc551bc9c3d2ac1553e5f3e9c0eabeae7b4a16f2f210a`, spec digest
`22f93f6eddb770d1582f7feba669e63448ef253e525f6e493427199a7115d00a`, submitted
digest `944ac58b80609db6ec4646262862464a1204438cd86b6afb136e33f6fd0812ea`, input
digest `2334b0b677e33d0eb16ed6f7f7927d4d2ec8d5dd1d1635258ffa270c0722764e`,
starting profile digest
`04df16201e8cff0f89d50082d162dcab00049da42aa9c1c5960e7f9a4e3e8b31`, target
profile
`proposed-candidate-haepari-0.1.0-aquarium-0.1.21-codex-0.164.0-podway-0.2.16-dev-8bd3e3e9283f`
digest `faa881f023f9b91ce1eecccc5d29ad2d305c2c95caea32fed52722cf2c65608e`, and
recipe digest
`4bcb10005360b57fc16e1ad593340ee53e4c0a606be0c9d0869c12051204f643`) completed
with terminal state `finished`, workload `pass`, `complete` evidence delivery
(all `45` exported manifest files verified against the immutable native result,
with the `utm-macos` resource available and no new VM or Job started during
read-only inspection), native cleanup `verified`, consumer cleanup `verified`
(`0` violations, retaining the tested Aquarium candidate, Podway `v0.2.16`,
paired skills, and selected candidate status runtime), and final verdict `PASS`.
The original startup result covers `VM-UPGRADE-01`, `VM-TASK-START-01`, and
`VM-EPIC-START-01`. This Job supplies no release-handler startup or full release
workflow result. Both the starting profile
(`04df16201e8cff0f89d50082d162dcab00049da42aa9c1c5960e7f9a4e3e8b31`) and the
admitted target profile
(`faa881f023f9b91ce1eecccc5d29ad2d305c2c95caea32fed52722cf2c65608e`) verified in
the immutable admission snapshot pin official Haepari `v0.1.0` (`tag_commit`
`800da97b7e2ca84a15d4ee5921702ec57bbc7d61`, `build_revision`
`fc3b975f8a99cacb96aecc988d3adbc04dda7309`, archive
`6667cab322f326eb390b8cab89fd292e22d7436312434e7facd66213fe1a8a18`), executable
and controller binary
`sha256:e1a4c0a047f9d6b6e7048fdcfea961b7bafb3a3c627786619cff3796433d6b20`
(matching the current reconnect client byte-for-byte, with
`haepari.release-service-plan/v1` `global_limit: 2` and
`host_macos_guest_limit: 1`), the complete `use-haepari` skill tree
`21ec3671639b8699fbd6e1f0ed2697c435793ee0fcf56e73a65fbea51cbe3ebf` under
`aquarium-skill-tree-sha256/v1`, and the six frozen capabilities
(`managed-execution/v1`, `durable-observation/v1`, `advisory-lock/v1`,
`managed-recovery/v1`, `artifact-delivery/v1`, and `evidence-retention/v1`, with
`compiled_backends: ["local"]` kept distinct from the registered `utm-macos`
runner `PASS`).

Both pre-workload and post-cleanup guest inspections verified official Podway
`v0.2.16` (`e9f4b41d1d09573b7acd443b91fbfb8f378fb8e1`, `aarch64-apple-darwin`,
CLI binary
`sha256:249685e65402049ecad83f1ecef8efee361f6ac979bde686a9ebabd10c685cf2`,
release archive
`sha256:cc91c083790da53977e193b09742836a7cec68aa18864df93989fed2df645835`,
checksum sidecar
`sha256:4eb8b039a022c1d3c6773e71f1284002c99bc48f95b22ec843cfbd81b865bab4`,
provenance
`sha256:63a7b1385fa766e6b23edb5eed0d0f63cf68f1008c04a4de8e4aceacb591553e`,
`podway.version-result/v2` `build_identity`
`sha256:2a11e45d3dee9a64143817f2b5bb92371f87947afd0b565d6feb34876768aafe`, and
`podway.contract-manifest/v2` digest
`sha256:57cb8463f0f24033f9bd0437ed1943e77b21b754a888e654bd847bec13f4b91d`) and
the complete five-file `use-podway` skill tree
`da9196f58d712d09de459dea423a9776f07c04014ebfb835105012697a833446` under
`aquarium-skill-tree-sha256/v1` (`SKILL.md`
`e1b067e8e64dc1d297c295ad6f17d0db202c4763fb496dce0d98e13513710200`,
`references/lifecycle.md`
`736998ddb12262da2a3fca6fc90c84001207623928c9e876908fa9b9e502f4f3`,
`references/goal.md`
`facf835661b08da9432d3d063df8be0c064d6899e132256b55ab6155a6bf41d9`,
`references/delegation.md`
`ea314acd2179ede83c19e92df6cb4db20a2b55b7c7e8a1ded907dd9617be232d`, and
`references/recovery.md`
`ac839571e629ef05c7e4cbb5dec2e6683dfa5fde11d91fe0d77a84557d8e465c`), with all
nine sealed release inputs reconciled as byte-equal. Four local
`test-podway-compat` passes against that same official binary across candidates
`c572e8075305c61ddc76714f2cdd40d1c0c609b9`,
`b76a36b1abb192234e7b737da657ea5dfbdc3045`,
`65f459ea07151d8e6a321b229f2f122676a49b70`, and
`8bd3e3e9283f1e234694920bde80c58af86a87c9` verified the exact structural and
native-graph compatibility scope for all five shipped v2 Procedures
(`aquarium-design-v2`, `aquarium-goal-v2`, `aquarium-task-v2`,
`aquarium-validation-v2`, and `aquarium-war-room-v2`), plus outcome lookup,
stale-fence refusal, workspace-removal refusal, recovery/restart, and settings
cases with clean disposable-workspace cleanup.

Under the official `e9f4b41d1d09573b7acd443b91fbfb8f378fb8e1` Podway
release-and-packaging Upgrade policy (`v0.2.16` Direct contract), operators must
finish or abandon active sessions and retire every legacy writer before updating
the binary; in-place live migration of an active workflow or legacy Store is not
supported (`not_applicable`). When an older v0.2.14 or v0.2.15 Store is present,
`v0.2.16` refuses reads, fresh writes, original-request replay, and UUID-fenced
reset without modifying the Store or source images. Explicit `podway reset` is a
separate destructive operation that creates a fresh workspace UUID and discards
prior runtime history while preserving workspace configuration, custom
Procedures, the Git index, and unrelated worktree files; it is not an in-place
migration. The `bee2e50f3be585793d07e2a095fe51ee2dc30783` direct-SSH observations
above already establish this upgrade contract (`Released baseline` sessions
cancelled before replacement, `Writer refusal` without modification, and
`Explicit fixture reset` creating a fresh UUID while preserving configuration,
custom Procedures, and Git state) and cover the recorded standalone Task,
one-Task Epic, and internal Epic validation fixtures (`task-commit` and
`release-handler` coverage is not claimed from that direct-SSH record). No
active workflow was migrated in place, and no fresh busy-session execution is
claimed.

Producer `aquarium-dev` source integration was removed in Podway commit
`b07942e30c85055643e8a1eb759d0e225f73a385` (`V2DFC` / `V2DFC-009`, ancestor of
`e9f4b41d1d09573b7acd443b91fbfb8f378fb8e1` and
`475b04fd28d9836e450ad90b8d358fef22bf3cc2`), and the exact E2E retirement and
direct-CLI checks passed on clean historical audit checkout
`98b8de7da9ac086ea0839f5e62a29dd88dc874ae`. For `TASK-091` reuse at
`759883a47676ad9efae2dd8ae373878a431ce031`, `git diff --name-only 8bd3e3e9283f1e234694920bde80c58af86a87c9..759883a47676ad9efae2dd8ae373878a431ce031 -- plugins/aquarium/shared plugins/aquarium/assets/podway tests/verify_podway_compatibility.py`
reports zero changed paths, and read-only host inspection confirms the installed
`podway` binary and all five `use-podway` skill files match the tested official
`v0.2.16` digests byte-for-byte after the temporary extracted CLI was removed by
original cleanup.

This recovered managed `PASS` (`8bd3e3e9283f1e234694920bde80c58af86a87c9`), the
separate earlier `INCOMPLETE` (`manual-timeout`) run, the
`bee2e50f3be585793d07e2a095fe51ee2dc30783` direct-SSH observations above, and
`EPIC-031` directed-closeout limits remain distinct. Later `tests/vm` harness and
release-orchestration changes between
`8bd3e3e9283f1e234694920bde80c58af86a87c9` and
`759883a47676ad9efae2dd8ae373878a431ce031` are not covered by the `8bd3e3e`
allocation, and reusing these Podway outcomes for `TASK-091` does not claim a
new VM or provider run, current-harness release qualification, or an aggregate
`EPIC-031`, `EPIC-032`, or `EPIC-033` pass.

## Release orchestration feature suite

The [release-orchestration scenario](recipes/scenarios/release-orchestration.md)
owns the full manual development feature suite and its
[original-row inventory](fixtures/release-orchestration/cases.json). Select
`SUITE=release-orchestration MODE=manual` through the existing host adapter with
the exact committed candidate, matching harness, sealed Podway input and an
explicit immutable `AQUARIUM_VM_BASELINE_PROFILE` matching the actual current
released combination. The optional existing-profile input also serves
release-acceptance and scoped probes; absent input preserves historical defaults
and does not make them proof of a current-baseline obligation.

The feature suite declares 13 case archives, 13 manifests and eight JSON outputs,
34 total. Complete original evidence and per-variant native/fixture/reused/
unobserved classes remain separate. Pre-main native P/Q callers prove genuine
queue-to-execution sharing after resource release; queued cancellation and
active cancellation are distinct. manual-hold's intentional INCOMPLETE remains
INCOMPLETE. Legitimate predeclared campaigns can contribute original applicable
evidence without replacement Jobs, omitted outputs or deadline extensions.

The feature recipe observes approved installation and verifies restoration of
the actual starting consumers. J-RA retains its upgraded installation instead.
Both stage consumer evidence before manual completion and retain native
collection/cleanup/export afterward. TASK-176's actual observations and early
closeout are recorded below; preparation alone proves no installed behavior.

J-RA adds only [release-startup](recipes/scenarios/release-acceptance.md#release-startup),
one native release-handler plan-readiness smoke with a summary and archive/manifest.
The ten historical scenarios remain. With `python-runtime-approval`, the
current manual inventory has twelve. That scenario and the existing Task/Epic
startup scenarios are recurring release acceptance. The
[shared Python environment](recipes/scenarios/python-runtime.md) feature cases
are required development qualification for that change before its first
release, and again for affected changes. They run under explicit
candidate-bound VM-test authority, with original evidence and verified
consumer cleanup. A J-RA PASS does not imply them.
Existing Task/Epic `make test-vm` behavior stays intact. Full feature verification
is not repeated inside that startup check.

## EPIC-031 verification and directed closeout

Master stopped further qualification and directed EPIC-031 and TASK-176 to close
on 2026-11-07 because a separate Epic proposes a substantial release-handler
redesign. The roadmap's `Completed` state records that decision. Full feature
qualification, whole-Epic technical acceptance and release readiness were not
established. The redesign and its acceptance remain outside these observations.

TASK-172 through TASK-175 delivered bounded release roles, preparation/QA
handoffs, both gate orders, publication assessments/recovery and reusable
verification scenarios with their focused source checks. The installed
observations below used the dedicated UTM macOS VM, managed Haepari allocations,
real Codex Coordinator/Executor/independent Evaluator conversations, local Git
repositories and a controlled hosting stand-in. The roles ran in the guest;
publication effects stayed inside fixtures.

The final exercised source was
`3869388667f15ae987423452cd22365d2bb71275`, with artifact tree
`5c41f2d4d63a6bee93f844dc99988fc83d9b243ca62821254cf2ef2287b3e824`
and harness tree
`44b070781bad3e896323ded8f4abbfba008931a122972a5182dd130c059f42ce`.
Earlier contributions keep their own original source, combination and
applicability bindings. These observations do not qualify a later changed
payload.

### Executed observations

| Area | What the retained evidence establishes |
| --- | --- |
| Installation and discovery | The candidate was installed in UTM. Actual native role startup, candidate discovery and status-runtime activation were observed. Each feature allocation retained its released starting state for restoration. |
| Release preparation and gates | Full-before-commit and commit-before-gate fixture paths ran with actual roles, QA and gate receipts. A controlled post-commit gate failure preserved the unpushed commit and stopped publication. |
| Light mode and stale evidence | Actual light-mode paths and same-world functional drift exercised candidate-specific confirmations and invalidation. Synthetic helper branches remain separately classified. |
| QA findings and confirmation | Actual initial findings, bounded correction, readiness assessment and confirmation were exercised. A separate neutral-change path retained direct-QA and release-basis identities, one permitted reuse and independent eligibility assessment. Original negative reports remain unchanged. |
| Final three native cases | Publication recovery, Executor replacement and managed-resource evidence intake each ran a full fixture QA pass. Those three QA results cover their own candidates and scenarios; they do not pass the full feature inventory. |
| Executor replacement | Actual distinct metadata Executors X and Y, intervening Coordinator settlement and the same independent Evaluator were observed. The replacement did not replay prior completed work or grant publication. |
| Partial publication recovery | Fresh invocations reconciled before-push, before-tag, before-hosted and already-hosted boundaries. Only the next expressly authorized mutation ran. A controlled effect-then-lost-reply produced one hosted object and one create effect, with no replay or duplicate. |
| Advanced remote | A second fixture clone advanced remote main to a proved descendant. Native recovery retained the original release, tag and hosted target rather than moving them to the descendant. |
| Semantic completion | An independent Evaluator first accepted the matching published highlights. After an authorized controlled highlight mismatch, it returned `FAIL/rework` while structural routing still reported complete. The Coordinator consumed the negative result and stopped without repair, rollback or republication. The unchanged Validation section remained separately supported. |
| Managed resource probes | Genuine queue/occupancy, caller wait timeout, same-key/spec/Job reconciliation, distinct host Executor recovery, queued cancellation and active cancellation were observed. Workload result, delivered evidence, consumer cleanup, native cleanup and resource return remain separate dimensions. |
| Objective helper checks | First-release, hook/gate/convergence, missing or stale inputs, unsafe report bindings, publication ancestry/retarget and cleanup controls ran as selected helpers. Disclosed synthetic retry/native-cleanup classifications establish helper behavior only. |
| Test-fixture correction | Five host-wrapper test children inherited the outer allocation's parent context and were correctly refused by the live anti-nesting guard. Clearing that inherited variable only in the child fixture let the five affected nodes and the explicit nested-context refusal node pass: six focused checks. The live wrapper was unchanged. |

### Failures and limits retained

The initial feature run failed; later source correction did not rewrite it.
The five earlier feature allocations returned native `INCOMPLETE` with partial
evidence, even where individual scenario observations passed. One later
allocation expired at its manual deadline after installation but before its
three native cases; its runtime proposal was not consumed. A subsequent prepare
attempt refused the changed installed identity. A separate operational recovery
restored consumers and passed only that recovery scope.

Managed probes retain their original outcomes: a guard/consumer failure was
`FAIL`; timeout/reconnect and partial-evidence runs were `INCOMPLETE`; queued
and active cancellations were `CANCELLED`. One controlled output-withholding
probe physically cleaned up but did not deliver its required post-cleanup
inventory. Its delivered consumer verification remains unverified. The installed
release-role Evaluator retained that gap and stopped readiness.

Protected input content was emitted into a private native tool transcript during
managed evidence intake. That handling failure remains unmet. A later bounded
typed intake emitted only approved digest/count/boolean facts; its narrow result
does not establish compliant handling for the whole run or erase the incident.
The managed compound objective was not awarded a final whole-objective pass.

Other actual failures remain in the retained originals, including the first
orphan-clone ancestry failure with no push, readout/index assembly failures and
the first evidence-staging attempt before the consumer receipt existed. The
corrected explicit-main clone, scoped index repairs and later staging do not
change those historical exits.

### Unexecuted or not established at closeout

- The frozen inventory contains 81 variants, including 16 native-required
  variants and seven complete native objectives. Final whole-inventory
  reconciliation was not completed. There is no all-81, all-16 or all-seven
  passing claim; earlier source-record counts are not final coverage totals.
- The separately prepared final J-RA was not submitted or executed. Its current
  installed upgrade/preservation, complete manual inventory, Task/Epic startup
  and bounded release-handler plan-readiness acceptance remain unverified for
  this candidate. Feature-suite observations do not replace them.
- Final TASK-176 completion assessment and whole-Epic integration/closeout
  technical panels were not completed. Master's directed closure does not
  relabel original unmet, unverified, `rework` or `evidence-needed` criteria.
- Private effective model/effort telemetry and complete physical-process absence
  were not established. Outer Herdr role profiles do not prove guest profiles.
- No production release, real hosted publication, host installation, distribution
  qualification or verification of the proposed redesign was performed.

The requested outer roles were Herdr Codex GPT-6.1 Sol/high for EE/TO,
Herdr Claude Opus 5.5/high for TE, and Herdr Cursor Agent Grok 4.7/high for SO.
Public launch/control observations are retained separately from assignment
metadata. TE's current native arguments explicitly selected the requested model
and high effort; an earlier UI observation reported max effort. Effective private
effort remains unknown. The Coordinator's exact applied model/effort was not
established by retained launch arguments. Guest roles used their own native
defaults and are not inferred from those outer profiles.

### Retention and termination

Original requests, role reports, negative judgments, failed attempts and complete
private host archives are retained for authorized later consumers. Protected raw
context stays private. Canonical documentation records the bounded findings
without importing transcripts, local runtime state or raw logs. The temporary
Epic dossier is removed after its durable contracts and these limits are linked
from the roadmap; Git history retains the original plan.

Further functional work and final J-RA were stopped at Master's direction.
The final feature allocation's actors settled, the original native plugin
registration and all 15 declared consumer roots were restored, consumer cleanup
was verified and evidence staging completed. The final native outcome was
`CANCELLED` with workload cancelled, complete declared-artifact delivery and
verified native cleanup. Resource and global occupancy were both zero on final
readback. All 34 delivered artifacts matched the preserved pre-cleanup originals.
Delivery completeness does not assert full functional coverage.

The development Goal was cancelled on the explicit stop, retaining its original
criteria and history without marking them achieved. Its terminal handoff records
the directed-closeout commit.
