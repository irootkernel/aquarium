---
name: dev-setup
description: "Diagnose and configure Aquarium repository tooling and root agent guidance. Use when the user invokes $aquarium:dev-setup or asks to install, initialize, repair, or audit supported tools, paired skills, global or project MCP state, or an evidence-based AGENTS.md operating contract with CLAUDE.md delegation. Do not use for routine supported Procedure v2 session observation, cancellation, discard, or reset; use $use-podway."
---

# Development Setup

Configure selected development tools and evidence-based repository operating guidance without inventing shared project state or silently rewriting instruction files. Treat diagnosis, installation, native configuration, and root AGENTS.md/CLAUDE.md editing as distinct authority boundaries.

Read [podway-integration.md](../../references/podway-integration.md) only when the user explicitly selects Podway diagnosis or setup. Managed Aquarium Procedures or other repository state never select Podway by themselves.

Do not use this skill to observe, cancel, discard, or reset a routine supported Procedure v2 current session. Return an exact standalone `$use-podway` lifecycle request naming the repository, operation, and any session ID supplied by the caller instead. Keep installation, daemon, workspace readiness, managed-Procedure changes, and `LEGACY_PROCEDURE_STATE_UNSUPPORTED` recovery in this skill; the legacy `podway reset --all` path is a setup-recovery exception, not normal session cleanup.

## Establish the Repository

1. Resolve the requested working directory to one Git root.
2. Read applicable instruction files and inspect the branch, upstream, staged, unstaged, and untracked state.
3. Resolve this skill's directory (the directory containing this `SKILL.md`) and, when `python3` is available, run `python3 <skill-directory>/scripts/inspect_tools.py --repository <git-root>`. This default inspection omits Podway and Ouroboros completely and keeps an absent optional Mulgae MCP registration non-gating.
   When the current request explicitly selects Podway, add `--include-podway`; when it selects Ouroboros, add `--include-ouroboros`; when it selects Mulgae MCP in either scope, add `--require-mulgae-mcp`. Rerun with the applicable flag when a component is selected later through ask/answer. Read the JSON as local diagnostic evidence, not as installation or mutation authority.
4. If `python3` is unavailable or the inspection script fails, report that gap and perform the same read-only discovery manually. Do not install Python as part of fallback diagnosis.
5. Discover existing root instruction files, project authorities, tool guidance, commit-message rules, verification commands, and non-secret environment variable names from repository files before asking questions.
   Never read credential values in this skill, even after setup approval. Do not open `.env*`, authentication, key, token, secret, or credential files. Use only non-secret documentation and templates proven to contain placeholders, plus redacted readiness from the owning CLI. When a check would require credential values, report the gap. Defer network contact or file changes to a separately authorized step except for the exact selected-skill freshness comparison authorized below.
6. Do not create or read `.aquarium` or any equivalent central selection file. `$aquarium:dev-setup-bundle` may separately normalize an explicit external manifest, but this skill receives only its bounded normalized handoff and never the manifest path or contents.

## Use Ask/Answer for Decisions

Use the host's structured ask/answer tool, normally `request_user_input`, whenever it is available.

- Ask one to three short questions per call with two or three meaningful, mutually exclusive choices.
- Put the recommended choice first and label it recommended.
- Do not simulate a multiple-choice UI in prose.
- Use direct text only for an identifier that cannot be discovered or represented by choices, such as an unknown private documentation repository URL.
- If ask/answer is unavailable, ask one concise approval question at a time. Never infer approval from silence or from approval of a different setup action.

After read-only discovery, use these batches and component boundaries:

- Ask about Sanho, Dolgorae, Mulgae, and Gaori first, then Podway, Ouroboros, Lora, upstream Deslop, and whether to prepare a repository operating-guidance proposal rooted in AGENTS.md.
- For each tool offer `Install and configure`, `Diagnose only`, and `Skip`, adapting the wording to current state.
- For Dolgorae, recommend the exact official v0.1.0 CLI while reporting release identity, executable checksum, platform, version envelope, and review admission independently. Dolgorae has no Aquarium paired skill or MCP registration.
- For Sanho, Mulgae, Gaori, and Podway, recommend installing or upgrading the CLI and paired skill while reporting each component independently.
- For Ouroboros, report the CLI, Codex rules and skills, MCP registration, and runtime readiness independently.
- For every paired or third-party skill, reject any symlink from the configured skill root through the required files before reading or hashing it. For Lora and Deslop, report every discovered user-global installation, frontmatter validity, duplicate or symlink state, and upstream freshness independently.

