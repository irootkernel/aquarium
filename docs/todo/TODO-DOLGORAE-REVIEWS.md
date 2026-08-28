# Dolgorae-backed Reviews Work Dossier

## Authority

**Roadmap epic:** `EPIC-003`

This dossier is the detailed scope and acceptance source of truth for `EPIC-003` and `TASK-019` through `TASK-023`. The [canonical roadmap](../roadmap/README.md) alone owns their identities, ordering, dependencies, lifecycle vocabulary, and current status. Checklist state in this file is review evidence only and never changes roadmap state.

Dolgorae `TASK-014` and `TASK-015` own their checked capture, settlement, Specialist Review, carrier, and candidate contracts. Aquarium owns its consumer requirements and must map the delivered contracts without inventing or weakening unfinished Dolgorae wire details. Dolgorae `TASK-016` consumes Aquarium's runtime Completed Confirm and is not an Aquarium prerequisite.

Adopting this dossier changes documentation authority only. It does not activate Dolgorae, modify review runtime behavior, install an executable, or establish release, installation, or distribution readiness.

## Goal

Make `$aquarium:independent-review` use one exact Dolgorae candidate to capture an immutable review target and supervise one fresh Codex Reviewer without creating any Orca object.

Keep `$aquarium:orca-review` under Orca lifecycle ownership while giving it the same captured source meanings. Keep Mulgae operationally independent while aligning only common source-scope, resolved-target, and digest semantics.

## Dependency Boundary

- `TASK-019` builds on the completed Aquarium `TASK-010` runtime and shared-contract foundation.
- `TASK-019` through `TASK-022` do not depend on unfinished EPIC-002 producer integration.
- Those tasks may use checked adapters, fixtures, and controlled fake executables, but cannot claim live Dolgorae readiness.
- `TASK-023` alone depends on the exact candidate supplied by external Dolgorae `TASK-015`.
- Dolgorae is bound directly from that handoff and is not added to `$aquarium:dev-aquarium` producer management.

## Common Review Target Contract

The public review contract has exactly six source scopes:

| Scope | Immutable captured meaning |
| --- | --- |
| `workspace` | The final eligible non-ignored workspace projection. Worktree bytes win over index bytes, deletion is absence, recreation uses worktree bytes, and eligible untracked files participate. |
| `staged` | The captured `HEAD`-to-index transition with immutable before and after manifests. The live index is never a post-capture review source. |
| `dirty` | The captured `HEAD`-to-final-workspace transition containing staged, unstaged, deleted, recreated, and eligible non-ignored untracked state. |
| `head` | The immutable tree of the commit resolved from `HEAD` at capture time. |
| `commit` | The first-parent transition into one resolved commit, using the empty tree as the base of a root commit. |
| `range` | The requested `A..B` transition or merge-base-to-`B` transition for `A...B`, preserving the selected operator. |

Task, epic, and special request are authority and review-focus selectors applied to one source scope. They are not additional source scopes.

## Capture and Trust Boundaries

Capture must not modify the source worktree, index, refs, or Git metadata. It resolves mutable references, records source identity, materializes outside the source repository, detects capture-time drift, publishes read-only material atomically, and binds the result to immutable manifests and digests.

The contract must define deterministic handling for conflicts, unborn `HEAD`, root commits, ignored and untracked files, deletions and recreation, rename representation, binary data, file mode, Git LFS pointers, sparse checkout, symbolic links, special files, submodule gitlinks, opaque paths, and empty targets. Unsafe or unsupported state fails closed instead of being silently omitted or normalized.

Repository bytes, paths, diffs, commit messages, roadmap text, and special requests are untrusted review data. Prompt-like content cannot change reviewer authority, system or developer policy, allowed tools or network behavior, selected scope, target identity, candidate identity, execution deadline, lifecycle ownership, or settlement rules.

Candidate-defined secret screening applies uniformly to every tracked and untracked candidate. Aquarium cannot bypass it or describe bounded heuristic screening as proof that arbitrary content is secret-free. A rejection must leave no partial provider-visible capture.

Read-only materialization is not an operating-system security boundary. Same-user readability must remain disclosed.

## Backend Ownership

`independent-review` invokes Dolgorae directly for exactly one fresh Codex Reviewer.

