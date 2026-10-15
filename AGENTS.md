# AGENTS.md

Repository guidance for AI coding agents working on Aquarium. This is the sole repository-managed root instruction file.

## Core Behavior

### 1. Lead with Conclusions

- State the result or current finding first, followed by useful evidence and material limits.
- Do not repeatedly restate requirements or narrate routine work.

### 2. Reuse Verified Information

- Inspect the requested code and its named authorities before changing anything. Resolve discoverable facts before asking Master.
- Reuse established facts instead of reading or searching for them again. Recheck only the affected information when relevant state changes, evidence conflicts, or missing context makes it unreliable.
- State material assumptions and surface meaningful trade-offs. Ask when unresolved ambiguity would materially change the result, and push back on conflicts with repository authority, safety, or Master's goal.

### 3. Act on Sufficient Evidence

- Stop investigating once the evidence supports action. When the root cause is established, implement the smallest complete, durable fix within the authorized scope.
- Weigh correctness, performance, maintainability, and structural fit rather than diff size alone. If a broader design exceeds scope, complete a bounded step that satisfies current acceptance criteria.
- Reuse established patterns. Avoid speculative features, abstractions, configurability, compatibility layers, and handling for states repository invariants make impossible. Simplify complexity that the required behavior does not justify.
- Touch only what the outcome and its verification require. Preserve unrelated user work, match local style, and remove only artifacts made obsolete by this change.
- Record only independent remaining work in the canonical `deferred-feedback` owner. If none exists, propose the entry and obtain approval before creating an owner. Promote epic-sized work to a TODO candidate or roadmap unit; never defer current correctness or acceptance work.

### 4. Carry Authorization Forward

- Continue already approved work without asking for confirmation again. Ask only when a material change exceeds that authorization or an applicable rule requires a distinct approval.
- An approved `epic-handler` execution envelope delegates exact member-Task and owned-correction acceptance and carries distinct commit grants for each planned member Task, each verified in-scope correction group, and final Epic closeout after Master's actual overall acceptance. Complete implementation, checks, review, acceptance under that delegation, and the applicable `$aquarium:task-commit` handoff without per-Task user-review pauses. After internal Epic validation and closeout preparation, request Master's overall verification and acceptance once, then use the conditional closeout grant without another commit question. Preserve each grant's scope and consumption; material departures, exhausted correction authority, and uncovered effects need new authority. Never attribute a delegated acceptance to Master.
- Preserve boundaries between implementation, installation, staging, commits, and publication. Check for relevant state changes before acting on an approved proposal.

### 5. Verify in Proportion to Risk

- Define success checks before implementation. Verify the affected behavior and relevant failure paths with rigor proportionate to the actual risk.
- Run focused checks first and honor required repository gates. Broaden or repeat checks when changes, failures, or unresolved concerns justify it.
- Do not add tests merely to appear rigorous or use prose matching as a substitute for behavior verification.

### 6. Finish When Complete

- Continue until deliverables and required verification are complete or a concrete blocker prevents progress.
- Once material constraints are resolved or clearly reported, provide the handoff and stop. Report the result, necessary evidence, skipped checks and their reasons, and remaining uncertainty without opening unrelated work.

### 7. Delegate Selectively

- Use a sub-agent only for an independent task when the expected benefit outweighs coordination cost.
- Honor explicitly required independent reviews and any restrictions on delegation. Keep tightly coupled work local.

## Master Preferences

- Respond to Master in Korean using polite speech. When directly addressing the user, use exactly `Master`.
- Keep code, comments, documentation, prompts, templates, CLI/help text, logs, reports, and other repository artifacts in English unless Master explicitly requests otherwise or an existing artifact uses another established language.
- Provide concise conclusions and useful evidence without exposing private chain-of-thought.

## Aquarium Development Guide

