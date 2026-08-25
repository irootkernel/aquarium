# Changing Skills

Skill changes are contract changes, even when the implementation is Markdown. Treat triggers, ordering, approval language, evidence claims, and handoff fields as executable interfaces.

## Before Editing

1. Read the complete owning `SKILL.md`, its directly linked references, the matching Procedure if one exists, and the relevant validator assertions.
2. Identify whether the rule belongs in one entrypoint or a shared reference. Put cross-skill semantics in one shared owner and keep entrypoints focused on routing and lifecycle order.
3. Trace callers and consumers. A leaf skill can be correct in isolation while breaking an orchestrator's handoff or approval boundary.
4. Confirm the public disclosure impact in the root README, privacy policy, terms, testing contract, and changelog.

## Preserve Contract Shape

- Keep explicit invocation and implicit-handoff rules accurate in front matter. `task-commit` is the only current skill that permits implicit invocation.
- Separate read-only discovery from network lookup, installation, native configuration, repository edits, provider transmission, Git mutation, and publication.
- Make stale-approval conditions concrete. If the displayed diff, target SHA, tool version, or remote state changes, obtain approval again where required.
- State the evidence boundary with the success path. A command exit, schema match, tool result, runtime observation, and distribution proof are different claims.
- Preserve upstream ownership. Do not copy Lora, Lore, Ouroboros, Deslop, or tool implementation sources into Aquarium.

## Shared Handoffs

When adding or changing a handoff, define the producer, consumer, required fields, failure states, and authority that remains with each side. Prefer a bounded structured artifact only when another durable workflow needs it. Otherwise keep transient output in the native runtime.

For cross-repository work, carry the exact repository and commit identity. A downstream statement that work exists is not proof until the owning repository and required independent validation confirm the exact candidate.

## Verification

Run the focused checks for the changed skill and its helpers first. Then run `ruby tests/validate.rb` to catch cross-skill and documentation drift. Scenario-focused tests are required when changing approval behavior, recovery, cross-skill handoffs, or claims that a phrase-only validator cannot exercise.
