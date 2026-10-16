# Testing

## Contract

- Contract: `aquarium-test-contract/v1`
- Profile: `make`

The root `Makefile` is the executable authority; this document records its intended meaning and never authorizes a handler to skip a check.

Ruby and Python validation is limited to objective package structure and executable helper behavior. It does not compare skill prose, sentence order, line wrapping, diagnostic wording, or private implementation names. Master verifies skill functionality separately after updates: multi-step workflows, decisions, recommendations, approvals, and handoffs. A passing `make test` does not establish that those behaviors work. The gate does not invoke LLM evaluators; agents report affected manual checks without claiming an unobserved result.

## Canonical Commands

- Complete serial gate: `make test`
- Static preparation: `make test-prepare`
- Unit tests: `make test-unit`
- Integration tests: `make test-int`
- End-to-end tests: `make test-e2e`
- Exact Podway v0.2.14 compatibility: `PODWAY_BIN=<absolute-path> make test-podway-compat`
- Explicit manual guest acceptance: `AQUARIUM_VM_REQUEST=<absolute-request-path> make test-vm`

The aggregate uses recursive Make recipe calls in prepare, unit, integration, and E2E order. It stops on the first failure and retains that order under parallel Make. Every handler is non-interactive: Make disables inherited pagers, clears inherited `PYTEST_ADDOPTS`, pytest ignores user-installed plugin entry points, and whitespace validation invokes Git with `--no-pager`. The repository selects `.venv/bin/python` when present, otherwise `python3`. It selects `.venv/bin/ruff` independently when present, otherwise `ruff`; command-line overrides cannot replace those identities.

## Stage Mapping

| Stage | Checks |
|---|---|
| `test-prepare` | Ruff formatting and lint for maintained Python files; plugin-manifest JSON parsing; Ruby syntax; package metadata, local references, basic Procedure structure, and release-version identity; whitespace validation. |
| `test-unit` | Native pytest tests for isolated installed-plugin resource containment through the Ruby link checker, complete upstream skill inventories, Procedure routing and qualification harnesses, production-status contracts and storage, aquarium-dev runtime, installer, service and isolated MCP STDIO helpers, release-QA evidence and publication helpers, and the setup, documentation, release-note, and review-target inspectors. |
| `test-int` | Native pytest production-status persistence, concurrency, stored-key removal and inventory-retention scenarios plus the documentation, global-tool and testing inspectors; the three approved legacy unittest suites exercise tool inspection, manifest normalization and commit gates across temporary Git repositories and subprocess boundaries. |
| `test-e2e` | Python pytest scenarios invoking the shipped production-status and test-setup CLIs and release-QA freeze/confirmation CLI as black boxes against isolated temporary fixtures. |

Dependency installation is outside every handler. Prepare may rewrite only the Python files listed in the root `Makefile` through deterministic Ruff formatting; later stages exercise the resulting candidate.

Goal Judge helper tests in `test-unit` cover assignment preparation and filesystem
safety, operative dispatch rendering, supplied native-record correlation, Codex
and Claude delivery binding, and the public Codex read client's protocol behavior.
Formal v1 cases use synthetic records and disposable transports and preserve their
original digest domains. Ordinary v2 cases validate schema-selected preparation
and rendering without snapshot reads or telemetry and reject ordinary input at
formal binders. These tests do not establish skill functionality. Actual native
dispatch, feedback, settlement and recovery need separate observations; declared
formal delegation additionally retains its genuine qualification contract.

`test-podway-compat` is an external-artifact gate outside the ordinary `make test` aggregate. It requires a clean committed candidate and one absolute, executable, nonsymlink official v0.2.14 CLI. It records Aquarium HEAD, the executable SHA-256 and native release source/manifest identities. All five canonical Procedures pass format check, validate, vet, lint and check with warnings as errors, and preview with exact digest-fenced start suggestions. Declaration-limit and unknown-field fixtures must fail.