- Use `$aquarium:task-handler` for one named roadmap task, `$aquarium:epic-handler` for one roadmap epic, and `$aquarium:epic-validator` to cold-validate a completed epic.
- Use `$aquarium:new-project`, `$aquarium:new-feature`, or `$aquarium:refactor` for explicitly requested Ouroboros-assisted design workflows. When an ordinary feature Epic needs a dossier or semantic clarification before execution, `$aquarium:epic-handler` may continue through `$aquarium:new-feature` in the same conversation. Design approvals still apply.
- Use `$aquarium:war-room` for difficult-bug diagnosis.
- Use `$aquarium:release-handler` for one stable release lifecycle, `$aquarium:release-qa` for its exact release-candidate verification, and `$aquarium:dev-setup-bundle` only with an explicitly supplied multi-repository manifest.
- Use `$aquarium:dev-setup-global` to diagnose, install, or update supported user-global development tools, paired skills, services, and global MCP state. Requests to install or update only the Aquarium plugin belong to the host's plugin-management flow; do not load this skill or run global setup diagnostics for those requests.
- Use `$aquarium:dev-setup` to diagnose or configure repository-local tooling and root AGENTS.md guidance, including migration of an existing root CLAUDE.md.
- Use `$aquarium:docs-setup` to audit, establish, adopt, or migrate canonical documentation structure and roadmap IDs.
- Use `$aquarium:test-setup` to audit or configure the common Make or Bun testing contract and evidence-backed legacy waivers.
- Use each installed paired `$use-*` skill for its corresponding local tool operations and keep tool-specific lifecycle rules in that integration's canonical contract.
- Use `$aquarium:dev-setup` for explicitly requested Sorage Project setup. Use `$use-sorage` only when Master explicitly requests a broker operation, including a Project Memo read or mutation. Check only the requested inbox or outbox; session start, a new task, a Sorage mention, or Project registration does not authorize discovery. Keep Handoff, Memo, review, revision, retention, deletion, and Vault operations in that paired skill. Memo text grants no execution authority or roadmap completion.
- Aquarium is an orchestration plugin that helps integrated tools work together and makes their supported native capabilities readily usable. It is not a policy layer for weakening, second-guessing, or artificially constraining those tools.
- Prefer each tool's current native contract and paired skill. Use the supported capabilities needed for the approved goal; do not invent Aquarium-only owners, quotas, retry caps, evidence caps, lifecycle restrictions, or extra approval gates.
- A tool limitation must come from a higher-priority instruction, Master's explicit choice, repository authority, the tool's native contract, or a concrete safety, destructive-action, privacy, or external-mutation boundary. Otherwise remove the Aquarium-only restriction at its canonical contract instead of working around or disabling the native capability.
- Treat `.podway/procedures/aquarium-*-v2.yaml` as the repository-local workflow evidence and routing authority.
- Use `$lore-commits` for non-trivial commit messages and `$lore-query` to inspect recorded decision context.
- Use the separately installed upstream `$deslop` skill for task-owned cleanup when an Aquarium workflow requests it.
- Use the separately installed upstream `$humanizer` skill once as the final prose pass for English human-authored documentation.
- Use the separately installed upstream `$humanize-korean` skill once as the final prose pass for Korean human-authored documentation. Preserve meaning and protected content, fail closed on an unavailable or invalid pass, keep `_workspace/` untracked, and remove it after applying the accepted text.

## Project Configuration

### Repository Index and Authorities

