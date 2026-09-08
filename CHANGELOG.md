# Changelog

This file records concise shipped outcomes and the planned next stable release.

## v0.1.15 - Unreleased

### Added

- Add optional Sorage v0.1.x setup support for exact-release CLI and paired-skill diagnosis, minimal local initialization, approved Git repository registration, derived-marker ignore safety, bundle selection, and repository guidance.
- Add `dev-setup-global` for automatic user-global CLI, skill, service, MCP, and Ouroboros diagnosis and updates.

### Changed

- Raise the minimum Dolgorae version to v0.1.2, consume version JSON and machine envelope v2, add same-release `use-dolgorae` setup, and use global Codex Profiles. Delegate review lifecycle and reusable Specialist Engagement operations to the upstream skill and remove the Aquarium-only review deadline, byte, and artifact ceilings.
- Replace the `aquarium-dev` skill with bundled MCP tools and a shared CLI runtime, with explicit installation and updates through `dev-setup-global`, stable Git-hook entrypoints, and preserved development-channel approvals.
- Raise the minimum Podway runtime to v0.2.9 and pin `use-podway` independently to commit `9014225982e4c316237e0d6e35052414d2dbc770` for context recovery and independent Codex goal coordination. Require successful UUID-fenced workspace-removal replay in the v5 compatibility receipt.
- Raise the minimum Mulgae version to v0.1.19 and consume command-result v6.
- Delegate Gaori and Mulgae asynchronous lifecycles to their upstream skills.
- Separate execution completion from evidence quality and approval.
- Count exact composite recovery within its original review round.
- Raise the minimum Gaori version to v0.1.16, preserve asynchronous MCP awaiting during timing queries, diagnose the optional `use-gaori-status` skill independently, and support Experimental Dart and Patrol parser selection from verified commands.
- Make `dev-setup` automatically diagnose evidenced repository configuration, propose only necessary changes, and retain ownership of root AGENTS.md and CLAUDE.md while trusting canonical global skill presence.
- Make general `dev-setup` review and reorganize complete agent guidance around seven core behaviors, preserving project-specific constraints and honoring tool-limited requests, diagnosis-only requests, and explicit guidance exclusions.
- Preserve setup bundle v1 while preparing global components once and applying repository configuration in target order.

### Fixed

- Schedule new-project test setup after executable product behavior exists and stop setup when implementation prerequisites are missing.
- Install and diagnose Ouroboros integrations independently in each Codex home, with per-home MCP binding and readiness plus supported-version upgrade guidance.
- Allow all Orca reviewers to write review-related files outside the current worktree without output-location warnings or failed reviews, while preserving worktree and Git protections.
- Wait for development-build request admission in generated `post-commit` hooks before returning, keep request failures visible, and detach only the build worker. Preserve queued requests when worker launch fails and support migration of recorded background-request hooks through approved re-enrollment. Producer probes now time out, non-main hooks skip requests, legacy hooks report outdated, and approved recovery clears matching queued requests. Queue and diagnostic storage errors preserve structured failure reporting.
- Make post-remediation release QA confirmation artifacts immutable, compute each verdict from the submitted evidence bytes bound to its admission, reject malformed admissions and overlong terminal basenames deterministically, and preserve recovery across reordered scenarios, output-parent aliases, pre-admission claim receipts, pending settlement inspection, and transient helper failures without reopening an admitted attempt.

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
