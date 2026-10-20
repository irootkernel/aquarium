# Aquarium

<img alt="Aquarium AI Fleet engineering ecosystem" src="plugins/aquarium/assets/hero.png" width="100%">

**Software engineering with AI Fleets, not vibe coding.**

English · [한국어](README.ko.md)

By [Root Kernel](https://rootkernel.xyz) · Support: [cs@rootkernel.xyz](mailto:cs@rootkernel.xyz)

Architected by Claude · Built by an AI Fleet

Aquarium is a plugin for engineering reliable software with AI Fleets, available for Codex, Claude Code, Grok, and ZCode (GLM). This repository holds Aquarium's single source and ships the Codex edition. Aquarium connects specialized agents, models, and development tools into workflows with three rules: every task has a tracked state, completion needs verified evidence, and consequential actions wait for your approval.

Aquarium is growing beyond vibe coding toward Agentic Engineering, Loop Engineering, Graph Engineering, and the practices that come next. These are not separate products or a rigid maturity model. They name a direction: AI work that is more specialized, more iterative, more connected, and more accountable.

## Aquarium Editions

The Claude Code, Grok, and ZCode editions are generated from this source and adapt packaging, skill invocation, setup, and review to their hosts.

- Aquarium (this repository) — Codex
- [Aquarium for Claude](https://github.com/irootkernel/aquarium-for-claude) — Claude Code
- [Aquarium for Grok](https://github.com/irootkernel/aquarium-for-grok) — Grok
- [Aquarium for GLM](https://github.com/irootkernel/aquarium-for-glm) — ZCode

## How Aquarium Is Built

Aquarium itself is built by an AI Fleet, with Claude as its architect. Claude sets the design that this source and every edition follow, and it develops Aquarium for Claude directly. Codex, Grok, and GLM implement that design.

## Why Aquarium

Even capable AI tools, used one at a time, leave the engineer to track context, approvals, task state, and evidence by hand. Aquarium connects them into one workflow and keeps these rules:

- **Work has identity.** A delivery task or epic lives in your roadmap with an ID and a lifecycle state. Commits go through `task-commit`, which records the lifecycle change you confirm instead of skipping it. Their trailers identify the responsible Aquarium skill, Epic, and Task, preserving the original skill when setup changes are committed later.
- **Delivery is phased and gated.** Task, Epic Goal, Validation, feature/project/refactor Design and Diagnosis select a Procedure that fits the actual work, reusing adequate definitions or preparing a qualified adaptation or composition. Applicable work, checks, independent assessments and selected reviews remain due. Nothing changes before you approve the plan. Every applicable roadmap requirement must map to current evidence. Closeout waits for your explicit approval. Adopted definitions stay local for recovery. After successful use, Aquarium can offer a useful whole Procedure or fragment for your library; its exact content needs your consent, application follows original finalization, and its commit needs separate authority. Declining keeps the completed work and local recovery material.
- **Evidence is verified.** A command's exit code decides pass or fail. Review findings stay advisory until Aquarium validates and reprioritizes them locally. Approved handlers fix and verify valid issues. Simple corrections with direct proof settle locally; changes requiring further independent judgment receive another review. Depending on scope, a Low issue is fixed locally, recorded as deferred feedback, or turned into a TODO candidate; once that finite set is settled and checked, its historical count does not trigger another review.
- **Evidence has a residence.** Ignored Mulgae, Gaori, Podway, and derived Sorage artifacts support the active workflow but never become roadmap history or durable repository authority. When downstream correctness truly requires retained evidence, Aquarium promotes only reviewed bounded artifacts into a tracked package outside canonical documentation.
- **Loops are bounded.** A clean review ends the loop at once. Review budgets are maxima rather than targets, eligible corrections settle locally, and changes requiring further independent judgment receive their authorized confirmation.
- **Invariants and tests are contracts.** Release QA re-runs repository-owned active Design Gates when they are enrolled. The test contract runs prepare, unit, integration, and E2E in order, fails on a missing prerequisite instead of skipping it, and gives a new project no waivers.
- **You keep authority.** Installing tools, sending source to a provider, staging, committing, pushing, and publishing each need their own approval. Design documents and setup files change only through an exact diff you approve. A local hook catches direct shell commits in roadmap repositories and points them to `task-commit`.
- **Work can pause, resume, and hand off.** `task-handler` and `epic-handler` support plan-only runs, explicit plan handoff to another agent, and resuming a matching session. A plan by itself creates no runtime state.

This source is written for Codex, and each edition adapts it to its host. Aquarium deliberately integrates a defined toolchain instead of abstracting over interchangeable tools. It owns the contracts among Codex, Dolgorae, Herdr, Podway, Sanho, Mulgae, Gaori, Sorage, Ouroboros, Lora, Deslop, Humanizer, and im-not-ai. Each contract says when a tool runs, what it may decide, and how its output becomes evidence for the next step.

## Install

```bash
codex plugin marketplace add irootkernel/aquarium --ref main
codex plugin add aquarium@root-kernel
```

Restart Codex after installing or upgrading, then open `/hooks` and explicitly trust Aquarium's roadmap commit guard. The hook catches direct shell commits. It is not complete enforcement: commits created indirectly by another tool may not pass through it.

Install or update the Aquarium plugin through Codex's plugin-management flow. A plugin-only request does not invoke `$aquarium:dev-setup-global` or start global tool diagnostics. Request global development tool setup separately when needed.

Aquarium does not vendor third-party skill or documentation sources. `$aquarium:dev-setup-global` checks and updates user-global tools from exact upstream sources, while `$aquarium:dev-setup` trusts canonical global skill presence and configures repository state plus AGENTS.md guidance. Project guidance can opt English documentation into a final Humanizer pass and Korean documentation into a final im-not-ai pass. The upstream `$deslop` skill is required when Task refinement is due, including canonical and direct phase execution.

Podway-backed adaptive helpers require an available supported Python environment with PyYAML and `jsonschema`. Choose an existing compatible interpreter; plugin installation and the helpers do not install these dependencies. This prerequisite does not apply to Podway opt-out or non-Git `new-project` paths. See [Podway setup](plugins/aquarium/references/tool-catalog.md#podway).

## Development Channel

`aquarium-dev` provides an explicit Apple Silicon macOS development channel for Aquarium maintainers. It enrolls one named canonical local-`main` checkout, builds immutable exact-commit artifacts below `~/.aquarium-dev/`, and atomically exposes foreground executables or producer-owned managed services through `~/.aquarium-dev/bin/`. Enrollment, hook changes, builds, managed-service activation, and launcher installation each retain a separate approval boundary.

Aquarium bundles the manager's MCP tools and CLI in the plugin. Ask for a development-channel diagnosis in chat, or run `aquarium-dev diagnose --repository <absolute-git-root>`. Use `$aquarium:dev-setup-global` when explicitly requesting initial installation or an update of the optional `aquarium-dev` runtime, then start a new Codex session. Plugin updates do not replace the installed runtime automatically. See the [development runbook](docs/ops/development-channel.md).

The user-local `aquarium-dev <tool> [args...]` launcher accepts only supported tools and prefers each available `~/.aquarium-dev/bin` generation. An absent foreground tool alone may fall back to the caller's global `PATH` outside both Aquarium roots. A managed service runs only when its producer controller reports the same active generation as ready or busy; pending, missing, mismatched, stopped, or recovering service state fails closed without production fallback. The Podway service enrollment applies to legacy development builds and does not support Podway >=v0.2.14, which uses a single Direct CLI. Sanho remains optional. EPIC-019 owns retirement of the legacy development channel. The manager does not change the caller's Codex home, authentication, plugin installation, or global MCP configuration. Development artifacts are local integration evidence only, not release or distribution proof.

## Main Workflows

1. **Shape** — `$aquarium:new-project` turns a goal into an approved PRD and a first roadmap. `$aquarium:new-feature` and `$aquarium:refactor` create or revise one epic. `$aquarium:war-room` diagnoses a hard bug and proposes the next work unit, confirms that no corrective work is needed, or reports an incomplete investigation. It does not implement the fix.
2. **Deliver** — `$aquarium:task-handler` runs one roadmap task through the stages above. With an approved execution envelope, `$aquarium:epic-handler` implements, verifies, reviews, and commits each Task through `$aquarium:task-commit`, then audits and corrects the whole epic. Task completion and internal validation proceed under your delegation. The handler asks for your overall acceptance after preparing final closeout.

3. **Validate** — `$aquarium:epic-validator` re-checks a completed epic from a clean start and fixes the gaps it confirms. Task, Epic and validation plans recommend Mulgae for small work, Subagent Review for medium work, and Herdr for large work, adjusted for difficulty and impact. The user selects the route or explicitly waives delegated review. Each route checks its own prerequisites and has no automatic fallback. `$aquarium:mulgae-review` provides one report-only review of an exact change or completion target. `$aquarium:herdr-review` uses a fresh explicitly requested main reviewer with multiple native subagents and conditional UI expertise in the current local Herdr session for staged, HEAD, commit or range targets. `$aquarium:subagent-review` uses three fresh base reviewers in the current harness, adding a UI/UX specialist for UI-related work, with one target and shared Review Brief, standalone or embedded. Aquarium adjudicates findings and keeps technical verdicts separate from completion assessment.
4. **Release** — `$aquarium:release-handler` settles cumulative notes, delegates exact-candidate scenarios to `$aquarium:release-qa`, runs the repository gate, publishes with separate approval, and opens the next planned version.

If an Epic needs a dossier before delivery, an executing `epic-handler` continues with `new-feature` in the same conversation for that Epic. The design still needs its own approvals and Podway session. Once its documents and any required commit are complete, start `epic-handler` in a new conversation using the updated roadmap.

Foundations: `$aquarium:docs-setup` governs canonical documentation structure, roadmap IDs, and explicitly adopted directory `AGENTS.md` guides. `$aquarium:test-setup` enrolls a repository in the common test contract. `$aquarium:dev-setup-global` maintains user-global tools; `$aquarium:dev-setup` automatically diagnoses repository configuration and agent guidance, proposing changes only when needed. `$aquarium:dev-setup-bundle` delegates those two scopes across several repositories from one v2 manifest with per-target MCP scope, Sorage Project slug, and Mulgae artist intent.

`$aquarium:status` reports the local production setup ledger, including stored
Go, Rust, Python, TypeScript, and Dart version declarations for each recorded
repository. Setup records those declarations automatically; an explicit
`aquarium-status refresh-languages` updates existing rows. Reporting does not
rerun setup or check installed toolchains. Optional release refresh is explicit,
and forgetting one recorded checkout requires approval bound to its current
revision and digest. Global setup diagnoses the managed `aquarium-status`
runtime; a plugin update alone does not replace it.

## How the Ecosystem Connects

- [Podway](https://github.com/irootkernel/podway) provides local execution memory for the goals, transitions, and handoffs of Git-backed workflows. It is selected by default for `task-handler`, `epic-handler`, `epic-validator`, `new-project`, `new-feature`, `refactor`, and `war-room`, and may be opted out before the first managed-session mutation. Aquarium runs the workflow and Podway records it; detailed lifecycle operations belong to the owning workflow or the standalone `use-podway` skill.
- [Gaori](https://github.com/irootkernel/gaori) runs your existing checks, keeps the raw logs, and returns a bounded summary as evidence. Gaori integration is optional, and the command's exit code stays the pass/fail authority.
- [Mulgae](https://github.com/irootkernel/mulgae) v0.1.25 or newer gives completed tasks and epics, plus explicitly requested standalone targets, an advisory multi-provider review of the original workspace, index or resolved Git objects through native read-only restrictions. Providers run from a neutral reviewer home. Mulgae retains reports and selected evidence under `.mulgae/`, without a full-source snapshot or replay archive. Callers keep workspace/index unchanged through completion; the native source identity describes selection metadata. Aquarium supplies the purpose and Review Brief, then verifies and reprioritizes findings without rewriting native lifecycle state. Config v5 requires deliberate migration, and `.mulgaeignore` no longer excludes files.
- [Sorage](https://github.com/irootkernel/sorage) brokers local document handoffs and Project Memos. Aquarium supports stable v0.1.x releases starting at v0.1.2 on Apple Silicon, with a matching `use-sorage` skill. It can diagnose and install the CLI, initialize the local installation, and register a Git repository after separate approval. The paired skill owns explicit Handoff and Memo operations, including uncertain-write recovery; Memo text does not authorize its own execution.
- [Dolgorae](https://github.com/irootkernel/dolgorae) remains an optional global tool for explicitly requested native operations such as Profiles and reusable External Specialist Engagements. Aquarium can diagnose compatible local v0.1.x Apple Silicon installations starting at v0.1.2 and install checksum-verified official stable releases in that range, while Aquarium Subagent Review uses host-native Codex subagents and does not discover, set up, or invoke Dolgorae.
- [Herdr Review](plugins/aquarium/skills/herdr-review/SKILL.md) uses the separately installed upstream Herdr skill to supervise a fresh requested reviewer in the current local session. It supports staged, HEAD, commit and range targets; workspace and dirty are unsupported. The reviewer reads the live index or resolved Git objects, preserves source and Git state, and returns a complete purpose-specific report. Admission requires reviewer identity and submission/activity correlation; idle or done alone is insufficient. Native output recovery keeps the same reviewer, and only the pane created for a successfully admitted review may be closed. Permitted external or Git-ignored review output remains a review aid. Herdr Review uses no Orca or Dolgorae operation and claims no immutable capture or backend CI. Native and manual migration qualification requires observed evidence separate from structural checks.
- [Sanho](https://github.com/irootkernel/sanho) syncs project documentation to its canonical documentation repository once Aquarium has settled what is ready to hand off.
- [Lora](https://github.com/tmdgusya/lora) keeps decision context in Git trailers, and [Cursor Team Kit](https://github.com/cursor/plugins/tree/main/cursor-team-kit) supplies the upstream `deslop` cleanup skill used during task refinement.
- [Humanizer](https://github.com/blader/humanizer) provides the final prose pass for English documentation, while [im-not-ai](https://github.com/epoko77-ai/im-not-ai) provides the corresponding Korean pass. Projects opt into either rule independently through `dev-setup` guidance.
- [Ouroboros](https://github.com/Q00/ouroboros) contributes discovery, PM, Seed, and QA inside explicitly requested design workflows and the bounded `epic-handler` to `new-feature` design route. Aquarium keeps document application, approval, and repository authority.

Together they form one governed path from scoping to documentation sync, so one tool's success is never mistaken for project completion.

Runtime evidence under `.mulgae/**`, `.gaori/runs/**`, `.podway/runtime/**`, derived `.sorage/**`, and disposable roots is local and expected to expire. Aquarium does not cite those paths or identities as evidence in tracked roadmaps, repository handoffs, or commit messages. A necessary durable exception uses only reviewed bounded non-sensitive structured evidence copied into a versioned promoted-evidence package under the repository's evidence root, `evidence/aquarium/` by default. New Mulgae live results use `aquarium.promoted-evidence/v2`, which preserves native source identity and consistency without claiming a content snapshot; historical v1 packages remain unchanged.

## Operating Boundaries

- Invoking a workflow grants only the effects its skill documents. Installation, authentication, source transmission, tests, staging, commits, pushes, publication, and destructive lifecycle actions each need separate authority.
- Invoking `release-handler` authorizes read-only release discovery and orchestration only; commits, pushes, tags, hosted Releases, destructive replacement, and the post-release next-cycle commit remain separate approvals. Its delegated `release-qa` pass may use existing ambient authentication for private repositories, remediate verified findings locally once, and never upload source or handle credentials.
- Explicitly invoking `dev-setup-global` selects all supported global components; scoped continuations select only named components. It authorizes disclosed official release, tag, and commit metadata reads. Dolgorae, Sanho, Mulgae, Gaori, Sorage, and Podway also compare complete commit-pinned paired-skill trees in ephemeral storage. Selected Lora or Deslop includes official npm metadata for the pinned installer. Downloads for installation, mutations, and provider calls remain separately controlled.
- Aquarium creates no central project-state file. [PRIVACY.md](PRIVACY.md) and [TERMS.md](TERMS.md) hold the complete data and authority contracts.

## References

- [Herdr migration](docs/ops/herdr-migration.md) explains selected-route readiness, preserved legacy review state and separately approved repository updates. Updating Procedure sources affects successors and preserves active snapshots; Herdr is not required for peer routes.
- [Canonical documentation](docs/README.md) maps the repository's specifications, architecture, decisions, implementation guidance, operations runbooks, roadmap, TODO candidates, and deferred feedback.
- [TESTING.md](TESTING.md) defines this repository's test authority and the `aquarium-test-contract/v1` evidence mapping.
- [CHANGELOG.md](CHANGELOG.md) records concise release outcomes and the planned next stable version.
- [Documentation governance](plugins/aquarium/references/documentation-governance.md) defines Aquarium's documentation roles, profiles, and default roadmap identity.
- [Bundle manifest reference](plugins/aquarium/skills/dev-setup-bundle/references/manifest.md) defines the manifest for setting up several repositories at once.
- Each skill's `SKILL.md` is authoritative for its triggers, effects, approval boundaries, and failure behavior.

## Validate

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
make test
```

The gate needs Python 3.11 or newer, Ruby 3.3 or newer, and dependency versions at or above the minimums in `requirements.txt`. Ruff may be installed separately. This repository is licensed under the [MIT License](LICENSE).

## Upgrading

- From the old `aquarium` marketplace identity: run `codex plugin remove aquarium@aquarium` and `codex plugin marketplace remove aquarium`, then use the install commands above.
- From the legacy Root Kernel plugin: finish or dispose of any active legacy Podway session, run `codex plugin remove root-kernel@root-kernel-dev-skills` and `codex plugin marketplace remove root-kernel-dev-skills`, install Aquarium, then let `$aquarium:dev-setup` migrate the managed Procedures.

## Thanks

Thanks to Lora, Ouroboros, Cursor Team Kit, Humanizer, and im-not-ai for the upstream skills Aquarium builds on. Aquarium does not vendor their skill or documentation sources. Each project retains its own license terms.
