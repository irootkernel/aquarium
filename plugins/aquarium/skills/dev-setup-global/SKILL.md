---
name: dev-setup-global
description: "Diagnose, install, and update Aquarium user-global development tools. Use when the user invokes $aquarium:dev-setup-global or a workflow reports a missing global CLI, paired skill, global MCP registration, service, Lore, Deslop, Humanizer, im-not-ai, or Ouroboros component. Use $aquarium:dev-setup for repository-local configuration."
---

# Global Development Setup

Own user-global installation, exact-upstream freshness, upgrades, services, and global Codex integration without inspecting or changing repository configuration.

Read the selected sections of [the shared tool catalog](../../references/tool-catalog.md). Do not read repository-local `.podway`, `.mulgae`, `.gaori`, `.sorage`, `.codex`, AGENTS.md, or CLAUDE.md as global setup evidence.

## Diagnose Automatically

1. On a direct invocation without a component list, select every supported global component. On a scoped continuation, select only the named components and their direct prerequisites.
2. A direct invocation authorizes bounded read-only official metadata and raw-file freshness requests for all selected components. A scoped continuation authorizes only its selected sources. Disclose the official endpoints before contact.
3. Resolve this skill's directory and run `python3 <skill-directory>/scripts/inspect_global_tools.py --verify-dolgorae-release` on a direct unscoped invocation. For a scoped continuation, add one `--component <name>` argument for each selected component in catalog order, add `--verify-dolgorae-release` only when Dolgorae is selected, and run no unselected component probe.

   When Ouroboros is selected, also add `--verify-ouroboros-release`; pass any explicitly supplied extra homes with repeatable `--codex-home <path>`. Use the catalog's home discovery and per-home readiness contract.

   Outside Plan Mode, disclose the Sorage open-and-migrate diagnostic side effect, then add `--include-sorage-initialization` when Sorage is selected. The same disclosure applies to a scoped Sorage continuation.
4. Treat `--repository <existing-directory>` only as a compatibility input. Validate that it is an existing directory, but never use it as command or configuration scope, so diagnosis also works outside a Git worktree.
5. Diagnose local installation, supported version, canonical target, exact-upstream tree, duplicate and symlink state, paired-skill compatibility, services, global MCP, and Ouroboros integration independently.
6. Do not ask the user to choose install, diagnose, or skip. Report current components without a question and propose actions only for missing, incompatible, unsafe, duplicated, or stale components.

If a freshness lookup, download, validation, or comparison fails, report `freshness_unverifiable`, clean ephemeral payloads, and do not propose installation or replacement from that payload.

## Owned Components

- Sanho, Dolgorae, Mulgae, Gaori, Sorage, and Podway user-global CLIs.
- `use-sanho`, `use-mulgae`, `use-gaori`, `use-gaori-status`, `use-sorage`, and `use-podway` under `~/.agents/skills`.
- Mulgae and Gaori user-global MCP registrations.
- Podway's per-user production daemon and Sorage's minimal user-global initialization.
- Lora's `lore-commits` and `lore-query`, upstream Deslop, Humanizer, and im-not-ai's `humanize-korean` skill.
- Ouroboros package version, Codex rules and skills, MCP runtime, effective global registration, and live exposure when safely observable.
- The optional `aquarium-dev` CLI and MCP runtime bundled with Aquarium. Install and update it only on an explicit request; it is not part of production-binary readiness. Its MCP registration belongs to the plugin, not the global MCP table, and it has no paired skill.
- Aquarium production-binary readiness requires supported global Podway, Mulgae, Gaori, and Dolgorae executables and fails closed when any is missing. Sanho remains optional and is excluded from this baseline.

Do not install provider CLIs, authenticate, read credentials, contact providers, transmit repository source, initialize repository workspaces, change project MCP, edit repository guidance, start tests or reviews, or invoke Ouroboros workflows.

## Exact-Upstream and Update Policy

Use one exact supported release tag or disclosed full commit SHA according to the shared catalog. Verify downloaded archives, manifests, checksums, signatures, frontmatter, complete regular-file trees, and expected source provenance before proposing an action. Never install from a moving branch or execute unverified fetched content.

For each selected paired or third-party skill, compare the verified source with its canonical target. Treat missing or extra files, different bytes, invalid frontmatter, symlinks, and duplicate installations as independent gaps.

Apply this duplicate rule to shared-location skills. Ouroboros uses the per-home contract below. Other Codex skill roots remain diagnostic evidence only. When another copy exists, report the duplicate risk and never create a known duplicate. Do not propose installation at the canonical target until the user separately approves removal or migration of the alternate copy so that one canonical target remains.

`dev-setup` trusting an existing canonical path is not freshness evidence.

Ouroboros update diagnosis reports installed, latest stable, and latest supported versions. Its CLI is user-global; rules, skills, and MCP registration belong to each Codex home. Propose all discovered homes by default. Never install its skills into `~/.agents/skills` or classify valid copies in different homes as duplicates. Keep current-home readiness, all-discovered-home readiness, package freshness, and live runtime evidence separate. Never cross the supported release range automatically.

## Respect Host Mode and Approval Boundaries

In Plan Mode, perform local and network read-only diagnosis and return exact proposals without mutation. Defer Sorage doctor or initialization checks that may update its database or journal to execution mode.

Outside Plan Mode, disclose any selected Sorage diagnostic side effect before running it. Keep release lookup, archive download, executable installation, skill installation or replacement, daemon changes, Sorage initialization, global MCP changes, Ouroboros package changes, and Ouroboros setup or refresh as distinct actions.

Before every persistent action:

1. Show the exact command, endpoints, targets, changed paths, expected side effects, and verification.
2. Establish the shared backup policy before the first overwrite or removal.
3. Obtain action-specific approval. For Ouroboros, one exact proposal and approval may cover the CLI upgrade, all listed home updates, MCP adjustments, and identified legacy migration. Do not repeat approval for covered actions.
4. Re-read the target and invalidate approval if its snapshot changed.
5. Execute only the approved action and verify through the owning CLI and exact tree comparison.

## Apply the Shared Backup Policy

Use `Choose a Backup Policy for Existing State` in the shared tool catalog for every overwrite or removal. The shared policy owns the request-scoped choice, loss and recovery disclosure, restoration evidence, and the rule that preparing an incoming payload is not a backup.

Never use `sudo`, `--force`, unapproved removal, provider invocation, source transmission, staging, committing, or pushing. Tell the user when Codex must restart.

## Bundle Intake

Accept a bounded `dev-setup-bundle` handoff containing the manifest digest and union of selected global components. Prepare each global component at most once. For Ouroboros, prepare the CLI once and integration once per distinct Codex home. Preserve all per-action approvals and return independent results for the bundle's target processing. Never read the manifest or infer repositories.

## Report

Report every selected component as current, missing, incompatible, different, duplicated, unsafe, or freshness-unverifiable; include resolved versions and sources, exact canonical targets, actions and exit status, backup and restoration evidence, cleanup, restart requirements, and remaining gaps. State explicitly that no repository configuration, staging, commit, or publication was performed.
