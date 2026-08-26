---
name: refactor
description: "Shape one major refactor or behavior-change epic with Ouroboros, without implementing it. Use when the user explicitly invokes $aquarium:refactor."
---

# Refactor

Create or revise exactly one refactor epic in the canonical roadmap. Do not implement, stage, commit, publish, or edit the Design Gate registry.

Always read [evidence-residency.md](../../references/evidence-residency.md), then read [ouroboros-integration.md](../../references/ouroboros-integration.md), [design-gates.md](../../references/design-gates.md), and [documentation-governance.md](../../references/documentation-governance.md), and use the default `aquarium-design-v2` Podway path.

Resolve the target roadmap's recorded identity contract before allocating an epic or task ID. Trace current contracts, consumers, data and runtime seams, compatibility guarantees, migration ordering, rollback, observability, failure containment, and proof of behavior preservation or intentional change.

After the approved envelope, use installed upstream `$interview` and `$seed` as needed. Produce one ordered epic with explicit compatibility, migration, rollback, and verification ownership. Create or revise exactly one scope-local `TODO-*.md` dossier that declares the epic, owns its temporary goal, scope, task objectives, required and prohibited actions, and acceptance, is recorded in the adopted section of the TODO index, and is linked from the roadmap as `Detailed SOT`.

Put `Design Gate impact` on the epic and every implementation task as `Not required`, `Pending`, or resolved `GATE-*` IDs; new invariants remain pending for `$aquarium:design-qa`.

Run upstream `$qa`, adjudicate the draft, show the exact diff, and apply only after explicit approval and snapshot recheck. End with the epic identity, affected contracts, validation, gate status, and unresolved migration risks.