Each runtime is a standalone Git fixture under a physical temporary root. The helper snapshots only the verified CLI and uses Direct execution, Output v4, Error v2 and observation/status v5. It runs one canonical five-Procedure lifecycle pass before independent batches with at most four concurrent fixtures. Existing correction subvariants, selected-route guards, delegation receipts, required evidence, manual and semantic rework, immutable snapshots, plan attachment, paged evidence and stale-token rejection remain required. Fixture outcome checks require committed success lookup and complete-envelope replay; rejected and unknown requests must retain no outcome. Fenced workspace removal must reject the wrong UUID, preserve Git and unrelated files, and return successful already-absent readback on the identical request after deletion. Removal ends runtime outcome retention.

All executed correction subvariants, assertions, per-batch cleanup and removal results are recorded in `aquarium-podway-compatibility.v9`. Scenario and command deadlines remain bounded. Every fixture root is removed on success or failure. No service, socket, runtime-mode selector, legacy account or installed writer is used. Synthetic receipts prove native guards only; provider execution and semantic assessments need separate installed functional verification.

Upgrade fixtures materialize the frozen populated generation-13 Store and a generation-15 Store with the v0.2.13 writer manifest. Both must refuse status, doctor, init and UUID-fenced reset while preserving Store and source bytes. An explicitly scoped fixture reset must create a UUID distinct from the seeded Store's UUID and preserve configuration, Procedures, ignore rules and unrelated files. The manifest fixture models writer admission; it does not prove an installed v0.2.13-to-v0.2.14 upgrade.

Goal and Validation native scenarios also read back the acceptance source,
authority, and exact candidate before closeout. Member and pre-validation goals
exercise delegated closeout; the standard Validation pass exercises the continuing
Epic's delegated handoff. Final Epic closeout and independent Validation retain user
acceptance. Each normal approval attempt first rejects the option for the wrong
acceptance source without changing state, then verifies the permitted destination.
Structural guard tests independently vary goal kind, validation owner, acceptance
source, and missing evidence. These checks establish routing, not the truth of a
recorded user decision or delegation.

Further bounded scenarios prove the serial completion contract directly. Task coverage includes `unverified` return to fresh review evidence, simultaneous-owner precedence, each sole phase owner, and inconsistent finding totals or owner evidence returning to review. The finding-total case includes a surplus unresolved finding beside a Low bucket. Goal coverage sends the same inconsistency back to evidence capture and also covers complete hardening-deferral traversal and an epic-closeout completion gap stopping for user direction. Goal and Validation coverage exercises both `unmet` and `unverified` completion routes.

War-room qualification also exercises evidence-backed no-work through draft, quality, approval, documentation and assessment. It verifies that work-classification and corrective-proposal nodes are not visited on that route. These fixture decisions prove Procedure reachability and guards; Master still verifies the diagnostic judgment and actual skill handoff.

A local development binary provides development-contract evidence only. For distribution readiness, first verify the official v0.2.14 Apple Silicon archive against its published checksum, then run the same target against the extracted exact binary. The target requires no network after artifact provisioning. Podway's own exact release-candidate gate remains authoritative for Podway distribution; Aquarium's independent target proves only compatibility of the exact Aquarium candidate named by the resulting Git revision.

Podway skill changes also need Master's manual verification: setup must compare the complete skill tree against the catalog's fixed commit even when the runtime release changes; resuming the same authorized workspace and session must retain approval while using fresh fences; an unauthorized identity change must stop session mutations; and Codex and Podway goals must follow their own creation, completion, and blocker rules. An uncertain mutation must retain its original request and idempotency key for recovery. Plan-handoff verification must also cover a plan file changed or removed after attachment: the handler must stop before implementation, while an ordinary session without an artifact remains valid. These checks remain unverified until Master provides their outcomes. `make test` and the binary compatibility gate do not prove skill behavior.

