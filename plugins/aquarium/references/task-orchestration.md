# Task orchestration

## Candidate and activation

The bundled `aquarium-task-v2` version `29` declares required native Worker and
Judge Actions. Execution requires an admitted delegated Procedure and native
qualification for its exact role snapshot, assignment and recovery path.
Released managed copies and admitted direct snapshots retain their original
contracts. Read the [shared contract](agent-orchestration.md),
[native mappings](native-agent-mappings.md) and installed `use-podway`
delegation contract. An unavailable required binding blocks execution; it never
permits direct fallback or a synthetic acceptance.

## Assignments and role identity

Use `binding_ref=aquarium-native`, Worker role `aquarium-worker/v1`, and Judge
role `aquarium-goal-judge/v1`. `after_accept=retain` requires acknowledged idle
settlement. `max_rounds=32` uses Podway's native per-placement maximum, without
imposing an Aquarium retry budget. Keep actual lifetime accounting across all
placements and retain one logical Judge throughout a standalone Task. Each
placement needs its own current acknowledged assignment, result and receipt;
prior package bindings remain historical. Never reset lifetime rounds or relabel
an earlier acceptance for a different Action. An
Epic-handler member keeps that Epic's Judge under its owning workflow.

Compute each declared role snapshot with
[prepare_assignment.py](../skills/goal-judge/scripts/prepare_assignment.py).
The Worker role path is `plugins/aquarium/references/worker-guidance.md`; the
Judge role path is `plugins/aquarium/skills/goal-judge/SKILL.md`. Both inventories
include these operative dependencies under `plugins/aquarium/references/`:

- `agent-orchestration.md`
- `native-agent-mappings.md`
- `evidence-residency.md`
- `review-routing-contract.md`
- `review-intent-contract.md`
- `finding-disposition.md`
- `ouroboros-integration.md`
- `design-gates.md`

The snapshot is `aquarium.prepared-role-snapshot/v1`: the role path and sorted
inventory contain each exact file path, byte count, SHA-256 and base64 body.
Its digest covers compact sorted-key ASCII JSON without a final newline. Preserve
complete bytes, including final newlines. Resolve tool contracts and phase
instructions as node-specific assignment input; original repository criteria and
artifacts remain task evidence. A changed operative dependency requires a new
snapshot, Procedure candidate and applicable native acknowledgement.

Every assignment carries the current full package, complete selected values,
objective, purpose, phase instructions, original canonical criteria, exact target
and base, authority, excluded effects, deliverables and success criteria. Use
operative role text through the dispatch renderer. Recompute and compare the
accepted role, configuration, task and complete result domains separately.
Local preparation establishes no native acceptance.

## Planning and phase progression

Before a session, a read-only `task-plan` Worker proposes the plan. The Primary
obtains actual approval and any required dossier waiver. `plan-only` ends there.
After approval and session admission, acknowledge or explicitly revalidate the
exact approved artifact against the fresh `record-plan` package. Preserve the
actual native acknowledgement; never relabel the pre-session receipt.

| Worker candidate | Retained Judge | Primary Decision |
| --- | --- | --- |
| `record-plan` | `judge-plan` | `decide-plan-assessment` |
| `implement` | `judge-implementation` | `decide-implementation-assessment` |
| `refine` | `judge-refinement` | `decide-refinement-assessment` |
| `verify` | `judge-verification` | `confirm-verification-operation`, then `decide-verification` |
| `document` | `judge-documentation` | `decide-documentation-assessment` |
| Admitted `review` evidence | `judge-review` | `confirm-review-completion` |
| `prepare-task-assessment` | `judge-task` | Applicability confirmation, then `assess-goal` |
| `prepare-stopped-task-assessment` | `judge-stopped-task` | Applicability confirmation, then `assess-stopped-goal` |

The Primary retains all Decisions and operational records. Judge Actions have no
recursive Judge. Candidate Actions return `aquarium.worker-handoff/v1`; Judge
Actions return `aquarium.judge-assessment/v1` with all original criterion rows.
Record their exact artifact metadata and retain complete bytes outside Podway.
Podway stores caller assertions and metadata; it neither authenticates records
nor establishes semantic truth.

