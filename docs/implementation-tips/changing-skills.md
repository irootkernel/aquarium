# Changing Skills

Skill changes are contract changes, even when the implementation is Markdown. Treat triggers, ordering, approval language, evidence claims, and handoff fields as executable interfaces.

## Before Editing

1. Read the complete owning `SKILL.md`, its directly linked references, and the matching Procedure if one exists.
2. Identify whether the rule belongs in one entrypoint or a shared reference. Put cross-skill semantics in one shared owner and keep entrypoints focused on routing and lifecycle order.
3. Trace callers and consumers. A leaf skill can be correct in isolation while breaking an orchestrator's handoff or approval boundary.
4. Confirm the public disclosure impact in the root README, privacy policy, terms, testing contract, and changelog.

## Preserve Contract Shape

- Keep invocation and implicit-handoff rules accurate in front matter. `task-commit` is the only skill that permits implicit workflow execution; `orca-review` additionally permits discovery from an explicit target-and-reviewer request.
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
