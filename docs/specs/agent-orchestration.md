# Supervised agent orchestration

## Reserved delivery contract

`TASK-110` freezes the shared Orchestrator, Judge, and Workers design for
`EPIC-021`. Required placements and workflow behavior await implementation and
qualification. TASK-111 provides the bounded native mapping components below. Current skills and admitted Procedure snapshots
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

## TASK-111 candidate instructions

[Goal Judge](../../plugins/aquarium/skills/goal-judge/SKILL.md) supplies report-only
assessment instructions; [Worker guidance](../../plugins/aquarium/references/worker-guidance.md)
supplies bounded assignments and handoffs. The
[native mapping profiles](../../plugins/aquarium/references/native-agent-mappings.md)
identify the Codex and Claude public fields, acknowledgement obligations, and
rejection paths. Isolated native assignments and serialized feedback on both
hosts have exercised Podway acceptance, Action completion and retained
settlement. Master's whole-skill functional verification remains pending.
Required delegation stays inactive while Task integration and completion review
remain pending.

The mapping profiles also own the caller's
[local assignment helper](../../plugins/aquarium/skills/goal-judge/scripts/prepare_assignment.py).
It preserves role, declared dependencies and full selected file evidence as exact
bytes and prepares local digests. It does not dispatch an agent or prove native
acceptance. Executable tests cover this preparation behavior separately from the
combined host/workflow and skill qualification.

The [native delivery mapper](../../plugins/aquarium/skills/goal-judge/scripts/map_native_delivery.py)
correlates supplied public Codex thread records, journaled Codex initial spawns
and serialized feedback, or synchronous Claude Agent records and same-agent
SendMessage feedback with exact inputs and complete results. It produces separate task and result digests and
reconciliation references. The binders establish acknowledged applicable
configuration; the collector and Primary establish authenticity, acceptance,
lifetime accounting, settlement and current Podway context. Supplied records and
isolated tests alone cannot establish those facts.

The [dispatch renderer](../../plugins/aquarium/skills/goal-judge/scripts/render_dispatch.py)
preserves role/dependency UTF-8 text as operative instructions and includes the
full node and selected evidence. The
[prepared-delivery binder](../../plugins/aquarium/skills/goal-judge/scripts/bind_prepared_delivery.py)
reruns rendering and native correlation to bind the complete role snapshot and
acknowledged fork/model/effort configuration to the native task and full result.
These components leave Primary acceptance, lifetime accounting, settlement,
current Podway context and durable host qualification to the integration.

The [Claude prepared-delivery binder](../../plugins/aquarium/skills/goal-judge/scripts/bind_claude_delivery.py)
binds the exact operative role snapshot and echoed prompt to acknowledged
synchronous Agent controls, the native resolved model and complete structured
result. Serialized feedback keeps a separate complete public child result
domain and per-run provenance. Actual isolated Claude delivery and feedback have
exercised acceptance and retained settlement; synthetic checks cover correlation
and rejection separately.

The [Codex record producer](../../plugins/aquarium/skills/goal-judge/scripts/read_codex_thread.py)
captures full native thread records through an explicitly selected existing Unix
WebSocket endpoint. It initializes a read client and hydrates history without
creating a Primary or changing configuration. The collector retains its
request/response provenance separately from mapping and acceptance. Both hosts
have recovered identical public histories after actual result-read response
withholding without redispatch. Physical dispatch-response loss remains
unverified and is required before affected placement activation.

## TASK-112 Task candidate

The bundled Task Procedure version `25` and [Task orchestration](../../plugins/aquarium/references/task-orchestration.md) apply Worker candidate Actions, retained Judge reports and Primary semantic Decisions to planning, implementation, refinement, verification, documentation, admitted review evidence and final normal/stopped Task outcomes. Technical route admission, ordinals, provenance, findings, backend checks, Low settlement, correction authority, actual approval and separate commit grants retain their own gates.

The candidate declares complete role snapshot bindings and rejects Worker-only, missing or stale assessment evidence and uncovered followup authority structurally. Installed managed copies retain the released contract. Source and authoring checks do not prove distributed execution or Master functional results. TASK-116/117 must qualify complete Claude Judge lifetime, feedback source access, physical dispatch-response loss and the installed combined candidate before activation.

## Related authority

- [Workflow runtime](../architecture/workflow-runtime.md) distinguishes current execution from the reserved role model.
- [ADR-0009](../architecture-decision-records/0009-supervised-agent-orchestration.md) records the accepted design and its consequences.
- [Review routing](review-routing.md) remains the shipped owner map for selected technical-review operations.