For each delegated Action, read the complete current package and selected evidence,
obtain authentic acknowledgement and full delivery, check scope, provenance,
complete original criterion coverage, current target and authority, and explicitly
accept the native result. Record every final item, establish retained idle state
including descendants, submit the exact Podway acceptance, then complete with a
current receipt and fresh fences. Worker acceptance establishes delivery. Judge
report acceptance checks the report and its applicability without repeating its
semantic assessment. The following Primary Decision consumes that assessment.
Any actual later item edit can stale the receipt.

A phase pass requires current applicability and a passing `judge-checkpoint-result`
for all actual due phase obligations and applicable parent constraints. Retain
every original global criterion row, verdict and unmet/unverified count; later
work can remain a global gap. A plan checkpoint proves the exact approved plan,
implementation proves its due implementation obligations, and verification proves
required checks. Review evidence preserves faithful negative provider rows and
their original completion, severity and Low routing. Report completeness alone
cannot establish implementation, correction or verification success. Worker-only
delivery, omitted original criteria, absent
reports, changed targets, stale requirements, unsupported native bindings and
inconsistent reports block passage. Return disputed or inapplicable assessments
to the retained Judge with original conflicting evidence. An unchanged artifact
still needs current revalidation and qualified acknowledgement after rework.

Established gaps and missing evidence use separate checkpoint-local followup
records. Before returning to the phase, the authority gate requires a passing
caller-supplied result for the exact existing grant, effect, target and owner.
A negative verdict grants no new effect, review ordinal or provider operation.
If another earlier phase owns the change, use its already authorized manual
rework target and retain the source attempt, report, target, criterion and
consumption basis. Never route forward around a required phase. Missing native
or evidence authority remains a blocker. Evidence collection uses its actual
owner and reconciles an existing provider operation before any new dispatch.

## Review, final assessment and closeout

Keep selected technical evidence and Judge assessments distinct. Route binding,
operation admission, ordinal, evidence, provenance, finding confirmation and
backend checks still precede `judge-review`. A failed backend check retains its
existing correction-authority path. Judge-owned negative completion first classifies eligible local corrections.
Nonlocal unmet completion enters `record-task-rework-basis` and the existing
serial authority and phase-owner chain; missing evidence retains its dedicated
review evidence/authority path.
Preserve original provider completion rows, frozen findings, accepted risks,
Low dispositions, review mode and every consumed ordinal. A Judge never counts
as a technical reviewer or permits another review by itself.

Final candidate assembly supplies the complete original phase, review and Judge
reports and all applicable canonical Task and parent constraints as original file
evidence in its handoff. Include branch-specific Low and stopped records when
present. The graph selectors provide current core and report references. The handoff
must also supply the remaining original evidence in full. Its summary cannot
substitute for those bytes. No new implementation, broad audit or provider
review occurs during assembly. Local-settlement composition retains the reviewed basis, verified permitted
delta, exact after-target, current criterion evidence and honest coverage limit;
ordinary Low-only settlement carries unaffected source rows unchanged. Do not consume a new review ordinal for that delta.

`achieved` requires the final applicable Judge pass, zero mandatory gaps and the
Judge's exact achieved outcome. Explicit stops retain their structural exclusion
of achievement. Negative outcomes do not authorize success status or reopening
stopped work. Actual task-close approval and the exact separate task-commit grant
remain required. Direct phase invocations retain their existing authority;
when the handler delegates a phase, the Primary owns approval conversations,
Podway acceptance and progression.

## Qualification applicability

Bounded both-host scenarios cover native Worker/Judge delivery, complete
serialized assignments and Primary phase Decisions. Claude SDK-facing feedback
ACK withholding and result-read recovery are distinct from Initial Agent,
inner-model and Codex dispatch-ACK loss, which remain unqualified. Arbitrary
active or outliving descendants also remain unqualified. Stop on any required
unsupported path; do not extrapolate a bounded result to full handler execution,
tool-bearing implementation or nested technical-review lifetimes.

Every changed operative snapshot needs fresh applicable native acknowledgement
and result/settlement evidence. Qualification cannot activate admitted released
snapshots or other repositories. Exact candidate installation and upgrade belong
in the dedicated UTM VM before release; Master's actual overall acceptance
remains the final Epic closeout gate.

After admitted review evidence, apply the [local-settlement contract](finding-disposition.md#decide-whether-a-correction-needs-another-review) before provider-rework authority. Preserve source negative rows, verify the exact correction and current criteria, then supply the complete composition to the required final Judge. `confirm-local-corrections-settled` checks pending repairs before ordinary Low completion. Native backend failures and missing reviewer coverage retain their existing gates.
