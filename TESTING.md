# Testing

## Contract

This repository is enrolled in `aquarium-test-contract/v1` with the `make` profile. The root `Makefile` is the executable authority; this document records its intended meaning and never authorizes a handler to skip a check.

## Canonical Commands

- Complete serial gate: `make test`
- Static preparation: `make test-prepare`
- Unit tests: `make test-unit`
- Integration tests: `make test-int`
- End-to-end tests: `make test-e2e`
- Exact Podway v0.2.7 compatibility: `PODWAY_BIN=<absolute-path> make test-podway-compat`

The aggregate uses recursive Make recipe calls in prepare, unit, integration, and E2E order. It stops on the first failure and retains that order under parallel Make. Every handler is non-interactive: Make disables inherited pagers, clears inherited `PYTEST_ADDOPTS`, pytest ignores user-installed plugin entry points, and whitespace validation invokes Git with `--no-pager`. The repository fixes its runners to `.venv/bin/python` and `.venv/bin/ruff` when the enrolled environment exists, otherwise to `python3` and `ruff`; command-line overrides cannot replace those identities.

## Stage Mapping

| Stage | Checks |
|---|---|
| `test-prepare` | Ruff formatting and lint for every maintained Python source and test file; plugin-manifest JSON parsing; Ruby syntax; the local cross-skill, procedure, documentation, and release-contract validator; whitespace validation. |
| `test-unit` | Native pytest tests for isolated pure functions in the test-setup, docs-setup, release-notes, publication-state, provider-terminal, Orca Review repository-state, and independent-review target inspectors and helpers. |
| `test-int` | The native pytest docs-setup and test-setup inspector suites followed by the three pre-existing Python `unittest` suites exercising tool inspection, manifest normalization, commit-gate behavior, temporary Git repositories, subprocess boundaries, and cross-component fixtures. |
| `test-e2e` | Python pytest scenarios invoking the shipped test-setup inspector CLI as a black box against isolated temporary repository fixtures. |

Dependency installation is outside every handler. Prepare may rewrite only the Python files listed in the root `Makefile` through deterministic Ruff formatting; later stages exercise the resulting candidate.

`test-podway-compat` is an external-artifact gate and is intentionally not part of the ordinary `make test` aggregate. It requires one absolute, executable, nonsymlink Podway binary path, derives an exact sibling `podwayd`, verifies both v0.2.7 identities, and records both artifact SHA-256 values. It runs format check, validate, vet, lint and check with warnings as errors, and preview against all five canonical Aquarium Procedures, requires each exact digest-fenced start suggestion, and rejects unknown fields and declaration values above `max_item_length: 8192` and `max_total_length: 1000000`.

The gate then uses two fresh isolated runtime roots under macOS's canonical `/private/tmp` backing for `/tmp`. Each root receives private account, Podway, socket, cache, temporary, sandbox-worktree, and binary-snapshot paths; it never installs or connects to the production daemon. Observable phase-aware readiness precedes execution. Both passes drive the five canonical Procedures through digest-fenced start, goal-bearing begin, observation v3, completion, and terminal disposition. The task path additionally proves conditional required items, the 20-entry runtime list limit, structured check results, guarded routing, verification and manual rework, immutable session snapshots, and a bounded 300-entry fixture's paged evidence and stale-token rejection. A third isolated root proves that an incorrect workspace UUID is rejected without mutation, an exact fenced removal deletes `.podway` while preserving the Git worktree, and replay converges through `already_absent`. Per-command, readiness, process-exit, and overall deadlines are enforced, and each daemon, socket, worktree, and runtime root is removed on context exit. The v3 JSON receipt requires both lifecycle runs and the workspace-removal result to pass.

A local development binary provides development-contract evidence only. For distribution readiness, first verify the official v0.2.7 Apple Silicon archive against its published checksum, then run the same target against the extracted exact binary. The target requires no network after artifact provisioning. Podway's own exact release-candidate gate remains authoritative for Podway distribution; Aquarium's independent target proves only compatibility of the exact Aquarium candidate named by the resulting Git revision.

## Test Frameworks

| Language and layer | Framework | Dependency evidence | Command | Waiver |
|---|---|---|---|---|
| Python unit | pytest with native assertions | `requirements.txt`, `pyproject.toml` | `$(PYTHON) -m pytest tests/unit` | None |
| Python integration | pytest with native fixtures and assertions plus waived legacy `unittest` | `requirements.txt`, `pyproject.toml`, Python standard library, and the committed pre-existing suites | `$(PYTHON) -m pytest tests/test_inspect_docs.py tests/test_inspect_testing.py`, then `$(PYTHON) -m unittest tests/test_inspect_tools.py tests/test_task_commit_gate.py tests/test_normalize_manifest.py` | `AQ-WAIVER-001` applies only to the three `unittest` suites |
| Python E2E | pytest with native assertions | `requirements.txt`, `pyproject.toml` | `$(PYTHON) -m pytest tests/e2e` | None |
| Ruby architecture validation | Standalone deterministic assertion script | User-provided Ruby 3.3 or newer | `ruby tests/validate.rb` inside `test-prepare` | Not a unit or integration test framework layer |

The test environment requires the exact Python development dependencies in `requirements.txt`. Every handler checks the selected environment before executing and fails with an installation command when Python, pytest, PyYAML, Ruff, or an exact dependency version is unavailable. Handlers never install dependencies implicitly.

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

The E2E production-equivalent artifact is the shipped `plugins/aquarium/skills/test-setup/scripts/inspect_testing.py` CLI. E2E invokes only its documented `--repository` public interface in a child process and treats its JSON and exit status as black-box output. The shipped docs-setup inspector is exercised through the same public CLI boundary in `test-int`; the release-notes, publication-state, provider-terminal, Orca Review repository-state, and independent-review target helpers' bounded structural states are covered in `test-unit` with isolated temporary repositories and fake local executables.

Each scenario creates one unique operating-system temporary directory containing only test-owned repository fixtures. It uses no credential, account, network, port, database, container, volume, provider, or production environment. `pytest` owns teardown through `tmp_path`; the test never deletes a path it did not create. A missing Python runtime, pytest dependency, script, or subprocess capability fails the gate rather than producing a successful skip.

## Language Diagnostics

- Ruff formatting and lint cover all maintained Python source and test files.
- Python bytecode compilation is implicit in every pytest and unittest import; syntax failures stop the applicable stage.
- Ruby syntax is checked explicitly before the architecture validator runs.
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
