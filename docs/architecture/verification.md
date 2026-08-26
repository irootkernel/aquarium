# Verification Architecture

Aquarium verification is local and layered. Each layer has a bounded claim, and a higher-level workflow must not present one layer as proof of another.

## Layers

| Layer | Main authority | Claim |
| --- | --- | --- |
| Static cross-contract validation | [`tests/validate.rb`](../../tests/validate.rb) | Required files, links, schema identifiers, Procedure declarations, and release invariants agree without pinning prose wording |
| Python unit tests | `tests/test_*.py` | Inspector, normalizer, observer, and helper logic behaves in isolated cases |
| Python E2E tests | `tests/e2e/` | Local scripts behave correctly against black-box repository fixtures |
| Approved legacy integration suites | `tests/integration/` | Executable inspection, commit-gate, and bundle-normalization boundaries remain compatible |
| Aggregate development gate | [`Makefile`](../../Makefile) | The enrolled preparation, unit, integration, and E2E stages pass for the candidate |
| Exact release gate | Repository release policy | Version metadata, release notes, candidate SHA, compatibility artifacts, and publication state satisfy the selected release mode |

[`TESTING.md`](../../TESTING.md) owns the meaning, environment, frameworks, diagnostic mapping, and waivers for these stages.

## Determinism and Effects

Structural inspectors are intentionally read-only, local, and conservative. They avoid project-code execution, credentials, ignored runtime evidence, and network access. A conforming result means the inspected structure satisfied the encoded rules; semantic review is still required.

Tests that start containers, contact providers, use credentials, publish data, or otherwise create external effects require the separate approval named by their workflow. Optional Gaori integration may compress evidence but does not replace the underlying test exit status or repository test authority.

## Candidate Identity

Verification attaches to exact content. A code or substantive documentation change after a release-QA confirmation creates a new candidate. Development checks can support contract readiness, but only the release workflow can establish distribution readiness through exact artifact and remote-state observation.

The repository does not use GitHub Actions as release authority. The selected local release gate and the ordered publication observations remain authoritative.