No Orca Run, Task, Dispatch, worker, terminal, context, worktree, or other Orca object may be created or accepted as evidence by this path. A missing or invalid Dolgorae candidate fails closed without falling back to Orca.

`orca-review` retains Orca Run, Task, Dispatch, terminal, provider, acknowledgement, and recovery semantics while consuming the common captured target meanings.

Mulgae retains its own provider, extraction, adjudication, publication, archive, and settlement lifecycle. Conformance is limited to source-scope meanings, resolved target identities, and comparable digests.

## Supervision and Settlement

Every launch receives a unique, non-reusable invocation identity and a bounded deadline. Aquarium owns explicit cancellation authorization. Dolgorae owns child termination, cleanup, and authoritative terminal observation.

- Only checked terminal evidence bound to the expected capture, backend lifecycle, and revisions may settle.
- Deadline exhaustion performs one authoritative observation. A terminal result wins; active or unknown state preserves the capture and recovery evidence.
- Repeated cancellation is idempotent. The authoritative lifecycle revision decides completion and cancellation races without rewriting an earlier terminal result.
- `cancelled` and `timed_out` require checked terminal evidence. Silence is `unknown`.
- A late receipt never settles automatically and requires explicit recovery-time revalidation.
- Exact accepted settlement replay is idempotent.
- Changed replay, stale revision, foreign owner, lifecycle mismatch, missing evidence, or a losing concurrent compare-and-set preserves the capture.
- Cleanup completes only after authoritative settlement reports removal or explicit retention.
- An active or unknown predecessor cannot be retried. A later authorized retry uses a fresh invocation identity that predecessor receipts cannot settle.

A process exit alone is not completion evidence. Post-capture source mutation cannot alter the captured target and must be reported separately from the review result.

## Task Composition

| Task | Outcome |
| --- | --- |
| `TASK-019` | One checked Aquarium consumer contract for exact Dolgorae candidate identity, capability, schemas, bounds, launch binding, and revalidation |
| `TASK-020` | One immutable capture and owner-bound settlement contract covering all six source scopes |
| `TASK-021` | Dolgorae-backed independent-review supervision with no Orca objects |
| `TASK-022` | Preserved Orca review lifecycle and Mulgae semantic conformance |
| `TASK-023` | Exact-candidate activation, complete runtime E2E, and candidate-bound Completed Confirm |

## TASK-019: Adopt the Dolgorae Candidate Contract

### Outcome

Adopt the exact executable acquisition and consumer boundary required before source-bearing Dolgorae execution.

The handoff must bind the Dolgorae commit, version, canonical executable path, platform file identity, executable SHA-256, and capability or contract digest.

### Required Contract

Before candidate acquisition implementation is accepted, freeze:

- checked closed schemas and their field types, required values, enums, compatibility rules, and size bounds;
- canonical serialization, digest domains and preimages, duplicate and unknown field behavior, and mutation-sensitive vectors;
- supported review operations, source scopes, machine constraints, and effective resource-limit intersection;
- a race-resistant mechanism proving the executed object is the validated object;
- launch-time revalidation of executable, capability, machine, and target identities;
- safe credential-carrier and model-visible-data boundaries inherited from the checked Dolgorae contract.

### Acceptance

- Valid fixtures and empty, malformed, wrong-type, unknown, duplicate, unsupported, exact-boundary, and over-boundary fixtures are deterministic.
- Replacement before or during launch, hash drift, capability drift, and machine mismatch fail before source transmission.
- Controlled fake executables may satisfy this task's contract tests.
- No live Dolgorae readiness or fallback-to-Orca claim is made.

## TASK-020: Adopt Immutable Review Targets

### Outcome

Implement all six immutable captures and the identities needed for owner-bound settlement.

### Required Contract

Before capture implementation is accepted, freeze:

- ordered current or before-and-after manifests, deletion representation, path ordering, modes, sizes, and content identities;
- source, manifest, whole-target, lifecycle, owner-binding, and settlement identities;
- included and excluded dispositions;
- Aquarium hard resource ceilings and the candidate-capability intersection algorithm;
- capture reference and revision, backend binding, compare-and-set key, replay, retention, and cleanup rules;
- the deterministic Git and file-state matrix.

