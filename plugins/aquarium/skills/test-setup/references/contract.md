# Aquarium Test Contract v1

`TESTING.md` enrolls a repository in `aquarium-test-contract/v1`. The executable handler remains authoritative; disagreement between the document and the Makefile or package scripts is a blocking contract defect.

## Setup Prerequisites

`new-project` schedules the testing-foundation work unit after the implementation that provides all of the following. `test-setup` checks that they exist before proposing configuration:

- Product source in the chosen implementation language, with an established toolchain recorded in build or dependency configuration.
- Repository-supported commands that build, run, or test the actual implementation. These may use the language's native tools or the repository's existing package manager. A Make or Bun root authority, the five common test entrypoints, and a complete test suite need not exist yet; creating or adapting them is setup work.
- Minimum executable product behavior exposed through a public interface, with a defined observable result that meaningful tests can exercise. Inspect the implementation and its public usage evidence; manifests, empty commands, and planning documents alone do not prove this condition.

If any prerequisite is missing or cannot be verified, `test-setup` reports the gap and the implementation or evidence needed before another explicit invocation. It stops without proposing or creating handlers, tests, environment configuration, or `TESTING.md`. Do not implement a placeholder product to satisfy setup, create passing no-op tests, or substitute a documentation-only facade. Unimplemented product behavior cannot justify `not applicable` or a legacy waiver.

Once the prerequisites are present, missing test coverage and root orchestration belong in the normal setup proposal. An existing npm, pnpm, or Yarn project proceeds to the audit and `AQTEST-008` waiver decision; its package manager alone does not trigger the prerequisite stop or grant a waiver. Structural inspection remains conservative evidence only; it does not evaluate whether the product behavior is meaningful or testable, and it does not authorize executing the product.

### Manual Cross-Skill Scenarios

Master verifies these scenarios through the actual skills. These are expected outcomes, not recorded test results; structural validation does not prove them.

| Scenario | Expected `new-project` roadmap | Expected `test-setup` behavior |
| --- | --- | --- |
| The repository contains only planning documents. | Place the testing-foundation work after tasks that supply the prerequisites, never ahead of the implementation. | Report missing prerequisites and re-entry conditions without proposing or writing setup files. Adding only a manifest or empty handler must not change the decision. |
| `EPIC-001` delivers a testable walking skeleton. | Make testing-foundation its final task, dependent on the skeleton implementation; subsequent feature expansion depends on setup. | Stop before the prerequisites exist. Once they exist, propose meaningful tests and common entrypoints even if the full test contract is absent. |
| The earliest testable vertical slice arrives after `EPIC-001`. | Place testing-foundation immediately after that slice and before broader feature expansion, with explicit dependencies. | Stop while only planning or incomplete scaffolding exists; proceed with the normal proposal after the slice supplies all prerequisites. |
| A ready product has source, toolchain, native build or run commands, and defined public behavior, but no root Makefile or test suite. | For a new project, keep setup after the task that provides that behavior. An existing project's standalone setup needs no new roadmap. | Read the relevant product source and public-interface definitions under the same symlink, sensitive-file, and output-redaction rules. Propose the missing root authority and meaningful tests without executing the product during prerequisite inspection. |
| An existing TypeScript product has executable behavior and npm, pnpm, or Yarn commands. | Not applicable to greenfield roadmap creation. | Proceed to the contract audit and the explicit `AQTEST-008` waiver decision. Do not stop merely because Make or Bun orchestration is absent, and do not retain the package manager without the required waiver approval. |

In the ready scenarios, verify that `test-setup` still requires approval of the exact proposed diff and preserves its separate authorization boundary for effectful E2E execution. The prerequisite implementation retains its own verification; the later setup work does not excuse untested product changes.

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

Additional named gates remain valid, but the aggregate must place them inside the closest common stage. Check the required entrypoints, execution order, failure propagation, framework evidence, and file-access boundaries. Equivalent whitespace, quoting, comments, and line continuations do not change conformance. Unrelated variables and targets do not invalidate known stage behavior.

The inspector reads a static subset of Make and shell syntax without executing project code. Assess aggregate execution separately from each stage's output. When a conditional recipe, target-specific variable, unresolved include, dynamic rule, shell setting, or expansion prevents a relevant conclusion, report that conclusion as unverifiable. Do not infer execution from help, version, collection-only, or other information-only commands. Static pytest `addopts` and `PYTEST_ADDOPTS` settings must not force or conceal those modes. Background execution, ignored failures, and reverse Make/Bun edges violate the corresponding execution requirement; unknown wrappers and Make-valued shell aliases need inspection before conformance can be established.

Reject symlinked roots, ancestors, and authority files before reading them, including lexical path components preceding `..`. Preserve sensitive-file exclusions and redacted output. A target that has no applicable subject may succeed with a clear message only when `TESTING.md` gives objective evidence for `not applicable`; it must not hide missing coverage.

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

Use `Contract: aquarium-test-contract/v1` and `Profile: <selected-profile>` in the Contract section for unambiguous machine-readable enrollment. Existing enrollment prose remains supported. Inline Markdown, heading capitalization, and closing heading markers do not change these declarations. Comments and fenced examples do not enroll the repository. The inspector checks section presence and declarations; human review checks the prose's meaning.

Each waiver entry records a unique local waiver ID, `AQTEST-*` rule, exact scope, pre-existing implementation, equivalence evidence, migration risk, residual risk, explicit `Approved by Master` status, and revalidation triggers. Approval timing and execution evidence belong in Git history or the owning workflow report, not in this authority document. An `AQTEST-009` waiver may cover subsequent tests in the same pre-existing layer so the project does not accumulate competing frameworks, but it does not cover a newly introduced layer. A waiver becomes stale only when a change affects a fact supporting that waiver: stage mapping or runner command, framework or major version, waiver scope, layer identity, integration boundary, isolation or failure semantics, execution-affecting CI, environment, or dependency authority, contract version, or the recorded evidence itself. Adding or changing test cases inside the same waived layer does not by itself stale the waiver while those supporting facts remain unchanged. Stale waivers do not authorize a skip or establish conformance.
