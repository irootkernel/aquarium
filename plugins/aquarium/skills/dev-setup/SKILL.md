---
name: dev-setup
description: "Diagnose and configure Aquarium repository tooling. Use when the user invokes $aquarium:dev-setup or asks to install, initialize, repair, or audit Sanho, Mulgae, Gaori, Podway, Lora, paired skills, MCP registrations, Config v3, provider profiles, or AGENTS.md tool guidance. Do not use for routine supported Procedure v2 session observation, cancellation, discard, or reset; use $use-podway."
---

# Development Setup

Configure selected development tools without inventing shared project state or silently rewriting agent guidance. Treat diagnosis, installation, native configuration, and AGENTS.md editing as distinct authority boundaries.

Read [podway-integration.md](../../references/podway-integration.md) only when the user explicitly selects Podway diagnosis or setup. Managed Aquarium Procedures or other repository state never select Podway by themselves.

Do not use this skill to observe, cancel, discard, or reset a routine supported Procedure v2 current session. Return an exact standalone `$use-podway` lifecycle request naming the repository, operation, and any session ID supplied by the caller instead. Keep installation, daemon, workspace readiness, managed-Procedure changes, and `LEGACY_PROCEDURE_STATE_UNSUPPORTED` recovery in this skill; the legacy `podway reset --all` path is a setup-recovery exception, not normal session cleanup.

## Establish the Repository

1. Resolve the requested working directory to one Git root.
2. Read applicable instruction files and inspect the branch, upstream, staged, unstaged, and untracked state.
3. Resolve this skill's directory (the directory containing this `SKILL.md`) and, when `python3` is available, run `python3 <skill-directory>/scripts/inspect_tools.py --repository <git-root>`. This default inspection omits Podway completely and keeps an absent optional Mulgae MCP registration non-gating.
   When the current request explicitly selects Podway, add `--include-podway`; when it selects project-local Mulgae MCP, add `--require-mulgae-mcp`. Rerun with the applicable flag when either component is selected later through ask/answer. Read the JSON as local diagnostic evidence, not as installation or mutation authority.
4. If `python3` is unavailable or the inspection script fails, report that gap and perform the same read-only discovery manually. Do not install Python as part of fallback diagnosis.
5. Discover existing tool guidance and verification commands from repository files before asking questions. Inspect the remaining state read-only; when a check would require reading credentials, contacting a network, or changing files, defer it to a separately authorized step except for the exact selected-skill freshness comparison authorized below.
6. Do not create or read `.aquarium` or any equivalent central selection file.

## Use Ask/Answer for Decisions

Use the host's structured ask/answer tool, normally `request_user_input`, whenever it is available.

- Ask one to three short questions per call with two or three meaningful, mutually exclusive choices.
- Put the recommended choice first and label it recommended.
- Do not simulate a multiple-choice UI in prose.
- Use direct text only for an identifier that cannot be discovered or represented by choices, such as an unknown private documentation repository URL.
- If ask/answer is unavailable, ask one concise approval question at a time. Never infer approval from silence or from approval of a different setup action.

After read-only discovery, ask about Sanho, Mulgae, and Gaori in the first batch. Ask about Podway, Lora, and whether to prepare an AGENTS.md proposal in subsequent batches. For each active tool offer `Install and configure`, `Diagnose only`, and `Skip`, adapting the wording when it is already installed. For Sanho, Mulgae, Gaori, and Podway, make `Install or upgrade the CLI and paired skill` the recommended setup choice, but report each component independently and preserve a healthy CLI when its optional skill is absent.

Disclose in these four tools' selection choices that either affirmative selection automatically contacts the official GitHub Releases metadata endpoint and `raw.githubusercontent.com` to compare the selected tool's latest supported stable skill with its exact `~/.agents/skills` target. This bounded freshness comparison needs no separate approval and authorizes no installation or replacement.

When Mulgae or Gaori is selected, ask separately whether to configure that tool's project-local MCP; offer `Configure project MCP`, `Diagnose only`, and `Skip` and recommend configuration only for a trusted project.

When another Aquarium skill routes a continuation request, treat it as scoped intake: the request must name the requesting skill, repository, exact failing tool or check, and evidence gap. Reject a handoff whose only requested action is routine supported Procedure v2 session observation, cancellation, discard, or reset, and return the exact `$use-podway` lifecycle request without starting broad setup discovery.

Otherwise keep the read-only discovery above, then ask only about the named tool and anything its repair requires, including explicitly requested Podway readiness repair or managed-Procedure removal. Skip the remaining batches and the AGENTS.md question unless the user asks for them, and end by reporting the resolved gap and the exact prompt that resumes the routing workflow.

Read [tool-catalog.md](references/tool-catalog.md) for every tool selected for diagnosis or setup.

