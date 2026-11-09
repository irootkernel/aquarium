---
name: dev-setup-global
description: "Diagnose, install, and update supported user-global development tools and integrations. Excludes Aquarium plugin installation or updates. Use when the user invokes $aquarium:dev-setup-global or a workflow reports a missing global CLI, paired skill, global MCP registration, service, Lore, Deslop, Humanizer, im-not-ai, or Ouroboros component. Use $aquarium:dev-setup for repository-local configuration."
---

# Global Development Setup

Read [commit-attribution.md](../../references/commit-attribution.md) for message formatting and change origins, within this skill's existing effect boundaries.

Own installation, exact-upstream freshness, upgrades, services, and global Codex integration for the supported components listed below without inspecting or changing repository configuration.

Aquarium's Python helpers use the shared user-global `aquarium-python`
environment. This skill owns its installation, diagnosis, update and repair.
Read [the Python runtime contract](../../references/python-runtime.md) when it
is selected. Project environments and global Python packages are never used to
supply helper dependencies.

## Check Request Scope Before Loading References

Aquarium plugin installation and updates belong to the host's plugin-management flow. A request to install or update only the Aquarium plugin, including a specific version, does not select this skill. If this skill was selected for that request, return to the host's plugin-management flow before reading the tool catalog or running any diagnostic. Do not infer a global tool setup request from plugin installation.

Use this skill for an explicit global development setup request or a workflow continuation naming a global component that needs attention. An explicit request to install or update the optional `aquarium-dev` or `aquarium-status` runtime remains in scope; installing or updating the Aquarium plugin alone does not request either runtime.

Read the selected sections of [the shared tool catalog](../../references/tool-catalog.md). Do not read repository-local `.podway`, `.mulgae`, `.gaori`, `.sorage`, `.codex`, AGENTS.md, or CLAUDE.md as global setup evidence.

## Diagnose Automatically

