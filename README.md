# Aquarium

<img alt="Aquarium AI Fleet engineering ecosystem" src="plugins/aquarium/assets/hero.png" width="100%">

**Software engineering with AI Fleets, not vibe coding.**

English · [한국어](README.ko.md)

By [Root Kernel](https://home.rootkernel.xyz) · Support: [cs@rootkernel.xyz](mailto:cs@rootkernel.xyz)

Aquarium is a Codex plugin for engineering reliable software with AI Fleets. It connects specialized agents, models, and development tools into workflows with three rules: every task has a tracked state, completion needs verified evidence, and consequential actions wait for your approval.

Aquarium is growing beyond vibe coding toward Agentic Engineering, Loop Engineering, Graph Engineering, and the practices that come next. These are not separate products or a rigid maturity model. They name a direction: AI work that is more specialized, more iterative, more connected, and more accountable.

## Aquarium Editions

- [Aquarium for Claude](https://github.com/irootkernel/aquarium-for-claude)
- [Aquarium for Grok](https://github.com/irootkernel/aquarium-for-grok)
- [Aquarium for GLM](https://github.com/irootkernel/aquarium-for-glm)

## Why Aquarium

Even capable AI tools, used one at a time, leave the engineer to track context, approvals, task state, and evidence by hand. Aquarium connects them into one workflow and keeps these rules:

- **Work has identity.** A delivery task or epic lives in your roadmap with an ID and a lifecycle state. Commits go through `task-commit`, which records the lifecycle change you confirm instead of skipping it.
- **Delivery is phased and gated.** `task-handler` moves one task through seven stages, from plan to close. Nothing changes before you approve the plan. Every applicable roadmap requirement must map to current evidence. Closeout waits for your explicit approval.
- **Evidence is verified.** A command's exit code decides pass or fail. Review findings stay advisory until Aquarium validates and reprioritizes them locally. Approved handlers fix and re-review valid Medium-or-higher issues. Depending on scope, a Low issue is fixed locally, recorded as deferred feedback, or turned into a TODO candidate; once that finite set is settled and checked, its historical count does not trigger another review.
- **Evidence has a residence.** Ignored Mulgae, Gaori, Podway, and derived Sorage artifacts support the active workflow but never become roadmap history or durable repository authority. When downstream correctness truly requires retained evidence, Aquarium promotes only reviewed bounded artifacts into a tracked package outside canonical documentation.
- **Loops are bounded.** A clean review ends the loop at once. Review budgets are maxima rather than targets, Low-only results settle locally, and required confirmation after a Medium-or-higher correction is never skipped.
- **Invariants and tests are contracts.** Release QA re-runs repository-owned active Design Gates when they are enrolled. The test contract runs prepare, unit, integration, and E2E in order, fails on a missing prerequisite instead of skipping it, and gives a new project no waivers.
- **You keep authority.** Installing tools, sending source to a provider, staging, committing, pushing, and publishing each need their own approval. Design documents and setup files change only through an exact diff you approve. A local hook catches direct shell commits in roadmap repositories and points them to `task-commit`.
- **Work can pause, resume, and hand off.** `task-handler` and `epic-handler` support plan-only runs, explicit plan handoff to another agent, and resuming a matching session. A plan by itself creates no runtime state.

Codex is Aquarium's primary agent runtime, and Aquarium deliberately integrates a defined toolchain rather than promising provider or framework neutrality. It owns the contracts among Codex, Dolgorae, Orca, Podway, Sanho, Mulgae, Gaori, Sorage, Ouroboros, Lora, Deslop, Humanizer, and im-not-ai. Each contract says when a tool runs, what it may decide, and how its output becomes evidence for the next step.

## Install

```bash
codex plugin marketplace add irootkernel/aquarium --ref main
codex plugin add aquarium@root-kernel
```

Restart Codex after installing or upgrading, then open `/hooks` and explicitly trust Aquarium's roadmap commit guard. The hook catches direct shell commits. It is not complete enforcement: commits created indirectly by another tool may not pass through it.

Install or update the Aquarium plugin through Codex's plugin-management flow. A plugin-only request does not invoke `$aquarium:dev-setup-global` or start global tool diagnostics. Request global development tool setup separately when needed.

Aquarium does not vendor third-party skill or documentation sources. `$aquarium:dev-setup-global` checks and updates user-global tools from exact upstream sources, while `$aquarium:dev-setup` trusts canonical global skill presence and configures repository state plus AGENTS.md and CLAUDE.md. Project guidance can opt English documentation into a final Humanizer pass and Korean documentation into a final im-not-ai pass. The upstream `$deslop` skill is a required prerequisite for task delivery.

## Development Channel

`aquarium-dev` provides an explicit Apple Silicon macOS development channel for Aquarium maintainers. It enrolls one named canonical local-`main` checkout, builds immutable exact-commit artifacts below `~/.aquarium-dev/`, and atomically exposes foreground executables or producer-owned managed services through `~/.aquarium-dev/bin/`. Enrollment, hook changes, builds, managed-service activation, and launcher installation each retain a separate approval boundary.

Aquarium bundles the manager's MCP tools and CLI in the plugin. Ask for a development-channel diagnosis in chat, or run `aquarium-dev diagnose --repository <absolute-git-root>`. Use `$aquarium:dev-setup-global` when explicitly requesting initial installation or an update of the optional `aquarium-dev` runtime, then start a new Codex session. Plugin updates do not replace the installed runtime automatically. See the [development runbook](docs/ops/development-channel.md).

The user-local `aquarium-dev <tool> [args...]` launcher accepts only supported tools and prefers each available `~/.aquarium-dev/bin` generation. An absent foreground tool alone may fall back to the caller's global `PATH` outside both Aquarium roots. A managed service runs only when its producer controller reports the same active generation as ready or busy; pending, missing, mismatched, stopped, or recovering service state fails closed without production fallback. Podway is the first required managed service, while Sanho remains optional. The manager does not change the caller's Codex home, authentication, plugin installation, or global MCP configuration. Development artifacts are local integration evidence only, not release or distribution proof.

## Main Workflows

1. **Shape** — `$aquarium:new-project` turns a goal into an approved PRD and a first roadmap. `$aquarium:new-feature` and `$aquarium:refactor` create or revise one epic. `$aquarium:war-room` diagnoses a hard bug and proposes the next work unit, or reports the investigation as incomplete, without writing the fix.
2. **Deliver** — `$aquarium:task-handler` runs one roadmap task through the stages above. `$aquarium:epic-handler` runs an epic's tasks in order and then hardens the whole epic. Commits stay separate and go through `$aquarium:task-commit` with your approval.
3. **Validate** — `$aquarium:epic-validator` re-checks a completed epic from a clean start and fixes the gaps it confirms. `$aquarium:independent-review` gives staged changes, commits, ranges, tasks, epics, and special investigations one canonical static Codex review contract. `$aquarium:orca-review` preserves those target meanings while running the reviewer you requested in the current Orca worktree. Aquarium checks every returned finding locally.
4. **Release** — `$aquarium:release-handler` settles cumulative notes, delegates exact-candidate scenarios to `$aquarium:release-qa`, runs the repository gate, publishes with separate approval, and opens the next planned version.

Foundations: `$aquarium:docs-setup` governs canonical documentation structure and roadmap IDs. `$aquarium:test-setup` enrolls a repository in the common test contract. `$aquarium:dev-setup-global` maintains user-global tools; `$aquarium:dev-setup` automatically diagnoses repository configuration and agent guidance, proposing changes only when needed. `$aquarium:dev-setup-bundle` delegates those two scopes across several repositories from one v1 manifest.

## How the Ecosystem Connects

- [Podway](https://github.com/irootkernel/podway) provides local execution memory for the goals, transitions, and handoffs of Git-backed workflows. It is selected by default for `task-handler`, `epic-handler`, `epic-validator`, `new-project`, `new-feature`, `refactor`, and `war-room`, and may be opted out before the first managed-session mutation. Aquarium runs the workflow and Podway records it; detailed lifecycle operations belong to the owning workflow or the standalone `use-podway` skill.
- [Gaori](https://github.com/irootkernel/gaori) runs your existing checks, keeps the raw logs, and returns a bounded summary as evidence. Gaori integration is optional, and the command's exit code stays the pass/fail authority.
- [Mulgae](https://github.com/irootkernel/mulgae) gives completed tasks and epics an advisory multi-provider review from an immutable capture exposed through an isolated read-only provider workspace. Temporary provider workspaces are removed after use. Durable captures and reports remain under `.mulgae/`, and results are returned through a staged file or standard output. Aquarium verifies and reprioritizes each finding locally.
- [Sorage](https://github.com/irootkernel/sorage) brokers local document handoffs between registered projects. Aquarium can install and diagnose the supported Apple Silicon CLI and paired `use-sorage` skill, initialize the local installation, and register the current Git repository after separate approval. The paired skill owns inbox, outbox, review, revision, retention, deletion, and Vault operations.
- [Dolgorae](https://github.com/irootkernel/dolgorae) supplies the exact immutable capture and checked review lifecycle used by Independent Review. Aquarium admits verified official stable v0.1.x Apple Silicon executables starting at v0.1.2 for that production review path. The same-release `use-dolgorae` skill also guides explicitly requested global Profile and reusable External Specialist Engagement operations.
- [Orca Review](plugins/aquarium/skills/orca-review/SKILL.md) uses the separately installed Orca runtime to launch and supervise the reviewer you requested, including Claude, in the current registered worktree. It accepts staged, HEAD, commit, and range targets; a staged review reads `git diff --cached` directly. Reviewers must preserve source files, tracked and non-ignored worktree files, and Git state. All reviewers may write review-related temporary files, native state, tool output, and reports outside the worktree or in Git-ignored runtime paths within it, such as ignored files under `.omc/`. External locations include `/tmp` or `/private/tmp`. Permitted external files and ignored runtime writes do not require warnings, extra checks, approval, or another review. Orca Review does not use Dolgorae, and Aquarium independently adjudicates the result.
- [Sanho](https://github.com/irootkernel/sanho) syncs project documentation to its canonical documentation repository once Aquarium has settled what is ready to hand off.
- [Lora](https://github.com/tmdgusya/lora) keeps decision context in Git trailers, and [Cursor Team Kit](https://github.com/cursor/plugins/tree/main/cursor-team-kit) supplies the upstream `deslop` cleanup skill used during task refinement.
- [Humanizer](https://github.com/blader/humanizer) provides the final prose pass for English documentation, while [im-not-ai](https://github.com/epoko77-ai/im-not-ai) provides the corresponding Korean pass. Projects opt into either rule independently through `dev-setup` guidance.
- [Ouroboros](https://github.com/Q00/ouroboros) contributes discovery, PM, Seed, and QA only inside the five explicitly invoked design workflows. Aquarium keeps document application, approval, and repository authority.

Together they form one governed path from scoping to documentation sync, so one tool's success is never mistaken for project completion.

Runtime evidence under `.mulgae/**`, `.gaori/runs/**`, `.podway/runtime/**`, derived `.sorage/**`, and disposable roots is local and expected to expire. Aquarium does not cite those paths or identities as evidence in tracked roadmaps, repository handoffs, or commit messages. A necessary durable exception uses only reviewed bounded non-sensitive structured evidence copied into an `aquarium.promoted-evidence/v1` package under the repository's evidence root, `evidence/aquarium/` by default.

## Operating Boundaries

- Invoking a workflow grants only the effects its skill documents. Installation, authentication, source transmission, tests, staging, commits, pushes, publication, and destructive lifecycle actions each need separate authority.
- Invoking `release-handler` authorizes read-only release discovery and orchestration only; commits, pushes, tags, hosted Releases, destructive replacement, and the post-release next-cycle commit remain separate approvals. Its delegated `release-qa` pass may use existing ambient authentication for private repositories, remediate verified findings locally once, and never upload source or handle credentials.
- Explicitly invoking `dev-setup-global` checks every supported global component and authorizes bounded official metadata and public paired-skill freshness reads. Dolgorae uses GitHub Releases metadata; Dolgorae, Sanho, Mulgae, Gaori, Sorage, and Podway compare public `raw.githubusercontent.com` files in ephemeral storage. Scoped continuations check only their named components. Downloads for installation, mutations, and provider calls remain separately controlled.
- Aquarium creates no central project-state file. [PRIVACY.md](PRIVACY.md) and [TERMS.md](TERMS.md) hold the complete data and authority contracts.

## References

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

The gate needs Python 3.11 or newer, Ruby 3.3 or newer, and the pinned `requirements.txt` versions. This repository is licensed under the [MIT License](LICENSE).

## Upgrading

- From the old `aquarium` marketplace identity: run `codex plugin remove aquarium@aquarium` and `codex plugin marketplace remove aquarium`, then use the install commands above.
- From the legacy Root Kernel plugin: finish or dispose of any active legacy Podway session, run `codex plugin remove root-kernel@root-kernel-dev-skills` and `codex plugin marketplace remove root-kernel-dev-skills`, install Aquarium, then let `$aquarium:dev-setup` migrate the managed Procedures.

## Thanks

Thanks to Lora, Ouroboros, Cursor Team Kit, Humanizer, and im-not-ai for the upstream skills Aquarium builds on. Aquarium does not vendor their skill or documentation sources. Each project retains its own license terms.
