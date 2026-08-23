---
name: new-feature
description: "Shape one feature epic for an existing project with Ouroboros, without implementing it. Use when the user explicitly invokes $aquarium:new-feature."
---

# New Feature

Create or revise exactly one feature epic in an existing project's canonical roadmap. Do not implement, stage, commit, publish, or edit the Design Gate registry.

Always read [evidence-residency.md](../../references/evidence-residency.md), then read [ouroboros-integration.md](../../references/ouroboros-integration.md), [design-gates.md](../../references/design-gates.md), and [documentation-governance.md](../../references/documentation-governance.md), and use the default `aquarium-design-v2` Podway path.

Resolve the target roadmap's recorded identity contract before allocating an epic or task ID. Establish repository authority, current architecture and behavior, epic identity, user outcome, non-goals, dependencies, migration needs, failure behavior, rollout boundary, and acceptance evidence.

After the approved envelope, use installed upstream `$interview`, `$pm`, or `$seed` only as needed. Produce one coherent epic with ordered work units and explicit ownership. Put an explicit `Design Gate impact` of `Not required`, `Pending`, or resolved `GATE-*` IDs on the epic and every implementation task, propagating the epic decision unless a task has a narrower resolved impact. A new or changed invariant must remain `Pending` until a separate `$aquarium:design-qa` run resolves it.

Run upstream `$qa`, adjudicate the draft, show the exact roadmap and documentation diff, and apply it only after explicit approval and snapshot recheck. End with the epic identity, applied paths, validation, gate status, and implementation blockers.
