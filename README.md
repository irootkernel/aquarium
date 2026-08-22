# Aquarium

<picture><source media="(prefers-color-scheme: dark)" srcset="plugins/aquarium/assets/logo-black.png"><img alt="Aquarium" src="plugins/aquarium/assets/logo-white.png" width="240"></picture>

By [Root Kernel](https://home.rootkernel.xyz)

Aquarium is a Codex plugin marketplace for Ouroboros-assisted project and epic design, durable Design Gates, common test setup, evidence-gated roadmap delivery, release-candidate QA, optional Podway v2 execution memory, and safe development-tool setup.

Website: [home.rootkernel.xyz](https://home.rootkernel.xyz) · Support: [cs@rootkernel.xyz](mailto:cs@rootkernel.xyz)

## Skills

| Skill | Purpose | Invocation |
|---|---|---|
| `new-project` | Shape a greenfield PRD and initial roadmap with Ouroboros, without implementation. | Explicit: `$aquarium:new-project` |
| `new-feature` | Shape one feature epic and its Design Gate impact for an existing project. | Explicit: `$aquarium:new-feature` |
| `refactor` | Shape one refactor epic with compatibility, migration, rollback, and gate impact. | Explicit: `$aquarium:refactor` |
| `war-room` | Diagnose a difficult bug and propose a task, epic, or incomplete investigation without a fix. | Explicit: `$aquarium:war-room` |
| `design-qa` | Create or update durable local Design Gates after Ouroboros QA and exact-diff approval. | Explicit: `$aquarium:design-qa` |
| `epic-handler` | Orchestrate an epic through sequential task goals and a convergent epic-wide audit, with optional plan handoff. | Explicit: `$aquarium:epic-handler` with a roadmap path and one epic ID |
| `epic-validator` | Cold-validate a completed epic and converge confirmed gaps through remediation goals. | Explicit: `$aquarium:epic-validator` with a roadmap path and one epic ID |
| `task-handler` | Strengthen the procedure around one task goal through focused phase skills, verified transitions, and optional plan handoff. | Explicit: `$aquarium:task-handler` with a roadmap path and one task ID |
| `task-commit` | Reconcile roadmap ownership and lifecycle state, then create one authorized isolated commit. | Automatic for commit requests, or explicit: `$aquarium:task-commit` |
| `release-qa` | Exercise every active Design Gate and every release change through separate isolated QA matrices. | Explicit: `$aquarium:release-qa` with an intended version or version confirmation |
| `dev-setup` | Diagnose and configure selected development tools, including independent Ouroboros CLI, Codex, MCP, and runtime state. | Explicit: `$aquarium:dev-setup` |
| `dev-setup-bundle` | Apply development-tool setup to explicit Git repositories from one external YAML manifest. | Explicit: `$aquarium:dev-setup-bundle` with a manifest path |
| `test-setup` | Audit and configure the common Make or Bun testing contract and approved legacy waivers. | Explicit: `$aquarium:test-setup` for one repository |
| `independent-review` | Run a supervised read-only requirements and code review with a fresh Codex, then adjudicate its findings. | Explicit: `$aquarium:independent-review` with one epic or task ID |
| `orca-review` | Review one exact repository snapshot with a user-selected installed AI CLI through supervised Orca orchestration. | Explicit: `$aquarium:orca-review` with one exact review target |

Invoking `release-qa` authorizes read-only queries to the repository's configured Git remote and hosting Release metadata without another network prompt. Configured clients may use existing ambient authentication for private repositories, but the skill never reads, reports, persists, refreshes, or changes credentials, starts authentication, uploads source, or permits network access from QA scenarios.

`$aquarium:orca-review` requires the separately installed `$orca-cli` skill and a ready Orca runtime, then offers only locally detected Claude, Codex, Cursor, and Kimi CLIs. The final tool:model selection discloses the exact target and digest and authorizes transmission of only that review scope to the selected provider; the skill does not install tools, authenticate providers, modify the checkout, run tests, or switch providers after a failed launch.

### Common test setup

`$aquarium:test-setup` enrolls one repository in `aquarium-test-contract/v1` through a root `TESTING.md`, after an exact-diff approval. The contract exposes prepare, unit, integration, and E2E stages plus one serial fail-fast aggregate. Make owns orchestration for ordinary and polyglot roots; a TypeScript-only root uses pinned Bun scripts as the execution authority and retains matching Make adapters. Integration remains self-contained without a real database or external service, while E2E drives a production-equivalent artifact in a reproducible non-production environment and fails instead of silently skipping missing prerequisites.

New projects receive no waivers. Their default frameworks are Ginkgo v2 with Gomega for Go, pytest for Python, Vitest executed through Bun for TypeScript, Cargo test for Rust, `package:test` for Dart, `flutter_test` for Flutter, and Patrol for Flutter E2E. Web E2E uses Playwright; other black-box E2E is Python-preferred. A pre-existing project may retain an equivalent package manager, runner, framework, or supported diagnostic deviation only after Master approves the exact legacy evidence, residual risk, and revalidation triggers recorded in `TESTING.md`. Common entrypoints, serial order, unit and integration isolation, silent-skip prevention, and production safety cannot be waived. Applying files never authorizes a container, database, external sandbox, or paid E2E run; the skill discloses and asks separately before those effects.

Gaori integration is optional. When present, framework-specific parsers are assigned only to commands with one output format; mixed aggregates use `generic`, and the wrapped command's exit code remains the pass/fail authority.

### Ouroboros-assisted design and Design Gates

The five design workflows are explicit-only. `new-project` produces a PRD and initial roadmap; `new-feature` and `refactor` each produce one epic; `war-room` stops at diagnosis and a task, epic, or incomplete-investigation proposal; `design-qa` alone may create, change, reactivate, or retire Design Gates. They use installed upstream Ouroboros interview, PM, Seed, and QA capabilities as bounded leaf operations. They never invoke Ouroboros execution loops or let a provider write repository files directly, and every durable document change requires a displayed exact diff and separate approval.

The default current and retired registries are `docs/gating-rules.md` and `docs/gating-rules-retired.md`; repository authority may override the resolved pair. Active gates must be local and offline, with stable IDs, concise titles, invariants, positive and failure scenarios, objective pass conditions, revalidation triggers, sources, and owners. Retired gate bodies move to the resolved retired registry while the current registry retains tombstones. Every newly authored implementation task records `Design Gate impact` as `Not required`, `Pending`, or resolved `GATE-*` IDs; legacy tasks inherit their parent epic, while a missing effective marker blocks enrolled repositories. `Pending` blocks implementation. `release-qa` runs every active gate plus its commit-to-scenario delta matrix. A repository that never had a registry remains unenrolled and receives delta QA only, while deleting an established registry is a finding.

### Task-handler phases

`task-handler` loads these leaf skills in order. Their implicit invocation is disabled; invoke one directly only to resume that exact phase with its required task context.

| Phase skill | Responsibility |
|---|---|
| `task-plan` | Read authority and produce an approved decision-complete plan without mutation. |
| `task-implement` | Implement only the approved task scope. |
| `task-verify` | Map requirements to current agent-run or user-run verification evidence. |
| `task-refine` | Run deslop, establish the staged baseline, and perform bounded optimization. |
| `task-document` | Update durable documentation and move the roadmap task to its defined review state. |
| `task-review` | Run Mulgae against one exact complete task target and resolve valid findings. |
| `task-close` | Obtain final user approval, apply the user-selected terminal status, and hand an authorized commit to `task-commit`. |

The three goal-centered workflows have distinct entry points. `epic-handler` connects multiple task goals into one epic outcome while leaving each task's internal procedure flexible. Its member tasks stop after at most two Mulgae reviews and defer second-review findings to epic hardening; hardening performs at most three review-and-fix rounds plus one confirmation review before asking the user. `task-handler` strengthens the procedure around one task goal with explicit phases and user-visible transition gates, moving it to a defined `In Progress` state after plan approval when available; it uses the same three-round-plus-confirmation limit. Any clean review ends immediately. `epic-validator` starts from a committed completed epic, independently audits it, and resolves confirmed gaps through sequential remediation goals. None invokes another. Their actual commits share `task-commit`. Direct commit requests require explicit task relationship and lifecycle or checkpoint confirmation; handler commits carry the owner's approved lifecycle or record decision in a bounded handoff. Commit, upstream publication, and live validation remain separate states.

`task-handler` and `epic-handler` accept `mode=execute` by default, `mode=plan-only` for a non-mutating plan, `mode=plan-handoff` when another agent will continue, and `mode=resume` for the matching running session. An explicit handoff stores the approved Markdown once under `.podway/runtime/handoffs/<initial-session-id>/plan.md`, records only its local artifact metadata in Podway, and reports the exact session ID and continuation request. A plain request to plan only does not create that file or a session. The other Aquarium workflows do not expose these modes.

### Roadmap commit guard

Aquarium includes a local `PreToolUse` hook that detects direct shell `git commit` commands in repositories with tracked roadmap lifecycle files. Such commits must pass through `task-commit`; repositories without a detected roadmap are unaffected. The hook uses only the command, working directory, tracked roadmap paths, and local lifecycle text, and neither writes project state nor transmits data.

After installing or upgrading Aquarium, open `/hooks` and explicitly trust the plugin hook. Skill matching is best-effort, while the trusted hook supplies the deterministic direct-command guard. It is not complete enforcement: commits created indirectly by another tool may not pass through the shell boundary.

### Optional Podway integration

[Podway](https://github.com/irootkernel/podway) v0.2.5 through v0.2.x can provide durable Procedure v2 state for Aquarium workflows on native Apple Silicon macOS. Every Git-backed Aquarium owner selects Podway by default; `dev-setup` can separately install the matching optional `use-podway` user skill and five managed Procedures. The binary, skill, configuration, Procedures, daemon, and any existing session describe availability and readiness. Git-backed design workflows use `aquarium-design-v2`, `war-room` uses `aquarium-war-room-v2`, and the delivery workflows retain their task, goal, and validation Procedures. A non-Git `new-project` never initializes Git or Podway merely for workflow state. A new session starts as prepared, then its Aquarium owner re-observes it and uses `begin` to create attempt 1 and the initial goal.

The user may explicitly opt the current Git-backed workflow out before its first managed-session mutation; that choice never carries into later work. Otherwise the Aquarium owner checks readiness and discloses Podway operations and bounded Ouroboros calls in its execution envelope. Degraded readiness routes to `dev-setup` repair or workflow opt-out. A prepared, running, incomplete, or undisposed terminal nonmatching session is a lifecycle conflict: resume it through its matching owner, leave it untouched through opt-out, or explicitly invoke `use-podway` when cancellation or deletion is the actual intent. A disposed terminal session with verified handoff evidence and a current eligible replacement template is instead atomically replaced by the approved successor through `start --replace-eligible`; reset is not a prerequisite. Aquarium owners alone advance their workflows; upstream Ouroboros skills are Podway-blind leaves.

During an active session, a stop request requires an explicit disposition: leave the session active for later resumption, cancel the task while preserving history, or reset the session and delete its history. Cancellation is not a pause and cannot reactivate; reset requires a dry run and separate confirmation of the irreversible history loss. Continuing the remaining Aquarium work without Podway starts a new explicitly opted-out workflow rather than changing the active workflow in place.

At a successful terminal boundary, Aquarium records `handed_off` only when an exact authoritative external result such as the committed roadmap task is verified. An approved internal epic boundary with no external handoff may record `not_required` only when the same handler retains ownership and must replace the session. Otherwise Aquarium leaves the terminal session undisposed. It never chooses force reset or force replacement automatically.

## Install

Add the Git marketplace and install the plugin:

```bash
codex plugin marketplace add irootkernel/aquarium --ref main
codex plugin add aquarium@aquarium
```

Restart Codex after installation or upgrade so the active session reloads the installed skill snapshot, then open `/hooks` and trust Aquarium's roadmap commit guard.

Aquarium does not bundle third-party skill or documentation sources. Its workflows use separately installed upstream Lora, Ouroboros, and Cursor Team Kit Deslop capabilities; `$aquarium:dev-setup` diagnoses them and proposes exact-source installation or repair behind separate approvals. The upstream `$deslop` skill is a required prerequisite for task delivery.

### Migrating from Root Kernel

Aquarium v0.1.4 replaces the previous marketplace, plugin invocation prefix, inspection schema, and managed Podway Procedure IDs without compatibility aliases. Before upgrading, finish or explicitly dispose of any active `root-kernel-*` Podway session; Aquarium does not convert or delete its runtime history. Then remove the previous installation, add the renamed marketplace, install Aquarium, and restart Codex:

```bash
codex plugin remove root-kernel
codex plugin marketplace remove root-kernel-dev-skills
codex plugin marketplace add irootkernel/aquarium --ref main
codex plugin add aquarium@aquarium
```

Repositories configured for Podway must remove the tracked `.podway/procedures/root-kernel-{task,goal,validation}-v2.yaml` files and install the corresponding `aquarium-*` Procedures through a separately approved `$aquarium:dev-setup` migration. Do not replace managed Procedures while an old session is active.

## Development-tool ecosystem

`$aquarium:dev-setup-bundle` accepts one explicitly supplied external YAML manifest, validates every target before setup, prepares shared user-global components once, and applies the existing `dev-setup` approval boundaries to each ready Git repository. It never discovers repositories, persists the manifest as Aquarium state, stages, commits, or rolls back successful work automatically; a failed target does not prevent independent targets from continuing. See the [bundle manifest reference](plugins/aquarium/skills/dev-setup-bundle/references/manifest.md) for the complete schema.

Bundle normalization requires user-provided Python 3.10 or newer and PyYAML 6.x. Aquarium never installs or upgrades those runtime dependencies as a setup side effect; missing or unsupported PyYAML stops before network access or repository mutation.

```yaml
schema: aquarium.dev-setup-bundle/v1
defaults:
  tools: [mulgae, gaori, podway, ouroboros, lora, deslop]
  project_mcp: [mulgae, gaori]
  agents_guidance: skip
targets:
  - path: ../dolgorae/gaori
  - path: ../ember-quest/ember-quest
    include: [sanho]
    exclude: [ouroboros]
    project_mcp_exclude: [gaori]
```

`agents_guidance: propose` prepares a separately approved, evidence-based repository operating contract rather than a tool-reference fragment. The proposal keeps AGENTS.md canonical, includes a mandatory project-specific commit-message subsection, and reconciles root CLAUDE.md to a thin delegation file; unresolved commit conventions or conflicting existing guidance still require a per-repository user decision before the exact diff can be applied.

When `dev-setup` selects Sanho, Mulgae, Gaori, or Podway for setup or diagnosis, it automatically reads that tool's official GitHub release metadata and four public skill files to compare the latest supported stable skill with the exact `~/.agents/skills/use-*` target. Matching skills require no prompt; missing or different skills are installed or replaced only after an exact proposal and separate approval. Unselected tools and other network operations are not covered by this comparison authorization.

- [Sanho](https://github.com/irootkernel/sanho) synchronizes project documentation with its canonical documentation repository. Aquarium supports stable v0.2.7 through v0.2.x, including read-only push preview and canonical history inspection, and can separately install the matching optional `use-sanho` user skill for Git-boundary guidance.
- [Mulgae](https://github.com/irootkernel/mulgae) performs advisory multi-provider code review against an explicitly selected capture. Aquarium supports stable v0.1.17 through v0.1.x, including Config v3, Doctor v2 offline readiness, prose-first structured finding extraction, explicit Codex provider profiles, and event-driven MCP review lifecycle tools, can install the matching optional `use-mulgae` user skill, and can separately configure a repository-bound local MCP server.
- [Gaori](https://github.com/irootkernel/gaori) runs existing checks while preserving raw logs and producing bounded evidence. Aquarium supports stable v0.1.14 through v0.1.x, including read-only parser and completed-run discovery plus event-driven terminal MCP waits, can install the matching optional `use-gaori` user skill, and can separately configure a repository-bound local MCP server.
- [Lora](https://github.com/tmdgusya/lora) provides Lore skills for recording and querying decision context in Git trailers.
- [Cursor Team Kit](https://github.com/cursor/plugins/tree/main/cursor-team-kit) provides the separately installed upstream `deslop` skill required by Aquarium task refinement.
- [Podway](https://github.com/irootkernel/podway) guards Aquarium's default local Procedure v2 execution state, rework, recorded evidence, and goal assessment without running commands or judging evidence truth. Aquarium supports stable v0.2.5 through v0.2.x and can separately install the matching optional `use-podway` user skill.
- [Ouroboros](https://github.com/Q00/ouroboros) supplies bounded discovery, PM, Seed, and QA leaf capabilities to the five explicit design workflows. Aquarium supports `>=0.51.1,<0.52.0`; `dev-setup` keeps package installation, Codex refresh, and MCP/runtime setup behind separate approvals and never invokes a provider during setup.

## Thanks

Thanks to [Lora](https://github.com/tmdgusya/lora) for the Lore commit skills, [Ouroboros](https://github.com/Q00/ouroboros) for its discovery and specification capabilities, and [Cursor Team Kit](https://github.com/cursor/plugins/tree/main/cursor-team-kit) for the `deslop` skill. Aquarium uses these as separately installed upstream capabilities and does not vendor their skill or documentation sources. Ouroboros and Cursor Team Kit provide MIT LICENSE files; Lora declares MIT in its README.

## Validate

Install the exact development dependencies outside the test handlers, then run the repository-owned serial gate:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
make test
```

See [TESTING.md](TESTING.md) for the authoritative stage mapping, framework evidence, local black-box E2E environment, diagnostics, and approved legacy waiver. The aggregate checks plugin metadata, skill frontmatter and UI metadata, the roadmap commit hook, development and test setup safety invariants, third-party attribution, distribution files, managed Podway procedures and their rework routes, cross-file pinned wording, relative Markdown links, and the no-hard-wrap documentation convention.

## Documentation style

Do not hard-wrap prose in project documentation. Keep each prose paragraph on one source line; use line breaks only for structural Markdown, code, tables, lists, or other syntax where the break is meaningful.

## License

This repository is licensed under the [MIT License](LICENSE).
