# Aquarium Documentation

This index adopts one canonical documentation model for the Aquarium repository without moving or duplicating its established code-adjacent authorities.

## Audience and Version Scope

This tree is written for Aquarium maintainers and workflow authors. The root [`README.md`](../README.md) remains the user-facing product overview, while [`README.ko.md`](../README.ko.md) remains its maintained Korean translation.

The plugin manifest identifies the current stable package as `v0.1.11`. The root CHANGELOG owns the open `v0.1.12` release candidate, while the roadmap records `v0.1.13` as a later planned release rather than an open candidate. Maintainer documents describe the current checkout and label candidate-only or planned behavior instead of presenting it as already released.

## Profile and Scope

- Profile: `single-scope`
- Delivery scope: `Aquarium`
- Canonical roadmap: `docs/roadmap/README.md`
- Roadmap namespace: `docs/roadmap/README.md`

## Role Ownership

| Role | Canonical owner | Purpose |
| --- | --- | --- |
| Specifications | `docs/specs/README.md` | Current requirements, implemented behavior, durable contracts, and their exact owning sources |
| Architecture | `docs/architecture/README.md` | Current components, boundaries, data flow, and responsibilities |
| Architecture decision records | `docs/architecture-decision-records/README.md` | Accepted, superseded, deprecated, and rejected decisions with rationale |
| Implementation tips | `docs/implementation-tips/README.md` | Non-normative development, verification, operation, and release guidance |
| Roadmap | `docs/roadmap/README.md` | Adopted epic and task identity, ordering, dependencies, lifecycle vocabulary, and status |
| TODO and work dossiers | `docs/todo/README.md` | Future epic-sized candidates plus detailed scope and acceptance dossiers referenced by adopted roadmap work |
| Deferred feedback | `docs/deferred-feedback/README.md` | Small actionable findings intentionally postponed from current work |

## Maintainer Navigation

- Start with the [capability specifications](specs/README.md) to identify current behavior and its exact owner.
- Use the [architecture map](architecture/README.md) to trace components, workflow runtime, state, evidence, and verification.
- Read the [accepted decisions](architecture-decision-records/README.md) for durable rationale behind current boundaries.
- Follow the [implementation tips](implementation-tips/README.md) when changing skills, Procedures, inspectors, tests, or releases.
- Use the [roadmap](roadmap/README.md) for delivery identity and state, its linked [TODO and work dossiers](todo/README.md) for detailed planned scope and acceptance, and [deferred feedback](deferred-feedback/README.md) for smaller postponed findings rather than adding future behavior to current specifications.

## Source-of-Truth Precedence

- `docs/roadmap/README.md` alone owns delivery identity and lifecycle state; TODO and deferred feedback never act as competing status authorities.
- A `docs/todo/TODO-*.md` file referenced by an adopted roadmap epic owns that work's detailed goal, scope, approach, and acceptance checklist, but never owns its ID, ordering, dependencies, or lifecycle status.
- `docs/specs/README.md` owns the specification catalog and declares the exact repository files that own each detailed product contract; the index does not restate those contracts.
- `docs/architecture/README.md` and architecture decision records own current structure and durable design rationale without overriding executable behavior.
- The plugin manifest owns the published version, skill entrypoints and linked references own workflow behavior, bundled Procedure files own installed Procedure source bytes, and `Makefile` with `TESTING.md` owns executable test behavior and its meaning.
- `CHANGELOG.md` owns cumulative release notes and the planned stable version; `README.md`, `PRIVACY.md`, and `TERMS.md` own the public product, privacy, and authority contracts.
- A conflict is corrected at the exact domain owner first, followed by any affected index or summary; generated output and ignored runtime evidence never become canonical documentation.

## Roadmap Identity

- Epic IDs match `EPIC-[0-9]{3,}` and task IDs match `TASK-[0-9]{3,}`.
- Epic and task sequences are independent and monotonic within the canonical roadmap, including archives and migration records.
- Task numbering does not restart for each epic, and a number is never reused after deletion, deferral, completion, archival, or migration.
- Identity does not encode execution order; roadmap order and explicit dependencies do.
- `docs/roadmap/README.md` is the namespace. A machine-readable cross-scope reference must use `scope:ID` if another delivery scope is introduced later.

## Language

English is canonical for repository documentation and artifacts. `README.ko.md` is the established Korean translation of the public product overview and must remain aligned with `README.md`.

## Documentation Checks

Run these non-writing checks from the canonical Git root:

```bash
python3 plugins/aquarium/skills/docs-setup/scripts/inspect_docs.py --repository "$(pwd -P)"
ruby -c tests/validate.rb
ruby tests/validate.rb
git --no-pager diff --check
```

The inspector proves conservative structure and roadmap-reference rules only. Semantic review must separately confirm that the indexes match current implementation and authority.
