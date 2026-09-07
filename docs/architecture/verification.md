# Verification Architecture

Aquarium verification is local and layered. Each layer has a bounded claim, and a higher-level workflow must not present one layer as proof of another.

## Layers

| Layer | Main authority | Claim |
| --- | --- | --- |
| Package structure validation | [`tests/validate.rb`](../../tests/validate.rb) | Package metadata and data parse, local references resolve, basic Procedure structure is valid, and release versions agree |
| Python unit tests | `tests/test_*.py` | Inspector, normalizer, observer, and helper logic behaves in isolated cases |
| Python E2E tests | `tests/e2e/` | Local scripts behave correctly against black-box repository fixtures |
| Approved legacy integration suites | [`tests/test_inspect_tools.py`](../../tests/test_inspect_tools.py), [`tests/test_task_commit_gate.py`](../../tests/test_task_commit_gate.py), [`tests/test_normalize_manifest.py`](../../tests/test_normalize_manifest.py) | Executable inspection, commit-gate, and bundle-normalization boundaries remain compatible |
| Aggregate development gate | [`Makefile`](../../Makefile) | The enrolled preparation, unit, integration, and E2E stages pass for the candidate |
| Exact release gate | Repository release policy | Version metadata, release notes, candidate SHA, compatibility artifacts, and publication state satisfy the selected release mode |

[`TESTING.md`](../../TESTING.md) owns the meaning, environment, frameworks, diagnostic mapping, and waivers for these stages.

Ruby and Python checks cover package structure and executable helper behavior. Master separately verifies skill behavior after skill updates; the automated gate does not evaluate skill prose or run LLM evaluations.

## Determinism and Effects

Structural inspectors are intentionally read-only, local, and conservative. They avoid project-code execution, credentials, ignored runtime evidence, and network access. A conforming result means the inspected structure satisfied the encoded rules; semantic review is still required.

Tests that start containers, contact providers, use credentials, publish data, or otherwise create external effects require the separate approval named by their workflow. Optional Gaori integration may compress evidence but does not replace the underlying test exit status or repository test authority.

## Candidate Identity

Verification attaches to exact content. A code or substantive documentation change after a release-QA confirmation creates a new candidate. Development checks can support contract readiness, but only the release workflow can establish distribution readiness through exact artifact and remote-state observation.

Release-QA confirmation has a machine-validated evidence lifecycle. A full pass atomically freezes its exact matrix before remediation; preparation binds the frozen inventory to the Git-derived remediation range and changed surfaces; admission uses an exclusive claim keyed by the frozen-record digest; and completion requires one fresh result for every retained scenario. Prose summaries and reconstructed manifests cannot authorize confirmation.

The repository does not use GitHub Actions as release authority. The selected local release gate and the ordered publication observations remain authoritative.