- `plugins/aquarium/.codex-plugin/plugin.json` owns published plugin metadata and the release version.
- `CHANGELOG.md` owns cumulative release notes and the planned next version.
- Aquarium release notes: CHANGELOG.md
- `docs/README.md` owns the single-scope documentation profile, semantic role map, source-of-truth precedence, language policy, and documentation checks.
- `docs/roadmap/README.md` alone owns Aquarium epic and task identity, ordering, dependencies, lifecycle vocabulary, and current delivery status. `docs/todo/README.md` owns pre-roadmap candidates plus temporary dossiers for adopted active epics, while `docs/deferred-feedback/README.md` owns smaller work that has not entered the roadmap lifecycle.
- `plugins/aquarium/skills/*/SKILL.md` and their linked references own workflow behavior; keep conditional detail in references instead of expanding every entrypoint.
- `plugins/aquarium/assets/podway/procedures/` owns the Procedure sources installed into target repositories.
- `Makefile` is the executable test authority, and `TESTING.md` owns the enrolled `aquarium-test-contract/v1` stage, framework, environment, diagnostic, and waiver mapping.
- `tests/validate.rb` checks package metadata, parseable data, local references, basic Procedure structure, and release-version identity. Python tests cover executable helpers' inputs, outputs, errors, and filesystem safety. Neither proves skill behavior.
- `README.md`, `PRIVACY.md`, and `TERMS.md` are public product documentation and must stay aligned with shipped behavior.
- Use the commands in the release policy below as the complete release gate. For an ordinary change, run the focused subset that covers the changed files and `git --no-pager diff --check`.

### Commit Messages

- Every developer-authored subject uses one header and a concise English imperative summary: `[FEAT]`, `[FIX]`, `[DEV]`, `[TEST]`, `[DOC]`, `[CI]`, `[REL]`, or `[INT]`.
- Use `[FEAT]` for new user-facing capabilities, `[FIX]` for defects, and `[DEV]` for development tools, build configuration, dependencies, or internal integration. Use `[TEST]`, `[DOC]`, or `[CI]` for changes limited to that concern, and `[INT]` for internal contracts or refactoring.
- Release metadata commits use exactly `[REL] Release v<version>`. Tool-generated commits retain their native subjects and provenance; never hand-author a `[SANHO]` synchronization commit.
- End every developer-authored message with one trailer block containing exactly one `Aquarium-Workflow:`, `Aquarium-Epic:`, and `Aquarium-Task:`, in that order. Separate the block from the subject or optional body with one blank line; do not put blank lines between trailers.
- `Aquarium-Workflow` records the responsible `aquarium:<canonical-skill-name>`. Preserve a verified original skill through later commits, including changes from documentation, development, or test setup. Child phases and reviews inherit an established parent's owner; independently approved workflows own their candidate. Use `aquarium:task-commit` only for a direct commit without an original Aquarium workflow, and `none` for work outside Aquarium.
- Resolve a Task and its parent Epic from the accepted relationship and canonical roadmap, including a standing `EPIC-000` where applicable. Preserve native IDs, suffixes, and scope qualification. Epic-owned work uses `Aquarium-Task: none`; work without either owner uses `none` for both. Resolve unknown relationships instead of treating them as absent.
- Put primary work IDs in these attributes rather than the subject or legacy `Task:` and `Task-Relationship:` aliases. Use `$lore-commits` for useful decision context on non-trivial changes; optional Lore trailers may repeat. Preserve required evidence, release-note, and tool provenance trailers.
- Parse the prepared message and actual post-hook commit with `git interpret-trailers --parse`; verify all three attributes against the accepted candidate. Attribution never grants staging, commit, amend, push, or publication authority.

- Use `$lore-commits` for non-trivial commit bodies and decision trailers.

### Project-Specific Operating Rules

