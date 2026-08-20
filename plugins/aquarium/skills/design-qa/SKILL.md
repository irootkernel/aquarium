---
name: design-qa
description: "Design or update durable local Design Gates with Ouroboros QA and an approved exact diff. Use when the user explicitly invokes $aquarium:design-qa."
---

# Design QA

Create, change, reactivate, or retire Design Gates for one approved design scope. Do not implement product code, stage, commit, publish, or register networked, provider-backed, credentialed, live-service, or subjective gates.

Read [ouroboros-integration.md](../../references/ouroboros-integration.md) and [design-gates.md](../../references/design-gates.md), then use the default `aquarium-design-v2` Podway path. Resolve and record the authoritative current and retired registry paths, using `docs/gating-rules.md` and `docs/gating-rules-retired.md` only as defaults.

Read the design artifacts, roadmap work units, architecture authority, resolved current registry, resolved retired registry when present, and local verification entrypoints. If the current registry never existed, propose its initial structure; if it existed in history but is missing, treat restoration as a contract issue rather than fresh enrollment.

After the approved envelope, use installed upstream `$interview` to resolve invariants and `$qa` to challenge every candidate gate. Require stable ID, concise title, invariant, scope, positive and failure scenarios, a local offline executable procedure that leaves the source repository unchanged and declares disposable outputs, objective pass condition, revalidation triggers, sources, and owner. Reject or defer any candidate that cannot meet all fields.

Show the exact registry, source-document, and impacted roadmap-marker diff only after the Ouroboros QA result is acceptable. Obtain explicit approval, recheck snapshots, and apply exactly that diff, replacing each resolved `Pending` marker with `Not required` or the active `GATE-*` IDs.

On retirement, leave a tombstone in the resolved authoritative current registry and place the full retired body and rationale in the resolved authoritative retired registry. On reactivation, replace the current tombstone with the active body, retain the retired history, and append the reactivation record. Validate every active gate locally with disposable outputs and an unchanged source repository after applying; a failed or unexecutable gate leaves the workflow incomplete and must not be reported as accepted.

Report added, changed, reactivated, retired, rejected, and still-pending gate IDs; commands and outcomes; document digests; and impacted roadmap work. Do not start implementation.
