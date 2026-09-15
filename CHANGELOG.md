# Changelog

This file records concise shipped outcomes and the planned next stable release.

## v0.1.16 - Unreleased

### Changed

- Raise the minimum Sanho version to v0.2.8, adopt its conflicted-sync content-retention fix, and install and verify the complete five-file `use-sanho` skill tree.
- Require explicit `Contract:` and `Profile:` fields for `TESTING.md` enrollment; repositories using prose-only enrollment must add both fields.
- Classify Codex MCP registration from its structured named lookup and bounded inventory instead of diagnostic stderr wording.
- Read each Dolgorae release identity from its authoritative structured source while tolerating ordinary release-note Markdown around the contained executable digest.
- Keep Orca change reviews proportional to the target: focus findings on concrete current defects, follow only plausible affected paths, and stop without auditing unrelated or pre-existing issues; style preferences, speculative risks, and verification gaps do not block approval by themselves.
- Raise the minimum Gaori version to v0.1.17, accept its simplified version JSON without commit identity, and install and verify the complete seven-file `use-gaori` skill tree.
- Align canonical and public review documentation with enabled Mulgae and Orca behavior, disabled Independent Review, and the host-limited native Codex subagent alternative.
- Align Orca Dispatch and result handling with the shared Review Brief, and define report-only guidance for an explicitly selected host-native Codex subagent review.
- Require embedded task, member-goal, and whole-epic Mulgae reviews to assess every actual requirement as met, unmet, unverified, or not applicable, and prevent approval or Low-finding settlement from bypassing semantic completion gaps or inconsistent finding totals.
- Add a report-only standalone Mulgae Review entrypoint for exact change targets and named Task or Epic completion candidates, using the shared review-intent contract and every accepted role report.
- Temporarily disable Dolgorae-based Independent Review before setup or source transmission, guide users to explicitly selected native Codex or Orca alternatives, and make Dolgorae optional for common production readiness.
- Raise the minimum Mulgae version to v0.1.21 and consume command-result v8. Adopt retained failed-review recovery, stage-specific provider rate-limit handling, and ZCode-only automatic initialization.
- Align all managed Podway Procedures and their owning skills around finite Low-finding settlement: preserve historical review facts, require current local verification, and proceed to assessment without another provider review solely to reduce a past Low count.
- Separate Podway native Procedure validity from Aquarium handler compatibility during repository setup while preserving same-ID customizations and immutable active-session snapshots.
- Replace the deprecated Aquarium for Kimi edition link with Aquarium for Grok.
- Require Sorage v0.1.1 or later in the v0.1 line; run `$aquarium:dev-setup-global` to update an installed v0.1.0 CLI and its same-tag `use-sorage` skill.
- Route explicitly requested broker operations through the paired skill, including Review Note reads before sender revision and bounded event timeline reads when needed.
- Require `.sorage/` in the repository root `.gitignore`; repositories that relied only on `.git/info/exclude`, a nested `.sorage/.gitignore`, or a global excludes file must add the root rule before Sorage setup is ready.
- Require an explicit Project setup request before `$aquarium:dev-setup` proposes Sorage Project registration; Project listing and mutation retain their separate approval boundaries.
- Remove automatic session-start and pre-task Sorage discovery; rerun `$aquarium:dev-setup` to refresh repository guidance written by an earlier Aquarium version.

### Fixed

- Preserve completion evidence through final task, goal, and validation assessment, and reconcile review provenance, omission handling, and disabled Independent Review alternatives.
- Allow Orca reviewers to write Git-ignored runtime files such as those under `.omc/` without warnings, extra checks, or approval requests.

- Keep Aquarium plugin installation and update requests in the host plugin-management flow without loading `dev-setup-global` or running global tool diagnostics.
- Recognize and install `humanize-korean` under `~/.agents/skills/` regardless of `CODEX_HOME`.
- Separate Orca review findings from operational deviations and withhold technical verdicts when review trustworthiness is compromised or cannot be established.

## v0.1.15 - 2026-09-08

### Added

- Add optional Sorage v0.1.x setup with exact-release CLI and paired-skill diagnosis, approved repository registration, derived-marker ignore safety, and bundle support.
- Add `dev-setup-global` for user-global CLI, skill, service, and MCP diagnosis and updates, including independent Ouroboros installation and readiness checks for each Codex home.

### Changed

- Raise the minimum Dolgorae version to v0.1.2 with machine envelope v2, same-release `use-dolgorae`, and global Codex Profiles, delegating reviews and Specialist Engagements to the upstream skill without Aquarium-only deadline or artifact limits.
- Replace the `aquarium-dev` skill with bundled MCP tools and a shared CLI, installed and updated explicitly through `dev-setup-global` while preserving stable Git-hook entrypoints, development-channel approvals, and runtime diagnosis isolated from caller modules.
- Raise the minimum Podway runtime to v0.2.9 with successful UUID-fenced workspace-removal replay, and pin `use-podway` independently to `9014225982e4c316237e0d6e35052414d2dbc770` for context recovery and independent Codex goal coordination.
- Raise the minimum Mulgae version to v0.1.19, consume command-result v6, and keep exact composite recovery within its original review round.
- Delegate Gaori and Mulgae asynchronous lifecycles to their upstream skills while assessing execution completion, evidence quality, and approval separately.
- Raise the minimum Gaori version to v0.1.16 with asynchronous timing queries, independent diagnosis of optional `use-gaori-status`, and Experimental Dart and Patrol parser selection from verified commands.
- Make `dev-setup` diagnose repository configuration and reorganize agent guidance around seven core behaviors, trusting canonical global skills while preserving project constraints and explicit limits on setup or guidance changes.
- Keep setup bundle v1 compatible while preparing global components once and configuring repositories in target order.

