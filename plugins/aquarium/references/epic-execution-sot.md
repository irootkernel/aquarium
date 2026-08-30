# Epic Execution SOT

Use this contract when an Aquarium design workflow defines an epic or a handler or validator resolves the context needed to execute or validate one. A dossier is a temporary consolidated execution SOT for complex work, not a mandatory documentation shape.

## Decide Whether a Dossier Is Required

Require one active dossier when either condition holds at design or preflight:

- the epic has three or more member tasks, counting the complete canonical membership rather than only unfinished tasks;
- goal, scope, constraints, task objectives, prohibited actions, acceptance, or required handoff ownership is distributed across three or more requirement-bearing canonical documents.

Count the roadmap as a requirement-bearing document only when it owns execution requirements beyond identity, ordering, dependencies, lifecycle vocabulary, and status. Do not count implementation outputs, tests, generated artifacts, evidence, or specifications and architecture documents first created during delivery; classify the planned execution context before implementation begins.

An epic with at most two member tasks and at most two requirement-bearing canonical documents may omit a dossier only when repository discovery still yields an unambiguous goal, scope, task identity and lifecycle, dependency ordering, acceptance, required artifacts and handoffs, and every safety-critical external-action boundary. Missing semantic information blocks the workflow regardless of file count.

## Create or Revise the Execution SOT

`$aquarium:new-project`, `$aquarium:new-feature`, `$aquarium:refactor`, and `$aquarium:war-room` own dossier creation and revision when they define work meeting the threshold. Use the repository's declared organization. Under Aquarium's default profile, create or reuse one scope-local `TODO-*.md`, record it in the adopted TODO index, and link it from every consumer epic as `Detailed SOT`. A shared dossier must identify its consumer epic IDs without taking ownership of their roadmap lifecycle.

Consolidate execution decisions without copying canonical product truth. When requirements already live in several canonical owners, use the dossier as a thin integration map that links each owner, maps member tasks and dependencies, and states cross-document acceptance and handoff boundaries. The roadmap remains the sole owner of identity, ordering, dependencies, lifecycle vocabulary, and status.

When a design workflow produces a small epic below the threshold, keep its complete execution context in the roadmap and at most two appropriate canonical documents. Do not create an empty or ceremonial dossier.

## Consume and Validate the Execution SOT

`$aquarium:epic-handler` and `$aquarium:task-handler` discover the canonical roadmap, documentation index, repository guidance, and requirement-bearing documents before applying the threshold. When a required dossier is absent, stop before mutation and route revision to the appropriate design workflow: `new-feature` for ordinary feature work, `refactor` for refactor work, `war-room` for a diagnosed difficult bug, or `new-project` while shaping a new project. Ask only when that ownership is ambiguous. Never route dossier creation to `docs-setup`.

When a dossier is not required, treat the discovered canonical document set collectively as the execution SOT and proceed. Leaf task phases consume the handler-resolved SOT and update a dossier only when one exists. They do not independently manufacture a dossier requirement.

`$aquarium:epic-validator` applies the same threshold while an epic is active or in review. For a completed epic, validate acceptance from its current canonical outcomes and repository-defined historical sources; never recreate a deleted temporary dossier. Report the exact missing semantic owner when the completed state cannot be validated.

## Close Out Without Manufacturing Documentation

When a dossier exists, keep it current across member tasks and consumer epics and follow the repository's declared closeout lifecycle. Before changing or deleting it, inventory all canonical roadmap references to that exact dossier. Closing one epic removes or replaces only that epic's link and must retain the dossier and TODO index entry while another consumer epic remains non-terminal or another epic still canonically references it.

Under Aquarium's default profile, promote durable information for the closing epic and replace only its `Detailed SOT` with valid `Canonical Outcomes` links. Delete the temporary dossier and remove its adopted TODO entry only during the last consumer epic's closeout, after every declared consumer epic is successfully terminal, no other canonical roadmap reference remains, and the approved destructive envelope includes the deletion.

When no dossier exists, update only lifecycle and canonical documents required by current behavior. Do not create, delete, rename, or relink documents solely to manufacture a dossier closeout diff. Do not remove an existing dossier during active work merely because a later recount falls below the threshold.
