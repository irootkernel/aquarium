---
name: war-room
description: "Diagnose one difficult bug and shape the next work unit with Ouroboros, without implementing a fix. Use when the user explicitly invokes $aquarium:war-room."
---

# War Room

Diagnose one difficult bug and stop at an evidence-backed work-unit proposal. Do not implement a fix, mutate production or shared services, stage, commit, publish, or edit the Design Gate registry.

Always read [evidence-residency.md](../../references/evidence-residency.md), then read [ouroboros-integration.md](../../references/ouroboros-integration.md) and [design-gates.md](../../references/design-gates.md) and use the default `aquarium-war-room-v2` Podway path. Keep repository sources read-only. Reproduce only in isolated fixtures or an already authorized safe environment, preserve commands and observations as orchestration evidence, distinguish symptoms from causes, and test competing hypotheses.

After the approved envelope, use installed upstream `$interview` and `$qa` as needed to challenge the investigation. Classify the result as exactly one of: a bounded task, a multi-work-unit epic, or investigation incomplete. Include scope, evidence, root cause or remaining hypotheses, acceptance evidence, dependencies, risks, and an explicit `Design Gate impact` on every resulting implementation task, propagating the epic decision when an epic is produced. Any gate candidate remains `Pending` for `$aquarium:design-qa`.

Run a final quality pass, record its adjudicated result at `quality`, and require `decide-quality` to pass with zero unresolved locally valid findings before showing the exact proposed roadmap or investigation-note diff. Apply it only after explicit approval and snapshot recheck.

Route every quality-driven evidence, classification, or draft revision back to `investigate`. For user-requested wording-only changes after a quality-passed draft is already on the valid trace, use only that draft's current allowed manual-rework target before recording an approval decision so the flow returns through `quality` and a fresh quality decision. If the user instead records `changes-requested`, preserve the unapplied proposal at `record-rejection` and close the session without document mutation.

End with the classification, local evidence references, applied documents, unresolved gaps, and the explicit next workflow. Never copy runtime paths or identities into the proposed roadmap or investigation note, and never continue into the fix.
