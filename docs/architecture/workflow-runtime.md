# Workflow Runtime

An Aquarium workflow is an instruction-driven state machine executed by Codex. The owning skill determines which repository authorities must be read, which effects are permitted, and which proof is required before a phase can advance.

## Invocation Path

1. Codex matches an explicit user request to a public skill. A parent skill may call a documented leaf skill when its contract authorizes that handoff.
2. The skill reads repository guidance, the named source of truth, Git state, and any required Procedure or tool state before proposing a change.
3. Read-only discovery establishes exact scope and reports ambiguities. Discovery alone does not authorize setup, mutation, provider use, commits, or publication.
4. The workflow requests approval at the boundary named by the owning contract. Approval is invalidated when the displayed target or exact diff becomes stale.
5. Codex performs only the approved effect, then re-observes the relevant authority rather than assuming success from command acceptance.
6. Verification records the claim that was actually proven. The owning workflow either advances, hands off a bounded result, or stops with a concrete blocker.

## Procedure-Backed Lifecycles

Task, epic, validation, design, and war-room workflows may install or use one of the five project-owned Procedure v2 assets. The YAML asset declares the graph and version. The owning skill supplies semantic rules that cannot be represented by the graph alone, including approval boundaries, repository authority, evidence quality, and recovery behavior.

Podway activation is repository-local runtime state. A Procedure file in this plugin proves only the source that Aquarium can install; it does not prove installation, activation, session state, or downstream execution in another repository.

## Leaf Handoffs

The task lifecycle separates planning, implementation, verification, refinement, documentation, review, closeout, and commit work. Each leaf receives a bounded task and returns a result suitable for its parent. A successful leaf result is not permission to skip later acceptance or Git checks.

The epic lifecycle coordinates multiple task lifecycles and a cold validation pass. Cross-repository dependencies remain owned by their repositories and require the exact downstream commit plus independent revalidation before Aquarium can treat them as satisfied.

## Failure and Recovery

Workflows prefer re-observation over replay. Unknown or interrupted external execution is quarantined until its actual state can be resolved. A retry never widens authority, and successful earlier effects are not rolled back automatically unless the owning contract explicitly provides a safe recovery action.

## Supervised orchestration candidate

The [EPIC-021 orchestration contract](../../plugins/aquarium/references/agent-orchestration.md)
defines the implemented candidate role model and versioned handoffs. Bounded
native Worker, Judge, and Primary scenarios qualify Task planning, Goal work,
Validation audit, Design context, and War-room baseline on Codex and Claude.
They do not establish full handler lifecycles or final Goal achievement. Installed
released skills and admitted snapshots retain their existing contracts; source
updates do not activate candidate placements in an existing session.

The candidate flow separates Worker delivery, report-only Judge
assessment, and Orchestrator Decisions. The Primary accepts a complete native
delivery under its placement's delivery checks and authority before completing
the Action. It accepts a complete Judge report without recursively judging it;
phase progression then requires current applicability and a result proving
actual due obligations. Complete original global rows and gaps stay intact, and
final achievement still requires the full original Goal to pass.
The Judge reads original criteria and evidence, including omitted assignment
criteria and Epic integration goals. One logical Judge follows an Epic-handler
across member Tasks and internal validation; independent cold validation starts
fresh. Operational records and approval transitions retain native checks without
an extra semantic cycle.

Host-native integrations own dispatch, feedback, actual identities, accepted
task/configuration bytes, complete results, settlement, and reconnect. Podway
owns receipts, structural progression, and fences. Native result acceptance
precedes separate Action completion. The shared contract owns the full mapping
requirements and recovery boundaries. TASK-111 through TASK-117 implement and
qualify the bounded native paths; required delegation still needs an applicable
qualified integration and admitted Procedure. Initial Agent, inner-model, and
Codex dispatch-ACK loss and arbitrary outliving descendants remain unqualified.
Unsupported required recovery stops at its native owner rather than direct
fallback. Candidate qualification does not establish release or host activation.