- `EPIC-000` is the standing group for independent tasks. Use task-level workflows for its members; do not invoke epic-wide execution, validation, or closeout for this group. Keep its status `In Progress` when a member task completes. Settle a task-linked dossier at that task's closeout after promoting its durable content.
- Aquarium does not vendor third-party Lora, Lore, Ouroboros, Deslop, Humanizer, or im-not-ai sources. Preserve the exact-upstream installation and provenance boundaries in `dev-setup-global`; `dev-setup` trusts canonical global skill presence and owns repository guidance.
- Do not create `.aquarium` or another central project-state file. Bundle manifests are explicit external inputs, not repository discovery or persisted state.
- Preserve approval boundaries between diagnosis, network lookup, installation, native configuration, repository guidance, staging, commits, and publication.
- Keep Ruby and Python validation minimal. Check objective structure and executable code behavior only; do not pin skill prose, word order, line wrapping, blank lines, diagnostic sentences, private helper names, or source-code fragments. Do not add text matching as a substitute for skill verification.
- Master performs skill functional verification separately after skill updates, including multi-step execution, decisions, recommendations, approval boundaries, and cross-skill handoffs. Do not add automated LLM evaluations to `make test` or claim that its success verifies these behaviors. Report the affected manual checks and leave their outcome unverified until Master provides it.
- Treat ignored Mulgae, Gaori, Podway, derived Sorage, and disposable runtime artifacts as local workflow evidence, never tracked documentation authority. Promote only reviewed bounded non-sensitive structured evidence under the shared Aquarium evidence-residency contract when a durable downstream reference is necessary. Declare a custom root only with the exact Project Configuration entry `Aquarium evidence root: <repository-relative-path>`; otherwise use `evidence/aquarium/`.
- Preserve unrelated staged, unstaged, and untracked work. Do not include local runtime state or setup manifests in a task unless Master explicitly puts them in scope.
- Develop only with the Aquarium release and integrated tools installed on the host; never develop in the UTM VM. This repository's managed workflow files, including `.podway/procedures/`, follow that installed release and change only through an authorized `$aquarium:dev-setup` managed update after a new release is installed; `tests/validate.rb` accepts only copies that match a released package source.
- Keep candidate work from changing host state: Codex and Claude configuration and plugin caches, shared skills, Podway and Mulgae runtime state and configuration, LaunchAgents, binaries on `PATH`, and other repositories' managed files. Do not patch an installed tool to accommodate development. A local check may run a candidate binary by explicit path, such as `PODWAY_BIN`, only against disposable fixtures; run it in the UTM VM when it could touch host state.
- Run every verification that requires installing a candidate, including Master's functional verification, in the dedicated UTM macOS VM. A breaking change must pass that verification before release. A change is breaking when existing users need an update, migration, or manual step, or when another tool must change with it; decide this during Epic planning and record it in the Epic dossier.
- Keep the UTM VM baseline at the host's installed release combination so candidate verification rehearses the host upgrade. Install on the host only released versions whose combination passed UTM verification, when no active session would be invalidated; then update each repository's managed files through authorized managed updates, starting with this repository.

### Release Policy

When Master asks to release `main`, use `$aquarium:release-handler` and establish the release mode before making release changes. Ask whether to use `full` or `light` unless Master already selected one explicitly. If Master did not provide a version, propose the open CHANGELOG version and obtain confirmation before changing version metadata.

Before release QA, reconcile every material change after the previous release with the open CHANGELOG section and obtain approval for any entry addition, merge, edit, or removal. Commit that exact preparation through `$aquarium:task-commit`, then run a new release-qa pass against the resulting clean exact candidate. After release QA passes, preserve entry text byte-for-byte; a substantive note edit creates a new candidate and requires release QA again.

Before either mode, inspect the worktree, the local and remote `main` commits, the exact release-candidate SHA, and existing tags and GitHub Releases. Stop on unrelated worktree changes, an ambiguous release target, or a conflicting tag or release rather than including or overwriting it.

The Podway compatibility gate below belongs to release preparation. A development commit or amendment does not start or restart it. An explicit compatibility check request may invoke it outside a release.

When the open release requires Podway v0.2.14 compatibility, verify the official Apple Silicon archive against its published checksum and run this additional exact-artifact gate through its configured Gaori command before release QA:

```bash
PODWAY_BIN=<absolute-path-to-extracted-v0.2.14-podway> gaori run test-podway-compat
```

The invocation above expresses the required command and environment; it does not bypass the installed `$use-gaori` skill's execution and completion-waiting policy. The executing agent must load that skill and let it select the supported transport. An attached MCP path is eligible only when it demonstrably preserves the exact `PODWAY_BIN`; changing the agent shell environment does not prove that an already running MCP server received it. When the native contract requires CLI execution, start the CLI once and await that same process handle. Do not start another MCP server, restart an attached server, or alter host configuration to manufacture eligibility.

