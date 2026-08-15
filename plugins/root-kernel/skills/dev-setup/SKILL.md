---
name: dev-setup
description: "Diagnose and configure Root Kernel development tooling for a repository. Use when the user explicitly invokes $root-kernel:dev-setup; asks to install, initialize, repair, or audit the Sanho CLI or use-sanho skill, the Mulgae CLI, use-mulgae skill, Config v2, or project MCP, the Gaori CLI, use-gaori skill, or project MCP, the Podway CLI, daemon, use-podway skill, or Root Kernel procedures, or the third-party Lora skills; or wants to replace duplicated AGENTS.md tool guidance with skill references and repository-specific overrides."
---

# Development Setup

Configure selected development tools without inventing shared project state or silently rewriting agent guidance. Treat diagnosis, installation, native configuration, and AGENTS.md editing as distinct authority boundaries.

Read [podway-integration.md](../../references/podway-integration.md) whenever Podway is selected or the repository contains any managed Root Kernel procedure.

## Establish the Repository

1. Resolve the requested working directory to one Git root.
2. Read applicable instruction files and inspect the branch, upstream, staged, unstaged, and untracked state.
3. Resolve this skill's directory (the directory containing this `SKILL.md`) and, when `python3` is available, run `python3 <skill-directory>/scripts/inspect_tools.py --repository <git-root>`. Read its JSON as local diagnostic evidence, not as installation or mutation authority.
4. If `python3` is unavailable or the inspection script fails, report that gap and perform the same read-only discovery manually. Do not install Python as part of fallback diagnosis.
5. Discover existing tool guidance and verification commands from repository files before asking questions. Inspect the remaining state read-only; when a check would require reading credentials, contacting a network, or changing files, defer it to a separately authorized step.
6. Do not create or read `.root-kernel-dev-skills` or any equivalent central selection file.

## Use Ask/Answer for Decisions

Use the host's structured ask/answer tool, normally `request_user_input`, whenever it is available.

- Ask one to three short questions per call with two or three meaningful, mutually exclusive choices.
- Put the recommended choice first and label it recommended.
- Do not simulate a multiple-choice UI in prose.
- Use direct text only for an identifier that cannot be discovered or represented by choices, such as an unknown private documentation repository URL.
- If ask/answer is unavailable, ask one concise approval question at a time. Never infer approval from silence or from approval of a different setup action.

After read-only discovery, ask about Sanho, Mulgae, and Gaori in the first batch. Ask about Podway, Lora, and whether to prepare an AGENTS.md proposal in subsequent batches. For each active tool offer `Install and configure`, `Diagnose only`, and `Skip`, adapting the wording when it is already installed. For Sanho, Mulgae, Gaori, and Podway, make `Install or upgrade the CLI and paired skill` the recommended setup choice, but report each component independently and preserve a healthy CLI when its optional skill is absent.

When Mulgae or Gaori is selected, ask separately whether to configure that tool's project-local MCP; offer `Configure project MCP`, `Diagnose only`, and `Skip` and recommend configuration only for a trusted project.

When another Root Kernel skill routes a continuation request, treat it as scoped intake: the request must name the requesting skill, repository, exact failing tool or check, and evidence gap. Keep the read-only discovery above, then ask only about the named tool and anything its repair requires, including Podway repair or opt-out; skip the remaining batches and the AGENTS.md question unless the user asks for them, and end by reporting the resolved gap and the exact prompt that resumes the routing workflow.

Read [tool-catalog.md](references/tool-catalog.md) for every tool selected for diagnosis or setup.

A selection expresses intent only. It does not authorize a command that writes files, installs software, changes hooks, contacts a provider, or modifies user-global state.

## Propose Exact Setup Actions

For each selected tool:

1. Disclose the official release-metadata endpoint and bounded lookup needed to resolve the version and source provenance described in the tool catalog, then obtain explicit ask/answer approval for that network operation.
2. Only after lookup approval, resolve the exact stable version and source provenance. A lookup approval authorizes no installation or other mutation.
3. Show the exact install and initialization commands, network endpoints, target paths, native files, ignore changes, and expected side effects.
4. Identify existing state that will be preserved and any command that might stage files or install hooks.
5. Obtain separate explicit ask/answer approval for the displayed action.
6. Execute only the approved action, stop on unexpected prompts or side effects, and verify with read-only commands.

