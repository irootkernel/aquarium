---
name: dev-setup
description: "Diagnose and configure Aquarium repository-local tooling and root agent guidance. Use when the user invokes $aquarium:dev-setup or asks to initialize, repair, or audit project configuration such as .podway, .mulgae, .gaori, Sorage binding, project MCP, AGENTS.md, or CLAUDE.md. Use $aquarium:dev-setup-global for supported user-global development tool installation or updates. Aquarium plugin installation and updates belong to the host plugin-management flow."
---

# Repository Development Setup

Diagnose the repository first, propose only changes supported by repository evidence, and leave supported user-global development tool installation and updates to `$aquarium:dev-setup-global`. Route requests to install or update only the Aquarium plugin directly to the host's plugin-management flow without repository or global setup diagnosis.

This skill owns root AGENTS.md and CLAUDE.md guidance. A general setup always reviews the complete guidance against the standard structure and behavior, then proposes a full reorganization where needed. `$aquarium:docs-setup` owns documentation structure and roadmap identity.

Read [podway-integration.md](../../references/podway-integration.md) only when Podway is selected by the request, repository guidance, or an Aquarium readiness requirement. Read the applicable sections of [the shared tool catalog](../../references/tool-catalog.md) for every repository component in scope. Read [agents-guidance.md](references/agents-guidance.md) whenever root operating guidance is in scope.

Do not use this skill for routine supported Procedure v2 observation, cancellation, discard, reset, or workspace runtime-mode moves. Route those operations to `$use-podway`. Keep repository initialization, managed Procedure readiness, product-rename migration, and `LEGACY_PROCEDURE_STATE_UNSUPPORTED` recovery here.

## Establish Scope From Evidence

1. Resolve the requested working directory to one Git root and inspect applicable instructions, branch, upstream, staged, unstaged, untracked, and conflict state.
2. Resolve this skill's directory and run `python3 <skill-directory>/scripts/inspect_tools.py --repository <git-root>`, adding only the flags required for repository components selected by explicit request, repository files or guidance, or an Aquarium readiness contract. Add `--include-podway` for Podway readiness, `--include-sorage` for the disclosed Sorage readiness diagnostic, and `--require-mulgae-mcp` when repository authority requires Mulgae MCP readiness to affect status.
3. Select only evidenced repository components: Sanho workspace state; Mulgae Config v3, local configuration, bootstrap or refresh, and project MCP; Gaori repository config, active rules, ignore policy, and project MCP; Sorage Project binding and `.sorage/` ignore or tracking safety; Podway workspace, managed Procedures, migrations, and legacy recovery; and root AGENTS.md and CLAUDE.md operating guidance.
4. Treat an absent optional tool component with no repository evidence as out of scope, not missing. An explicit component request adds that component to scope. General setup includes root guidance even when the files are absent. A request limited to a tool or a scoped continuation stays within that component and its direct prerequisites; it does not add a full guidance review. Honor explicit guidance exclusions, including bundle `agents_guidance: skip`.
5. Never ask the user to choose `Install and configure`, `Diagnose only`, or `Skip`, and never ask whether to `Show proposal`, `Diagnose only`, or `Skip`. Diagnosis is automatic. For tool configuration, report no change when ready and otherwise prepare the smallest exact proposal. For guidance, follow the whole-file review below.

If Python is unavailable or inspection fails, report the gap and perform the same read-only discovery manually. Do not install Python as a side effect.

Never read credential values or open `.env*`, authentication, key, token, secret, or credential files. Use repository authorities, safe placeholders, and redacted native readiness only. Do not create or read `.aquarium` or another central selection file.

## Trust Canonical Global Installations

This skill may inspect an owning global executable only through the bounded version, compatibility, and readiness probes required to diagnose a selected repository component. For a canonical user-global skill path under `~/.agents/skills`, or the active canonical Codex skill root where an upstream contract requires it, check only whether the path exists. Do not read its files, validate frontmatter, follow or reject symlinks, hash content, enumerate duplicates, contact upstream, or ask about installation or freshness.

Existence here means the repository workflow may use the global skill. Exact tree safety, provenance, duplicate detection, exact-upstream compatibility, and freshness belong exclusively to `$aquarium:dev-setup-global`.

Stop the dependent proposal when a required global executable or canonical skill path is absent, the owning CLI reports an incompatible runtime, a required user-global MCP registration is missing or degraded, a required user-global service such as the Podway daemon is unavailable or not ready, or selected Sorage diagnosis reports `initialization_required` or `not_initialized`.