For the v0.2.14 adoption, UTM installed verification must also cover fresh Codex and Claude skill discovery, Direct setup and managed-session workflows, stable-version eligibility without an upper bound, legacy and writer-mismatch recovery with separately approved history loss, and the absence of retired daemon/job/mode commands from the affected current paths. Preserve the baseline's running sessions and services. Bind results to the exact installed candidate and distinguish fixture evidence from Master's functional results.

## Workflow Functional Verification

Source and fixture checks do not establish host routing or multi-step skill behavior.
Bind every observed result to the exact Aquarium candidate and applicable native
tool source. Record performed and unperformed outcomes in the owning workflow's
Podway evidence and final handoff; without Podway, use the final handoff. Apply the
[evidence residency contract](plugins/aquarium/references/evidence-residency.md)
when promoting a durable result. The scenarios below require their own applicable
execution authority; this list
authorizes no installation, session replacement, provider call, clipboard write,
broker operation, deletion, commit, or publication.

| Scenario | Required observation |
| --- | --- |
| Selected review route on a prior Procedure and after context restoration | Reject unsupported routes before dispatch; preserve the exact live operation and supported recovery without silent provider or route changes. |
| Blocker at ordinal four and one additional authorized correction | Stop at an unset user choice; consume one granted correction and confirmation once, then ask again if a blocker remains. |
| Task resume with an optional plan artifact | Verify the exact attached digest and size; changed or missing content blocks implementation, while absence of an optional artifact remains valid. |
| Staged Herdr review and native recovery | Dispatch the complete current staged target with every canonical reviewer restriction; resume or retry only through native support and existing authority. |
| Task records, prose, dossier, and commit handoff | Settle the canonical record and required dossier decision before review; apply the final prose pass before capture; delegated member acceptance consumes only its applicable one-commit grant. |
| Epic delivery through final acceptance | After one execution-envelope approval, complete each Task and owned correction with evidence, delegated acceptance, and its scoped commit; finish internal validation, prepare closeout, then wait for one actual user acceptance. Progress reports do not pause execution. |
| Epic acceptance after correction or context restoration | Reconstruct the exact envelope, candidate, consumed grants and review ordinals; reject stale acceptance and duplicate grants, refresh affected evidence, and never attribute coordinator acceptance to the user. |
| Independent validation, final Epic closeout, and stopped outcomes | Keep actual user acceptance; reject the internal Epic delegation route. Prior Procedure snapshots retain their original approval contract. |
| Final Task commit and permitted no-commit closeout | After the leaf returns, the caller completes the terminal Action and observes the same session as `completed`. Verify `handed_off` for the required commit; preserve the approved uncommitted diff and report an undisposed reason when no handoff is supported. |
| Epic session boundaries and no-change validation | Finalize each member, pre-validation-remediation Goal and internal validation session before its authorized successor, even when whole-Epic validation remains. Keep correction-group commits inside an active Validation session intermediate. Finalize accepted Epic closeout or independent validation even when no final commit is needed; verify each supported disposition and preserve terminal history. |
| Commit succeeded but Podway finalization failed, became uncertain, or lost context | Report the existing commit and unfinished finalization separately; reconcile the original request and fences before any new mutation. With recoverable acceptance and exact candidate binding, resume the same session without another commit, repeated acceptance, replacement, or repetition of valid checks. If acceptance cannot be recovered, preserve the result and session, report the gap, and obtain the required decision without inferring approval from the commit or committing again. |
| Intermediate commits, approval holds, and changed session identity | Continue work that remains inside the same session after checkpoint or correction commits. Preserve sessions while approval is pending or work is paused, and stop mutations on an unauthorized workspace or session mismatch. |
| Design and War-room final delivery | For a verified required commit or permitted no-commit artifact delivery, observe `completed` and verify `handed_off` with artifact paths, digests and the commit when required. For approved War-room no-change, observe `completed` and verify `not_required`; withheld required commit authority leaves finalization pending and the session running. |
| User-limited commits and excluded Podway paths | An explicitly commit-only continuation reports pending finalization without performing withheld lifecycle actions. Opted-out workflows and non-Git new-project invocations perform no Podway observation, finalization or disposition. |
| First release, settled light candidate, active Design Gate, and publication recovery | Keep baseline, candidate SHA, required scenario evidence, release title, remote ancestry, and separate publication authority consistent. Fixture success is not a release outcome. |
| Corrected plugin loaded in a fresh installed Codex session | Bind the installed package to the exact candidate and observe all tools declared by the packaged MCP server's OPERATIONS map through host discovery. JSON parsing and direct STDIO calls do not satisfy this check. |
| PM, setup lookup, installer, and Sorage Project setup | Disclose PM files and clipboard replacement separately; preserve selected lookup and pinned installer/cache/lock-file boundaries; Project setup does not trigger broker discovery. |
| Sorage v0.1.2 upgrade and Memo routing | Confirm that existing pre-Memo databases stop before doctor, format-1 backup and restore preparation precedes separately approved native migration, and diagnosis resumes only after migration. Confirm that missing databases in nonempty homes and incomplete or mismatched configurations stop for recovery, including a binding ID mismatch when the Installation row is empty. Verify explicit Memo reads and writes use the release-matched skill without requiring current repository setup or treating Memo text or closure as work authority. |
| Design QA and committed delivery input | Preserve raw PASS, REVISE, and FAIL separately from operation failure; route content corrections to their owner; document approval alone does not grant commit or implementation authority. |
| War-room no-work and incomplete investigation | Require evidence that expected behavior holds for no-work, retain quality and approval, use canonical note owners or verified no-change, and leave unexplained symptoms incomplete. |
| Status removal after path reuse or symlink replacement | Show and approve the exact stored row; preserve all revision and digest fences and leave replacement paths untouched. |