For Sanho, support only stable `v0.2.6` through `v0.2.x`. Resolve one exact tag and use it for both the CLI and `use-sanho` source. Keep CLI installation or upgrade, user-scoped skill installation or replacement, workspace initialization, and lifecycle repair as separate approval boundaries. A paired recommendation is not approval for both components. Treat missing, incomplete, invalid, and duplicate skill installations separately from CLI or workspace health.

For Mulgae, support only stable `v0.1.13` through `v0.1.x` on native Apple Silicon macOS. Resolve one exact tag and use it for both the CLI and `use-mulgae` source. Require Go `1.26.6` or newer for installation, without treating an older Go toolchain as a runtime failure of an already healthy binary.

Keep CLI installation or upgrade, user-scoped skill installation or replacement, project Config v2 and ignore changes, local bootstrap or refresh, and project-local MCP configuration as separate approval boundaries. Treat missing, incomplete, invalid, and duplicate skill installations and missing MCP registration independently from CLI and configuration health. Never start a Mulgae review, preflight capture, provider call, or MCP server during setup.

For Gaori, support only stable `v0.1.12` through `v0.1.x`. Resolve one exact tag and use it for both the CLI and `use-gaori` source. Keep CLI installation or upgrade, user-scoped skill installation or replacement, repository config and ignore changes, and project-local MCP configuration as separate approval boundaries. Treat missing, incomplete, invalid, and duplicate skill installations and missing MCP registration independently from CLI health. Never start a Gaori run or MCP test command during setup.

Approval for one tool does not authorize another. Never use `sudo`, `--force`, destructive cleanup, credential extraction, provider invocation, source transmission, staging, committing, or pushing unless the user separately grants that exact authority.

For Podway, support only stable `v0.2.1` through `v0.2.x` on native Apple Silicon macOS. Resolve one exact tag and use it for both binaries and the `use-podway` source. Keep release lookup, binary installation, user-scoped skill installation or replacement, LaunchAgent installation, repository initialization, managed-procedure installation or update, legacy-state recovery, and opt-out as distinct proposed actions. Treat a missing, incomplete, invalid, or duplicate skill independently from CLI and repository health.

Verify the release checksum before installing both matching binaries, then install or refresh the per-user LaunchAgent using the approved absolute daemon path. Disclose that the release is unsigned and not notarized, runs as a same-user local service after GUI login, and stores runtime state in the worktree.

Never convert or delete Procedure v1 state automatically. On `LEGACY_PROCEDURE_STATE_UNSUPPORTED`, report the exact worktree and stable error code, require the user to make any desired backup, and separately propose the confirmed `podway reset --all` recovery. Do not treat the inspection status `not_opted_in` as legacy Procedure state.

Repository opt-in has four disclosed parts:

- Copy all three plugin-owned procedure sources from [the bundled procedure directory](../../assets/podway/procedures/) byte-for-byte to `.podway/procedures/` and check each with `podway procedure check --warnings-as-errors`.
- `podway init` also creates `.podway/config.yaml`, `.podway/.gitignore`, and ignored runtime state; show the exact proposed files and diff before approval.
- When a managed procedure differs, show the exact source-to-project diff and obtain approval before replacing it; do not alter an active procedure snapshot.
- Treat partial installation as degraded, not legacy.

Opt-out is a separate destructive proposal. Show the exact managed procedure files to remove, preserve `.podway/config.yaml`, runtime state, custom procedures, and every non-Root-Kernel session, and obtain explicit approval. Do not reset, cancel, or delete any session as part of setup or opt-out.

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
- Sanho CLI, workspace, and `use-sanho` skill state separately;
- Mulgae CLI, project and local Config v2, `use-mulgae` skill, provider readiness, installation prerequisites, and project MCP state separately;
- Gaori CLI, repository config, `use-gaori` skill, and project MCP state separately;
- Podway CLI, daemon, workspace, Root Kernel opt-in, legacy-state detection, and `use-podway` skill state separately;
- commands run and their exit status;
- native configuration and ignore paths changed;
- verification evidence and remaining auth or environment gaps;
- whether AGENTS.md was skipped, proposed, revised, or applied;
- worktree changes, with staging and publication state stated separately.

Do not claim a tool is configured merely because its binary exists. Do not claim AGENTS.md was approved when only a proposal was requested.