A selection expresses intent and, only for a selected Sanho, Mulgae, Gaori, or Podway tool, authorizes the disclosed bounded skill freshness comparison below. It does not authorize a command that writes persistent files, installs software, replaces a skill, changes hooks, contacts a provider, or modifies user-global state.

## Compare Selected Agent Skills First

Immediately after Sanho, Mulgae, Gaori, or Podway is selected as either `Install and configure` or `Diagnose only`, and before proposing any other network operation for that tool, compare its paired skill. Do not fetch or compare a skipped or not-yet-selected tool, and do not widen a scoped continuation to the other three tools.

1. From the official GitHub Releases metadata, resolve the newest non-draft, non-prerelease tag within the tool's supported release line. Fetch only `SKILL.md`, `references/lifecycle.md`, `references/authoring.md`, and `references/recovery.md` for that tag from the catalog's `raw.githubusercontent.com` source into an ephemeral temporary directory.
2. Before comparing, require all four regular files, compute their SHA-256 digests, and verify the expected `name: use-sanho`, `name: use-mulgae`, `name: use-gaori`, or `name: use-podway` frontmatter. Reject redirects or responses that resolve outside the disclosed official endpoints. Never execute fetched content.
3. Compare the verified source against exactly `~/.agents/skills/<skill-name>` as complete directory trees. Treat missing expected files, different bytes, invalid frontmatter, symlinks, and any extra local files as differences. Other Codex skill roots remain diagnostic evidence only; never update or remove another discovered copy through this automatic comparison.
4. If the trees match exactly, report the source tag and `current` status without asking an update question. If the target is absent, show the exact target and ask separately whether to install it. If it differs, show the source tag, the complete file-set diff including additions and deletions, and ask separately whether to replace it after establishing the backup policy. One skill target requires one explicit installation or replacement approval; approval for another tool does not apply.
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

1. For Sanho, Mulgae, Gaori, or Podway, reuse the exact version, source provenance, and verified payload from the automatic selected-skill comparison. Do not ask for a second lookup approval. For Lora or any lookup outside that bounded comparison, disclose the official release-metadata endpoint and obtain explicit ask/answer approval before resolving it; a lookup approval authorizes no installation or other mutation.
2. Show the exact resolved stable version and source provenance. If the automatic comparison was `freshness_unverifiable`, repeat the bounded comparison without separate approval before proposing a skill action, but obtain approval for any other lookup or download.
3. Show the exact install and initialization commands, network endpoints, target paths, native files, ignore changes, expected side effects, and the active backup policy when existing state will be overwritten or removed.
4. Identify existing state that will be preserved or lost and any command that might stage files or install hooks.
5. Obtain separate explicit ask/answer approval for the displayed action.
6. Execute only the approved action, stop on unexpected prompts or side effects, and verify with read-only commands.

For Sanho, support only stable `v0.2.7` through `v0.2.x`. Resolve one exact tag and use it for both the CLI and `use-sanho` source. Keep CLI installation or upgrade, user-scoped skill installation or replacement, workspace initialization, and lifecycle repair as separate approval boundaries. A paired recommendation is not approval for both components. Treat missing, incomplete, invalid, and duplicate skill installations separately from CLI or workspace health.

For Mulgae, support only stable `v0.1.16` through `v0.1.x` on native Apple Silicon macOS. Resolve one exact tag and use it for both the CLI and `use-mulgae` source. Require Go `1.26.6` or newer for installation, without treating an older Go toolchain as a runtime failure of an already healthy binary.

Keep CLI installation or upgrade, user-scoped skill installation or replacement, project Config v3 and ignore changes, local bootstrap or refresh, Codex credential-profile mapping, and project-local MCP configuration as separate approval boundaries. Treat missing, incomplete, invalid, and duplicate skill installations and missing MCP registration independently from CLI and configuration health.

Report Mulgae CLI compatibility, Doctor v2 contract support, Config v3, local configuration, provider identity, configured readiness, role-route readiness, each configured provider's binary availability and CLI compatibility, and MCP registration separately. Do not expose static admission, heartbeat, historical review, or `review_qualified` as setup dimensions.

Never authenticate a provider, inspect a prior run, or start a Mulgae heartbeat, review, qualification, preflight capture, live provider request, source transmission, or MCP server during setup. Doctor v2 may run only Mulgae's adapter-owned local version commands in its offline boundary.

For Gaori, support only stable `v0.1.13` through `v0.1.x`. Resolve one exact tag and use it for both the CLI and `use-gaori` source. Keep CLI installation or upgrade, user-scoped skill installation or replacement, repository config and ignore changes, and project-local MCP configuration as separate approval boundaries. Treat missing, incomplete, invalid, and duplicate skill installations and missing MCP registration independently from CLI health. Never start a Gaori run or MCP test command during setup.

Approval for one tool does not authorize another. Never use `sudo`, `--force`, destructive cleanup, credential extraction, provider invocation, source transmission, staging, committing, or pushing unless the user separately grants that exact authority.

