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
- Exact Podway v0.2.11 compatibility: `PODWAY_BIN=<absolute-path> make test-podway-compat`

The aggregate uses recursive Make recipe calls in prepare, unit, integration, and E2E order. It stops on the first failure and retains that order under parallel Make. Every handler is non-interactive: Make disables inherited pagers, clears inherited `PYTEST_ADDOPTS`, pytest ignores user-installed plugin entry points, and whitespace validation invokes Git with `--no-pager`. The repository fixes its runners to `.venv/bin/python` and `.venv/bin/ruff` when the enrolled environment exists, otherwise to `python3` and `ruff`; command-line overrides cannot replace those identities.

## Stage Mapping

| Stage | Checks |
|---|---|
| `test-prepare` | Ruff formatting and lint for maintained Python files; plugin-manifest JSON parsing; Ruby syntax; package metadata, local references, basic Procedure structure, and release-version identity; whitespace validation. |
| `test-unit` | Native pytest tests for isolated installed-plugin resource containment through the Ruby link checker, complete upstream skill inventories, Procedure routing and qualification harnesses, production-status contracts and storage, aquarium-dev runtime, installer, service and isolated MCP STDIO helpers, release-QA evidence and publication helpers, and the setup, documentation, release-note, and review-target inspectors. |
| `test-int` | Native pytest production-status persistence, concurrency, stored-key removal and inventory-retention scenarios plus the documentation, global-tool and testing inspectors; the three approved legacy unittest suites exercise tool inspection, manifest normalization and commit gates across temporary Git repositories and subprocess boundaries. |
| `test-e2e` | Python pytest scenarios invoking the shipped production-status and test-setup CLIs and release-QA freeze/confirmation CLI as black boxes against isolated temporary fixtures. |

Dependency installation is outside every handler. Prepare may rewrite only the Python files listed in the root `Makefile` through deterministic Ruff formatting; later stages exercise the resulting candidate.

`test-podway-compat` is an external-artifact gate and is intentionally not part of the ordinary `make test` aggregate. It binds its receipt to `git rev-parse HEAD`, refuses any dirty worktree, and therefore runs only against a clean committed candidate. It requires one absolute, executable, nonsymlink Podway binary path, derives an exact sibling `podwayd`, verifies both v0.2.11 identities, and records both artifact SHA-256 values. It runs format check, validate, vet, lint and check with warnings as errors, and preview against all five canonical Aquarium Procedures, requires each exact digest-fenced start suggestion, and rejects unknown fields and declaration values above `max_item_length: 8192` and `max_total_length: 1000000`.

The gate uses isolated `release-qa` runtime roots under macOS's canonical `/private/tmp` backing for `/tmp`. Each root receives private account, Podway, socket, cache, temporary, sandbox-worktree, and binary-snapshot paths; it never installs or connects to the production daemon. Observable daemon-status v3 readiness precedes execution. At most four roots run concurrently. One canonical lifecycle pass drives all five managed Procedures through digest-fenced start, goal-bearing begin, observation v3, completion, and terminal disposition. Task, goal, and validation paths each exercise a nonzero historical Low result through completed local settlement without another review node. The task path first routes a Medium implementation finding through correction and the required next review; validation preserves its independently required final review. A separate Validation scenario covers the provider-Low variant without repeating the other four Procedures or the pagination fixture.