Disclose in the Dolgorae selection choice that either affirmative selection automatically contacts its official GitHub Releases metadata endpoint to confirm the exact supported release. This metadata lookup needs no separate approval and authorizes no archive download or installation. Disclose separately in the Sanho, Mulgae, Gaori, and Podway choices that either affirmative selection also downloads four public skill files from `raw.githubusercontent.com` for paired-skill comparison.

When Mulgae or Gaori is selected, inspect its active user-global and isolated project-local MCP registrations independently. If neither is configured, offer `Configure global MCP` (recommended), `Configure project MCP`, and `Skip`. If a project-local registration exists, ask whether it is intentional; preserve it only when the user confirms local scope. Otherwise propose removal of only that named local registration. Never infer local intent from the presence of `.codex/config.toml` or another local MCP entry.

A `dev-setup-bundle` handoff is a preselected multi-tool setup request, not a scoped repair continuation. Require the requesting skill, manifest digest, target index, canonical Git root, effective tools, explicit local MCP overrides, and repository-guidance policy.

Reinspect that repository, use the normalized tools as `Install and configure` selections, use explicit local MCP overrides and repository-guidance values as their preselected choices, and retain every exact mutation, backup, approval, and stale-target boundary below. Treat selected Mulgae or Gaori MCP as user-global by default and use an override only for its named target.

Reject a handoff that includes an unsupported tool, selects a local MCP override outside Mulgae or Gaori, selects an override for an absent effective tool, or asks this skill to read the manifest.

When another Aquarium skill routes a continuation request, treat it as scoped intake: the request must name the requesting skill, repository, exact failing tool or check, and evidence gap. Reject a handoff whose only requested action is routine supported Procedure v2 session observation, cancellation, discard, or reset, and return the exact `$use-podway` lifecycle request without starting broad setup discovery.

Otherwise keep the read-only discovery above, then ask only about the named tool and anything its repair requires, including explicitly requested Podway readiness repair or managed-Procedure removal. Skip the remaining batches and the repository-guidance question unless the user asks for it, and end by reporting the resolved gap and the exact prompt that resumes the routing workflow.

Read [tool-catalog.md](references/tool-catalog.md) for every tool selected for diagnosis or setup.

A selection expresses intent and authorizes only the disclosed bounded metadata lookup for Dolgorae or selected-skill freshness comparison for Sanho, Mulgae, Gaori, or Podway. It does not authorize an archive download, a command that writes persistent files, installation, skill replacement, hook changes, provider contact, or user-global mutation.

## Compare Selected Agent Skills First

Immediately after Sanho, Mulgae, Gaori, or Podway is selected as either `Install and configure` or `Diagnose only`, and before proposing any other network operation for that tool, compare its paired skill. Do not fetch or compare a skipped or not-yet-selected tool, and do not widen a scoped continuation to the other three tools.

Within one confirmed `dev-setup-bundle` request, accept the bundle owner's already verified exact tag, complete source file set, digests, endpoint provenance, ephemeral payload, and installed-target digest snapshot for a selected tool instead of repeating the comparison for each repository. Revalidate the payload and target snapshot before an approved action, use it only for the matching tool, and preserve every cleanup and stale-approval rule below.

1. From the official GitHub Releases metadata, resolve the newest non-draft, non-prerelease tag within the tool's supported release line. For Sanho, Mulgae, and Gaori, fetch only `SKILL.md`, `references/lifecycle.md`, `references/authoring.md`, and `references/recovery.md`. For Podway, fetch only `SKILL.md`, `references/lifecycle.md`, `references/goal.md`, and `references/recovery.md`.
   Fetch the selected set for that tag from the catalog's `raw.githubusercontent.com` source into an ephemeral temporary directory. `create-podway-procedure` is a separate maintainer authoring dependency and is never installed, compared, or required by this workflow.