For Podway, support only stable `v0.2.5` through `v0.2.x` on native Apple Silicon macOS. Resolve one exact tag and use it for both binaries and the `use-podway` source. Treat a missing, incomplete, invalid, or duplicate skill independently from CLI and repository readiness.

Keep release lookup, binary installation, user-scoped skill installation or replacement, LaunchAgent installation, repository initialization, managed-procedure installation or update, legacy-state recovery, and managed-Procedure removal as distinct proposed actions. None of these actions activates Podway for an Aquarium workflow.

Verify the release checksum before installing both matching binaries, then install or refresh the per-user LaunchAgent using the approved absolute daemon path. Disclose that the release is unsigned and not notarized, runs as a same-user local service after GUI login, and stores runtime state in the worktree.

If an installation is interrupted after Podway prepares authenticated service metadata, rerun the same approved `podway daemon install --daemon-path <absolute-podwayd-path>` command without a socket override. Do not edit service metadata or LaunchAgent files manually.

Never convert or delete Procedure v1 state automatically. On `LEGACY_PROCEDURE_STATE_UNSUPPORTED`, report the exact worktree and stable error code, apply the current backup policy, and separately propose the confirmed `podway reset --all` recovery. Do not treat the inspection status `not_configured` as legacy Procedure state.

Treat tracked `root-kernel-task-v2.yaml`, `root-kernel-goal-v2.yaml`, and `root-kernel-validation-v2.yaml` files as a product-rename migration, not as Procedure v1 runtime state. Report `migration_required`, require any active old session to reach an explicitly chosen terminal disposition first, then propose removal of the old managed files and installation of the corresponding `aquarium-*` files as separate approved actions. Never convert, cancel, reset, or delete runtime history as part of this migration.

Aquarium Podway readiness configuration has four disclosed parts:

- Copy all three plugin-owned procedure sources from [the bundled procedure directory](../../assets/podway/procedures/) byte-for-byte to `.podway/procedures/` and check each with `podway procedure check --warnings-as-errors`.
- `podway init` also creates `.podway/config.yaml`, `.podway/.gitignore`, and ignored runtime state; show the exact proposed files and diff before approval.
- When a managed procedure differs, show the exact source-to-project diff and obtain approval before replacing it; do not alter an active procedure snapshot.
- Treat partial installation as degraded readiness, not activation or legacy state.

Managed-Procedure removal is a separate destructive proposal. Show the exact managed procedure files to remove, preserve `.podway/config.yaml`, runtime state, custom procedures, and every session, and obtain explicit approval. Do not reset, cancel, or delete any session as part of setup or removal.

## Gate AGENTS.md With Two Approvals

Handle AGENTS.md independently from tool setup:

1. Ask whether to prepare a reference-based AGENTS.md proposal. Offer `Show proposal`, `Diagnose only`, and `Skip`.
2. Only after `Show proposal`, read [agents-guidance.md](references/agents-guidance.md), then classify existing text into duplicated skill behavior, repository-specific overrides, and ambiguous text that must be preserved.
3. Display the exact target path and complete proposed diff. Do not edit the file yet.
4. Ask whether to `Apply exactly this diff`, `Revise proposal`, or `Do not apply`.
5. Before applying, re-read the file and compare it with the bytes used to produce the proposal. If it changed, discard the approval, regenerate the diff, and ask again.
6. Apply only the approved diff. Then show the actual diff and verify that overrides and unrelated user content remain.

The first answer authorizes proposal preparation only. General setup approval, install approval, and the instruction to use this skill never authorize AGENTS.md mutation. Do not edit nested AGENTS.md, CLAUDE.md, stage, or commit without separate explicit approval.

## Report the Result

Report:

- selected, skipped, and planned tools;
- resolved versions and sources;
- each selected paired skill's comparison tag, exact `~/.agents/skills` target, `current`, `missing`, `different`, or `freshness_unverifiable` result, temporary-payload cleanup, and any installation or replacement decision;
- selected backup policy, existing state backed up or deliberately left without a backup, backup verification and restoration paths when applicable, and the disclosed recovery boundary;
- Sanho CLI, workspace, and `use-sanho` skill state separately;
- Mulgae CLI and Doctor v2 compatibility, project Config v3, local configuration, provider identity, binary availability, provider CLI compatibility, configured and role-route readiness, `use-mulgae` skill, installation prerequisites, and project MCP state separately;
- Gaori CLI, repository config, `use-gaori` skill, and project MCP state separately;
- Podway CLI, daemon, workspace, Aquarium readiness, legacy-state detection, and `use-podway` skill state separately;
- commands run and their exit status;
- native configuration and ignore paths changed;
- verification evidence and remaining auth or environment gaps;
- whether AGENTS.md was skipped, proposed, revised, or applied;
- worktree changes, with staging and publication state stated separately.

Do not claim a tool is configured merely because its binary exists. Do not claim AGENTS.md was approved when only a proposal was requested.
