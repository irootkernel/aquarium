---
name: war-room
description: "Diagnose one difficult bug and shape the next work unit with Ouroboros, without implementing a fix. Use when the user explicitly invokes $aquarium:war-room."
---

# War Room

Read [commit-attribution.md](../../references/commit-attribution.md) for message formatting and change origins, within this skill's existing effect boundaries.

Diagnose one difficult bug and stop at an evidence-backed work-unit proposal or an approved no-work outcome. Do not implement a fix, mutate production or shared services, or publish. Staging and committing diagnostic documents require the shared delivery-input commit boundary.

Always read [evidence-residency.md](../../references/evidence-residency.md), [ouroboros-integration.md](../../references/ouroboros-integration.md), [documentation-governance.md](../../references/documentation-governance.md), and [epic-execution-sot.md](../../references/epic-execution-sot.md). On the Podway path, also read [adaptive-execution.md](../../references/adaptive-execution.md#diagnosis). Select an adequate Diagnosis Procedure, preferring unchanged reuse; `aquarium-war-room-v2` retains its released reference contract. Use exact qualification, local retention and mapped prepared/running recovery before begin or work. Keep product and source behavior read-only; applying approved canonical diagnostic documents is a separate boundary. Reproduce only in isolated fixtures or an authorized safe environment, preserve observations as orchestration evidence, and test competing hypotheses.

After approval, use installed upstream `$interview` and `$qa` as needed. Classify the result as one bounded task, one multi-work-unit epic, investigation incomplete, or no work needed. Include scope, evidence, root cause or hypotheses, acceptance, dependencies, and risks on every implementation task. Apply the shared execution-SOT threshold to a multi-work-unit epic and create or revise its dossier only when required.

A bounded task added to an existing epic updates its dossier when one exists. When the resulting epic first meets the shared threshold, create and declare the dossier in the same approved work-definition diff; otherwise do not manufacture one.

Run a final quality pass, record its adjudicated result at the mapped quality operation (`quality` in the reference), and require the consuming quality Decision to pass with zero unresolved locally valid findings before showing the exact proposed canonical-document diff or no-change outcome. Apply it only after explicit approval and snapshot recheck.

Route quality findings about baseline or reproduction to their mapped baseline owner (`capture-baseline` in the reference), and classification or proposal findings to investigation (`investigate` in the reference). For user-requested wording-only changes after a quality-passed draft is already on the valid trace, use only that draft's current allowed manual-rework target before recording an approval decision so the flow returns through `quality` and a fresh quality decision.

An approval requesting changes returns to the mapped investigation owner (`investigate` in the reference); every terminal route requires an approved task, epic, incomplete-investigation record, or no-work outcome.

End with the classification, local evidence references, applied documents, unresolved gaps, and the next action, including no follow-up when warranted. Never copy runtime paths or identities into the proposed canonical documents, and never continue into the fix.

## Own Diagnostic Records and No-work Outcomes

Before drafting, choose an existing canonical owner from the repository role map:
specifications for durable requirements, ADRs for decisions, and operations
documentation for repeatable diagnosis or recovery. Propose an exact missing owner
and path before creating one. Do not create an investigation-log file merely to
store a run. Raw reproduction output, transcripts, and runtime identities remain
private orchestration evidence under the evidence-residency contract.

Select `decide-cause: no-work` only when current evidence shows that expected
behavior holds and no corrective work unit is needed. An unreproduced or unexplained
symptom remains incomplete. Record the rationale and next action in the mapped no-work proposal (`draft-no-work` in the reference),
then follow its quality, approval and document/no-change verification path. If no durable documentation change is warranted, seek approval for that
explicit no-change outcome and record its verification at `document`; do not
invent a Task or dossier. Otherwise apply only the approved canonical document.

Use the shared [QA outcome mapping](../../references/ouroboros-integration.md#interpret-qa-outcomes)
and [delivery-input commit boundary](../../references/ouroboros-integration.md#commit-approved-delivery-input).
Never treat diagnostic document approval as authority to implement the fix.

## Ordinary native orchestration

Follow [Design and diagnosis orchestration](../../references/design-diagnosis-orchestration.md) for ordinary v3 native assignments, grouped independent assessments, original evidence and recovery. Preserve this skill's original leaf, exact approval and effect boundaries. No native history, role snapshot or configuration qualification is required. Existing formal snapshots retain their original contracts; source updates do not authorize managed-file rollout.

Ordinary investigation changes use declared native rework. If a required route is absent from the running snapshot, preserve it and follow the shared [explicitly consented atomic transition](../../references/adaptive-execution.md#consented-atomic-supersede). Never replace a session to retrieve a missing report, reset review authority, or imply that a diagnosis repaired the defect.
