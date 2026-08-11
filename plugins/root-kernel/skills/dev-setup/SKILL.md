---
name: dev-setup
description: "Diagnose and configure Root Kernel development tooling for a repository. Use when the user explicitly invokes $root-kernel:dev-setup; asks to install, initialize, repair, or audit Sanho, Mulgae, Gaori, or the third-party Lora skills; asks whether the planned Podway integration is available; or wants to replace duplicated AGENTS.md tool guidance with skill references and repository-specific overrides."
---

# Development Setup

Configure selected development tools without inventing shared project state or silently rewriting agent guidance. Treat diagnosis, installation, native configuration, and AGENTS.md editing as distinct authority boundaries.

## Establish the Repository

1. Resolve the requested working directory to one Git root.
2. Read applicable instruction files and inspect the branch, upstream, staged, unstaged, and untracked state.
3. Resolve this skill's directory and, when `python3` is available, run `python3 <skill-directory>/scripts/inspect_tools.py --repository <git-root>`. Read its JSON as local diagnostic evidence, not as installation or mutation authority.
4. If `python3` is unavailable or the inspection script fails, report that gap and perform the same read-only discovery manually. Do not install Python as part of fallback diagnosis.
5. Discover existing tool guidance and verification commands from repository files before asking questions. Inspect any state that the script cannot determine without reading credentials, contacting a network, or changing files only through separately authorized steps.
6. Do not create or read `.root-kernel-dev-skills` or any equivalent central selection file.

Read [tool-catalog.md](references/tool-catalog.md) for every tool selected for diagnosis or setup. Read [agents-guidance.md](references/agents-guidance.md) only when the user requests an AGENTS.md proposal.

## Use Ask/Answer for Decisions

Use the host's structured ask/answer tool, normally `request_user_input`, whenever it is available.

- Ask one to three short questions per call with two or three meaningful, mutually exclusive choices.
- Put the recommended choice first and label it recommended.
- Do not simulate a multiple-choice UI in prose.
- Use direct text only for an identifier that cannot be discovered or represented by choices, such as an unknown private documentation repository URL.
- If ask/answer is unavailable, ask one concise approval question at a time. Never infer approval from silence or from approval of a different setup action.

After read-only discovery, ask about Sanho, Mulgae, and Gaori in the first batch. Ask about Lora and whether to prepare an AGENTS.md proposal in the second batch. For each active tool offer `Install and configure`, `Diagnose only`, and `Skip`, adapting the wording when it is already installed.

A selection expresses intent only. It does not authorize a command that writes files, installs software, changes hooks, contacts a provider, or modifies user-global state.

## Propose Exact Setup Actions

For each selected tool:

1. Resolve the version and source provenance described in the tool catalog.
2. Show the exact install and initialization commands, network endpoints, target paths, native files, ignore changes, and expected side effects.
3. Identify existing state that will be preserved and any command that might stage files or install hooks.
4. Obtain explicit ask/answer approval for the displayed action.
5. Execute only the approved action, stop on unexpected prompts or side effects, and verify with read-only commands.

Approval for one tool does not authorize another. Never use `sudo`, `--force`, destructive cleanup, credential extraction, provider invocation, source transmission, staging, committing, or pushing unless the user separately grants that exact authority.

Podway is a planned catalog entry only. Report it as unavailable for setup and do not install a binary, initialize state, or operate its daemon.

## Gate AGENTS.md With Two Approvals

Handle AGENTS.md independently from tool setup:

1. Ask whether to prepare a reference-based AGENTS.md proposal. Offer `Show proposal`, `Diagnose only`, and `Skip`.
2. Only after `Show proposal`, classify existing text into duplicated skill behavior, repository-specific overrides, and ambiguous text that must be preserved.
3. Display the exact target path and complete proposed diff. Do not edit the file yet.
4. Ask whether to `Apply exactly this diff`, `Revise proposal`, or `Do not apply`.
5. Before applying, re-read the file and compare it with the bytes used to produce the proposal. If it changed, discard the approval, regenerate the diff, and ask again.
6. Apply only the approved diff. Then show the actual diff and verify that overrides and unrelated user content remain.

The first answer authorizes proposal preparation only. General setup approval, install approval, and the instruction to use this skill never authorize AGENTS.md mutation. Do not edit nested AGENTS.md, CLAUDE.md, stage, or commit without separate explicit approval.

## Report the Result

Report:

- selected, skipped, and planned tools;
- resolved versions and sources;
- commands run and their exit status;
- native configuration and ignore paths changed;
- verification evidence and remaining auth or environment gaps;
- whether AGENTS.md was skipped, proposed, revised, or applied;
- worktree changes, with staging and publication state stated separately.

Do not claim a tool is configured merely because its binary exists. Do not claim AGENTS.md was approved when only a proposal was requested.
