# ADR-0009: Use supervised agent orchestration

**Status:** `Accepted`

**Recorded:** `2026-10-09`

**Implementation status:** Reserved design accepted for EPIC-021; required
native mappings and workflow placements remain unimplemented and unqualified.

## Context

An implementing agent can deliver a candidate while omitting a canonical
criterion, missing original evidence, or overlooking an Epic integration goal.
Worker delivery, technical review, semantic assessment, formal native acceptance,
and user authority answer separate questions. Combining them allows a successful
operation to mask an incomplete outcome.

Podway supports structural delegation but does not establish semantic truth or
current filesystem candidate bytes. Aquarium needs host-native agent supervision
that preserves its existing tool contracts, authority planes, review budgets,
and exact candidate bindings.

## Decision

Reserve separate Orchestrator, Judge, and Workers roles under the
[shared orchestration contract](../../plugins/aquarium/references/agent-orchestration.md).
Workers deliver bounded candidates. A report-only Judge reads canonical criteria
and original evidence and assesses every applicable requirement. The Orchestrator
accepts complete native Worker deliveries and Judge reports under their placement
checks and execution authority, then completes their Actions. Semantic Decisions
require an applicable Judge verdict. A disputed verdict returns to the Judge with
conflicting evidence; accepting the Judge report requires no recursive assessment.

Retain one logical Judge per standalone Task, Epic-handler, Design, or War-room
lifecycle. Epic-handler preserves continuity across members and internal
validation. Independent cold validation uses a fresh Judge. Use supported
host-native Codex and Claude subagents first, with sequential implementation on
a shared checkout and parallel reading when useful.

Define versioned Worker handoff, Judge assessment, and recovery checkpoint
documents. Require a qualified native mapping for real dispatch, accepted task
and configuration bytes, complete results, acknowledgement, settlement, and
recovery before mandatory delegation activates. Unsupported public capabilities
block qualification; synthetic receipts or direct fallback cannot satisfy them.
No new scheduler, daemon, central state owner, or Podway core change is part of
this decision.

## Consequences

- Work-bearing Actions separate candidate delivery from semantic assessment;
  the Primary retains Decision execution and native authority checks.
- Missing mandatory criteria or evidence prevent semantic progress even when technical
  review finds no defect. Technical-review routes retain their independent
  topology, targets, findings, budgets, recovery, and completion evidence.
- Native result acceptance and Podway Action completion remain separate. Exact
  target, goal, configuration, and attempt bindings govern applicability and
  restoration; agent replacement cannot reset consumed authority.
- Existing users need updated managed Procedures and compatible successor
  sessions. Immutable admitted snapshots and repository customizations remain
  preserved. This breaking change needs exact candidate upgrade verification in
  the dedicated UTM macOS VM before release.
- Local structural validation does not qualify either host integration or
  Master's semantic functional checks. Those remain delivery requirements.

## Rejected alternatives

- Treating Worker delivery or a clean technical review as semantic completion
  leaves canonical omissions and integration gaps unassessed.
- Repeating the full Judge assessment in the Orchestrator obscures ownership
  and permits silent substitution of the Judge's verdict.
- Fabricated adapter metadata, synthetic live receipts, private database
  scraping, or automatic direct work cannot establish native acknowledgement.
- Adding a scheduler or modifying Podway core exceeds the accepted native
  integration scope.

## References

- [Reserved specification](../specs/agent-orchestration.md)
- [Separate workflow authority planes](0002-separate-workflow-authorities.md)
- [Separate effect approvals](0005-separate-effect-approvals.md)
