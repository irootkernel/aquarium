# Architecture Decision Records

This directory preserves durable Aquarium architecture decisions after they are explicitly accepted. The initial records are retrospective descriptions of authority already implemented by the current repository; `2026-08-25` is the recording date, not necessarily the original adoption date.

## Accepted Decisions

- [ADR-0001: Use Codex as the Primary Runtime and Keep the Toolchain Upstream](0001-codex-primary-runtime-and-defined-toolchain.md)
- [ADR-0002: Keep Workflow Authority Planes Separate](0002-separate-workflow-authorities.md)
- [ADR-0003: Do Not Create Central Aquarium Project State](0003-no-central-aquarium-state.md)
- [ADR-0004: Keep Runtime Evidence Native and Promote Only Bounded Artifacts](0004-bounded-evidence-residency.md)
- [ADR-0005: Require Separate Approval for Distinct Effects](0005-separate-effect-approvals.md)
- [ADR-0006: Use Local Deterministic and Exact-Candidate Verification](0006-local-exact-candidate-verification.md)

## Record Contract

Each record must state its context, decision, consequences, and one lifecycle state: `Accepted`, `Superseded`, `Deprecated`, or `Rejected`. A superseding record links the prior decision without rewriting its history.

Proposed decisions remain in the owning roadmap task or TODO candidate until accepted. Implementation history and transient workflow evidence are not architecture decision records.