2. Before comparing, require all four regular files, compute their SHA-256 digests, and verify the expected `name: use-sanho`, `name: use-mulgae`, `name: use-gaori`, or `name: use-podway` frontmatter. Reject redirects or responses that resolve outside the disclosed official endpoints. Never execute fetched content.
3. Compare the verified source against exactly `~/.agents/skills/<skill-name>` as complete directory trees. Treat missing expected files, different bytes, invalid frontmatter, symlinks, and any extra local files as differences. Other Codex skill roots remain diagnostic evidence only; never update or remove another discovered copy through this automatic comparison.
4. If the trees match exactly, report the source tag and `current` status without asking an update question. If the exact target is absent, first inspect the already discovered diagnostic roots. When another copy exists, report the duplicate risk and do not propose installation until the user separately chooses a removal or migration that leaves one canonical target; never create a known duplicate.
   Otherwise show the exact target and ask separately whether to install it. If the target differs, show the source tag, the complete file-set diff including additions and deletions, and ask separately whether to replace it after establishing the backup policy. One skill target requires one explicit installation or replacement approval; approval for another tool does not apply.
5. If metadata lookup, download, validation, or comparison fails, report `freshness_unverifiable` with the failed endpoint or validation stage, make no freshness claim, remove the temporary payload when possible, and continue any safe local diagnosis. Do not propose an installation or replacement from an unverified payload.

The automatic comparison authorizes only these selected-skill metadata and raw-file reads plus ephemeral payload preparation. CLI archives, checksums, package managers, repository remotes, providers, MCP processes, and every other network operation retain their normal disclosure and explicit approval requirements. Reuse the verified exact tag and payload for a later approved skill action instead of performing a second release lookup.

If a selected tool's installed CLI, or Podway's CLI and daemon, does not match that tag, report the compatibility mismatch and keep each required runtime upgrade and skill replacement as separately approved actions; never create a mixed-version installation.

Immediately before an approved installation or replacement, re-read the exact target and require it to match the absence or complete digest snapshot used for the displayed proposal. If it changed, discard the approval, fetch and validate a fresh payload, regenerate the complete diff, and ask again. Clean up every ephemeral payload after an exact match, refusal, failure, or completed action.

## Choose a Backup Policy for Existing State

When an approved setup plan will first overwrite or remove existing tool, skill, configuration, service, managed-Procedure, or runtime state, establish one backup policy for the current setup request. If the user already explicitly requested backups or no backups, adopt that choice without asking again. Otherwise offer `Create and verify backups` and `Proceed without backups`, recommending the backup choice. Do not ask about backups for diagnosis or a new installation that replaces nothing.

Keep the selected policy for later overwrite and removal proposals in the same setup request unless the user changes it. The policy does not authorize any mutation: continue to show and separately approve every exact replacement or removal. Never persist the choice in repository or user-global configuration.

For the backup policy, show the exact backup path, commands, verification, and restoration procedure before approval, and stop before mutation if the selected backup cannot be verified. For the no-backup policy, state the exact existing paths or state that will be lost and the available recovery boundary.

A published Git ref may allow a distributed skill or binary to be installed again, but it does not recover local modifications. Treat tracked state as recoverable only when it already exists in Git history, and disclose that private configuration, untracked files, and runtime history may be permanently lost.

Preparing and validating an incoming payload in a temporary location is not a backup and remains required.

## Propose Exact Setup Actions

For each selected tool:

1. For Dolgorae, reuse the exact release metadata from its automatic bounded lookup. For Sanho, Mulgae, Gaori, or Podway, reuse the exact version, source provenance, and verified payload from the automatic selected-skill comparison. Do not ask for a second lookup approval. For Lora, Deslop, or any lookup outside those bounded comparisons, disclose the official repository and commit-metadata endpoint and obtain explicit ask/answer approval before resolving it; a lookup approval authorizes no installation or other mutation.
2. Show the exact resolved stable version and source provenance. If the automatic comparison was `freshness_unverifiable`, repeat the bounded comparison without separate approval before proposing a skill action, but obtain approval for any other lookup or download.
3. Show the exact install and initialization commands, network endpoints, target paths, native files, ignore changes, expected side effects, and the active backup policy when existing state will be overwritten or removed.
4. Identify existing state that will be preserved or lost and any command that might stage files or install hooks.
5. Obtain separate explicit ask/answer approval for the displayed action.
6. Execute only the approved action, stop on unexpected prompts or side effects, and verify with read-only commands.

For Sanho, support only stable `v0.2.7` through `v0.2.x`. Resolve one exact tag and use it for both the CLI and `use-sanho` source. Keep CLI installation or upgrade, user-scoped skill installation or replacement, workspace initialization, and lifecycle repair as separate approval boundaries. A paired recommendation is not approval for both components. Treat missing, incomplete, invalid, and duplicate skill installations separately from CLI or workspace health.

