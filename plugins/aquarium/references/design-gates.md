# Design Gate Contract

Resolve and record the authoritative current and retired registry paths together at workflow start. The defaults are `docs/gating-rules.md` and `docs/gating-rules-retired.md`. Repository authority may explicitly override both paths; when it overrides only the current path, derive the retired path as its sibling `gating-rules-retired.md`. The first retirement creates the resolved retired registry; current entries retain only a tombstone pointing to the retired gate ID and retirement record, while the full retired body and rationale live in the retired registry. Reactivation replaces that current tombstone with an active body using the same stable ID, retains every historical retired record, and appends a reactivation record that names the restored source and approval. The latest lifecycle record determines whether the ID is active; it must never have both an active body and a current tombstone.

Only `$aquarium:design-qa` may create, materially change, reactivate, or retire a Design Gate. Other workflows may propose gate candidates and must hand them to `design-qa`. Generic documentation work, including `$aquarium:task-document`, must not edit either registry.

## Gate Shape

Every active gate must contain:

- a stable `GATE-*` ID and concise title;
- the invariant it protects and its authoritative scope;
- at least one positive scenario and one failure scenario;
- an offline, locally executable command or inspection procedure that leaves the source repository unchanged and declares any disposable output or cache paths;
- an objective pass condition;
- revalidation triggers;
- source documents and owning roadmap or architecture identity.

Do not register a gate that requires network access, credentials, a live service, provider invocation, user-global writes, persistent processes, source-repository mutation, or unverifiable human judgment. Redirect allowed temporary outputs and caches to a declared disposable root, and record requirements that cannot meet this contract as unresolved design constraints instead.

## Impact Marker

Every newly authored implementation work unit, including every task inside a new project, feature epic, refactor epic, or diagnostic result, must state `Design Gate impact` as exactly one of:

- `Not required`, with a reason;
- `Pending`, with the candidate invariant and required `$aquarium:design-qa` handoff;
- one or more resolved `GATE-*` IDs with the expected impact.

Authoring workflows must propagate the resolved IDs, `Pending`, or `Not required` decision into every implementation task they create. A task's explicit marker is authoritative. When a legacy task lacks one, inherit its parent epic's marker. If neither task nor parent has a marker and the authoritative current registry has never been enrolled, treat the effective marker as `Not required` only after recording that legacy reason. If the registry is enrolled, a missing effective marker is a contract gap that blocks plan approval and implementation until the roadmap is documented.

`Pending` blocks implementation. `task-handler` and `epic-handler` must resolve the effective task marker and stop before plan approval or implementation when it is pending or missing in an enrolled repository. `task-verify` verifies every impacted active gate inherited or named by the exact task snapshot, and `epic-validator` verifies all effective task gates plus applicable epic and seam gates.

If a repository has never enrolled a registry, `release-qa` runs only its release-delta matrix and reports `Design Gate not enrolled`. Once the registry exists in history, its absence from the candidate is a contract finding, not opt-out. Active gates form the candidate-wide gate matrix; gate additions, changes, reactivations, and retirements are also part of the release delta.
