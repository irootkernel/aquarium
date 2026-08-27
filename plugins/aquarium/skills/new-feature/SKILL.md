---
name: new-feature
description: "Shape one feature epic for an existing project with Ouroboros, without implementing it. Use when the user explicitly invokes $aquarium:new-feature."
---

# New Feature

Create or revise exactly one feature epic in an existing project's canonical roadmap. Do not implement, stage, commit, or publish.

Always read [evidence-residency.md](../../references/evidence-residency.md), then read [ouroboros-integration.md](../../references/ouroboros-integration.md) and [documentation-governance.md](../../references/documentation-governance.md), and use the default `aquarium-design-v2` Podway path.

Resolve the target roadmap's recorded identity contract before allocating an epic or task ID. Establish repository authority, current architecture and behavior, epic identity, user outcome, non-goals, dependencies, migration needs, failure behavior, rollout boundary, and acceptance evidence.

After the approved envelope, use installed upstream `$interview`, `$pm`, or `$seed` only as needed. Produce one coherent epic with ordered work units and explicit ownership. Create or revise exactly one scope-local `TODO-*.md` dossier that declares the epic, owns its temporary goal, scope, task objectives, required and prohibited actions, and acceptance, is recorded in the adopted section of the TODO index, and is linked from the roadmap as `Detailed SOT`.

Run upstream `$qa`, adjudicate the draft, show the exact roadmap and documentation diff, and apply it only after explicit approval and snapshot recheck. End with the epic identity, applied paths, validation, and implementation blockers.
