# Repository Operating Guidance

This reference is the `dev-setup` standard for root AGENTS.md and CLAUDE.md. General setup always reviews the complete instruction body against it and prepares a full reorganization where needed. Tool-limited requests and scoped continuations stay within their requested component and direct prerequisites. Honor explicit guidance exclusions, including `agents_guidance: skip`; diagnosis-only requests report findings without drafting a proposal.

Aim for the standard's full structure and behavior while preserving project-specific meaning. Rewrite, regroup, and consolidate common guidance as needed. If the complete review establishes that the files already meet the standard, report no change; equivalent wording alone is not a reason to rewrite.

The scope and root-cause principles incorporate guidance adapted from `multica-ai/andrej-karpathy-skills` commit `2c606141936f1eeef17fa3043a72095b4765b9c2`. Do not contact that repository or fetch its text while preparing a proposal. The seven-part core behavior below and this repository's instructions are the proposal authority.

## Required Structure

Use this order for both new and existing files. Reorganize the complete body to fit it while retaining the meaning of project-specific rules and applicable stricter constraints:

```markdown
# AGENTS.md

<one sentence naming the repository and declaring AGENTS.md as local agent guidance>

## Core Behavior

### 1. Lead with Conclusions

- State the result or current finding first, followed by useful evidence and material limits.
- Do not repeatedly restate requirements or narrate routine work.

### 2. Reuse Verified Information

- Inspect the requested code and its named authorities before changing anything. Resolve discoverable facts before asking Master.
- Reuse established facts instead of reading or searching for them again. Recheck only the affected information when relevant state changes, evidence conflicts, or missing context makes it unreliable.
- State material assumptions and surface meaningful trade-offs. Ask when unresolved ambiguity would materially change the result, and push back on conflicts with repository authority, safety, or Master's goal.

### 3. Act on Sufficient Evidence

- Stop investigating once the evidence supports action. When the root cause is established, implement the smallest complete, durable fix within the authorized scope.
- Weigh correctness, performance, maintainability, and structural fit rather than diff size alone. If a broader design exceeds scope, complete a bounded step that satisfies current acceptance criteria.
- Reuse established patterns. Avoid speculative features, abstractions, configurability, compatibility layers, and handling for states repository invariants make impossible. Simplify complexity that the required behavior does not justify.
- Touch only what the outcome and its verification require. Preserve unrelated user work, match local style, and remove only artifacts made obsolete by this change.
- Record only independent remaining work in the canonical `deferred-feedback` owner. If none exists, propose the entry and obtain approval before creating an owner. Promote epic-sized work to a TODO candidate or roadmap unit; never defer current correctness or acceptance work.

### 4. Carry Authorization Forward

- Continue already approved work without asking for confirmation again. Ask only when a material change exceeds that authorization or an applicable rule requires a distinct approval.
- Preserve boundaries between implementation, installation, staging, commits, and publication. Check for relevant state changes before acting on an approved proposal.

### 5. Verify in Proportion to Risk

- Define success checks before implementation. Verify the affected behavior and relevant failure paths with rigor proportionate to the actual risk.
- Run focused checks first and honor required repository gates. Broaden or repeat checks when changes, failures, or unresolved concerns justify it.
- Do not add tests merely to appear rigorous or use prose matching as a substitute for behavior verification.

### 6. Finish When Complete

- Continue until deliverables and required verification are complete or a concrete blocker prevents progress.
- Once material constraints are resolved or clearly reported, provide the handoff and stop. Report the result, necessary evidence, skipped checks and their reasons, and remaining uncertainty without opening unrelated work.

### 7. Delegate Selectively

- Use a sub-agent only for an independent task when the expected benefit outweighs coordination cost.
- Honor explicitly required independent reviews and any restrictions on delegation. Keep tightly coupled work local.

## Master Preferences

- Respond to Master in Korean using polite speech. When directly addressing the user, use exactly `Master`.
- Keep repository artifacts in the repository's established language and style. When no convention exists, use English unless Master requests otherwise.
- Report concise conclusions and useful evidence without exposing private chain-of-thought.

## Aquarium Development Guide

<references only for selected and installed Aquarium or paired skills, plus repository-specific command routing>

## Project Configuration

### Repository Index and Authorities

<project purpose, authority documents, key components or entrypoints, and canonical build, generation, lint, and test commands>

### Commit Messages

<mandatory repository-specific commit header and subject rules>

### Project-Specific Operating Rules

<only verified repository-specific constraints and exceptions>
```

Every applied AGENTS.md must contain all four top-level sections and all three `Project Configuration` subsections. Keep `Commit Messages` inside `Project Configuration`; never promote it to a separate top-level section or omit it because no rule was discovered.

## Build the Project Configuration From Evidence

Before drafting, establish the relevant facts from root `AGENTS.md` and `CLAUDE.md`, README files, task runners such as Makefiles or package scripts, manifests, CI configuration, roadmap and specification indexes, generated-file notices, and other repository-local authorities that materially affect agent work. Reuse facts already verified during setup; read or search further only to resolve a gap, conflict, or relevant state change. Use recent commit subjects only as evidence of a possible convention, never as authority by themselves.