Additional bounded sessions exercise the native correction matrix. Terminal scenarios are distributed across four reusable runtimes. The harness restores canonical Procedure bytes and session-local state before each case. Scenarios that stop before terminal disposition retain separate roots so their active state cannot affect another case. C-01 proves two audit Low findings, no provider finding, rejection of premature `validated`, exact disposition readback, unchanged target, and settlement without re-audit. C-02 repeats the proof with one namespaced provider Low finding and three pending dispositions. C-04 and C-05 cover the Goal Procedure's failed, inconclusive, and passing verification and review-readiness results while all finding counts remain zero. C-16 separately covers failed and inconclusive Validation final-review operations independently from required-evidence counts, plus passing operations with and without required evidence gaps, including guarded rejection without state mutation and the distinct validated, evidence-incomplete, and review-operation-incomplete routes. C-09 covers member-task, pre-validation-remediation, and epic-closeout goal kinds with validated-closeout evidence plus member-task with native-review evidence, isolating the goal-kind guard. C-08 reads the current Low blocker basis and tests both remaining remediation authority and exhausted-authority waits. Task cases retain zero historical phase obligations while routing the new blocker to implementation preparation, verification, or documentation; separate cases select stop and one bounded correction. Goal and Validation cases preserve the exact native rework cause or stop at an unset user choice. C-10 covers the third work-unit assessment, the ordinal-four confirmation boundary, Goal and Validation Medium-or-higher authority waits, a Task confirmation-only completion gap, and an epic-closeout completion gap. Each Task completion-gap, Goal Medium, and Validation Medium variant selects `fix-and-review` once, completes one bounded correction route, reproduces the gap, and proves that the next user choice is fresh and unset. Separate Task, Goal, and Validation stop variants carry the completion assessment and user direction to final goal assessment and require a `not-achieved` outcome. The receipt records every executed subvariant and its completed assertions; a case ID is emitted only after all assertions for that subvariant pass. The canonical lifecycle pass also checks the archive-list v2 count and oldest summary. The task path also attaches its optional plan while `record-plan` is current, reads exact path, digest, and size at preparation and implementation, preserves distinct decision and manual rework causes through fresh preparation, and composes a different verified Low target without another ordinal. It additionally proves conditional required items, the 20-entry runtime list limit, structured check results, guarded routing, verification and manual rework, immutable session snapshots, and a bounded 300-entry fixture's paged evidence and stale-token rejection. Another isolated root proves that an incorrect workspace UUID is rejected without mutation and that an exact fenced removal deletes `.podway` while preserving the Git worktree. It requires the identical UUID-fenced replay to succeed with `podway.workspace-removal-result/v1`, a null workspace UUID, `registry_entry_removed=false`, `podway_directory_removed=false`, and `already_absent=true`, then independently verifies the absent registry entry and `.podway` tree. Per-command, readiness, process-exit, and per-scenario deadlines are enforced, and each daemon, socket, worktree, and runtime root is removed on context exit. The v8 JSON receipt requires the canonical lifecycle pass, exact correction-case subvariant map, per-case assertion record, runtime-batch cleanup results, and complete workspace-removal result to pass.

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

A local development binary provides development-contract evidence only. For distribution readiness, first verify the official v0.2.11 Apple Silicon archive against its published checksum, then run the same target against the extracted exact binary. The target requires no network after artifact provisioning. Podway's own exact release-candidate gate remains authoritative for Podway distribution; Aquarium's independent target proves only compatibility of the exact Aquarium candidate named by the resulting Git revision.

Podway skill changes also need Master's manual verification: setup must compare the complete skill tree against the catalog's fixed commit even when the runtime release changes; resuming the same authorized workspace and session must retain approval while using fresh fences; an unauthorized identity change must stop session mutations; and Codex and Podway goals must follow their own creation, completion, and blocker rules. An uncertain mutation must retain its original request and idempotency key for recovery. Plan-handoff verification must also cover a plan file changed or removed after attachment: the handler must stop before implementation, while an ordinary session without an artifact remains valid. These checks remain unverified until Master provides their outcomes. `make test` and the binary compatibility gate do not prove skill behavior.

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
| Staged Orca review and native recovery | Dispatch the complete current staged target with every canonical reviewer restriction; resume or retry only through native support and existing authority. |
| Task records, prose, dossier, and commit handoff | Settle the canonical record and required dossier decision before review; apply the final prose pass before capture; delegated member acceptance consumes only its applicable one-commit grant. |
| Epic delivery through final acceptance | After one execution-envelope approval, complete each Task and owned correction with evidence, delegated acceptance, and its scoped commit; finish internal validation, prepare closeout, then wait for one actual user acceptance. Progress reports do not pause execution. |
| Epic acceptance after correction or context restoration | Reconstruct the exact envelope, candidate, consumed grants and review ordinals; reject stale acceptance and duplicate grants, refresh affected evidence, and never attribute coordinator acceptance to the user. |
| Independent validation, final Epic closeout, and stopped outcomes | Keep actual user acceptance; reject the internal Epic delegation route. Prior Procedure snapshots retain their original approval contract. |
| First release, settled light candidate, active Design Gate, and publication recovery | Keep baseline, candidate SHA, required scenario evidence, release title, remote ancestry, and separate publication authority consistent. Fixture success is not a release outcome. |
| Corrected plugin loaded in a fresh installed Codex session | Bind the installed package to the exact candidate and observe all tools declared by the packaged MCP server's OPERATIONS map through host discovery. JSON parsing and direct STDIO calls do not satisfy this check. |
| PM, setup lookup, installer, and Sorage Project setup | Disclose PM files and clipboard replacement separately; preserve selected lookup and pinned installer/cache/lock-file boundaries; Project setup does not trigger broker discovery. |
| Design QA and committed delivery input | Preserve raw PASS, REVISE, and FAIL separately from operation failure; route content corrections to their owner; document approval alone does not grant commit or implementation authority. |
| War-room no-work and incomplete investigation | Require evidence that expected behavior holds for no-work, retain quality and approval, use canonical note owners or verified no-change, and leave unexplained symptoms incomplete. |
| Status removal after path reuse or symlink replacement | Show and approve the exact stored row; preserve all revision and digest fences and leave replacement paths untouched. |

