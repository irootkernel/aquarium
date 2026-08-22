# Testing

## Contract

This repository is enrolled in `aquarium-test-contract/v1` with the `make` profile. The root `Makefile` is the executable authority; this document records its intended meaning and never authorizes a handler to skip a check.

## Canonical Commands

- Complete serial gate: `make test`
- Static preparation: `make test-prepare`
- Unit tests: `make test-unit`
- Integration tests: `make test-int`
- End-to-end tests: `make test-e2e`

The aggregate uses recursive Make recipe calls in prepare, unit, integration, and E2E order. It stops on the first failure and retains that order under parallel Make. Every handler is non-interactive: Make disables inherited pagers, pytest ignores user-installed plugin entry points, and whitespace validation invokes Git with `--no-pager`. An existing `.venv` is selected automatically without requiring shell activation; explicit `PYTHON` and `RUFF` Make overrides take precedence.

## Stage Mapping

| Stage | Checks |
|---|---|
| `test-prepare` | Ruff formatting and lint for every maintained Python source and test file; plugin-manifest JSON parsing; Ruby syntax; the local cross-skill, procedure, documentation, and release-contract validator; whitespace validation. |
| `test-unit` | Native pytest tests for isolated pure functions in the test-setup structural inspector. |
| `test-int` | The pre-existing Python `unittest` suites exercising executable inspectors, manifest normalization, commit-gate behavior, temporary Git repositories, subprocess boundaries, and cross-component fixtures. |
| `test-e2e` | Python pytest scenarios invoking the shipped test-setup inspector CLI as a black box against isolated temporary repository fixtures. |

Dependency installation is outside every handler. Prepare may rewrite only the Python files listed in the root `Makefile` through deterministic Ruff formatting; later stages exercise the resulting candidate.

## Test Frameworks

| Language and layer | Framework | Dependency evidence | Command | Waiver |
|---|---|---|---|---|
| Python unit | pytest with native assertions | `requirements.txt`, `pyproject.toml` | `python3 -m pytest tests/unit` | None |
| Python integration | `unittest` | Python standard library and the committed pre-existing suites | `python3 -m unittest tests/test_inspect_tools.py tests/test_inspect_testing.py tests/test_task_commit_gate.py tests/test_normalize_manifest.py` | `AQ-WAIVER-001` |
| Python E2E | pytest with native assertions | `requirements.txt`, `pyproject.toml` | `python3 -m pytest tests/e2e` | None |
| Ruby architecture validation | Standalone deterministic assertion script | User-provided Ruby 3.3 or newer | `ruby tests/validate.rb` inside `test-prepare` | Not a unit or integration test framework layer |

The test environment requires the exact Python development dependencies in `requirements.txt`. Every handler checks the selected environment before executing and fails with an installation command when Python, pytest, PyYAML, Ruff, or an exact dependency version is unavailable. Handlers never install dependencies implicitly.

## Gaori Mapping

Gaori is optional evidence compression. Each command wraps one authoritative Make handler, and the wrapped process exit code remains authoritative.

| Gaori command | Handler | Output family | Parser |
|---|---|---|---|
| `test` | `make test` | Mixed Python, Ruby, Ruff, Git, and Make | `generic` |
| `test-prepare` | `make test-prepare` | Mixed static tooling | `generic` |
| `test-unit` | `make test-unit` | pytest | `pytest` |
| `test-int` | `make test-int` | Python unittest | `generic` |
| `test-e2e` | `make test-e2e` | pytest | `pytest` |

## E2E Environment

The production-equivalent artifact under test is the shipped `plugins/aquarium/skills/test-setup/scripts/inspect_testing.py` CLI. E2E invokes only its documented `--repository` public interface in a child process and treats its JSON and exit status as black-box output.

Each scenario creates one unique operating-system temporary directory containing only test-owned repository fixtures. It uses no credential, account, network, port, database, container, volume, provider, or production environment. `pytest` owns teardown through `tmp_path`; the test never deletes a path it did not create. A missing Python runtime, pytest dependency, script, or subprocess capability fails the gate rather than producing a successful skip.

## Language Diagnostics

- Ruff formatting and lint cover all maintained Python source and test files.
- Python bytecode compilation is implicit in every pytest and unittest import; syntax failures stop the applicable stage.
- Ruby syntax is checked explicitly before the architecture validator runs.
- Race, undefined-behavior, sanitizer, browser, device, and database diagnostics are not applicable because Aquarium ships declarative plugin assets and local Python/Ruby inspection utilities with no native, concurrent, browser, device, or database runtime.

## Legacy Waivers

### AQ-WAIVER-001

- Rule: `AQTEST-009`
- Scope: The pre-existing integration suites `tests/test_inspect_tools.py`, `tests/test_inspect_testing.py`, `tests/test_task_commit_gate.py`, and `tests/test_normalize_manifest.py` may retain `unittest`, including subsequent tests in those same established suites.
- Pre-existing implementation: Each suite existed before Aquarium's first repository self-enrollment proposal on 2026-08-22 and exercises temporary repositories, subprocesses, fixtures, and component boundaries through standard-library `unittest` assertions.
- Equivalence evidence: The suites fail through ordinary nonzero unittest exits, isolate state with per-test temporary directories, and cover positive, negative, malformed-input, timeout, and boundary scenarios without a separately managed service.
- Migration risk: A wholesale assertion and fixture rewrite would create broad test-only churn and could alter subprocess, cleanup, and temporary-repository semantics without increasing product coverage.
- Residual risk: The waived integration layer does not use pytest-native fixtures, assertions, markers, or diagnostics. New unit and E2E layers remain outside this waiver and use pytest.
- Approved by Master: 2026-08-22
- Last revalidated: 2026-08-22 after conservative inspector coverage for pre-normalization repository and skill-root ancestry, Gaori rule descendants, symlinked root test authorities, Make continuations and extended aliases, redirected and parameter-default test commands, control-safe Orca identities, terminal ack-only settlement, consent-bound outside-repository provider identity, verified local Orca routing, and the disclosed same-user CLI boundary was added; the complete local gate passed with the same isolated unittest suites and no new integration boundary.
- Revalidation triggers: Any related suite, runner command, framework major version, integration boundary, `requirements.txt`, `pyproject.toml`, or `aquarium-test-contract` version change. A stale waiver does not authorize execution or establish conformance.