1. On a direct invocation without a component list, select every supported global component. On a scoped continuation, select only the named components and their direct prerequisites.
2. A direct invocation authorizes disclosed read-only official release, tag, and commit metadata lookup for selected components. Only the paired-tool sources receive the catalog's complete-tree and commit-pinned raw-file freshness comparison; selected Lora or Deslop also includes official npm installer metadata. A scoped continuation selects only its named sources. Follow the catalog's exact lookup boundary; materialization, installation and execution remain separate actions.
3. Resolve this skill's directory and run `python3 <skill-directory>/scripts/inspect_global_tools.py` on a direct unscoped invocation. For a scoped continuation, add one `--component <name>` argument for each selected component in catalog order and run no unselected component probe. Scoped Podway setup also selects `--component aquarium-python` as its direct prerequisite. The bootstrap inspector uses only the standard library; do not run it through an environment that is not yet prepared.

   When Ouroboros is selected, also add `--verify-ouroboros-release`; pass any explicitly supplied extra homes with repeatable `--codex-home <path>`. Use the catalog's home discovery and per-home readiness contract.

   Start Sorage with version-only inventory. For selected diagnosis, use native `preflight --json` under the [Sorage catalog](../../references/tool-catalog.md#sorage). Preflight is permitted in Plan Mode; doctor and Project resolution remain execution-phase diagnostics. Only `compatible` admits those operational probes. A fresh home needs approved initialization; an older home needs matching-old-binary backup, verification and a separate restore drill before the approved new-binary `backup run` migration. Keep initialization and migration with global setup; Project mutations and ignore changes remain local.
4. Treat `--repository <existing-directory>` only as a compatibility input. Validate that it is an existing directory, but never use it as command or configuration scope, so diagnosis also works outside a Git worktree.
5. Diagnose local installation, supported version, canonical target, exact-upstream tree, duplicate and symlink state, paired-skill compatibility, services, global MCP, and Ouroboros integration independently.
6. Do not ask the user to choose install, diagnose, or skip. Report current components without a question and propose actions only for missing, incompatible, unsafe, duplicated, or stale components.

When `dev-setup-bundle` supplies `required_global_mcp`, keep CLI, paired-skill, and other global component diagnosis for every selected tool, but require or prepare a Mulgae, Gaori, or Sorage global MCP registration only for names in that union. A selected tool with no global MCP request must not make local-only targets depend on global MCP readiness. Preserve any existing global registration; no MCP request means unrequested, not disabled.

If a freshness lookup, download, validation, or comparison fails, report `freshness_unverifiable`, clean ephemeral payloads, and do not propose installation or replacement from that payload.

## Owned Components

- Sanho, Dolgorae, Mulgae, Gaori, Sorage, Podway, and Haepari user-global CLIs.
- `use-sanho`, `use-dolgorae`, `use-mulgae`, `use-gaori`, `use-gaori-status`, `use-sorage`, `use-podway`, and `use-haepari` under `~/.agents/skills`.
- Mulgae, Gaori, and Sorage user-global MCP registrations.
- Podway's single Direct CLI identity and Sorage's minimal user-global initialization.
- Lora's `lore-commits` and `lore-query`, upstream Deslop, Humanizer, and im-not-ai's `humanize-korean` skill.
- Ouroboros package version, Codex rules and skills, MCP runtime, effective global registration, and live exposure when safely observable.
- The optional `aquarium-dev` CLI and MCP runtime bundled with Aquarium. Install and update it only on an explicit request; it is not part of production-binary readiness. Its MCP registration belongs to the plugin, not the global MCP table, and it has no paired skill.
- The `aquarium-python` shared virtual environment. Diagnose it by default and include it as a direct prerequisite of scoped Podway setup. Prepare it once for a setup bundle before manifest normalization.
- The `aquarium-status` user-global reporter runtime bundled with Aquarium. Diagnose it by default. Install, update, or repair its private hash-pinned runtime and launcher only after a separate exact approval. It is setup-recording infrastructure, not a bundle manifest tool and not part of production-binary readiness.
- Haepari's shared per-user release controller and capacity-one VM resource: the controller is selected only through its explicit `HAEPARI_HOME` root, its readiness is separate from CLI, paired-skill, and resource readiness, and registration or service installation stays with Haepari's native authority. Haepari is optional like Dolgorae and Sanho.
- Aquarium production-binary readiness requires supported global Podway, Mulgae, and Gaori executables and fails closed when any is missing. Dolgorae, Sanho, and Haepari remain optional and are excluded from this baseline.

Do not install provider CLIs, authenticate, read credentials, contact providers, transmit repository source, initialize repository workspaces, change project MCP, edit repository guidance, start tests or reviews, or invoke Ouroboros workflows.

## Exact-Upstream and Update Policy

Use one exact supported release tag or disclosed full commit SHA according to the shared catalog. Verify downloaded archives, manifests, checksums, signatures, frontmatter, complete regular-file trees, and expected source provenance before proposing an action. Never install from a moving branch or execute unverified fetched content.

For each selected paired or third-party skill, compare the verified source with its canonical target. Treat missing or extra files, different bytes, invalid frontmatter, symlinks, and duplicate installations as independent gaps.

Apply this duplicate rule to shared-location skills. Resolve the target from the selected upstream release's default installation guidance: use the active Codex home's skills directory when it names `$CODEX_HOME`, and `~/.agents/skills` when it names no default. Ouroboros uses the per-home contract below. Other Codex skill roots remain diagnostic evidence only. When another copy would be loaded beside the selected target, report the duplicate risk and never create a known duplicate. Do not propose installation at the canonical target until the user separately approves removal or migration of the conflicting copy.

`dev-setup` trusting an existing canonical path is not freshness evidence.

Ouroboros update diagnosis reports installed, latest stable, and latest supported versions. Its CLI is user-global; rules, skills, and MCP registration belong to each Codex home. Propose all discovered homes by default. Never install its skills into `~/.agents/skills` or classify valid copies in different homes as duplicates. A shared copy matching a selected package skill name or a same-name shared conflict prevents completed home readiness; inspect provenance before proposing removal. Keep current-home readiness, all-discovered-home readiness, package freshness, and live runtime evidence separate. Never install below the minimum supported version.

im-not-ai's `humanize-korean` skill also belongs to the active Codex home. Use `<active CODEX_HOME>/skills/humanize-korean`, or `~/.codex/skills/humanize-korean` when unset. Do not install it in `~/.agents/skills`; copies in other Codex homes are independent, while a shared-root copy is a duplicate to report and resolve separately.

## Respect Host Mode and Approval Boundaries

In Plan Mode, perform local and network read-only diagnosis and return exact proposals without mutation. Defer Sorage doctor or initialization checks that may update its database or journal to execution mode.

Start Sorage with version-only inventory. For selected diagnosis, use native `preflight --json` under the [Sorage catalog](../../references/tool-catalog.md#sorage). Preflight is permitted in Plan Mode; doctor and Project resolution remain execution-phase diagnostics. Only `compatible` admits those operational probes. A fresh home needs approved initialization; an older home needs matching-old-binary backup, verification and a separate restore drill before the approved new-binary `backup run` migration. Keep initialization and migration with global setup; Project mutations and ignore changes remain local.

Before every persistent action:

1. Show the exact command, endpoints, targets, changed paths, expected side effects, and verification.
2. Establish the shared backup policy before the first overwrite or removal.
3. Obtain action-specific approval. For Ouroboros, one exact proposal and approval may cover the CLI upgrade, all listed home updates, MCP adjustments, and identified legacy migration. Do not repeat approval for covered actions.
4. Re-read the target and invalidate approval if its snapshot changed.
5. Execute only the approved action and verify through the owning CLI and exact tree comparison.

For `aquarium-python`, use the [runtime contract](../../references/python-runtime.md)
to choose an installed host interpreter matching the pinned wheels before
proposing creation or repair. If the default Python is outside that coverage,
inspect available `python3.14`, `python3.13`, `python3.12` and `python3.11`
executables with stdlib-only version/platform probes; select a matching installed
one without asking the user to choose. Reuse a healthy managed environment even
when the bootstrap Python is newer. Report a creator prerequisite gap if none
matches; do not install Python or borrow a project's packages. Then disclose the exact runtime root, pinned dependency source, PyPI endpoints and verification before the approved install or repair. A plugin update never installs it implicitly.

For `aquarium-status`, disclose the exact PyPI endpoints and use only the bundled
installer's hash-pinned PyYAML environment. Never replace an unknown regular
launcher. Run the bundled installer with `--approve-install --approve-launcher`
only after approval covering both exact targets, then rerun the scoped inspector.

## Apply the Shared Backup Policy

Use `Choose a Backup Policy for Existing State` in the shared tool catalog for every overwrite or removal. The shared policy owns the request-scoped choice, loss and recovery disclosure, restoration evidence, and the rule that preparing an incoming payload is not a backup.

Never use `sudo`, `--force`, unapproved removal, provider invocation, source transmission, staging, committing, or pushing. Tell the user when Codex must restart.

## Bundle Intake

Accept a bounded `dev-setup-bundle` handoff containing the manifest digest and union of selected global components. Reuse the pre-normalization `aquarium-python` preparation and add `aquarium-status` as bundle infrastructure without changing or reinterpreting the manifest tool vocabulary. Prepare each global component and that runtime at most once. For Ouroboros, prepare the CLI once and integration once per distinct Codex home. Preserve all per-action approvals and return independent results for the bundle's target processing. Never read the manifest or infer repositories.

## Report

Report every selected component as current, missing, incompatible, different, duplicated, unsafe, or freshness-unverifiable; include resolved versions and sources, exact canonical targets, actions and exit status, backup and restoration evidence, cleanup, restart requirements, and remaining gaps. State explicitly that no repository configuration, staging, commit, or publication was performed.