Keep the index compact and point to authorities rather than copying domain design into AGENTS.md. Include only facts that affect navigation or decisions:

- the project's purpose and major components or entrypoints;
- authoritative roadmap, specification, lifecycle, and task sources, including an explicit precedence only when the repository defines one;
- canonical build, generation, lint, test, and release entrypoints;
- generated or sensitive paths, evidence artifacts, unavailable gates, and destructive or externally mutating boundaries;
- repository-specific tool routing, command IDs, version pins, timeouts, or approval rules.

Do not insert placeholders, guessed commands, exhaustive file inventories, copied architecture prose, or facts inferred only from directory names. Omit optional facts that cannot be established. `Commit Messages` is the exception: if no authoritative header rule exists, ask the user to choose one and do not finalize or apply the proposal until it is resolved.

## Add Aquarium References Without Copying Manuals

Adapt names only when the installed skill namespace differs. Include only references for selected and installed skills:

- Use `$aquarium:task-handler` for one named roadmap task.
- Use `$aquarium:epic-handler` to implement one roadmap epic as sequential task goals.
- Use `$aquarium:epic-validator` to cold-validate and remediate one completed roadmap epic.
- Use `$aquarium:new-project`, `$aquarium:new-feature`, or `$aquarium:refactor` for an explicitly requested Ouroboros-assisted project or epic design workflow.
- Use `$aquarium:war-room` to diagnose one difficult bug and stop at a task, epic, or incomplete-investigation proposal.
- Use `$aquarium:dev-setup-global` to diagnose, install, or update supported user-global development tools, paired skills, services, and global MCP state. Requests to install or update only the Aquarium plugin belong to the host's plugin-management flow; do not load this skill or run global setup diagnostics for those requests.
- Use `$aquarium:dev-setup` to diagnose or configure repository-local tooling and operating guidance.
- Use `$aquarium:docs-setup` to audit, establish, adopt, or migrate canonical documentation structure and roadmap IDs.
- Use `$aquarium:test-setup` to audit or configure the common Make or Bun testing contract and evidence-backed legacy waivers.
- Use `$aquarium:release-handler` for one stable release lifecycle and `$aquarium:release-qa` for its exact committed-candidate scenario verification.
- Use `$use-dolgorae` for explicitly requested workspace, global Profile, review, External Specialist Engagement, and recovery operations. Keep execution and lifecycle rules in the paired skill.
- Use `$use-sanho` at an authorized commit or push boundary in a Sanho-managed repository, or for an explicitly requested Sanho operation.
- Use `$use-mulgae` as the native authority for authorized Mulgae asynchronous review, waiting, cancellation, evidence inspection, and recovery. Aquarium workflows own the target, approval criteria, and review-round accounting.
- Use `$use-gaori` as the native authority for asynchronous execution, waiting, cancellation, and recovery when a selected check uses Gaori. Repository requirements select the command; Aquarium evaluates its terminal result and evidence separately.
- Use `$use-gaori-status` for Gaori-calculated duration, outcome history, and detailed timing explanations. Keep test execution and one-off live estimates with `$use-gaori`; a missing status skill does not block a selected check.
- Use `$use-sorage` at session start and before every task in a Sorage-enabled repository. Resolve every inbox, outbox, Handoff, review, retention, deletion, and Vault operation through that paired skill; never edit the managed Vault or derived `.sorage/INBOX.md` directly.
- Let Aquarium workflows use Podway by default for Git-backed work unless the current user opts out before the first managed-session mutation. No Aquarium skill owns a Podway session; only when starting a different session should the workflow ask whether to preserve, finish, delete, or replace the existing one.
- Use `$use-podway` directly for an explicitly requested Procedure v2 lifecycle, goal, diagnosis, recovery, cancellation, or discard operation. Route Procedure authoring to the separately installed `$create-podway-procedure` maintainer skill.
- Use `$lore-commits` for non-trivial commit messages and `$lore-query` to inspect recorded decision context.
- Use the separately installed upstream `$deslop` skill for task-owned cleanup when an Aquarium workflow requests it.
- Use the separately installed upstream `$humanizer` skill once as the final prose pass for English human-authored documentation.
- Use the separately installed upstream `$humanize-korean` skill once as the final prose pass for Korean human-authored documentation. Keep its `_workspace/` output untracked and remove it after applying the accepted text.
- For either writing pass, preserve meaning, facts, code, commands, identifiers, URLs, citations, quotes, legal text, and generated content. Route mixed-language prose by block, and fail closed with the unchanged draft when the skill is unavailable or validation fails.
- Keep `.mulgae/**`, `.gaori/runs/**`, `.podway/runtime/**`, derived `.sorage/**`, and disposable roots as local runtime evidence. Do not cite their paths or identities as durable evidence in tracked documentation or commit messages; use an approved tracked `aquarium.promoted-evidence/v1` package only when a downstream consumer genuinely requires retained evidence.
  Declare at most one custom root with the exact Project Configuration entry `Aquarium evidence root: <repository-relative-path>`; otherwise use `evidence/aquarium/`. Promotion accepts only reviewed bounded non-sensitive structured evidence and never accepted reports, raw logs, excerpts, provider prose, runtime identities, or machine-specific paths.