Complete applicable functional verification during development, before release
preparation. Do not claim functional completion before Master confirms the
required outcomes or their explicitly delegated verification is settled.
Producer source fixes, release, installation, activation, and cross-skill
acceptance remain separate evidence classes.

Herdr review and migration qualification follow the
[observed-scenario guide](docs/implementation-tips/qualifying-herdr-review.md).
Both Codex and Claude reviewers must cover the four supported scopes and both
review purposes, with actual readiness, output, recovery, embedded workflows,
legacy state and peer routes. Keep reviewer identity and activity,
complete report, native operation outcome, criterion assessment and Master's
manual result separate. Missing observations remain unverified; a fixture
receipt or passing Make gate cannot substitute for them.

## Manual VM release acceptance

Complete development functional verification before release preparation.
Release acceptance checks whether an existing installed system accepts the exact
candidate and starts real work. [VM preparation and results](tests/vm/README.md)
and [release scenarios](tests/vm/release-acceptance.md) define the reusable manual
methods. `make test-vm` executes the guest driver and fixed scenarios. Helper
tests exercise guards, actual byte/source identity, native-result correlation,
failure propagation and recovery without providers; they do not verify skills.

Invoke that gate only through release-handler or Master's explicit VM-test
request. Keep it outside ordinary `make test` and automatic Task/Epic checks.
For this Epic, operate the dedicated UTM VM manually and verify Codex only;
Haepari is not a prerequisite. The entrypoint runs in the guest using
candidate-matched test sources. The host release workflow guides preparation and
collects the result.

Observe meaningful released-version state before upgrading. Release acceptance
checks the exact candidate upgrade, state preservation, managed-file updates,
fresh skill discovery and actual Task/Epic startup with initial Worker/Judge
progression. Development verification covers full functionality and recovery
before release; the release gate does not repeat the full feature suite or Epic
lifecycle. Preserve both evidence classes and the separate offline release-QA
contract. Missing required observations, failed checks and incomplete cleanup
cannot produce a passing VM result.

The driver checks Darwin, the native hypervisor-present flag and the externally
selected guest hardware UUID before writes or dispatch. Host transport and VM
selection remain environment-owned. Candidate test sources run from a clean exact Git
checkout; package and installed bytes are verified independently. Original
released baseline capture and actual installed managed updates precede startup.

