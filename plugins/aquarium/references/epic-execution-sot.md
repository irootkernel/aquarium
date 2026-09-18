# Epic Execution SOT

Use this contract when an Aquarium design workflow defines an epic or a handler or validator resolves the context needed to execute or validate one. A dossier is the default consolidated execution SOT. When no dossier is declared, an explicit waiver permits execution from a complete composite execution SOT.

## Decide When to Create a Dossier

At work-definition time, create one active dossier when either condition holds:

- the epic has three or more member tasks, counting the complete canonical membership rather than only unfinished tasks;
- goal, scope, constraints, task objectives, prohibited actions, acceptance, or required handoff ownership is distributed across three or more requirement-bearing canonical documents.

Count the roadmap as a requirement-bearing document only when it owns execution requirements beyond identity, ordering, dependencies, lifecycle vocabulary, and status. Do not count implementation outputs, tests, generated artifacts, evidence, or specifications and architecture documents first created during delivery; classify the planned execution context before implementation begins.

An epic may proceed without a dossier only when repository discovery still yields an unambiguous goal, scope, task identity and lifecycle, dependency ordering, acceptance, required artifacts and handoffs, and every safety-critical external-action boundary, and the user explicitly waives the dossier. Missing semantic information blocks the workflow regardless of file count and cannot be waived.

## Create or Revise the Execution SOT

`$aquarium:new-project`, `$aquarium:new-feature`, `$aquarium:refactor`, and `$aquarium:war-room` own dossier creation and revision when they define work meeting the threshold. Use the repository's declared organization. Under Aquarium's default profile, create or reuse one scope-local `TODO-*.md`, record it in the adopted TODO index, and link it from every consumer epic as `Detailed SOT`. A shared dossier must identify its consumer epic IDs without taking ownership of their roadmap lifecycle.

Consolidate execution decisions without copying canonical product truth. When requirements already live in several canonical owners, use the dossier as a thin integration map that links each owner, maps member tasks and dependencies, and states cross-document acceptance and handoff boundaries. The roadmap remains the sole owner of identity, ordering, dependencies, lifecycle vocabulary, and status.

When a design workflow produces a small epic below the threshold, keep its complete execution context in the roadmap and at most two appropriate canonical documents. Do not create an empty or ceremonial dossier.

## Consume and Validate the Execution SOT

`$aquarium:epic-handler` and `$aquarium:task-handler` discover the canonical roadmap, documentation index, repository guidance, and requirement-bearing documents before requesting approval. Use a linked active dossier when one exists. Treat a dossier as absent only when the canonical roadmap and document links declare none. If the epic declares a dossier but its link cannot be resolved under the repository's documentation rules, treat that broken link as an unresolved requirement owner. When no dossier is declared, resolve the canonical document set collectively as a composite execution SOT.

Before mutation, the handler's decision-complete plan must disclose that no dossier is declared and identify the canonical source paths and owners for the goal, scope, constraints and prohibited actions, complete task membership and dependency order, acceptance, required artifacts, handoffs, and safety-critical external-action boundaries. For work below the creation threshold, the plan approval must also explicitly waive the dossier. Generic plan approval, discussion, or partial agreement is not a waiver.

When work meets either creation threshold and no dossier is declared, first explain the coordination risk, recommend creating the dossier, and ask the user to choose between routing to the appropriate work-definition skill or considering a waiver. Choosing to consider a waiver authorizes only preparation of the composite-SOT plan. The plan must disclose the risk again, and execution requires a second explicit approval that both accepts the plan and waives the dossier. If an approved source set or its requirements change materially, update the plan and obtain approval again before further mutation; when the revised source set still has no dossier, renew the applicable waiver in that approval.

Approval cannot supply missing product meaning. When discovery cannot resolve a required semantic owner or the composite set is ambiguous or incomplete, stop before mutation and report the exact gap. An unresolvable declared dossier is such a gap, not dossier absence. Route revision to `new-feature` for ordinary feature work, `refactor` for refactor work, `war-room` for a diagnosed difficult bug, or `new-project` while shaping a new project. Ask only when that ownership is ambiguous, and never route dossier creation to `docs-setup`.

Leaf task phases consume the handler-resolved execution SOT and update a dossier only when one exists. They do not independently manufacture a dossier requirement.

For an active or in-review epic, `$aquarium:epic-validator` uses the linked dossier or applies the same waiver flow before validating a disclosed composite execution SOT. Its validation-envelope approval carries the explicit waiver for work below the creation threshold and is the second confirmation when the work meets a creation threshold. If the resolved source set or its requirements change materially after approval, update the envelope and renew the applicable waiver before further mutation. For a completed epic, validate acceptance from its current canonical outcomes and repository-defined historical sources without requesting a waiver or recreating a deleted temporary dossier. Report the exact missing semantic owner when the completed state cannot be validated.

## Close Out Without Manufacturing Documentation

When a dossier exists, keep it current across member tasks and consumer epics and follow the repository's declared closeout lifecycle. Before changing or deleting it, inventory all canonical roadmap references to that exact dossier. Closing one epic removes or replaces only that epic's link and must retain the dossier and TODO index entry while another consumer epic remains non-terminal or another epic still canonically references it.

Under Aquarium's default profile, promote durable information for the closing epic and replace only its `Detailed SOT` with valid `Canonical Outcomes` links. Delete the temporary dossier and remove its adopted TODO entry only during the last consumer epic's closeout, after every declared consumer epic is successfully terminal, no other canonical roadmap reference remains, and the approved destructive envelope includes the deletion.

When no dossier exists, update only lifecycle and canonical documents required by current behavior. Do not create, delete, rename, or relink documents solely to manufacture a dossier closeout diff. Do not remove an existing dossier during active work merely because a later recount falls below the threshold.
