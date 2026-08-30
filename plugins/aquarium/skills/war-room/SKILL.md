---
name: war-room
description: "Diagnose one difficult bug and shape the next work unit with Ouroboros, without implementing a fix. Use when the user explicitly invokes $aquarium:war-room."
---

# War Room

Diagnose one difficult bug and stop at an evidence-backed work-unit proposal. Do not implement a fix, mutate production or shared services, stage, commit, or publish.

Always read [evidence-residency.md](../../references/evidence-residency.md), [ouroboros-integration.md](../../references/ouroboros-integration.md), [documentation-governance.md](../../references/documentation-governance.md), and [epic-execution-sot.md](../../references/epic-execution-sot.md), and use the default `aquarium-war-room-v2` Podway path. Keep repository sources read-only. Reproduce only in isolated fixtures or an authorized safe environment, preserve observations as orchestration evidence, and test competing hypotheses.

After approval, use installed upstream `$interview` and `$qa` as needed. Classify the result as one bounded task, one multi-work-unit epic, or investigation incomplete. Include scope, evidence, root cause or hypotheses, acceptance, dependencies, and risks on every implementation task. Apply the shared execution-SOT threshold to a multi-work-unit epic and create or revise its dossier only when required.

A bounded task added to an existing epic updates its dossier when one exists. When the resulting epic first meets the shared threshold, create and declare the dossier in the same approved work-definition diff; otherwise do not manufacture one.

Run a final quality pass, record its adjudicated result at `quality`, and require `decide-quality` to pass with zero unresolved locally valid findings before showing the exact proposed roadmap or investigation-note diff. Apply it only after explicit approval and snapshot recheck.

Route quality findings about the baseline or reproduction back to `capture-baseline`, and route classification or proposal findings back to `investigate`. For user-requested wording-only changes after a quality-passed draft is already on the valid trace, use only that draft's current allowed manual-rework target before recording an approval decision so the flow returns through `quality` and a fresh quality decision.

A `changes-requested` approval returns to `investigate`; no terminal route may bypass an approved task, epic, or incomplete-investigation document.

End with the classification, local evidence references, applied documents, unresolved gaps, and the explicit next workflow. Never copy runtime paths or identities into the proposed roadmap or investigation note, and never continue into the fix.
