---
name: war-room
description: "Diagnose one difficult bug and shape the next work unit with Ouroboros, without implementing a fix. Use when the user explicitly invokes $aquarium:war-room."
---

# War Room

Diagnose one difficult bug and stop at an evidence-backed work-unit proposal. Do not implement a fix, mutate production or shared services, stage, commit, or publish.

Always read [evidence-residency.md](../../references/evidence-residency.md), [ouroboros-integration.md](../../references/ouroboros-integration.md), and [documentation-governance.md](../../references/documentation-governance.md), and use the default `aquarium-war-room-v2` Podway path. Keep repository sources read-only. Reproduce only in isolated fixtures or an authorized safe environment, preserve observations as orchestration evidence, and test competing hypotheses.

After approval, use installed upstream `$interview` and `$qa` as needed. Classify the result as one bounded task, one multi-work-unit epic, or investigation incomplete. Include scope, evidence, root cause or hypotheses, acceptance, dependencies, and risks on every implementation task. A multi-work-unit epic includes one scope-local active dossier recorded in the adopted TODO index and linked as `Detailed SOT`.

A bounded task added to an existing epic updates its dossier; when it gives a task-less placeholder its first task, create and declare the dossier, record it in the adopted TODO index, and link it as `Detailed SOT`.

Run a final quality pass, record its adjudicated result at `quality`, and require `decide-quality` to pass with zero unresolved locally valid findings before showing the exact proposed roadmap or investigation-note diff. Apply it only after explicit approval and snapshot recheck.

Route quality findings about the baseline or reproduction back to `capture-baseline`, and route classification or proposal findings back to `investigate`. For user-requested wording-only changes after a quality-passed draft is already on the valid trace, use only that draft's current allowed manual-rework target before recording an approval decision so the flow returns through `quality` and a fresh quality decision.

A `changes-requested` approval returns to `investigate`; no terminal route may bypass an approved task, epic, or incomplete-investigation document.

End with the classification, local evidence references, applied documents, unresolved gaps, and the explicit next workflow. Never copy runtime paths or identities into the proposed roadmap or investigation note, and never continue into the fix.
