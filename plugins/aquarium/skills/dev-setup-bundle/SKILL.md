---
name: dev-setup-bundle
description: "Apply Aquarium development-tool setup across multiple Git repositories from one external YAML manifest. Use when the user explicitly invokes $aquarium:dev-setup-bundle with a manifest path. Do not use for single-repository setup or implicit workspace discovery; use $aquarium:dev-setup."
---

# Development Setup Bundle

Apply the existing `dev-setup` contract to an explicit ordered set of Git repositories without turning the manifest into project state or widening any installation approval.

Read [manifest.md](references/manifest.md), then read [the development setup skill](../dev-setup/SKILL.md). Read only the selected sections of [the tool catalog](../dev-setup/references/tool-catalog.md) after the manifest is normalized.

## Normalize Before Discovery

1. Require an explicit manifest path. Require Python 3.10 or newer and PyYAML 6.x, resolve this skill's directory, and run `python3 <skill-directory>/scripts/normalize_manifest.py --manifest <path>`. If either runtime dependency is missing or unsupported, stop before network access or mutation; do not install or upgrade either dependency as a side effect and do not parse the manifest approximately.
2. Treat a nonzero result or an error envelope as a manifest-wide failure. Treat an `invalid` target in a successful plan as an isolated preflight failure and continue with the remaining `ready` targets.
3. Never create, copy, edit, stage, or commit the manifest. Keep its absolute path and SHA-256 only for this request. Do not discover manifests, repositories, or tools outside the normalized plan.
4. For every ready target, read applicable repository instructions and inspect branch, upstream, staged, unstaged, untracked, and conflict state. Preserve unrelated work. If an approved change overlaps existing work and cannot be applied exactly, fail that action for that target instead of overwriting it.
5. Run the existing `inspect_tools.py` once for each ready target with `--include-podway`, `--include-ouroboros`, and `--require-mulgae-mcp` only when the normalized selection requires those dimensions. Inspection is read-only evidence, not setup authority.

## Confirm the Normalized Selection

Show the manifest digest and an ordered matrix of ready and invalid targets, input paths, canonical Git roots, effective tools, project MCP selections, AGENTS.md proposal policy, worktree state, and local readiness. Disclose that confirming a selection containing Sanho, Mulgae, Gaori, or Podway authorizes the bounded official GitHub Releases and raw-file freshness comparison defined by `dev-setup`, but no installation or replacement.

Use the host's structured ask/answer tool when available to confirm the normalized selection before any network comparison. A refusal stops the bundle without mutation. Confirmation is not approval for a CLI, skill, daemon, configuration, MCP registration, managed Procedure, AGENTS.md edit, or any other persistent action.

Immediately before that confirmation, rerun the normalizer and require the manifest digest, target order, canonical repositories, and selections to match. Any change invalidates the displayed selection and requires a new preflight.

## Prepare Shared Components Once

Resolve the union of effective tools across ready targets. Compare each selected Sanho, Mulgae, Gaori, or Podway paired skill once and reuse the verified exact tag, file set, digests, and ephemeral payload throughout this bundle request. Resolve other approved upstream sources once. Never refetch merely because another target selects the same tool.

Handle user-global CLIs, paired skills, Lora, Deslop, the Podway daemon, and Ouroboros package, Codex, and runtime components before repository-local actions. Follow every distinct proposal, backup, approval, stale-target check, checksum, version, and verification boundary in `dev-setup`; a bundle selection never groups or waives them.

If a shared action fails or is declined, mark every dependent target `partial`, `failed`, or `declined` as appropriate, but continue actions and targets that do not depend on it. Keep the verified payload until its last applicable action, then remove it as required by `dev-setup`.

## Configure Targets in Order

Process ready targets in manifest order. Pass `dev-setup` a normalized bundle handoff containing the requesting skill, manifest digest, target index, canonical Git root, effective tools, project MCP selection, and AGENTS.md policy. Never pass the manifest path or ask `dev-setup` to read it.

Use the normalized tools as `Install and configure` selections and the normalized project MCP and AGENTS.md values as preselected choices. Still show and separately approve every exact persistent action required by `dev-setup`. Ask only for identifiers that repository state and the manifest selection cannot supply, such as a new Sanho project name or documentation repository URL.

An unexpected failure, declined action, lifecycle conflict, or overlapping worktree change affects only that action and its dependent readiness. Record the actual state and continue with the next independent action or target. Do not roll back successful actions automatically, retry an unchanged failed mutation, stage, commit, push, invoke providers, start reviews or tests, or activate a Podway workflow.

Before the first mutation and before each later target, rerun the normalizer and require the original manifest digest and normalized target identity to match. A manifest change stops all remaining work and requires a fresh invocation.

## Report the Bundle

Report shared actions once, then every target as `ready`, `partial`, `failed`, `declined`, or `skipped`. Include commands and exit status, changed native paths, verification evidence, preserved worktree state, unmet dependencies, failure or refusal reasons, cleanup status, and the exact next request needed to resume each unfinished target. State staging, commit, push, and publication status separately.