### Fixed

- Schedule new-project test setup after executable product behavior exists and stop setup when implementation prerequisites are missing.
- Make `test-setup` inspection accept equivalent command syntax and `TESTING.md` declarations, respect Make variable assignment timing, and report uncertainty only for behavior it cannot establish.
- Allow all Orca reviewers to write review files outside the current worktree while preserving worktree and Git protections.
- Make `post-commit` hooks wait for development-build request admission, preserve queued requests and visible failures when workers cannot start, and support migration of legacy hooks through approved re-enrollment.
- Bind release QA confirmation verdicts to immutable admitted evidence, revalidate terminal results on exact retries, reject invalid submissions, and recover interrupted settlement without reopening the single permitted attempt.

## v0.1.14 - 2026-09-04

### Added

- Add the production-isolated `aquarium-dev` channel for clean local-main artifacts, with explicit enrollment, immutable generations under `~/.aquarium-dev`, the caller's environment, per-tool foreground fallback, and fail-closed managed services.
- Add official Dolgorae v0.1.1 support as the minimum Apple Silicon runtime for setup diagnosis and checksum-bound Independent Review, while accepting compatible stable v0.1.x releases.
- Add exact-upstream Humanizer and im-not-ai installation, inspection, bundle selection, and opt-in English and Korean repository guidance.

### Changed

- Require execution dossiers only for epics with at least three member tasks or three requirement-bearing canonical documents, and retain shared dossiers until the final consumer closes.
- Raise the minimum supported Podway version to v0.2.8, adopt named-mode daemon readiness v3, qualify managed Procedures and fenced workspace removal against the official artifact, and require explicit authorization for runtime-mode changes.
- Apply one finding-disposition contract across Independent Review, Mulgae, and Orca Review, with mandatory correction and re-review for Medium-or-higher issues and explicit dispositions for Low issues.

### Fixed

- Pin roadmap commit authors and committers to repository-local or worktree Git identities instead of falling back to system or global identities.
- Let Orca Review inspect staged changes directly in the registered worktree with the requested native reviewer, while restricting Claude's native output to `~/.claude`.

## v0.1.13 - 2026-08-28

### Removed

- Remove `design-qa` and its Design Gate coupling from design, delivery, and validation workflows.

## v0.1.12 - 2026-08-27

### Added

- Add maintainer documentation for Aquarium's implemented capabilities, architecture, decisions, operations, and implementation guidance.
- Add an isolated official Podway v0.2.6 compatibility gate covering both released binaries, every canonical Procedure, and Aquarium lifecycle seams.

### Changed

- Let Aquarium workflows use native tool capabilities without skill-owned sessions or unsupported orchestration limits.
- Extend docs-setup with governed roadmap and dossier lifecycles, canonical closeout, operations documentation, and conservative role- and lifecycle-vocabulary-aware structural inspection.
- Strengthen release QA and publication recovery with machine-validated frozen scenario records, exact remediation manifests, atomic one-attempt confirmation admission, clean local-main candidates ahead of remote main, resumable full gates, one approved QA-neutral direct child, and v4 ordered publication observation.
- Run Orca reviewers with provider-native auto-approval while enforcing exact repository identity and no-mutation supervision across refs, the index, tracked worktrees, submodules, and untracked content.
- Reauthor the task, goal, validation, design, and war-room Procedures for Podway v0.2.6 with typed checks, CI-aware phase-owned review routing, refined-target verification, fresh evidence handoffs, explicit approval boundaries, and reviewed preservation of valid local customizations.
- Strengthen development setup for Podway v0.2.6, isolated Ouroboros MCP runtimes, and structurally valid but upstream-unverified Deslop installations.

### Fixed

- Fix the Kimi and GLM edition links in the English and Korean project READMEs.

## v0.1.11 - 2026-08-25

### Added

- Add canonical documentation governance and roadmap identity setup with `docs-setup`.
- Add cumulative release notes and a governed `release-handler` lifecycle.

### Changed

- Add Aquarium edition links to the English and Korean project READMEs.
- Keep runtime evidence outside canonical documentation and tracked workflow records.
- Align development setup with Mulgae v0.1.18.
- Make repository guidance prefer durable root-cause solutions and route deferred work through canonical documentation owners.
- Unify independent review targets across staged changes, commits, ranges, roadmap work, and special investigations.

### Fixed

- Fix macOS release QA fixture isolation.
- Fix docs-setup roadmap alias, legacy ID, task status, cross-scope reference, migration record, and preserved-path validation.
- Revalidate Orca provider identity at process start and enforce the exact Git-root boundary.
- Require separate approval before executing release gates.
- Reject noncanonical Mulgae and Go version strings during dev-setup inspection.
- Allow Orca Review to use verified installed launchers safely.
- Allow review target and provider selection to fall back to an explicit conversation when structured UI is unavailable.

## v0.1.10 - 2026-08-23

### Added

- Add supervised Orca review and a common Make and Bun testing contract with evidence-backed legacy waivers.

### Changed

- Namespace Aquarium under the Root Kernel marketplace and refresh its AI Fleet product and distribution identity.
- Strengthen commit gating, tool inspection, consent checks, and bounded review lifecycle settlement.
- Add one-attempt five-cluster confirmation to stop automatic release QA hardening loops.
