# AGENTS.md

Repository guidance for AI coding agents working on Aquarium. `CLAUDE.md` delegates to this file.

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
- Use `$aquarium:new-project`, `$aquarium:new-feature`, or `$aquarium:refactor` for explicitly requested Ouroboros-assisted design workflows.
- Use `$aquarium:war-room` for difficult-bug diagnosis.
- Use `$aquarium:release-handler` for one stable release lifecycle, `$aquarium:release-qa` for its exact release-candidate verification, and `$aquarium:dev-setup-bundle` only with an explicitly supplied multi-repository manifest.
- Use `$aquarium:dev-setup-global` to diagnose, install, or update supported user-global development tools, paired skills, services, and global MCP state. Requests to install or update only the Aquarium plugin belong to the host's plugin-management flow; do not load this skill or run global setup diagnostics for those requests.
- Use `$aquarium:dev-setup` to diagnose or configure repository-local tooling and repository operating guidance, including root AGENTS.md and CLAUDE.md.
- Use `$aquarium:docs-setup` to audit, establish, adopt, or migrate canonical documentation structure and roadmap IDs.
- Use `$aquarium:test-setup` to audit or configure the common Make or Bun testing contract and evidence-backed legacy waivers.
- Use each installed paired `$use-*` skill for its corresponding local tool operations and keep tool-specific lifecycle rules in that integration's canonical contract.
- Use `$aquarium:dev-setup` for explicitly requested Sorage Project setup. Use `$use-sorage` only when Master explicitly requests a broker operation. Check only the requested inbox or outbox; session start, a new task, a Sorage mention, or Project registration does not authorize discovery. Keep Handoff, review, revision, retention, deletion, and Vault operations in that paired skill.
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

- Every commit title must start with exactly one approved uppercase header: `[FEAT]`, `[FIX]`, `[DEV]`, `[TEST]`, `[DOC]`, `[CI]`, `[REL]`, or `[INT]`.
- Use `[FEAT]` for new user-facing capabilities, `[FIX]` for defect corrections, and `[DEV]` for development-tool or internal integration changes.
- Use `[TEST]`, `[DOC]`, or `[CI]` when the change is limited to that concern. Use `[REL]` for releases and `[INT]` for other internal cross-cutting contract changes.
- Choose the header for the commit's primary purpose and write one imperative summary after it. Do not combine multiple headers.
- Release commits must use exactly `[REL] Release v<version>`; this rule overrides the general header choice.
- Use `$lore-commits` for non-trivial commit bodies and decision trailers.

### Project-Specific Operating Rules

- Aquarium does not vendor third-party Lora, Lore, Ouroboros, Deslop, Humanizer, or im-not-ai sources. Preserve the exact-upstream installation and provenance boundaries in `dev-setup-global`; `dev-setup` trusts canonical global skill presence and owns repository guidance.
- Do not create `.aquarium` or another central project-state file. Bundle manifests are explicit external inputs, not repository discovery or persisted state.
- Preserve approval boundaries between diagnosis, network lookup, installation, native configuration, repository guidance, staging, commits, and publication.
- Keep Ruby and Python validation minimal. Check objective structure and executable code behavior only; do not pin skill prose, word order, line wrapping, blank lines, diagnostic sentences, private helper names, or source-code fragments. Do not add text matching as a substitute for skill verification.
- Master performs skill functional verification separately after skill updates, including multi-step execution, decisions, recommendations, approval boundaries, and cross-skill handoffs. Do not add automated LLM evaluations to `make test` or claim that its success verifies these behaviors. Report the affected manual checks and leave their outcome unverified until Master provides it.
- Treat ignored Mulgae, Gaori, Podway, derived Sorage, and disposable runtime artifacts as local workflow evidence, never tracked documentation authority. Promote only reviewed bounded non-sensitive structured evidence under the shared Aquarium evidence-residency contract when a durable downstream reference is necessary. Declare a custom root only with the exact Project Configuration entry `Aquarium evidence root: <repository-relative-path>`; otherwise use `evidence/aquarium/`.
- Preserve unrelated staged, unstaged, and untracked work. Do not include local runtime state or setup manifests in a task unless Master explicitly puts them in scope.

### Release Policy

When Master asks to release `main`, use `$aquarium:release-handler` and establish the release mode before making release changes. Ask whether to use `full` or `light` unless Master already selected one explicitly. If Master did not provide a version, propose the open CHANGELOG version and obtain confirmation before changing version metadata.

Before release QA, reconcile every material change after the previous release with the open CHANGELOG section and obtain approval for any entry addition, merge, edit, or removal. Commit that exact preparation through `$aquarium:task-commit`, then run a new release-qa pass against the resulting clean exact candidate. After release QA passes, preserve entry text byte-for-byte; a substantive note edit creates a new candidate and requires release QA again.

Before either mode, inspect the worktree, the local and remote `main` commits, the exact release-candidate SHA, and existing tags and GitHub Releases. Stop on unrelated worktree changes, an ambiguous release target, or a conflicting tag or release rather than including or overwriting it.

When the open release requires Podway v0.2.9 compatibility, verify the official Apple Silicon archive against its published checksum and run this additional exact-artifact gate before release QA:

```bash
PODWAY_BIN=<absolute-path-to-extracted-v0.2.9-podway> make test-podway-compat
```

A local development binary is development-contract evidence only and cannot satisfy this distribution gate. In light mode, the required prior test confirmation must cover this result for the exact Aquarium candidate SHA; in full mode, run it in addition to the complete local release gate. Podway's own exact release-candidate gate remains authoritative for runtime record enforcement and Podway distribution readiness.

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
