# Repository Operating Guidance

Use this reference only after the user selects `Show proposal` or `Diagnose only` for repository guidance. Diagnosis uses its structure and evidence rules without drafting; only `Show proposal` authorizes proposal preparation. A proposal creates or reconciles a repository operating contract and is not limited to tool guidance.

The four-part core behavior below is adapted, rather than copied verbatim, from the Karpathy-inspired guidance at `multica-ai/andrej-karpathy-skills` commit `2c606141936f1eeef17fa3043a72095b4765b9c2`. Do not contact that repository or fetch its text while preparing a proposal. The bundled structure and this repository's instructions are the proposal authority.

## Required Structure

Use this order for a new file and reconcile an existing file toward it when content can be moved without changing its meaning:

```markdown
# AGENTS.md

<one sentence naming the repository and declaring AGENTS.md as local agent guidance>

## Core Behavior

### 1. Inspect Before Acting

- Resolve repository facts and named authorities before implementation.
- State material assumptions, surface trade-offs, and ask when unresolved ambiguity would materially change the result.
- Push back when a request conflicts with repository authority, safety, or the user's stated goal.

### 2. Prefer the Smallest Complete Solution

- Implement only the verified requirement and reuse established patterns.
- Avoid speculative features, abstractions, configurability, and compatibility layers.
- Simplify an implementation whose size or complexity is not justified by its behavior.

### 3. Make Surgical Changes

- Touch only what the requested outcome and its verification require.
- Preserve unrelated work and match local style.
- Remove only artifacts made obsolete by the current change.

### 4. Work Toward Verifiable Goals

- Define success checks before implementation.
- Match verification strength to the claimed behavior and relevant failure paths.
- Continue until the result is verified or a concrete blocker is established; report skipped checks and remaining uncertainty.

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

Before drafting, inspect the root `AGENTS.md` and `CLAUDE.md`, README files, task runners such as Makefiles or package scripts, manifests, CI configuration, roadmap and specification indexes, generated-file notices, and other repository-local authorities that materially affect agent work. Use recent commit subjects only as evidence of a possible convention, never as authority by themselves.

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
- Use `$aquarium:design-qa` to create, change, reactivate, or retire local Design Gates.
- Use `$aquarium:dev-setup` to diagnose or configure development tooling and repository operating guidance.
- Use `$aquarium:test-setup` to audit or configure the common Make or Bun testing contract and evidence-backed legacy waivers.
- Use `$use-sanho` at an authorized commit or push boundary in a Sanho-managed repository, or for an explicitly requested Sanho operation.
- Use `$use-mulgae` for an authorized Mulgae review, run inspection, finding follow-up, configuration diagnosis, cleanup plan, or recovery.
- Use `$use-gaori` when a selected long or noisy check is routed through Gaori or existing Gaori evidence must be inspected.
- Let Aquarium workflow owners use Podway by default for Git-backed workflows unless the current user opts out before the first managed-session mutation; Aquarium workflow skills retain their stricter roadmap, ownership, and approval rules.
- Use `$use-podway` directly for an explicitly requested Procedure v2 lifecycle, authoring, diagnosis, recovery, cancellation, or discard operation.
- Use `$lore-commits` for non-trivial commit messages and `$lore-query` to inspect recorded decision context.
- Use the separately installed upstream `$deslop` skill for task-owned cleanup when an Aquarium workflow requests it.
- Repository-specific rules in `Project Configuration` override these defaults.

Omit `$use-*`, Lore, Deslop, or Aquarium workflow references whose corresponding skills are unavailable. A CLI alone does not justify a paired-skill reference. Put exact repository commands and stricter exceptions in `Project Configuration`; do not duplicate generic tool manuals, lifecycle procedures, recovery instructions, or Lore trailer vocabularies.

## Reconcile Existing Instruction Files

Classify existing AGENTS.md and substantive CLAUDE.md text as:

- common behavior already covered by the required structure;
- repository-specific guidance to retain under `Project Configuration`;
- a stricter rule that must override a common default;
- an actual conflict or ambiguity requiring a focused user decision;
- unrelated content that must remain unchanged.

Merge clear duplicates without weakening them. Preserve stricter rules and user-authored content. Moving content into the required hierarchy is allowed only in the displayed proposal and must not change its meaning. Do not rewrite a file merely for formatting or insert generated markers.

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

For `Diagnose only`, report the presence and coverage of the required structure, missing commit-message authority, duplicated or conflicting guidance, CLAUDE.md delegation state, and the local evidence available for project indexing. Do not draft or mutate files.

For `Show proposal`:

1. Record the exact root AGENTS.md and CLAUDE.md paths and their current bytes, object hashes, or explicit absence.
2. Resolve every conflict and the mandatory commit-message rule before presenting an applicable proposal.
3. Show one complete combined diff for both files, labeling retained repository rules through their final placement.
4. Explain ambiguous text left unchanged and every fact omitted for lack of authority.
5. Ask whether to `Apply exactly this diff`, `Revise proposal`, or `Do not apply`.
6. Immediately before writing, re-read both targets and require them to match the snapshots used for the proposal. A change to either target invalidates approval for the combined diff.
7. Apply only the approved diff, then show the actual diff and verify the required structure, mandatory commit-message subsection, CLAUDE.md delegation, retained overrides, and unrelated content.

Proposal approval covers only the exact displayed root instruction-file diff. It does not authorize nested-file edits, tool setup, staging, committing, or publication.
