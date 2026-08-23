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

### 3. Make Surgical Changes

- Touch only what the requested outcome and its verification require.
- Do not refactor, reformat, rename, or clean up adjacent code unless the task requires it.
- Match local style and preserve unrelated user work in a dirty worktree.
- Remove imports, files, references, or documentation made obsolete by the current change, but leave pre-existing unrelated cleanup alone.

### 4. Work Toward Verifiable Goals

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
- Use `$aquarium:war-room` for difficult-bug diagnosis and `$aquarium:design-qa` for local Design Gate lifecycle work.
- Use `$aquarium:release-qa` for exact release-candidate verification and `$aquarium:dev-setup-bundle` only with an explicitly supplied multi-repository manifest.
- Use `$aquarium:dev-setup` to diagnose or configure development tooling and repository operating guidance.
- Use `$aquarium:test-setup` to audit or configure the common Make or Bun testing contract and evidence-backed legacy waivers.
- Use `$use-sanho`, `$use-mulgae`, `$use-gaori`, and `$use-podway` for their respective local tool operations. Aquarium workflow skills retain their stricter roadmap, ownership, and approval rules.
- Treat `.podway/procedures/aquarium-*-v2.yaml` as the repository-local workflow evidence and routing authority.
- Use `$lore-commits` for non-trivial commit messages and `$lore-query` to inspect recorded decision context.
- Use the separately installed upstream `$deslop` skill for task-owned cleanup when an Aquarium workflow requests it.

## Project Configuration

### Repository Index and Authorities

- `plugins/aquarium/.codex-plugin/plugin.json` owns published plugin metadata and the release version.
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

When Master asks to release `main`, establish the release mode before making release changes. Ask whether to use `full` or `light` unless Master already selected one explicitly. If Master did not provide a version, propose the next patch version and obtain confirmation before changing version metadata.

Before either mode, inspect the worktree, the local and remote `main` commits, the exact release-candidate SHA, and existing tags and GitHub Releases. Stop on unrelated worktree changes, an ambiguous release target, or a conflicting tag or release rather than including or overwriting it.

#### Full Release

Update the plugin manifest version and its pinned validation expectation, then run the complete applicable local release gate:

```bash
RELEASE_TAG=v<version> make test
git --no-pager diff --check <previous-release-tag>
```

Also verify that a deliberately mismatched `RELEASE_TAG` is rejected, and run any additional repository-required or change-specific checks. Do not commit or publish when a required check fails or cannot be completed.

#### Light Release

Before changing version metadata, show the exact current release-candidate HEAD SHA and ask whether Master has confirmed the required test results for that SHA. Proceed only after an explicit positive answer. If HEAD or functional code changes after that confirmation, obtain confirmation again or switch to a full release.

A light release may change only release metadata: the plugin manifest version and its pinned validation expectation. Validate only that release delta locally:

```bash
python3 -m json.tool plugins/aquarium/.codex-plugin/plugin.json >/dev/null
ruby -c tests/validate.rb
RELEASE_TAG=v<version> ruby tests/validate.rb
git --no-pager diff --check <previous-release-tag>
```

Do not rerun the full Python unit suite or lint unchanged Python files locally in light mode. The release-tag validation is the basic release-contract check. If preparing the release requires functional code changes, stop light mode and ask Master to choose full verification or provide fresh test confirmation for the new candidate.

#### Publication

After the selected local gate passes, create one `[REL] Release v<version>` commit. Push `main` first, then create and push an annotated `v<version>` tag and create the GitHub Release. Finally verify that remote `main`, the tag, and the GitHub Release resolve to the intended release commit.

The selected local gate is the release validation authority; this repository does not use GitHub Actions. Do not rewrite or delete a published tag without explicit authorization from Master. A light release reduces duplicated local execution but does not weaken its required local checks or publication-order safeguards.
