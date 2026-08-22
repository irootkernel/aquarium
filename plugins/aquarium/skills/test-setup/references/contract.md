# Aquarium Test Contract v1

`TESTING.md` enrolls a repository in `aquarium-test-contract/v1`. The executable handler remains authoritative; disagreement between the document and the Makefile or package scripts is a blocking contract defect.

## Rules

| ID | Requirement | Waiver |
|---|---|---|
| `AQTEST-001` | The root exposes `test`, prepare, unit, integration, and E2E entrypoints through its selected profile. | Never |
| `AQTEST-002` | The aggregate runs prepare, unit, integration, and E2E once, in that order, stops on the first failure, and remains serial under parallel Make. | Never |
| `AQTEST-003` | Prepare applies meaning-preserving formatting before deterministic static, type, vet, architecture, build, and established generation checks. It uses no database, container, or external service. | Legacy equivalent only |
| `AQTEST-004` | Unit tests isolate one logical unit and use no separately managed external resource. | Never |
| `AQTEST-005` | Integration tests exercise internal package or component cooperation with mocks, fakes, stubs, fixtures, temporary files, local subprocesses, or loopback fakes, but no real database, container, live provider, or separately managed service. | Never |
| `AQTEST-006` | E2E tests treat the built product as a black box, reproduce a non-production environment, fail on missing prerequisites, and clean up only resources they created. | Never for black-box scope, silent skips, or production safety |
| `AQTEST-007` | The project uses applicable language-native race, concurrency, undefined-behavior, type, and runtime diagnostics. | Legacy equivalent or unsupported platform only |
| `AQTEST-008` | The repository uses the selected Make or TypeScript/Bun runner profile and the profile's preferred E2E implementation. | Legacy equivalent only |
| `AQTEST-009` | New projects and newly established test layers use the canonical framework for each implementation language and product surface. | Pre-existing equivalent framework only |

Additional named gates remain valid, but the aggregate must place them inside the closest common stage. Symlinked repository roots, root authorities, every lexical component before normalization including components preceding `..`, Make control flags or recipe line continuations that can alter parsing or error handling, background commands, opaque or overridden runner variables, reverse runner edges hidden behind quoted shell wrappers, quote or backslash token joining, redirects, parameter defaults, or Make-valued shell aliases, and help, version, collection-only, fixture-listing, marker-listing, cache-display, setup-plan, setup-only, or other list-only commands even when adjacent to shell operators cannot prove this contract and must fail closed. Static pytest `addopts` and `PYTEST_ADDOPTS` settings, including quoted, quote-joined, multiline-array, and additive forms, that force one of those control-only modes invalidate otherwise executable pytest stage commands. A target that has no applicable subject may succeed with a clear message only when `TESTING.md` gives objective evidence for `not applicable`; it must not hide missing coverage.

## Stage Semantics

`prepare` runs first and may rewrite source only through deterministic, meaning-preserving formatters or established generation. Its output is the candidate exercised by every later stage. Dependency installation, database preparation, live discovery, and service startup are outside this stage.

`unit` tests one logical unit in isolation. Repository-local temporary files or in-process fakes are acceptable when they are part of the unit's interface, but shared state, externally started services, and order-dependent fixtures are not.

`integration` joins internal packages or components and may launch a locally built child process or loopback fake. It must remain self-contained and reproducible without Docker, a real database, cloud service, provider, or separately maintained environment.

`e2e` builds or selects the production-equivalent artifact, then interacts only through documented public interfaces. A test-only hook may prepare, reset, or observe test state only when production cannot enable it; the scenario assertion must still cross the public product boundary.

## E2E Environment Safety

Every E2E runner must establish an environment identity before mutation. It uses a dedicated test account, tenant, database, namespace, Compose project, port, and volume as applicable. It refuses production-looking or unverified targets, records health and readiness, applies migrations and deterministic seeds, captures bounded evidence, and tears down only the exact resources it created.

A Docker-backed environment uses a test-owned Compose definition or an equivalently isolated test profile. Names must be unique per run or deliberately serialized, credentials must be test-only and absent from Git, and cleanup must not use broad unresolved variables or shared production volumes.

The complete gate never treats unavailable credentials, devices, ports, databases, browsers, or external sandboxes as success. It fails with the exact missing prerequisite. Running an effectful E2E remains a separate authorization boundary from writing its configuration.

## TESTING.md Authority

Create one root `TESTING.md` in English with these sections:

- `Contract`: `aquarium-test-contract/v1`, enrollment status, and the selected `make`, `typescript-bun`, or `polyglot-make` profile.
- `Canonical Commands`: the aggregate and four stage entrypoints, including both Bun and Make forms when applicable.
- `Stage Mapping`: the concrete checks and suites owned by each stage, including justified `not applicable` cases.
- `Test Frameworks`: each language and layer, its canonical or approved legacy framework, manifest and lockfile evidence, exact runner command, and any local waiver ID.
- `Gaori Mapping`: when Gaori is present, each Gaori command, the one output format it produces, and its explicit parser label. Record `generic` for mixed or unsupported output rather than claiming specialized extraction.
- `E2E Environment`: artifact, public interfaces, identity checks, setup, health, seed, evidence, teardown, credentials by variable name only, and production refusal behavior.
- `Language Diagnostics`: applicable native diagnostics and explicit unsupported cases.
- `Legacy Waivers`: either `None` or one entry per approved waiver.

Each waiver entry records a unique local waiver ID, `AQTEST-*` rule, exact scope, pre-existing implementation, equivalence evidence, migration risk, residual risk, `Approved by Master` with the approval date, and revalidation triggers. An `AQTEST-009` waiver may cover subsequent tests in the same pre-existing layer so the project does not accumulate competing frameworks, but it does not cover a newly introduced layer. A waiver becomes stale after a related Makefile, package script, lockfile, runner, framework major version, suite, CI, environment, or contract-version change, or when its evidence fails. Stale waivers do not authorize a skip or establish conformance.
