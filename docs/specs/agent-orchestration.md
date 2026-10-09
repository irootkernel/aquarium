# Supervised agent orchestration

## Reserved delivery contract

`TASK-110` freezes the shared Orchestrator, Judge, and Workers design for
`EPIC-021`. Required placements, backend mappings, and workflow behavior are
unimplemented and unqualified. Current skills and admitted Procedure snapshots
continue under their existing contracts. This specification records reserved
interfaces without claiming a shipped capability.

The exact owner is the
[supervised agent orchestration contract](../../plugins/aquarium/references/agent-orchestration.md).
It defines role ownership and logical Judge lifetimes, original-criterion
assessment, applicability, all five Procedure evaluation boundaries, native
acknowledgement responsibilities, recovery, and retained technical-review and
approval constraints. Its versioned document interfaces are
`aquarium.worker-handoff/v1`, `aquarium.judge-assessment/v1`, and
`aquarium.orchestration-checkpoint/v1`; they are assessment documents, not native
wire schemas or evidence that an adapter exists.

The [roadmap](../roadmap/README.md#epic-021-adopt-supervised-agent-orchestration)
owns delivery status and dependencies. The
[active dossier](../todo/TODO-AGENT-ORCHESTRATION.md) owns detailed execution and
acceptance requirements until closeout. `TASK-111` qualifies Codex and Claude
native mappings. `TASK-112` through `TASK-116` apply and align the handlers,
Procedures, and compatibility contract; `TASK-117` qualifies the combined
outcome and Master's functional results.

## Related authority

- [Workflow runtime](../architecture/workflow-runtime.md) distinguishes current execution from the reserved role model.
- [ADR-0009](../architecture-decision-records/0009-supervised-agent-orchestration.md) records the accepted design and its consequences.
- [Review routing](review-routing.md) remains the shipped owner map for selected technical-review operations.
