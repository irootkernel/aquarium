---
name: dev-setup-bundle
description: "Apply Aquarium global and repository development setup across explicit Git repositories. Use when the user explicitly invokes $aquarium:dev-setup-bundle with an aquarium.dev-setup-bundle/v2 manifest path. Do not use for one repository or implicit workspace discovery."
---

# Development Setup Bundle

Normalize one explicit external manifest, prepare its user-global components once through `$aquarium:dev-setup-global`, and configure repository components in target order through `$aquarium:dev-setup`.

Read [manifest.md](references/manifest.md), [the global setup skill](../dev-setup-global/SKILL.md), [the repository setup skill](../dev-setup/SKILL.md), and only the selected sections of [the shared tool catalog](../../references/tool-catalog.md).

## Normalize and Confirm

1. Require an explicit manifest path, Python 3.10 or newer, and PyYAML 6.x. Resolve this skill's directory and run `python3 <skill-directory>/scripts/normalize_manifest.py --manifest <path>`. Do not install dependencies or parse the manifest approximately.
2. Never create, copy, edit, stage, or commit the manifest. Preserve its absolute path and SHA-256 only for this request.
3. Inspect applicable instructions and worktree state for every ready target. Invalid targets remain isolated failures.
4. Show the normalized digest, ordered targets, effective tools, target MCP scopes, Sorage slug and artist intent, guidance policy, and worktree state. Confirm this exact selection before its authorized network comparisons or Sorage diagnostic side effects. A refusal stops the bundle without mutation.
5. Immediately before confirmation and before the first mutation or each later target, rerun normalization and require the original digest and target identities to match. A mismatch stops all remaining work and requires a fresh invocation.

Confirmation authorizes only the global skill's documented bounded official metadata and raw-file reads plus disclosed non-network Sorage diagnostics outside Plan Mode. It never authorizes installation, replacement, initialization, repository mutation, Handoff access, staging, commit, or publication.

## Prepare Global Components Once

Pass the normalized `shared_tools` union, `required_global_mcp` union, manifest digest, requesting skill, and
the infrastructure component `aquarium-status` to `$aquarium:dev-setup-global`.
The global skill maps each selected name to one `--component <name>` inspector
argument and runs no other component. `aquarium-status` is common bundle
infrastructure, not a new manifest tool.

Prepare each selected global CLI, paired skill, daemon, Sorage initialization, third-party writing or Lore skill, and Ouroboros component at most once. Prepare a Mulgae or Gaori global MCP only when that name is in `required_global_mcp`; local-only targets do not depend on global MCP readiness for that tool. For Ouroboros, this means one CLI upgrade and one integration update per distinct discovered Codex home, not one installation per repository. Preserve every exact proposal, backup, approval, stale-target, verification, and cleanup boundary from `dev-setup-global`.

If a shared action fails or is declined, record the dependent targets as partial, failed, or declined while continuing independent components and targets.

## Configure Targets in Order

For each ready target, after manifest revalidation and canonical identity freeze,
read its current row through `aquarium-status show --format json` and create one
`aquarium-production-status-attempt/v1` with exactly `schema`, a new UUIDv4
`attempt_id`, that `expected_row_revision` or 0, the canonical `git_root`, the
project label equal to the canonical Git root's final NFC-normalized path
component, the UTC `started_at`, and a scoped component `scope`. Its component
list is the sorted unique effective `tools` list plus `agents-guidance` exactly
when the effective guidance policy is `propose`. A bundle target is never a
full attempt, because the manifest is an explicit component selection; this
prevents it from advancing `last_full_ready`. The
[production-status specification](../../../../docs/specs/production-status.md)
owns this closed envelope. Pass it with the requesting
skill, manifest digest, target index, canonical Git root, complete effective tool
list, effective `global_mcp` and `local_mcp` lists, `sorage_project_slug`, `mulgae_artist`, and guidance policy to `$aquarium:dev-setup`.
The repository skill interprets the list as target intent, preserves that attempt
unchanged, and never repeats global installation or freshness work.

- Process only repository portions: workspace/configuration readiness, selected project MCP, Sorage Project binding and ignore state, Mulgae artist role, Podway managed Procedures, and AGENTS.md/CLAUDE.md guidance. Compare each requested MCP scope with the effective Codex registration; a configured registration at another scope is a mismatch. Diagnose and propose a bounded correction without deleting or replacing either registration silently. An MCP omitted from both lists is unrequested, not disabled; preserve any existing registration and do not claim its tools are hidden.
- Compare an explicit Sorage slug with native Project resolution. A different binding is a mismatch requiring a separate bounded proposal; the slug grants no registration, rebind, unarchive, Handoff, or Vault authority. Compare the artist boolean with effective Mulgae roles. A mismatch requires an exact native configuration proposal under existing approval rules, without changing provider or model selection. Neither a configured registration nor a role config proves live exposure in this Codex session.
- `agents_guidance: propose` requests the complete repository guidance proposal. `skip` suppresses that proposal. Effective Humanizer and im-not-ai selections still determine target-specific writing rules without repeating their global setup.
- Ask only for identifiers or conflicts that repository evidence and the manifest cannot decide. Do not ask each target to select install, diagnose, or skip.
- In Plan Mode, defer Sorage doctor and Project resolution because their native migration path may write local state. Outside Plan Mode, disclose the bounded side effect before running the selected target diagnosis.
- Do not roll back successful actions, retry unchanged failures, stage, commit, push, invoke providers, start reviews or tests, or activate a Podway workflow.

Once a target enters `dev-setup`, accept its recording receipt only when the
attempt ID, canonical root, predecessor row revision, and resulting revisions
match the handoff contract. Never record that target a second time. If a target
settles before entry, complete and record the bundle-owned original attempt once.
The recorder's v2 receipt reports language observation separately; an
unavailable scan does not invalidate an otherwise successful setup record.
On recording failure, preserve the exact record-only retry request and never
repeat target mutations. Validate the closed recording-result fields and problem
codes against the same specification. Continue independent targets.

## Report

Report global actions once, then every target as `ready`, `partial`, `failed`, `declined`, or `skipped`. Include the manifest digest, commands and exits, changed paths, verification, preserved worktree state, unmet dependencies, cleanup, and exact resumption requests. State staging, commit, push, and publication separately.
