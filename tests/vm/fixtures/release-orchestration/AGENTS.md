# Local release fixture

Use normally discovered installed Aquarium release skills. Release work uses
ordinary v3 reports and `procedure: null`; it has no synthetic roadmap Task.
Use native Executors and an independent report-only Evaluator. Only one
mutating Executor operates in this repository. The authorized fixture operator
reads each concrete proposal/result and supplies its actual decision.

## Project Configuration

Aquarium release notes: CHANGELOG.md

`manifest.json` owns the version. [Testing](TESTING.md) and [Make](Makefile)
own public checkpoints. Distributed surfaces are `greet.py` and `manifest.json`;
`support/` is non-distributed internal fixture support. Classification does not
establish QA neutrality for a path consumed by a scenario.

Release mode: @MODE@. Gate order: @GATE_ORDER@ (`before` means gate before
commit; `after` requires the exact clean release commit before its gate).
The sole metadata allowlist is the manifest version and open CHANGELOG heading's
publication date; settled entry text stays unchanged. Release subjects are
exactly `[REL] Release v<version>`, with ordinary Aquarium attribution trailers.
Use `task-commit` for actual authorized commits and retain post-hook identity.

Git origin is the owned local bare repository. Hosting is the disclosed
process-only stand-in for `fixture/release`. Before every native start/resume,
verify its exact owned executable identity. Never use production hosting,
credentials, global configuration or a fallback CLI. Scope and initial fixture
preparation do not grant unseen approvals, gate execution or publication.