Return an exact continuation naming `$aquarium:dev-setup-global`, the missing, incompatible, degraded, or uninitialized global component, the canonical Git root and requesting workflow, the bounded observed reason code, and the exact repository request to resume after global repair.

Do not offer to install, upgrade, replace, or compare global state from this skill.

## Respect Host Mode

In Plan Mode, run every non-mutating repository diagnostic available and return exact proposed repository diffs or actions only for verified gaps. Never mutate files or native state. A diagnostic such as Sorage Project resolution that may open and migrate local state is deferred as an execution-phase prerequisite and must not become a question merely because it cannot run in Plan Mode.

Outside Plan Mode, use the same automatic discovery. Before each persistent action, show the exact command or complete diff, target paths, side effects, preserved state, verification, and backup policy when replacement or removal is involved. Establish `Choose a Backup Policy for Existing State` from the shared tool catalog before the first action-specific approval for an overwrite or removal, then obtain the action-specific approval required by the host. Re-read every target immediately before an approved mutation and invalidate stale approval.

An explicit diagnosis-only request suppresses mutation proposals. A scoped continuation inspects only the named repository component and its direct prerequisites.

## Configure Repository Components

- Preserve the existing Sanho workspace, Mulgae, Gaori, Sorage, and Podway version, validity, approval, backup, and verification rules in the shared catalog, but apply only their repository-local portions.
- Prefer global Mulgae and Gaori MCP registrations as prerequisites. Create, change, or remove a project-local registration only when the user explicitly requested local scope or repository authority already requires it. Preserve unrelated Codex configuration.
- For Sorage, do not run doctor or Project resolution in Plan Mode because native open-and-migrate paths may write local database or journal state. Outside Plan Mode, disclose those bounded diagnostic side effects before the automatic selected-component diagnosis. Initialization remains global; Project add, bind, unarchive, and repository ignore changes remain local and separately approved.
- For Podway, preserve custom same-ID Procedures that Podway validates, show exact canonical replacement diffs, and keep session lifecycle and runtime-mode changes outside setup. Managed-Procedure removal and legacy reset retain their destructive-action approvals.
- Never stage, commit, push, authenticate a provider, transmit source, start a review or test, or invoke a workflow as part of setup.

## Reconcile Repository Guidance

Review the complete AGENTS.md and CLAUDE.md during general setup or an explicit guidance request. Reuse verified repository facts while assessing structure, behavior, duplication, and project-specific constraints. An explicit diagnosis-only request reports findings without drafting a proposal.

When a change is needed:

1. Preserve the meaning of repository-specific rules, applicable stricter constraints, unrelated content, and tool-managed blocks. Resolve actual semantic conflicts with the user.
2. Reorganize the full instruction body around the standard in `agents-guidance.md`, including its seven core behaviors and mandatory commit-message authority. Rewrite and consolidate common prose, move rules to their proper sections, and remove duplication; do not limit the proposal to small additions or preserve the old arrangement for its own sake.
3. Include tool references only for evidenced repository integrations and canonical global skills that exist. Do not inspect those global skill contents.
4. Show one complete combined AGENTS.md and CLAUDE.md diff.
5. Apply only that exact diff under authorization that covers it and after a fresh target snapshot check. Use existing approval when it covers the displayed changes; otherwise obtain approval once.

When the full review establishes that both files already satisfy the standard in structure and meaning, report no change. Equivalent wording does not require a rewrite. Guidance approval never authorizes tool setup, staging, commit, or publication.

## Bundle and Continuation Intake

A `dev-setup-bundle` handoff must name the requesting skill, manifest digest, target index, canonical Git root, effective tools, explicit local MCP overrides, and repository-guidance policy. Accept the full effective tool list only as target intent: process repository components and guidance here, while the bundle owner sends the global union once to `$aquarium:dev-setup-global`.

Reject unsupported tools, invalid local MCP overrides, or any request to read the manifest. Preserve per-target partial failure and return `ready`, `partial`, `failed`, `declined`, or `skipped` with an exact resumption request.

## Report

Report selected and out-of-scope repository components, diagnostic evidence, proposed or completed repository changes, deferred side-effectful diagnostics, global continuation gaps, verification, preserved worktree state, and whether staging, commit, or publication occurred. Do not report a global component as current or exact-upstream-verified; that claim belongs to `$aquarium:dev-setup-global`.