The Python command returns 0, 1 or 2 for pass, fail or incomplete. GNU Make maps
recipe failures to its own nonzero status. Use the current invocation's stdout
and exit status for classification; `result.json` supports that result only when
refreshed by the same invocation.
A nonzero invocation cannot pass using an older result file; early binding
failure, termination or a write error may leave that file unchanged.
Preparation cannot pass the acceptance gate. Operator decisions
resume actual native handles without automatic replay. Public observations and
meaningful application artifacts are required; success sentences are insufficient.

## Test Frameworks

| Language and layer | Framework | Dependency evidence | Command | Waiver |
|---|---|---|---|---|
| Python unit | pytest with native assertions | `requirements.txt`, `pyproject.toml`, and Ruby 3.3+ for the package fixture | `$(PYTHON) -m pytest tests/unit` | None |
| Python integration | pytest with native fixtures and assertions plus waived legacy `unittest` | `requirements.txt`, `pyproject.toml`, Python standard library, and the committed pre-existing suites | `$(PYTHON) -m pytest tests/test_aquarium_status_integration.py tests/test_inspect_docs.py tests/test_inspect_global_tools.py tests/test_inspect_testing.py`, then `$(PYTHON) -m unittest tests/test_inspect_tools.py tests/test_task_commit_gate.py tests/test_normalize_manifest.py` | `AQ-WAIVER-001` applies only to the three `unittest` suites |
| Python E2E | pytest with native assertions | `requirements.txt`, `pyproject.toml` | `$(PYTHON) -m pytest tests/e2e` | None |
| Ruby package validation | Standalone structural assertion script | User-provided Ruby 3.3 or newer | `ruby tests/validate.rb` inside `test-prepare` | Also invoked by pytest package fixtures through the shared local-reference checker |

The test environment requires the minimum Python development dependency versions in `requirements.txt`, including the MCP SDK and its runtime dependencies. Runtime installation tests reuse these dependencies in temporary environments without downloading packages; stdio tests exercise the packaged server launcher. The shipped runtime has its own hash-pinned `plugins/aquarium/tools/aquarium-dev/requirements.txt`. Every handler checks the selected environment before executing and fails with an installation command when Ruby, Python, pytest, PyYAML, Ruff, or a dependency is missing or below its minimum version. Newer compatible versions are admitted without an upper bound. Ruff may be installed as a standalone executable; its reported version is checked independently of Python package metadata. Handlers never install dependencies implicitly.

The production-status tests use temporary homes, temporary Git worktrees, bounded child processes, local fault injection, and test-owned runtime generations. They verify merge and conflict behavior, replay and exact deletion fences, durable rollback, offline and refreshed reporting, language declaration capture and explicit refresh, v1 ledger migration, enrollment joins, isolated hash-pinned installation, launcher recovery, and cache-independent execution without contacting PyPI or mutating production state. The global inspector tests use temporary Codex homes, synthetic package assets, and local executable fixtures to check home discovery, CLI probe reuse, independent artifact health, MCP home binding, package pins, and partial readiness. PyPI responses are mocked, so the standard gate remains offline. The asset-probe test checks the native rendered-rules contract separately from raw skill bytes; a successful aggregate doctor cannot substitute for either comparison.

## Gaori Mapping

Gaori is optional evidence compression. Each command wraps one authoritative Make handler, and the wrapped process exit code remains authoritative.

| Gaori command | Handler | Output family | Parser |
|---|---|---|---|
| `test` | `make test` | Mixed Python, Ruby, Ruff, Git, and Make | `generic` |
| `test-prepare` | `make test-prepare` | Mixed static tooling | `generic` |
| `test-unit` | `make test-unit` | pytest | `pytest` |
| `test-int` | `make test-int` | Mixed pytest and Python unittest | `generic` |
| `test-e2e` | `make test-e2e` | pytest | `pytest` |
| `test-podway-compat` | `make test-podway-compat` | Mixed Python and Podway runtime output | `generic` |

