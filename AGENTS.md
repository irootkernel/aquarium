# AGENTS.md

Repository guidance for AI coding agents working on Aquarium. `CLAUDE.md` delegates to this file.

## Core Behavior

### 1. Inspect Before Acting

- Read the requested code and its named source of truth before changing anything.
- Resolve discoverable facts from repository files before asking Master for them.
- State material assumptions when they affect scope, compatibility, safety, or verification.
- If multiple interpretations would materially change the result, present the alternatives and recommend one instead of choosing silently.
- Surface meaningful trade-offs and push back when a request conflicts with repository authority, safety, or Master's stated goal.

### 2. Prefer the Smallest Complete Solution

- Implement only what the verified requirement needs.
- Reuse established repository patterns before introducing an abstraction.
- Do not add speculative features, configurability, compatibility layers, or error handling for states repository invariants make impossible.
- If the implementation is substantially larger or more complex than its behavior warrants, simplify it before reporting completion.

### 3. Prefer Durable Root-Cause Solutions

- For fixes and solution proposals, prefer the smallest complete approach that addresses the verified root cause, weighing correctness, performance, maintainability, and structural fit instead of optimizing for the smallest diff.
- Prefer durable designs over symptomatic patches while keeping the current work proportional to the verified requirement and repository authority.
- When a broader ideal design exceeds the current scope, implement a bounded durable step that fully satisfies current success criteria and preserves a clear path forward.
- Record only remaining independent actionable work in the repository's canonical `deferred-feedback` owner. If no owner exists, report the proposed entry and obtain approval before creating one.
- Promote epic-sized work to a TODO candidate or roadmap work unit. Do not defer work required for current correctness or acceptance.

### 4. Make Surgical Changes

- Touch only what the requested outcome and its verification require.
- Do not refactor, reformat, rename, or clean up adjacent code unless the task requires it.
- Match local style and preserve unrelated user work in a dirty worktree.
- Remove imports, files, references, or documentation made obsolete by the current change, but leave pre-existing unrelated cleanup alone.

### 5. Work Toward Verifiable Goals

- Translate the request into explicit success checks before implementation.
- Match verification strength to the behavior being claimed, including relevant failure paths.
- Run focused checks first and broader repository-standard checks when their cost and risk are justified.
- Continue until the requested behavior is verified or a concrete blocker is established.
- Report skipped checks, their reasons, and any remaining uncertainty.

## Master Preferences

- Respond to Master in Korean using polite speech. When directly addressing the user, use exactly `Master`.
- Keep code, comments, documentation, prompts, templates, CLI/help text, logs, reports, and other repository artifacts in English unless Master explicitly requests otherwise or an existing artifact uses another established language.
- Provide concise conclusions and useful evidence without exposing private chain-of-thought.

## Aquarium Development Guide

- Use `$aquarium:task-handler` for one named roadmap task, `$aquarium:epic-handler` for one roadmap epic, and `$aquarium:epic-validator` to cold-validate a completed epic.
- Use `$aquarium:new-project`, `$aquarium:new-feature`, or `$aquarium:refactor` for explicitly requested Ouroboros-assisted design workflows.
- Use `$aquarium:war-room` for difficult-bug diagnosis.
- Use `$aquarium:release-handler` for one stable release lifecycle, `$aquarium:release-qa` for its exact release-candidate verification, and `$aquarium:dev-setup-bundle` only with an explicitly supplied multi-repository manifest.
- Use `$aquarium:dev-setup` to diagnose or configure development tooling and repository operating guidance.
- Use `$aquarium:docs-setup` to audit, establish, adopt, or migrate canonical documentation structure and roadmap IDs.
- Use `$aquarium:test-setup` to audit or configure the common Make or Bun testing contract and evidence-backed legacy waivers.
- Use each installed paired `$use-*` skill for its corresponding local tool operations and keep tool-specific lifecycle rules in that integration's canonical contract.
- Aquarium is an orchestration plugin that helps integrated tools work together and makes their supported native capabilities readily usable. It is not a policy layer for weakening, second-guessing, or artificially constraining those tools.
- Prefer each tool's current native contract and paired skill. Use the supported capabilities needed for the approved goal; do not invent Aquarium-only owners, quotas, retry caps, evidence caps, lifecycle restrictions, or extra approval gates.
- A tool limitation must come from a higher-priority instruction, Master's explicit choice, repository authority, the tool's native contract, or a concrete safety, destructive-action, privacy, or external-mutation boundary. Otherwise remove the Aquarium-only restriction at its canonical contract instead of working around or disabling the native capability.
- Treat `.podway/procedures/aquarium-*-v2.yaml` as the repository-local workflow evidence and routing authority.
- Use `$lore-commits` for non-trivial commit messages and `$lore-query` to inspect recorded decision context.
- Use the separately installed upstream `$deslop` skill for task-owned cleanup when an Aquarium workflow requests it.

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
- `tests/validate.rb` checks cross-skill, procedure, documentation, and release-contract invariants. Python pytest unit and E2E tests cover isolated logic and black-box inspector scenarios; the approved legacy `unittest` integration suites cover executable inspection, commit-gate, and bundle-normalization boundaries.
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

- Aquarium does not vendor third-party Lora, Lore, Ouroboros, or Deslop sources. Preserve the exact-upstream installation and provenance boundaries in `dev-setup`.
- Do not create `.aquarium` or another central project-state file. Bundle manifests are explicit external inputs, not repository discovery or persisted state.
- Preserve approval boundaries between diagnosis, network lookup, installation, native configuration, repository guidance, staging, commits, and publication.
- Green phrase or schema validators prove only their bounded contracts. Add scenario-focused coverage when changing cross-skill handoffs or approval behavior.
- Treat ignored Mulgae, Gaori, Podway, and disposable runtime artifacts as local workflow evidence, never tracked documentation authority. Promote only reviewed bounded non-sensitive structured evidence under the shared Aquarium evidence-residency contract when a durable downstream reference is necessary. Declare a custom root only with the exact Project Configuration entry `Aquarium evidence root: <repository-relative-path>`; otherwise use `evidence/aquarium/`.
- Preserve unrelated staged, unstaged, and untracked work. Do not include local runtime state or setup manifests in a task unless Master explicitly puts them in scope.

### Release Policy

When Master asks to release `main`, use `$aquarium:release-handler` and establish the release mode before making release changes. Ask whether to use `full` or `light` unless Master already selected one explicitly. If Master did not provide a version, propose the open CHANGELOG version and obtain confirmation before changing version metadata.

Before release QA, reconcile every material change after the previous release with the open CHANGELOG section and obtain approval for any entry addition, merge, edit, or removal. Commit that exact preparation through `$aquarium:task-commit`, then run a new release-qa pass against the resulting clean exact candidate. After release QA passes, preserve entry text byte-for-byte; a substantive note edit creates a new candidate and requires release QA again.

Before either mode, inspect the worktree, the local and remote `main` commits, the exact release-candidate SHA, and existing tags and GitHub Releases. Stop on unrelated worktree changes, an ambiguous release target, or a conflicting tag or release rather than including or overwriting it.

When the open release requires Podway v0.2.7 compatibility, verify the official Apple Silicon archive against its published checksum and run this additional exact-artifact gate before release QA:

```bash
PODWAY_BIN=<absolute-path-to-extracted-v0.2.7-podway> make test-podway-compat
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
