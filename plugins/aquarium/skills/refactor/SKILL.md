---
name: refactor
description: "Shape one major refactor or behavior-change epic with Ouroboros, without implementing it. Use when the user explicitly invokes $aquarium:refactor."
---

# Refactor

Read [commit-attribution.md](../../references/commit-attribution.md) for message formatting and change origins, within this skill's existing effect boundaries.

Create or revise exactly one refactor epic in the canonical roadmap. Do not implement or publish. Staging and committing approved documents require the separate delivery-input boundary in the shared integration contract.

Always read [evidence-residency.md](../../references/evidence-residency.md), then read [ouroboros-integration.md](../../references/ouroboros-integration.md), [documentation-governance.md](../../references/documentation-governance.md), and [epic-execution-sot.md](../../references/epic-execution-sot.md), and use the default `aquarium-design-v2` Podway path.

Resolve the target roadmap's recorded identity contract before allocating an epic or task ID. Trace current contracts, consumers, data and runtime seams, compatibility guarantees, migration ordering, rollback, observability, failure containment, and proof of behavior preservation or intentional change.

After the approved envelope, use installed upstream `$interview` and `$seed` as needed. Produce one ordered epic with explicit compatibility, migration, rollback, and verification ownership. Apply the shared execution-SOT threshold; create or revise one scope-local dossier only when required, otherwise keep the complete execution contract in the roadmap and at most two requirement-bearing canonical documents.

Run upstream `$qa`, adjudicate the draft, show the exact diff, and apply only after explicit approval and snapshot recheck. End with the epic identity, affected contracts, validation, and unresolved migration risks.

Apply the shared QA outcome mapping and [delivery-input commit boundary](../../references/ouroboros-integration.md#commit-approved-delivery-input). Report whether documents are applied or committed before naming the next explicit workflow.