- Repository-specific rules in `Project Configuration` override these defaults.

When `$aquarium:release-handler` is selected, inspect established changelog and release-note authorities. Preserve one existing unambiguous owner and propose the exact Project Configuration entry `Aquarium release notes: <repository-relative-path>`. When no owner exists, ask before proposing a new root `CHANGELOG.md`; never infer enrollment from a filename, create release history from commit subjects alone, or replace an established changelog. Keep the selected path regular, non-symlinked, tracked, and inside the repository.

Omit `$use-*`, Lore, Deslop, Humanizer, im-not-ai, or Aquarium workflow references whose corresponding skills are unavailable or not selected for project guidance. A CLI alone does not justify a paired-skill reference. Sorage guidance additionally requires the selected repository to resolve as an active registered Project. Put exact repository commands and stricter exceptions in `Project Configuration`; do not duplicate generic tool manuals, lifecycle procedures, recovery instructions, or Lore trailer vocabularies.

## Reconcile Existing Instruction Files

Classify existing AGENTS.md and substantive CLAUDE.md text as:

- common behavior already covered by the required structure;
- repository-specific guidance to retain under `Project Configuration`;
- a stricter rule that must override a common default;
- an actual conflict or ambiguity requiring a focused user decision;
- unrelated content that must remain unchanged.

Use this classification to rebuild the instruction body around the required hierarchy. Rewrite common guidance to express the seven core behaviors, merge duplicates without weakening them, and place project-specific rules under `Project Configuration`. Preserve the meaning of user-authored rules and applicable stricter constraints; ask only about actual semantic conflicts. Preserve unrelated content and tool-managed blocks, including their markers. Do not add generated markers or rewrite equivalent wording solely to match the template byte-for-byte.

AGENTS.md is the canonical instruction body. Handle root CLAUDE.md as follows:

- If absent, propose the delegation file below.
- If it already contains exactly equivalent delegation, leave it unchanged.
- If it contains substantive guidance, merge every non-duplicate or stricter rule into AGENTS.md, resolve conflicts with the user, then propose replacing CLAUDE.md with the delegation file.
- Never replace substantive CLAUDE.md until its retained guidance is visible in the same complete proposal.

```markdown
# CLAUDE.md

This repository uses `AGENTS.md` as the canonical agent instruction file.

Claude Code agents must read and follow `AGENTS.md` first. If any guidance here conflicts with `AGENTS.md`, `AGENTS.md` wins.
```

Do not edit nested AGENTS.md, nested CLAUDE.md, or other agent instruction formats by default.

## Diagnose, Propose, and Apply

Report the complete review's findings: standard structure and behavior coverage, missing commit-message authority, duplicated or conflicting guidance, CLAUDE.md delegation state, and the evidence for project indexing. An explicit diagnosis-only request stops after this report. Otherwise, when reorganization is needed:

1. Record the exact root AGENTS.md and CLAUDE.md paths and their current bytes, object hashes, or explicit absence.
2. Resolve every conflict and the mandatory commit-message rule before presenting an applicable proposal.
3. Show one complete combined diff for both files, labeling retained repository rules through their final placement.
4. Explain ambiguous text left unchanged and every fact omitted for lack of authority.
5. Use existing authorization when it covers the exact displayed diff; otherwise ask for approval once. The user may request revision or decline it.
6. Immediately before writing, re-read both targets and require them to match the snapshots used for the proposal. A change to either target invalidates approval for the combined diff.
7. Apply only the approved diff, then show the actual diff and verify the required structure, mandatory commit-message subsection, CLAUDE.md delegation, retained overrides, and unrelated content.

Proposal approval covers only the exact displayed root instruction-file diff. It does not authorize nested-file edits, tool setup, staging, committing, or publication.

## Manual Verification Scenarios

These scenarios describe expected outcomes for Master's separate verification of skill changes. They are not recorded results, and structural checks do not prove them.

| Scenario | Expected behavior |
| --- | --- |
| General setup with fragmented or repetitive guidance | Review the complete body and propose one combined diff that reorganizes it around the standard, even when tool configuration is healthy. |
| Guidance already meets the standard | Finish the full review and report no change; do not rewrite equivalent wording. |
| Project-specific constraints or tool-managed blocks | Preserve their meaning and managed content; ask only about actual semantic conflicts. |
| Substantive CLAUDE.md | Retain every non-duplicate or stricter rule in the combined proposal before replacing it with delegation. |
| Tool-limited request, scoped continuation, or guidance `skip` | Keep the requested scope without adding a whole-file guidance proposal. |
| Diagnosis-only request | Report the review findings without drafting or applying a proposal. |
| Approved proposal or changed target snapshot | Reuse approval for the unchanged diff; if either target changes, invalidate the combined approval and prepare a current proposal. |
