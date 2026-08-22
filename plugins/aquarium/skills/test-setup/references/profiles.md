# Test Runner and Language Profiles

Read only the selected runner profile and the detected language sections. Preserve stricter repository-local checks.

## Make

For a non-TypeScript single-language root, the Makefile owns orchestration. Declare all five targets phony and use recursive calls in the aggregate recipe:

```make
.PHONY: test test-prepare test-unit test-int test-e2e

test:
	$(MAKE) test-prepare
	$(MAKE) test-unit
	$(MAKE) test-int
	$(MAKE) test-e2e
```

Do not express the four stages as prerequisites: `make -j` may run them concurrently. Assignments to `MAKEFLAGS`, `MFLAGS`, or `GNUMAKEFLAGS` and custom global shell semantics make fail-fast behavior unverifiable unless a future inspector proves them harmless. Additional logging is allowed, but additional test gates belong inside one of the four handlers rather than beside them in `test`.

## TypeScript and Bun

When TypeScript is the sole root product language, `package.json` owns orchestration and pins an exact Bun version through `packageManager`. Track `bun.lock`; `bun.lockb`, npm, pnpm, or Yarn requires a legacy waiver rather than silent acceptance.

The scripts are literal, one-way handlers:

```json
{
  "packageManager": "bun@1.3.14",
  "scripts": {
    "test": "bun run test:prepare && bun run test:unit && bun run test:int && bun run test:e2e",
    "test:prepare": "bun run format && bun run lint && bun run typecheck",
    "test:unit": "bun run vitest run tests/unit",
    "test:int": "bun run vitest run tests/integration",
    "test:e2e": "python3 -m pytest tests/e2e"
  }
}
```

These command bodies are examples except for the four script names and aggregate order. New TypeScript unit and integration layers use a project-pinned Vitest dependency executed through `bun run`; Bun remains the package manager and script orchestrator, and npm is not introduced. A pre-existing Bun test, Jest, or Node.js test layer requires an approved `AQTEST-009` waiver rather than introducing Vitest beside it. Do not install dependencies from a test handler.

The root Makefile is a compatibility adapter whose five targets call only `bun run test`, `bun run test:prepare`, `bun run test:unit`, `bun run test:int`, and `bun run test:e2e` respectively. A `$(BUN)` adapter is valid only when every static, exported, or overridden definition resolves to `bun`. Package scripts never call Make, including through `time`, `command`, `exec`, `env`, grouping, quoted shell text, or another shell wrapper, so `make test` and `bun run test` execute the same handlers exactly once. Always use `bun run test` for the package script; bare `bun test` invokes Bun's test runner instead.

For a browser or web-page product, Playwright in TypeScript is the preferred E2E implementation and needs no waiver. For a TypeScript CLI, service, library, or other non-web-page product, Python remains the preferred black-box E2E implementation and the Bun handler launches it. An existing equivalent runner in another language may remain only through an approved legacy waiver.

## Polyglot

When TypeScript shares the root product with Go, Rust, Python, Dart, or another implementation language, the root Makefile remains the aggregate authority and uses the Make profile. Each common Make stage may delegate the TypeScript portion to the matching Bun stage script, but the root aggregate still calls each common stage once. Do not add a second Bun aggregate beneath `make test` that repeats non-TypeScript stages.

## Go

New unit and integration layers use Ginkgo v2 with Gomega. Pin `github.com/onsi/ginkgo/v2` and `github.com/onsi/gomega` through `go.mod` and `go.sum`; do not add another assertion library without a concrete missing capability. Run suites through the Ginkgo CLI with race detection and without result caching wherever the platform and build mode support it. A pre-existing standard-library `testing`, Testify, or other runner may remain only through an approved `AQTEST-009` waiver, and subsequent tests in that existing layer follow the waived framework rather than mixing styles.

Run `gofmt` or the repository formatter in prepare, plus `go vet`, established lint, generation, module, and architecture checks. Process-level E2E need not use race instrumentation when it would instrument only the Python harness; concurrency-sensitive in-process suites retain it.

## Rust

Use Rust's built-in test harness through repository-pinned `cargo test` scopes. Use repository-pinned `cargo fmt`, `cargo check`, and `cargo clippy` in prepare. Miri, sanitizers, or Loom are required only when unsafe or concurrency risk makes them applicable and the project adopts or already configures them. Do not install nightly toolchains or new dependencies merely because they appear in this profile.

## Python

New unit, integration, and Python E2E layers use pytest and native pytest assertions. Separate unit and integration selection through directories, registered markers, or configuration without duplicating test collection. Use the established formatter, linter, and type checker in prepare. Enable strict configuration, marker, warning, async-leak, timeout, or parallel-order diagnostics when the repository risk warrants them. A pre-existing unittest, nose, or other runner requires an approved `AQTEST-009` waiver.

## Dart and Flutter

New Dart unit and integration layers use `package:test`. New Flutter unit, widget, and self-contained component layers use `flutter_test`; classify them as unit or integration according to their dependency boundary. Flutter E2E uses Patrol and an isolated test backend or test account. Non-Flutter Dart follows the ordinary Python-preferred black-box E2E policy. Use `dart format`, `dart analyze`, established generation, architecture, and Flutter lint checks in prepare.

## Gaori Parser Mapping

Gaori is an optional evidence-compression adapter, not a test gate. The wrapped command's exit code remains authoritative. When Gaori is already selected for a repository, verify installed labels with the read-only `gaori parsers list`; do not install, update, or execute a test merely to complete this mapping.

Map parsers by command output, not source language:

| Output | Parser |
|---|---|
| Mixed aggregate or prepare output | `generic` |
| Ginkgo v2, including Gomega matcher failures | `ginkgo` |
| pytest | `pytest` |
| Vitest | `vitest` |
| Cargo test | `cargo-test` |
| Flutter test | `flutter-test` |
| Playwright | `playwright` |
| Dart `package:test` | `generic` until an installed `dart-test` parser is verified |
| Patrol | `generic` until an installed `patrol` parser is verified |

A single Gaori command has one parser. Use `generic` when a stage mixes output formats, or add language-specific Gaori leaf commands that each call one existing handler without changing the five common entrypoints. Never select a specialized parser merely because its language matches: a specialized miss does not fall back to `generic`.