The Podway compatibility command inherits `PODWAY_BIN` from the Gaori process environment. The required invocation is `PODWAY_BIN=<absolute-path-to-extracted-v0.2.14-podway> gaori run test-podway-compat`; this expresses the command and environment rather than bypassing `$use-gaori`. The executing agent must load that skill and let it select the transport and completion-waiting path. An attached MCP path is eligible only when it demonstrably preserves the exact environment input. Changing the agent shell environment does not prove that an already running MCP server received it. When the native contract selects CLI, run it once and await the same process handle. Do not start or restart an MCP server or change host configuration to make MCP eligible. The configured gate allows up to 9000 seconds for the complete native runtime scenario inventory, running the canonical lifecycle alone before the independent batches with at most four workers. The existing scenario and command limits remain 900 and 20 seconds. The configured gate does not use Gaori's shorter ad-hoc default.

## E2E Environment

The E2E production-equivalent artifacts are the shipped `plugins/aquarium/tools/aquarium-status/aquarium_status.py`, `plugins/aquarium/skills/test-setup/scripts/inspect_testing.py`, and `plugins/aquarium/skills/release-qa/scripts/manage_release_qa.py` CLIs. E2E invokes only their documented public interfaces in child processes and treats output streams and exit status as black-box results. The shipped docs-setup inspector is exercised through the same public CLI boundary in `test-int`; the release-notes, publication-state, and independent-review target helpers' bounded structural states are covered in `test-unit` with isolated temporary repositories and fake local executables. Master verifies actual reviewer-team dispatch, UI coverage and result handling separately; static tests cannot establish the requested model, effort, target, or Brief delivered to host agents.

Scenarios use test-owned temporary repositories and input files under `tmp_path`, which pytest cleans up. Release-QA scenarios also create private `release-qa.*` evidence and confirmation roots under `/tmp`; their fixture teardown and `finally` blocks remove those additional roots. Tests never delete a path they did not create or use a production environment, credential, account, network, port, database, container, volume, or provider. A missing Python runtime, pytest dependency, script, or subprocess capability fails the gate rather than producing a successful skip.

Offline installation fixtures use development SDK code with simulated pinned
artifact metadata and version identity. Newer development dependencies therefore
do not conflict with production artifact checks. The fixtures verify installer
behavior; they do not qualify downloaded distribution artifacts.

## Language Diagnostics

- Ruff formatting and lint cover all maintained Python source and test files.
- Python bytecode compilation is implicit in every pytest and unittest import; syntax failures stop the applicable stage.
- Ruby syntax is checked explicitly before the package validator runs.
- Bounded multi-process tests exercise the production-status ledger's lock and revision behavior. Native race sanitizers, undefined-behavior sanitizers, browser, device, and database diagnostics are not applicable to the Python/Ruby plugin assets and local utilities.

## Legacy Waivers

### AQ-WAIVER-001

- Rule: `AQTEST-009`
- Scope: The pre-existing integration suites `tests/test_inspect_tools.py`, `tests/test_task_commit_gate.py`, and `tests/test_normalize_manifest.py` may retain `unittest`, including subsequent tests in those same established suites. `tests/test_inspect_testing.py` uses native pytest fixtures and assertions and is outside this waiver.
- Pre-existing implementation: Each suite existed before Aquarium first enrolled itself in the common test contract and exercises temporary repositories, subprocesses, fixtures, and component boundaries through standard-library `unittest` assertions.
- Equivalence evidence: The suites fail through ordinary nonzero unittest exits, isolate state with per-test temporary directories, and cover positive, negative, malformed-input, timeout, and boundary scenarios without a separately managed service.
- Migration risk: A wholesale assertion and fixture rewrite would create broad test-only churn and could alter subprocess, cleanup, and temporary-repository semantics without increasing product coverage.
- Residual risk: The waived integration layer does not use pytest-native fixtures, assertions, markers, or diagnostics. New unit and E2E layers remain outside this waiver and use pytest.
- Approved by Master
- Revalidation triggers: A change to the waived layer's stage mapping or runner command, framework or major version, waiver scope, layer identity, integration boundary, isolation or failure semantics, execution-affecting CI, environment, or dependency authority, `aquarium-test-contract` version, or a failure of the recorded equivalence evidence. Routine additions or edits to test cases inside the same waived suites do not by themselves stale the waiver while those supporting facts remain unchanged. A stale waiver does not authorize execution or establish conformance.