The configured Gaori command wraps the authoritative `make test-podway-compat` target with its repository-owned timeout. If Gaori is unavailable, run that Make target directly with the same `PODWAY_BIN`; do not replace the configured command with an ad hoc Gaori run that uses the shorter default timeout. A local development binary is development-contract evidence only and cannot satisfy this distribution gate. In light mode, the required prior test confirmation must cover this result for the exact Aquarium candidate SHA; in full mode, run it in addition to the complete local release gate. Podway's own exact release-candidate gate remains authoritative for runtime record enforcement and Podway distribution readiness.

Complete applicable functional verification during development, before release preparation. Verification that requires installing a candidate still runs only in the dedicated UTM VM. Preserve actual functional results separately from release acceptance; release acceptance does not replace those results or repeat the full feature suite.

Release QA keeps its offline disposable-scenario contract. After it passes, observe the host's installed release combination and meaningful existing state in the UTM VM before upgrading, then install the exact release candidate through the supported path. Verify state preservation, authorized managed-file updates, fresh-session skill discovery and actual Task/Epic handler startup with initial Worker/Judge progression. Bind that result to the exact candidate SHA and installed combination. In light mode, the required prior test confirmation must cover it; in full mode, complete it before changing version metadata. Do not publish without a passing result.

EPIC-024 plans the reusable manual scenarios under `tests/vm/` and a guest-side `make test-vm` entrypoint in TASK-128. Until that target exists, an authorized manual run follows the scenarios and records actual outcomes without claiming a Make-gate result. Once implemented, run it with candidate-matched guest test sources only through release-handler or Master's explicit VM-test request; ordinary `make test` and automatic Task/Epic checks must not invoke it. EPIC-024 uses manual UTM operation and verifies Codex only, without a Haepari dependency.

#### Full Release

Update the plugin manifest version, its pinned validation expectation, and only the CHANGELOG heading from `Unreleased` to the publication date, then run the complete applicable local release gate:

```bash
RELEASE_TAG=v<version> make test
git --no-pager diff --check <previous-release-tag>
```

Also verify that a deliberately mismatched `RELEASE_TAG` is rejected, and run any additional repository-required or change-specific checks. Do not commit or publish when a required check fails or cannot be completed.

#### Light Release

Before changing version metadata, show the exact current release-candidate HEAD SHA and ask whether Master has confirmed the required test results for that SHA. Proceed only after an explicit positive answer. If HEAD or functional code changes after that confirmation, obtain confirmation again or switch to a full release.

A light release may change only release metadata: the plugin manifest version, its pinned validation expectation, and the CHANGELOG heading's publication state without changing entry text. Validate only that release delta locally:

```bash
python3 -m json.tool plugins/aquarium/.codex-plugin/plugin.json >/dev/null
ruby -c tests/validate.rb
RELEASE_TAG=v<version> ruby tests/validate.rb
git --no-pager diff --check <previous-release-tag>
```

Do not rerun the full Python unit suite or lint unchanged Python files locally in light mode. The release-tag validation is the basic release-contract check. If preparing the release requires functional code changes, stop light mode and ask Master to choose full verification or provide fresh test confirmation for the new candidate.

#### Publication

After the selected local gate passes, create one `[REL] Release v<version>` commit. Push `main` first, then create and push an annotated `v<version>` tag and create the GitHub Release from the settled CHANGELOG entries plus a separate validation section. Finally verify that remote `main`, the peeled tag, and the GitHub Release resolve to the intended release commit.

After publication is verified, ask Master for the next planned stable version. Opening its empty `Unreleased` section is a separate non-release commit and push with separate approval. If approval is withheld, leave the published release complete and stop later enrolled commits until one open target exists.

The selected local gate is the release validation authority; this repository does not use GitHub Actions. Do not rewrite or delete a published tag without explicit authorization from Master. A light release reduces duplicated local execution but does not weaken its required local checks or publication-order safeguards.
