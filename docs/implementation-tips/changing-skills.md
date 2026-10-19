# Changing Skills

Skill changes are contract changes, even when the implementation is Markdown. Treat triggers, ordering, approval language, evidence claims, and handoff fields as executable interfaces.

## Before Editing

1. Read the complete owning `SKILL.md`, its directly linked references, and the matching Procedure if one exists.
2. Identify whether the rule belongs in one entrypoint or a shared reference. Put cross-skill semantics in one shared owner and keep entrypoints focused on routing and lifecycle order.
3. Trace callers and consumers. A leaf skill can be correct in isolation while breaking a Coordinator's handoff or approval boundary.
4. Confirm the public disclosure impact in the root README, privacy policy, terms, testing contract, and changelog.

## Preserve Contract Shape

- Keep invocation and implicit-handoff rules accurate in front matter. `task-commit` permits implicit workflow execution; `herdr-review` permits discovery from an explicit target-and-reviewer request. `dev-setup` supports natural-language repository setup requests, including Sorage Project setup, within the selected component scope.
- Separate read-only discovery from network lookup, installation, native configuration, repository edits, provider transmission, Git mutation, and publication.
- Make stale-approval conditions concrete. If the displayed diff, target SHA, tool version, or remote state changes, obtain approval again where required.
- State the evidence boundary with the success path. A command exit, schema match, tool result, runtime observation, and distribution proof are different claims.
- Preserve upstream ownership. Do not copy Lora, Lore, Ouroboros, Deslop, Humanizer, im-not-ai, or tool implementation sources into Aquarium.

## Shared Handoffs

When adding or changing a handoff, define the producer, consumer, required fields, failure states, and authority that remains with each side. Prefer a bounded structured artifact only when another durable workflow needs it. Otherwise keep transient output in the native runtime.

For cross-repository work, carry the exact repository and commit identity. A downstream statement that work exists is not proof until the owning repository and required independent validation confirm the exact candidate.

## Verification

Run `ruby tests/validate.rb` for package structure and local references. Run focused Python tests when executable helpers change. Keep these checks minimal: do not encode skill sentences, ordering, whitespace, or private source fragments as assertions.

Master performs skill functional verification separately after updates. Report which multi-step workflows, decision points, recommendations, approval boundaries, recovery paths, and handoffs need manual verification. Do not add an automated LLM gate or treat a passing structural check as a functional result.

For Herdr changes, use the [qualification guide](qualifying-herdr-review.md).
Cover both reviewer kinds, all supported targets and purposes, context gaps,
recovery of the same operation, legacy state and isolation between peer routes.
Record each actual outcome separately from static checks and Master's manual acceptance.

### Review result handoffs

Use the [result handoff contract](../../plugins/aquarium/references/review-result-handoff.md)
to distinguish production, submission and recipient readback. Check the actual
native surface and its expected participant set:

- For inline, API or host-returned results, read the complete report through the
  returned handle or receipt. A Markdown file is not required.
- For temporary-file delivery, confirm that the producer finished and read back
  the file, returned its actual absolute path, and the recipient opened it in
  its own filesystem view. Check missing or unreadable paths and different
  working directories; preserve the file until the recipient reads it.
- For console, pipe or captured output, distinguish report content from
  diagnostics. Recover truncated or interrupted content from the same operation
  before considering a fresh assessment. An exit or completion notice is not
  the report.
- Collect every expected base, native child and applicable UI report. Carry
  the original goal, finding decisions, reasons and correction evidence into
  the next authorized Brief. Recovery preserves findings and ordinals.

Use disposable fixtures where executable interfaces own changed behavior,
including paths with spaces or non-ASCII characters and temporary-root choice
when applicable. For instruction-only handoffs, review producer/consumer
contracts and available native observations. Do not build a synthetic relay or
prose-matching tests to test instructions. Review quality remains a qualitative
judgment against the original goal and evidence.

These handoff checks add no dedicated VM campaign, route-by-host matrix or
automated LLM evaluation. Existing candidate-installation, breaking-update and
release verification requirements remain under their current owners. Record
unperformed native scenarios as unverified; one successful review establishes
only its own observed operation.
