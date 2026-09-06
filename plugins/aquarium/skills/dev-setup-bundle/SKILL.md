---
name: dev-setup-bundle
description: "Apply Aquarium global and repository development setup across explicit Git repositories. Use when the user explicitly invokes $aquarium:dev-setup-bundle with an aquarium.dev-setup-bundle/v1 manifest path. Do not use for one repository or implicit workspace discovery."
---

# Development Setup Bundle

Normalize one explicit external manifest, prepare its user-global components once through `$aquarium:dev-setup-global`, and configure repository components in target order through `$aquarium:dev-setup`.

Read [manifest.md](references/manifest.md), [the global setup skill](../dev-setup-global/SKILL.md), [the repository setup skill](../dev-setup/SKILL.md), and only the selected sections of [the shared tool catalog](../../references/tool-catalog.md).

## Normalize and Confirm

1. Require an explicit manifest path, Python 3.10 or newer, and PyYAML 6.x. Resolve this skill's directory and run `python3 <skill-directory>/scripts/normalize_manifest.py --manifest <path>`. Do not install dependencies or parse the manifest approximately.
2. Never create, copy, edit, stage, or commit the manifest. Preserve its absolute path and SHA-256 only for this request.
3. Inspect applicable instructions and worktree state for every ready target. Invalid targets remain isolated failures.
4. Show the normalized digest, ordered targets, effective tools, local MCP overrides, guidance policy, and worktree state. Confirm this exact selection before its authorized network comparisons or Sorage diagnostic side effects. A refusal stops the bundle without mutation.
5. Immediately before confirmation and before the first mutation or each later target, rerun normalization and require the original digest and target identities to match. A mismatch stops all remaining work and requires a fresh invocation.

Confirmation authorizes only the global skill's documented bounded official metadata and raw-file reads plus disclosed non-network Sorage diagnostics outside Plan Mode. It never authorizes installation, replacement, initialization, repository mutation, Handoff access, staging, commit, or publication.

## Prepare Global Components Once

Pass the normalized `shared_tools` union, manifest digest, and requesting skill to `$aquarium:dev-setup-global`. The global skill maps each union member to one `--component <name>` inspector argument and runs no component outside that union. This preserves `aquarium.dev-setup-bundle/v1`: existing tool names continue to select both their global and repository portions where applicable.

Prepare each selected global CLI, paired skill, global MCP registration, daemon, Sorage initialization, third-party writing or Lore skill, and Ouroboros component at most once. For Ouroboros, this means one CLI upgrade and one integration update per distinct discovered Codex home, not one installation per repository. Preserve every exact proposal, backup, approval, stale-target, verification, and cleanup boundary from `dev-setup-global`.

If a shared action fails or is declined, record the dependent targets as partial, failed, or declined while continuing independent components and targets.

## Configure Targets in Order

For each ready target, pass `$aquarium:dev-setup` the requesting skill, manifest digest, target index, canonical Git root, complete effective tool list, explicit local MCP overrides, and guidance policy. The repository skill interprets the list as target intent and never repeats global installation or freshness work.

- Process only repository portions: workspace/configuration readiness, project MCP, Sorage Project binding and ignore state, Podway managed Procedures, and AGENTS.md/CLAUDE.md guidance.
- `agents_guidance: propose` requests the complete repository guidance proposal. `skip` suppresses that proposal. Effective Humanizer and im-not-ai selections still determine target-specific writing rules without repeating their global setup.
- Ask only for identifiers or conflicts that repository evidence and the manifest cannot decide. Do not ask each target to select install, diagnose, or skip.
- In Plan Mode, defer Sorage doctor and Project resolution because their native migration path may write local state. Outside Plan Mode, disclose the bounded side effect before running the selected target diagnosis.
- Do not roll back successful actions, retry unchanged failures, stage, commit, push, invoke providers, start reviews or tests, or activate a Podway workflow.

## Report

Report global actions once, then every target as `ready`, `partial`, `failed`, `declined`, or `skipped`. Include the manifest digest, commands and exits, changed paths, verification, preserved worktree state, unmet dependencies, cleanup, and exact resumption requests. State staging, commit, push, and publication separately.
