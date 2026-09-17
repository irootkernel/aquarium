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
- Exact Podway v0.2.10 compatibility: `PODWAY_BIN=<absolute-path> make test-podway-compat`

The aggregate uses recursive Make recipe calls in prepare, unit, integration, and E2E order. It stops on the first failure and retains that order under parallel Make. Every handler is non-interactive: Make disables inherited pagers, clears inherited `PYTEST_ADDOPTS`, pytest ignores user-installed plugin entry points, and whitespace validation invokes Git with `--no-pager`. The repository fixes its runners to `.venv/bin/python` and `.venv/bin/ruff` when the enrolled environment exists, otherwise to `python3` and `ruff`; command-line overrides cannot replace those identities.

## Stage Mapping

| Stage | Checks |
|---|---|
| `test-prepare` | Ruff formatting and lint for maintained Python files; plugin-manifest JSON parsing; Ruby syntax; package metadata, local references, basic Procedure structure, and release-version identity; whitespace validation. |
| `test-unit` | Native pytest tests for isolated pure functions in the test-setup, docs-setup, release-notes, publication-state, and independent-review target inspectors and helpers. |
| `test-int` | The native pytest docs-setup, global-tool, and test-setup inspector suites followed by the three pre-existing Python `unittest` suites exercising tool inspection, manifest normalization, commit-gate behavior, temporary Git repositories, subprocess boundaries, and cross-component fixtures. |
| `test-e2e` | Python pytest scenarios invoking the shipped test-setup inspector CLI as a black box against isolated temporary repository fixtures. |

Dependency installation is outside every handler. Prepare may rewrite only the Python files listed in the root `Makefile` through deterministic Ruff formatting; later stages exercise the resulting candidate.

`test-podway-compat` is an external-artifact gate and is intentionally not part of the ordinary `make test` aggregate. It binds its receipt to `git rev-parse HEAD`, refuses any dirty worktree, and therefore runs only against a clean committed candidate. It requires one absolute, executable, nonsymlink Podway binary path, derives an exact sibling `podwayd`, verifies both v0.2.10 identities, and records both artifact SHA-256 values. It runs format check, validate, vet, lint and check with warnings as errors, and preview against all five canonical Aquarium Procedures, requires each exact digest-fenced start suggestion, and rejects unknown fields and declaration values above `max_item_length: 8192` and `max_total_length: 1000000`.

The gate then uses fresh isolated `release-qa` runtime roots under macOS's canonical `/private/tmp` backing for `/tmp`. Each root receives private account, Podway, socket, cache, temporary, sandbox-worktree, and binary-snapshot paths; it never installs or connects to the production daemon. Observable daemon-status v3 readiness precedes execution. Two standard passes drive the five canonical Procedures through digest-fenced start, goal-bearing begin, observation v3, completion, and terminal disposition. Task, goal, and validation paths each exercise a nonzero historical Low result through completed local settlement without another review node. The task path first routes a Medium implementation finding through correction and the required next review; validation preserves its independently required final review.

Additional bounded roots exercise the native correction matrix. C-01 proves two audit Low findings, no provider finding, rejection of premature `validated`, exact disposition readback, unchanged target, and settlement without re-audit. C-02 repeats the proof with one namespaced provider Low finding and three pending dispositions. C-04 and C-05 cover the Goal Procedure's failed, inconclusive, and passing verification and review-readiness results while all finding counts remain zero. C-16 separately covers failed and inconclusive Validation final-review operations independently from required-evidence counts, plus passing operations with and without required evidence gaps, including guarded rejection without state mutation and the distinct validated, evidence-incomplete, and review-operation-incomplete routes. C-09 covers member-task, pre-validation-remediation, and epic-closeout goal kinds with validated-closeout evidence plus member-task with native-review evidence, isolating the goal-kind guard. C-08 reads the Low settlement basis, disposition, blocker count, and target from both Goal and Validation wait actions before proving that the following user choice remains unset. C-10 covers Goal and Validation Medium-or-higher authority waits, a Task confirmation-only completion gap, and an epic-closeout completion gap. The Task completion-gap and Goal Medium variants each select `fix-and-review` once, complete the resulting correction route, reproduce the gap, and prove that the next fresh user choice is unset. Separate Task, Goal, and Validation stop variants carry the completion assessment and user direction to final goal assessment and require a `not-achieved` outcome. The receipt records every executed subvariant and its completed assertions; a case ID is emitted only after all assertions for that subvariant pass. The task path additionally proves conditional required items, the 20-entry runtime list limit, structured check results, guarded routing, verification and manual rework, immutable session snapshots, and a bounded 300-entry fixture's paged evidence and stale-token rejection. Another isolated root proves that an incorrect workspace UUID is rejected without mutation and that an exact fenced removal deletes `.podway` while preserving the Git worktree. It requires the identical UUID-fenced replay to succeed with `podway.workspace-removal-result/v1`, a null workspace UUID, `registry_entry_removed=false`, `podway_directory_removed=false`, and `already_absent=true`, then independently verifies the absent registry entry and `.podway` tree. Per-command, readiness, process-exit, and overall deadlines are enforced, and each daemon, socket, worktree, and runtime root is removed on context exit. The v6 JSON receipt requires both lifecycle runs, the exact correction-case subvariant map, the per-case assertion record, and the complete workspace-removal result to pass.