For Dolgorae, support only the exact official `v0.1.0` Apple Silicon release. Require archive SHA-256 `598ffaff7883b4f8cc794b890186d758795f57c1f373e6905c138abb7f3bfe41`, executable SHA-256 `6087b484cfd8d61d88ed69a5b84ab4a515ba2efaebe4fa282d51679536cccdb8`, and the checked machine `--version` result `dolgorae 0.1.0`.

Downloading the archive and installing its executable are separate approvals. Extract only the expected regular `README.txt` and `bin/dolgorae` entries into ephemeral storage, reject links and special files, then propose the exact absolute user target, normally `~/.local/bin/dolgorae`.

Disclose that the Integration Preview is ad-hoc signed and not notarized, so Gatekeeper may require explicit local approval. Do not initialize a workspace, create a profile, authenticate, call a provider, transmit source, or start a review during setup.

For Mulgae, support only stable `v0.1.18` through `v0.1.x` on native Apple Silicon macOS. Resolve one exact tag and use it for both the CLI and `use-mulgae` source. Require Go `1.26.6` or newer for installation, without treating an older Go toolchain as a runtime failure of an already healthy binary.

Keep CLI installation or upgrade, user-scoped skill installation or replacement, project Config v3 and ignore changes, local bootstrap or refresh, Codex credential-profile mapping, and global or project-local MCP configuration as separate approval boundaries. Treat missing, incomplete, invalid, and duplicate skill installations and missing MCP registration independently from CLI and configuration health.

Report Mulgae CLI compatibility, Doctor v2 contract support, Config v3, local configuration, provider identity, configured readiness, role-route readiness, each configured provider's binary availability and CLI compatibility, and MCP registration separately. Do not expose static admission, heartbeat, historical review, or `review_qualified` as setup dimensions.

Never authenticate a provider, inspect a prior run, or start a Mulgae heartbeat, review, qualification, preflight capture, live provider request, source transmission, or MCP server during setup. Doctor v2 may run only Mulgae's adapter-owned local version commands in its offline boundary.

For Gaori, support only stable `v0.1.14` through `v0.1.x`. Resolve one exact tag and use it for both the CLI and `use-gaori` source. Keep CLI installation or upgrade, user-scoped skill installation or replacement, repository config and ignore changes, and global or project-local MCP configuration as separate approval boundaries. Treat missing, incomplete, invalid, and duplicate skill installations and missing MCP registration independently from CLI health. Never start a Gaori run or MCP test command during setup.

Approval for one tool does not authorize another. Never use `sudo`, `--force`, destructive cleanup, credential extraction, provider invocation, source transmission, staging, committing, or pushing unless the user separately grants that exact authority.

For Podway, support only stable `v0.2.7` through `v0.2.x` on native Apple Silicon macOS. Resolve one exact tag and use it for both binaries and the `use-podway` source. Treat a missing, incomplete, invalid, or duplicate skill independently from CLI and repository readiness.

Keep release lookup, binary installation, user-scoped skill installation or replacement, LaunchAgent installation, repository initialization, managed-procedure installation or update, legacy-state recovery, and managed-Procedure removal as distinct proposed actions. None of these actions activates Podway for an Aquarium workflow.

Verify the release checksum before installing both matching binaries, then install or refresh the per-user LaunchAgent using the approved absolute daemon path. Disclose that the release is unsigned and not notarized, runs as a same-user local service after GUI login, and stores runtime state in the worktree.

If an installation is interrupted after Podway prepares authenticated service metadata, rerun the same approved `podway daemon install --daemon-path <absolute-podwayd-path>` command without a socket override. Do not edit service metadata or LaunchAgent files manually.

Never convert or delete Procedure v1 state automatically. On `LEGACY_PROCEDURE_STATE_UNSUPPORTED`, report the exact worktree and stable error code, apply the current backup policy, and separately propose the confirmed `podway reset --all` recovery. Do not treat the inspection status `not_configured` as legacy Procedure state.

Treat tracked `root-kernel-task-v2.yaml`, `root-kernel-goal-v2.yaml`, and `root-kernel-validation-v2.yaml` files as a product-rename migration, not as Procedure v1 runtime state. Report `migration_required`, require any active old session to reach an explicitly chosen terminal disposition first, then propose removal of the old managed files and installation of the corresponding `aquarium-*` files as separate approved actions. Never convert, cancel, reset, or delete runtime history as part of this migration.

