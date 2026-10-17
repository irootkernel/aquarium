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

For these test cases, the Primary saves original ordinary v2 assignments and
role reports inside `run_root/task-startup` or `run_root/epic-startup`, with each
case's `startup-evidence.json` pointing only to files in that directory. Preserve
the other case's evidence during incomplete runs and resumes. Actual child final
results include their JSON report or its path
and digest. Reports identify `greet.py` bytes through `target.greet_sha256`;
Judge rows retain the original smoke IDs, sources, evidence and states. The
Judge remains report-only. Native role metadata may be null; child user messages,
model telemetry, full private history and formal accepted-task bindings are not
required. This collection protocol belongs to VM acceptance, not ordinary startup.

Use a cumulative delivery handoff that lists the Worker's actual implementation
changes and subsequent refinement and check results. Preserve a verification
phase's no-op result without dropping the earlier changes from that handoff.
Both reports use a 64-character lowercase SHA-256 hex digest for
`target.greet_sha256`, with an optional `sha256:` prefix. Both forms must match
the current source bytes exactly.
Return the complete report JSON in the native final result, or its original
absolute path and `sha256:<64 lowercase hex>` digest. Point `startup-evidence.json`
to that original report path. Preserve previous captures when reconciling a
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

Each case captures original assignments and actual returned ordinary v2 reports
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
Worker/Judge children and complete returned results; cold validation can use a
Judge without an unused corrective Worker. It compares every due original
criterion, current target bytes and the case oracle while preserving future
unverified rows. Synthetic unit reports prove only the checks, never installed
agent behavior.
Assessed-file and upstream-result digests accept the same optional `sha256:`
prefix; candidate and native binding identities retain their specified formats.

Git-backed adaptive cases recover the current exact source/binding through the
installed public context helper. Their family, source bytes, native tuple,
current role and selected producer/item values must agree. The source must show
an actual structural difference from its canonical regression, not only renamed
placements. Fenced native evidence reads must include the real returned Judge
report or its exact content digest. This instrumentation belongs only to these
VM cases and adds no ordinary startup receipt or authentication protocol.
Non-Git project verification checks documents and absence of Git/Podway without
invoking a native observer on that branch.

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