Further bounded roots prove the serial completion contract directly. Task coverage includes `unverified` return to fresh review evidence, simultaneous-owner precedence, each sole phase owner, and inconsistent finding totals or owner evidence returning to review. The finding-total case includes a surplus unresolved finding beside a Low bucket. Goal coverage sends the same inconsistency back to evidence capture and also covers complete hardening-deferral traversal and an epic-closeout completion gap stopping for user direction. Goal and Validation coverage exercises both `unmet` and `unverified` completion routes.

A local development binary provides development-contract evidence only. For distribution readiness, first verify the official v0.2.10 Apple Silicon archive against its published checksum, then run the same target against the extracted exact binary. The target requires no network after artifact provisioning. Podway's own exact release-candidate gate remains authoritative for Podway distribution; Aquarium's independent target proves only compatibility of the exact Aquarium candidate named by the resulting Git revision.

Podway skill changes also need Master's manual verification: setup must compare the complete skill tree against the catalog's fixed commit even when the runtime release changes; resuming the same authorized workspace and session must retain approval while using fresh fences; an unauthorized identity change must stop session mutations; and Codex and Podway goals must follow their own creation, completion, and blocker rules. An uncertain mutation must retain its original request and idempotency key for recovery. These checks remain unverified until Master provides their outcomes. `make test` and the binary compatibility gate do not prove skill behavior.

## Test Frameworks

| Language and layer | Framework | Dependency evidence | Command | Waiver |
|---|---|---|---|---|
| Python unit | pytest with native assertions | `requirements.txt`, `pyproject.toml` | `$(PYTHON) -m pytest tests/unit` | None |
| Python integration | pytest with native fixtures and assertions plus waived legacy `unittest` | `requirements.txt`, `pyproject.toml`, Python standard library, and the committed pre-existing suites | `$(PYTHON) -m pytest tests/test_inspect_docs.py tests/test_inspect_global_tools.py tests/test_inspect_testing.py`, then `$(PYTHON) -m unittest tests/test_inspect_tools.py tests/test_task_commit_gate.py tests/test_normalize_manifest.py` | `AQ-WAIVER-001` applies only to the three `unittest` suites |
| Python E2E | pytest with native assertions | `requirements.txt`, `pyproject.toml` | `$(PYTHON) -m pytest tests/e2e` | None |
| Ruby package validation | Standalone structural assertion script | User-provided Ruby 3.3 or newer | `ruby tests/validate.rb` inside `test-prepare` | Not a unit or integration test framework layer |

The test environment requires the exact Python development dependencies in `requirements.txt`, including the MCP SDK and its runtime dependencies. Runtime installation tests reuse these dependencies in temporary environments without downloading packages; stdio tests exercise the packaged server launcher. The shipped runtime has its own hash-pinned `plugins/aquarium/tools/aquarium-dev/requirements.txt`. Every handler checks the selected environment before executing and fails with an installation command when Python, pytest, PyYAML, Ruff, or an exact dependency version is unavailable. Handlers never install dependencies implicitly.

The global inspector tests use temporary Codex homes, synthetic package assets, and local executable fixtures to check home discovery, CLI probe reuse, independent artifact health, MCP home binding, package pins, and partial readiness. PyPI responses are mocked, so the standard gate remains offline. The asset-probe test checks the native rendered-rules contract separately from raw skill bytes; a successful aggregate doctor cannot substitute for either comparison.

## Gaori Mapping

Gaori is optional evidence compression. Each command wraps one authoritative Make handler, and the wrapped process exit code remains authoritative.

| Gaori command | Handler | Output family | Parser |
|---|---|---|---|
| `test` | `make test` | Mixed Python, Ruby, Ruff, Git, and Make | `generic` |
| `test-prepare` | `make test-prepare` | Mixed static tooling | `generic` |
| `test-unit` | `make test-unit` | pytest | `pytest` |
| `test-int` | `make test-int` | Mixed pytest and Python unittest | `generic` |
| `test-e2e` | `make test-e2e` | pytest | `pytest` |

## E2E Environment

The E2E production-equivalent artifact is the shipped `plugins/aquarium/skills/test-setup/scripts/inspect_testing.py` CLI. E2E invokes only its documented `--repository` public interface in a child process and treats its JSON and exit status as black-box output. The shipped docs-setup inspector is exercised through the same public CLI boundary in `test-int`; the release-notes, publication-state, and independent-review target helpers' bounded structural states are covered in `test-unit` with isolated temporary repositories and fake local executables.

Each scenario creates one unique operating-system temporary directory containing only test-owned repository fixtures. It uses no credential, account, network, port, database, container, volume, provider, or production environment. `pytest` owns teardown through `tmp_path`; the test never deletes a path it did not create. A missing Python runtime, pytest dependency, script, or subprocess capability fails the gate rather than producing a successful skip.

## Language Diagnostics

- Ruff formatting and lint cover all maintained Python source and test files.
- Python bytecode compilation is implicit in every pytest and unittest import; syntax failures stop the applicable stage.
- Ruby syntax is checked explicitly before the package validator runs.
- Race, undefined-behavior, sanitizer, browser, device, and database diagnostics are not applicable because Aquarium ships declarative plugin assets and local Python/Ruby inspection utilities with no native, concurrent, browser, device, or database runtime.

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
