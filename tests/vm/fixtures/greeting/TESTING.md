# Testing

## Contract

- Contract: `aquarium-test-contract/v1`
- Profile: `make`

## Canonical Commands

Use `make test` for the complete serial gate, or `make test-prepare`,
`make test-unit`, `make test-int` and `make test-e2e` for its stages.

## Stage Mapping

| Stage | Checks |
| --- | --- |
| test-prepare | Format and lint maintained Python with Ruff, then parse the application. |
| test-unit | Run native pytest greeting-function tests. |
| test-int | Run native pytest CLI subprocess tests. |
| test-e2e | Invoke the CLI help interface through native pytest. |

## Test Frameworks

Python unit, integration and E2E tests use pytest. `requirements.txt` declares
pytest and Ruff; install them before the gate. Make uses `.venv/bin/python` when
available and otherwise `python3`, disables user pytest plugins and options,
and disables inherited pagers. Dependency installation is outside test targets.

## Gaori Mapping

No Gaori commands are configured. The Make commands are authoritative.

## E2E Environment

The production artifact is `greet.py`. Tests invoke it locally through the
selected Python interpreter, without services, credentials or external resources.

## Language Diagnostics

Ruff, Python source parsing and pytest import failures stop their stage. The aggregate
stops on its first failure and preserves prepare, unit, integration and E2E order.

## Legacy Waivers

None.