Do not claim functional completion before Master confirms the required outcomes.
Producer source fixes, release, installation, activation, and cross-skill
acceptance remain separate evidence classes.

## Test Frameworks

| Language and layer | Framework | Dependency evidence | Command | Waiver |
|---|---|---|---|---|
| Python unit | pytest with native assertions | `requirements.txt`, `pyproject.toml`, and Ruby 3.3+ for the package fixture | `$(PYTHON) -m pytest tests/unit` | None |
| Python integration | pytest with native fixtures and assertions plus waived legacy `unittest` | `requirements.txt`, `pyproject.toml`, Python standard library, and the committed pre-existing suites | `$(PYTHON) -m pytest tests/test_aquarium_status_integration.py tests/test_inspect_docs.py tests/test_inspect_global_tools.py tests/test_inspect_testing.py`, then `$(PYTHON) -m unittest tests/test_inspect_tools.py tests/test_task_commit_gate.py tests/test_normalize_manifest.py` | `AQ-WAIVER-001` applies only to the three `unittest` suites |
| Python E2E | pytest with native assertions | `requirements.txt`, `pyproject.toml` | `$(PYTHON) -m pytest tests/e2e` | None |
| Ruby package validation | Standalone structural assertion script | User-provided Ruby 3.3 or newer | `ruby tests/validate.rb` inside `test-prepare` | Also invoked by pytest package fixtures through the shared local-reference checker |

The test environment requires the exact Python development dependencies in `requirements.txt`, including the MCP SDK and its runtime dependencies. Runtime installation tests reuse these dependencies in temporary environments without downloading packages; stdio tests exercise the packaged server launcher. The shipped runtime has its own hash-pinned `plugins/aquarium/tools/aquarium-dev/requirements.txt`. Every handler checks the selected environment before executing and fails with an installation command when Ruby, Python, pytest, PyYAML, Ruff, or an exact dependency version is unavailable. Handlers never install dependencies implicitly.

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

The Podway compatibility command inherits `PODWAY_BIN` from the Gaori process environment. The required invocation is `PODWAY_BIN=<absolute-path-to-extracted-v0.2.11-podway> gaori run test-podway-compat`; this expresses the command and environment rather than bypassing `$use-gaori`. The executing agent must load that skill and let it select the transport and completion-waiting path. An attached MCP path is eligible only when it demonstrably preserves the exact environment input. Changing the agent shell environment does not prove that an already running MCP server received it. When the native contract selects CLI, run it once and await the same process handle. Do not start or restart an MCP server or change host configuration to make MCP eligible. The configured 3600-second timeout covers the bounded parallel runtime matrix without relying on Gaori's shorter ad-hoc default.

## E2E Environment

The E2E production-equivalent artifacts are the shipped `plugins/aquarium/tools/aquarium-status/aquarium_status.py`, `plugins/aquarium/skills/test-setup/scripts/inspect_testing.py`, and `plugins/aquarium/skills/release-qa/scripts/manage_release_qa.py` CLIs. E2E invokes only their documented public interfaces in child processes and treats output streams and exit status as black-box results. The shipped docs-setup inspector is exercised through the same public CLI boundary in `test-int`; the release-notes, publication-state, and independent-review target helpers' bounded structural states are covered in `test-unit` with isolated temporary repositories and fake local executables. Master verifies the three-subagent skill dispatch and result handling separately; static tests cannot establish the requested model, effort, target, or Brief delivered to host agents.

Scenarios use test-owned temporary repositories and input files under `tmp_path`, which pytest cleans up. Release-QA scenarios also create private `release-qa.*` evidence and confirmation roots under `/tmp`; their fixture teardown and `finally` blocks remove those additional roots. Tests never delete a path they did not create or use a production environment, credential, account, network, port, database, container, volume, or provider. A missing Python runtime, pytest dependency, script, or subprocess capability fails the gate rather than producing a successful skip.

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