Use the v11 inspector's `migration_kinds.product_rename` only for the product rename. For each safe present managed file, require the expected filename and Procedure ID and use the selected Podway v0.2.7 binary's `procedure check --warnings-as-errors` and `procedure preview` results as the document-validity and identity authority. Report `canonical`, `valid_customization`, `invalid`, `missing`, `unsafe`, or `unverifiable`; never add an Aquarium compatibility schema for graph, item, prompt, bound, or route differences.

Treat `update_explanation` values such as `prior_canonical` and `podway_v0.2.5_workaround` only as bounded explanations for an offered canonical update. They never form a validity, ownership, migration, or readiness class. A tracked same-ID `valid_customization` is configured when the other Podway readiness requirements pass.

Aquarium Podway readiness configuration has four disclosed parts:

- Install a missing or explicitly selected canonical copy from [the bundled procedure directory](../../assets/podway/procedures/) byte-for-byte to `.podway/procedures/`, then check its expected ID and validity with the selected Podway binary.
- `podway init` also creates `.podway/config.yaml`, `.podway/.gitignore`, and ignored runtime state; show the exact proposed files and diff before approval.
- When a valid managed Procedure differs, show the exact current-to-canonical diff and ask whether to preserve that local file or replace it with canonical bytes. Preservation writes no file or metadata. Replacement follows the selected backup policy, rechecks the exact target snapshot, and requires explicit approval for that one diff; never merge, normalize, or reformat it.
- Treat partial installation as degraded readiness, not activation or legacy state.

Do not create an ownership manifest, provenance registry, or central Aquarium state. Replacing a managed file never alters an active session's immutable Procedure snapshot.

Managed-Procedure removal is a separate destructive proposal. Show the exact managed procedure files to remove, preserve `.podway/config.yaml`, runtime state, custom procedures, and every session, and obtain explicit approval. Do not reset, cancel, or delete any session as part of setup or removal.

## Install Third-Party Skills From Exact Upstream Sources

Aquarium does not bundle Lora, Lore, or Deslop source. For Lora or Deslop, read the selected catalog section, obtain approval for the disclosed GitHub lookup, resolve the exact upstream commit, and compare the complete installed target with a temporary detached checkout before proposing installation or replacement. Never install directly from a moving `main`, use a full commit SHA as an `npx skills` URL fragment, merge local and upstream files, or treat frontmatter validity as freshness proof.

For Lora, install only `lore-commits` and `lore-query` from the approved checkout through the catalog's local-source `npx skills add` command. After installation, compare the complete source and target file sets and every digest, rejecting extras and symlinks; structural inspector output alone never proves current source. Do not install `lore-setup`.

For Deslop, install only `deslop` from the approved Cursor Team Kit checkout and preserve that checkout's upstream LICENSE beside the installed `SKILL.md`. Require byte-identical source files, `name: deslop`, one regular non-symlink installation, and no extra target files before reporting it current.

Keep source lookup, existing-target backup policy, installation or replacement, and Codex restart as separate disclosed boundaries. A scoped continuation from `task-handler` or `task-refine` selects only Deslop; after successful installation, return the exact repository, roadmap, and task prompt needed to resume the caller.

## Configure Ouroboros With Separate Approvals

Support only Ouroboros `>=0.51.1,<0.52.0`. Read [tool-catalog.md](references/tool-catalog.md), then diagnose with `--include-ouroboros`. Keep these four states independent: the `ooo` CLI and version, installed Codex rules and skills, Ouroboros MCP runtime configuration, and effective Codex MCP registration. Do not infer readiness from one passing component.

Installation requires an already installed `uv`; never install a package manager as a side effect. Resolve one exact `ouroboros-ai` version inside the supported range, disclose the Python package index request and package target, show `uv tool install ouroboros-ai==<exact-version>` or the exact approved upgrade form, and obtain a dedicated approval before running it. Do not install from an unpinned range.

Treat exact package installation or upgrade through `uv` and the selected configuration action as separate persistent mutations. Display each command and its changed paths, obtain explicit approval, re-read targets immediately before mutation, and invalidate stale approval.

For full configuration, run only `ooo setup --runtime codex --non-interactive --mcp-mode auto`. Full setup installs and prunes packaged Codex rules and upstream Ouroboros skills while it may also update Codex MCP configuration and Ouroboros runtime state; do not run `ooo codex refresh` first. Offer `ooo codex refresh` as a separate repair alternative only when the user selects rules-and-skills refresh without full setup.