### Acceptance

- All six scopes and every declared Git and file-state boundary have unit, contract, and black-box fixtures.
- Capture-time drift, unsafe paths, screening rejection, overflow, partial publication, and snapshot mutation fail closed.
- Capture proves source and index non-mutation.
- Exact accepted replay, foreign ownership, stale revision, lifecycle mismatch, missing evidence, and simultaneous settlement races are covered.

## TASK-021: Implement Dolgorae Independent-review Supervision

### Outcome

Run one fresh Codex Reviewer through Dolgorae and settle only from authoritative terminal evidence, without creating an Orca object.

### Acceptance

- Success, review failure, timeout, cancellation, interruption, hung execution, active or unknown recovery, late receipt, cleanup, and fresh-identity retry are covered.
- Timing-sensitive fixtures use controlled clocks and processes and repeat without ambient network or ordering dependencies.
- Prompt-injection fixtures cover every untrusted source and request channel.
- Tests prove that no Orca Run, Task, Dispatch, worker, terminal, context, or worktree is created.

## TASK-022: Preserve Orca Review and Align Mulgae Semantics

### Outcome

Move `orca-review` to the common immutable target meanings without changing Orca lifecycle ownership, and prove Mulgae semantic conformance without lifecycle coupling.

### Acceptance

- Golden vectors produce the same scope and resolved-target meanings across applicable adapters.
- Mismatched targets or digests fail closed.
- Orca lifecycle evidence remains present for `orca-review`.
- Mulgae remains independently executable and does not become a Dolgorae or Aquarium settlement owner.

## TASK-023: Activate and Validate the Exact Candidate

### Outcome

Bind the exact external Dolgorae `TASK-015` artifact, activate it under Aquarium authority, run the complete E2E campaign, and return the runtime Completed Confirm required by Dolgorae `TASK-016`.

### Acceptance

- The delivered commit, version, canonical path, file identity, executable SHA-256, capability digest, and launch identity are revalidated.
- Checked Dolgorae wire documents map to every adopted Aquarium semantic requirement.
- All six scopes, Git boundary cases, failure and recovery paths, backend isolation, settlement authorization, cleanup, and rollback pass against the exact candidate.
- Aquarium's focused and complete applicable repository gates pass for the exact committed candidate.
- The Completed Confirm binds exact Dolgorae, Aquarium, installed-plugin, scope-matrix, backend, mutation, settlement, recovery, command, evidence, and blocker state.
- A documentation-only result, mutable path, uncommitted diff, placeholder, prose success statement, identity mismatch, or unresolved blocker returns `Blocked`.

## Prohibited Shortcuts and Non-Goals

- Do not add Dolgorae to `$aquarium:dev-aquarium` producer management in this epic.
- Do not make EPIC-003 depend on unfinished EPIC-002 producer tasks.
- Do not invent unchecked Dolgorae wire fields, carriers, or candidate limits.
- Do not reinterpret task, epic, or special request as source scopes.
- Do not read live mutable Git state after capture as review input.
- Do not create Orca objects in `independent-review` or remove Orca ownership from `orca-review`.
- Do not couple Mulgae provider or settlement lifecycle to Dolgorae.
- Do not silently omit unsafe or secret-bearing content, mutate source state, or fall back on mismatch.
- Do not treat documentation, local runtime evidence, an uncommitted change, or a process exit as activation proof.
- Do not commit, push, publish, tag, release, or mutate another repository without separate authority.

## Epic Acceptance and Closeout

`EPIC-003` may become `Completed` only when:

- `TASK-019` through `TASK-023` have individually passed their acceptance and closeout;
- exact-candidate runtime E2E and complete Aquarium validation pass;
- independent-review proves Dolgorae and zero Orca objects;
- orca-review proves retained Orca lifecycle ownership;
- Mulgae semantic conformance passes without lifecycle coupling;
- the candidate-bound Completed Confirm exists with no unresolved blocker.

The final closeout promotes durable contracts to canonical specifications, architecture, ADRs, implementation tips, operations, or public documentation. In the same change it replaces the roadmap's `Detailed SOT` with `Canonical Outcomes`, removes this dossier from the TODO index, and deletes this file without archiving a copy. Git history remains the archive.