## Local review settlement qualification

Procedure guard and graph tests cover local-correction eligibility, retained source gaps, serial pending-correction admission, failed checks, ordinary rework for nonlocal or mixed issues, native backend admission and required final Judge dominance. Existing native fixtures default to zero local candidates and retain their original rework scenarios. C-17 adds six native qualification scenarios: Task, Goal and Validation each record one eligible Medium correction with an original unmet criterion, then settle immediately or retry a failed local check. Each scenario requires final judgment and preserves the original review count and source obligations. Helper unit tests verify the generated values; native execution of these new scenarios is unverified until an exact-artifact qualification receipt records it. These checks do not prove skill decisions.

Before release, exercise these cases against the exact candidate installed in the dedicated UTM VM, over the host's installed release combination:

| Case | Agent-observed expectation |
| --- | --- |
| LOCAL-01 | A documentation correction that originally fails a completion criterion is read back and checked, then advances with current criterion evidence and no new provider ordinal or approval request. |
| LOCAL-02 | A simple behavioral fix passes its focused regression and affected required checks, retains the original Medium priority and proceeds through the final Judge without provider re-review. |
| LOCAL-03 | A harmless unauthorized command, read or file creation is reported separately; prohibited results are excluded and usable complete reports remain admitted. Covered cleanup creates no product finding or provider round. |
| LOCAL-04 | A target write, lost reviewer coverage or missing required evidence keeps the affected verdict pending; recovery addresses that guarantee and never converts an apology into proof. |
| LOCAL-05 | A mixed set containing a design or safety issue takes ordinary authorized rework and necessary review; a failed local check or unresolved final criterion cannot advance. |
| LOCAL-06 | A confirmation-only review can settle an eligible correction within existing effect authority; a genuine further provider assessment with no remaining grant asks for its exact bounded authority. |

Run the applicable Task, Goal and Validation cases on Independent Review, Herdr and Mulgae, retaining native CI, publication and coverage admission for Mulgae. A waiver uses coordinator provenance. Verify resumption, exact staged or committed composition, commit handoff, prior snapshot preservation and fresh-session discovery after an authorized managed-file update. Master's functional results and exact-candidate upgrade evidence remain required; a source gate does not report those outcomes.

## Mulgae v0.1.25 adoption

The inspector tests exercise the stable v0.1.25 floor, command-result v19 and Doctor v5 admission, Config v5 fixture diagnostics, redaction and private-file safeguards. Promoted-evidence v2 schema tests reject native-impossible scope/operand/Git-base combinations, missing bindings, capture fields, runtime identities and unsafe package-relative names. The stdin digest helper tests use official v0.1.25 example digests and an independently calculated Go encoding case with HTML and Unicode separators, including a non-UTF-8 stdin text configuration. These checks do not establish actual native publication, source consistency or staged payload integrity. Procedure tests exercise explicit fresh-root admission after terminal settlement, rejection of active, completed or wrong-route states for that admission, truthful completed-checkpoint recording, pending-ordinal continuity and retained historical snapshots.

Installed qualification must cover the exact Aquarium candidate in UTM over the host's released baseline: Config v4-to-v5 migration and restoration, release-matched skill discovery, all five native targets, independent project binding errors, expected empty capture/guard capabilities, terminal partial failures and explicit new-review authority, historical reads and v2 hardening/commit handoffs. These skill and upgrade outcomes remain unverified until actual results, including Master's functional assessment, are available. No host candidate installation is permitted by the local test gate.