Approval for package mutation never authorizes configuration, and approval for one configuration path never authorizes the other. Setup and refresh must not call an Ouroboros provider, authenticate, run `auto`, `run`, `ralph`, or `evolve`, transmit repository source, create a Seed, or start an Aquarium design workflow.

After approved mutations, verify `ooo --version`, `ooo codex doctor`, and `codex mcp get ouroboros --json`.

Run `ooo mcp doctor --json` only when Codex directly launches the selected `ooo` executable; it inspects that package environment and is not evidence about a separate `uvx --isolated` MCP environment.

For the canonical isolated launcher, validate its exact executable, arguments, supported package requirement, and Codex runtime selectors without starting it or contacting the network.

When the active host can expose MCP tools safely, verify live exposure separately without invoking a provider.

Report missing skills, rules, registration, runtime configuration, and live exposure as distinct gaps, and tell the user when a Codex restart is required.

## Gate Repository Guidance With Two Approvals

Handle root AGENTS.md and CLAUDE.md independently from tool setup:

1. Ask whether to prepare an evidence-based repository operating-guidance proposal. Offer `Show proposal`, `Diagnose only`, and `Skip`.
2. For either `Show proposal` or `Diagnose only`, read [agents-guidance.md](references/agents-guidance.md) and inspect the non-secret local sources it identifies. Diagnosis reports coverage and conflicts without drafting or mutation.
3. For `Show proposal`, resolve every material conflict and the mandatory `Project Configuration` > `Commit Messages` rule before finalizing the proposal. If no authoritative commit header exists, ask the user to choose one; recent Git history is evidence only and never sufficient authority by itself.
4. For `Show proposal` only, display the exact root AGENTS.md and CLAUDE.md paths and one complete combined diff. Do not edit either file yet. Preserve substantive CLAUDE.md guidance in AGENTS.md before proposing the canonical delegation file.
5. For `Show proposal` only, ask whether to `Apply exactly this diff`, `Revise proposal`, or `Do not apply`.
6. Before applying a shown proposal, re-read both files and compare them with the bytes or explicit absence used to produce it. If either changed, discard the approval, regenerate the combined diff, and ask again.
7. Apply only the approved shown diff. Then show the actual diff and verify the required structure, mandatory commit-message subsection, CLAUDE.md delegation, repository-specific rules, and unrelated user content.

The first answer authorizes proposal preparation or diagnosis only. General setup approval, install approval, and the instruction to use this skill never authorize instruction-file mutation. The second approval covers only the exact displayed root AGENTS.md/CLAUDE.md diff; it never authorizes nested instruction files, staging, committing, or publication.

## Report the Result

Report:

- selected, skipped, and planned tools;
- resolved versions and sources;
- each selected paired skill's comparison tag, exact `~/.agents/skills` target, `current`, `missing`, `different`, or `freshness_unverifiable` result, temporary-payload cleanup, and any installation or replacement decision;
- selected backup policy, existing state backed up or deliberately left without a backup, backup verification and restoration paths when applicable, and the disclosed recovery boundary;
- Sanho CLI, workspace, and `use-sanho` skill state separately;
- Dolgorae exact release, platform, version envelope, official executable checksum, and stable review admission separately;
- Mulgae CLI and Doctor v2 compatibility, project Config v3, local configuration, provider identity, binary availability, provider CLI compatibility, configured and role-route readiness, `use-mulgae` skill, installation prerequisites, and global, local, and effective MCP scope separately;
- Gaori CLI, repository config, `use-gaori` skill, and global, local, and effective MCP scope separately;
- Podway CLI, daemon, workspace, Aquarium readiness, legacy-state detection, and `use-podway` skill state separately;
- Ouroboros CLI and version support, Codex rules and skills, MCP runtime, effective registration, and live exposure separately;
- commands run and their exit status;
- native configuration and ignore paths changed;
- verification evidence and remaining auth or environment gaps;
- whether repository guidance was skipped, diagnosed, proposed, revised, or applied, including AGENTS.md structure, mandatory commit-message authority, and CLAUDE.md delegation state;
- worktree changes, with staging and publication state stated separately.

For a `dev-setup-bundle` handoff, also return the manifest digest, target index, canonical Git root, and a target result of `ready`, `partial`, `failed`, `declined`, or `skipped`, with unmet dependencies and an exact resumption request. Return the result to the bundle owner so it can continue independent targets and produce one aggregate report.

Do not claim a tool is configured merely because its binary exists. Do not claim repository guidance was approved when only a proposal was requested.
