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

## Ordinary native orchestration

The [ordinary v2 contract](../../plugins/aquarium/references/ordinary-agent-orchestration.md)
owns the current source roles, assignments, handoffs and recovery boundaries.
The current Primary's harness runs native Workers and an independent report-only
Judge. Workers deliver coherent implementation or documentation with refinement
and required checks; the Judge assesses due criteria from original artifacts.
The Primary records workflow evidence and makes permitted Decisions. Operational
bookkeeping and unchanged final-report assembly create no extra Judge cycle.

Ordinary Podway Actions retain structural progression and current fences without
native receipts. Available public handles and actual results support recovery;
private executor history, internal model telemetry and configuration digests are
not startup prerequisites. Reconcile unknown work before replay and settle a
mutating Worker before replacement. A fresh independent Judge can restore
original criteria, current artifacts, prior gaps and remaining authority.

Selected technical reviews, required checks, scope, correction grants, actual
user acceptance and commit boundaries retain their own contracts. Every due
criterion must have sufficient evidence; future work remains distinct from
current obligations. A complete existing final assessment is reusable only with
verified applicability to current candidate, original criteria and checks.

The [formal v1 contract](../../plugins/aquarium/references/formal-agent-orchestration-v1.md)
and native mappings preserve genuine delegation receipts, original digest domains
and admitted historical snapshots. Never reinterpret a formal session as ordinary.
Source updates require authorized managed rollout and compatible successors;
customized bytes and existing sessions are preserved. Local structural fixtures
prove neither actual native functionality nor installed upgrades. Record those
observed results separately. In this repository, installation-dependent checks
run only in the dedicated UTM VM.
