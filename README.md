# Aquarium

<img alt="Aquarium AI Fleet engineering ecosystem" src="plugins/aquarium/assets/hero.png" width="100%">

**Software engineering with AI Fleets, not vibe coding.**

English · [한국어](README.ko.md)

By [Root Kernel](https://home.rootkernel.xyz) · Support: [cs@rootkernel.xyz](mailto:cs@rootkernel.xyz)

Aquarium is a Codex plugin for engineering reliable software with AI Fleets. It connects specialized agents, models, and development tools into workflows with three rules: every task has a tracked state, completion needs verified evidence, and consequential actions wait for your approval.

Aquarium is growing beyond vibe coding toward Agentic Engineering, Loop Engineering, Graph Engineering, and the practices that come next. These are not separate products or a rigid maturity model. They name a direction: AI work that is more specialized, more iterative, more connected, and more accountable.

## Aquarium Editions

- [Aquarium for Claude](https://github.com/irootkernel/aquarium-for-claude)
- [Aquarium for Kimi](https://github.com/irootkernel/aquarium-for-kimi)
- [Aquarium for GLM](https://github.com/irootkernel/aquarium-for-glm)

## Why Aquarium

Even capable AI tools, used one at a time, leave the engineer to track context, approvals, task state, and evidence by hand. Aquarium connects them into one workflow and keeps these rules:

- **Work has identity.** A delivery task or epic lives in your roadmap with an ID and a lifecycle state. Commits go through `task-commit`, which records the lifecycle change you confirm instead of skipping it.
- **Delivery is phased and gated.** `task-handler` moves one task through seven stages, from plan to close. Nothing changes before you approve the plan. Every applicable roadmap requirement must map to current evidence. Closeout waits for your explicit approval.
- **Evidence is verified.** A command's exit code decides pass or fail. Review findings stay advisory until they are checked locally against the roadmap, the code, and the tests.
- **Evidence has a residence.** Ignored Mulgae, Gaori, and Podway runtime artifacts support the active workflow but never become roadmap history or durable repository authority. When downstream correctness truly requires retained evidence, Aquarium promotes only reviewed bounded artifacts into a tracked package outside canonical documentation.
- **Loops are bounded.** A clean review ends the loop at once. Review and remediation rounds run inside explicit budgets, and cold validation stops when no new gaps appear.
- **Invariants and tests are contracts.** Design Gates are offline, objectively checkable rules. A task whose gate impact is still pending cannot be implemented, and release QA re-runs every active gate. The test contract runs prepare, unit, integration, and E2E in order, fails on a missing prerequisite instead of skipping it, and gives a new project no waivers.
- **You keep authority.** Installing tools, sending source to a provider, staging, committing, pushing, and publishing each need their own approval. Design documents and setup files change only through an exact diff you approve. A local hook catches direct shell commits in roadmap repositories and points them to `task-commit`.
- **Work can pause, resume, and hand off.** `task-handler` and `epic-handler` support plan-only runs, explicit plan handoff to another agent, and resuming a matching session. A plan by itself creates no runtime state.

Codex is Aquarium's primary agent runtime, and Aquarium deliberately integrates a defined toolchain rather than promising provider or framework neutrality. It owns the contracts among Codex, Orca, Podway, Sanho, Mulgae, Gaori, Ouroboros, Lora, and Deslop. Each contract says when a tool runs, what it may decide, and how its output becomes evidence for the next step.

## Install

```bash
codex plugin marketplace add irootkernel/aquarium --ref main
codex plugin add aquarium@root-kernel
```

Restart Codex after installing or upgrading, then open `/hooks` and explicitly trust Aquarium's roadmap commit guard. The hook catches direct shell commits. It is not complete enforcement: commits created indirectly by another tool may not pass through it.

Aquarium does not vendor third-party skill or documentation sources. `$aquarium:dev-setup` checks the supported tools and proposes installs or repairs from their exact upstream sources, each behind its own approval. The upstream `$deslop` skill is a required prerequisite for task delivery.

## Main Workflows

1. **Shape** — `$aquarium:new-project` turns a goal into an approved PRD and a first roadmap. `$aquarium:new-feature` and `$aquarium:refactor` create or revise one epic. `$aquarium:war-room` diagnoses a hard bug and proposes the next work unit, or reports the investigation as incomplete, without writing the fix. `$aquarium:design-qa` creates, changes, or retires Design Gates.
2. **Deliver** — `$aquarium:task-handler` runs one roadmap task through the stages above. `$aquarium:epic-handler` runs an epic's tasks in order and then hardens the whole epic. Commits stay separate and go through `$aquarium:task-commit` with your approval.
3. **Validate** — `$aquarium:epic-validator` re-checks a completed epic from a clean start and fixes the gaps it confirms. `$aquarium:independent-review` gives staged changes, commits, ranges, tasks, epics, and special investigations one canonical static Codex review contract. `$aquarium:orca-review` applies the same contract to a selected non-Codex provider. Aquarium checks every returned finding locally.
4. **Release** — `$aquarium:release-handler` settles cumulative notes, delegates exact-candidate scenarios to `$aquarium:release-qa`, runs the repository gate, publishes with separate approval, and opens the next planned version.

Foundations: `$aquarium:docs-setup` governs canonical documentation structure and roadmap IDs. `$aquarium:test-setup` enrolls a repository in the common test contract. `$aquarium:dev-setup` checks and configures the toolchain and the repository's agent guidance. `$aquarium:dev-setup-bundle` applies that setup to several repositories from one manifest.

## How the Ecosystem Connects

- [Podway](https://github.com/irootkernel/podway) provides local execution memory for the goals, transitions, and handoffs of Git-backed workflows. It is selected by default for `task-handler`, `epic-handler`, `epic-validator`, `new-project`, `new-feature`, `refactor`, `war-room`, and `design-qa`, and may be opted out before the first managed-session mutation. Aquarium runs the workflow and Podway records it; detailed lifecycle operations belong to the owning workflow or the standalone `use-podway` skill.
- [Gaori](https://github.com/irootkernel/gaori) runs your existing checks, keeps the raw logs, and returns a bounded summary as evidence. Gaori integration is optional, and the command's exit code stays the pass/fail authority.
- [Mulgae](https://github.com/irootkernel/mulgae) gives completed tasks and epics an advisory multi-provider review. Aquarium verifies each finding locally and sets explicit limits on remediation.
- [Orca Review](plugins/aquarium/skills/orca-review/SKILL.md) uses the separately installed Orca runtime to supervise Claude Fable, Kimi, Agy, or Cursor Agent against one exact Git target. Dirty working-tree content is excluded or staged only with explicit path approval, and Aquarium independently adjudicates the result.
- [Sanho](https://github.com/irootkernel/sanho) syncs project documentation to its canonical documentation repository once Aquarium has settled what is ready to hand off.
- [Lora](https://github.com/tmdgusya/lora) keeps decision context in Git trailers, and [Cursor Team Kit](https://github.com/cursor/plugins/tree/main/cursor-team-kit) supplies the upstream `deslop` cleanup skill used during task refinement.
- [Ouroboros](https://github.com/Q00/ouroboros) contributes discovery, PM, Seed, and QA only inside the five explicitly invoked design workflows. Aquarium keeps document application, approval, and repository authority.

Together they form one governed path from scoping to documentation sync, so one tool's success is never mistaken for project completion.

Runtime evidence under `.mulgae/**`, `.gaori/runs/**`, `.podway/runtime/**`, and disposable roots is local and expected to expire. Aquarium does not cite those paths or identities as evidence in tracked roadmaps, repository handoffs, or commit messages. A necessary durable exception uses only reviewed bounded non-sensitive structured evidence copied into an `aquarium.promoted-evidence/v1` package under the repository's evidence root, `evidence/aquarium/` by default.

## Operating Boundaries

- Invoking a workflow grants only the effects its skill documents. Installation, authentication, source transmission, tests, staging, commits, pushes, publication, and destructive lifecycle actions each need separate authority.
- Invoking `release-handler` authorizes read-only release discovery and orchestration only; commits, pushes, tags, hosted Releases, destructive replacement, and the post-release next-cycle commit remain separate approvals. Its delegated `release-qa` pass may use existing ambient authentication for private repositories, remediate verified findings locally once, and never upload source or handle credentials.
- When selected for setup or diagnosis, Sanho, Mulgae, Gaori, and Podway automatically query their official GitHub Releases metadata and download four public skill files from `raw.githubusercontent.com` into ephemeral storage to compare with the installed `use-*` skill. Unselected tools and other network operations are not covered, and setup never calls an AI provider.
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

Thanks to Lora, Ouroboros, and Cursor Team Kit for the upstream skills Aquarium builds on. Aquarium does not vendor their skill or documentation sources. Ouroboros and Cursor Team Kit provide MIT LICENSE files, and Lora declares MIT in its README.
