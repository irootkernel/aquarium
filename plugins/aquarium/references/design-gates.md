# Design Gate Contract

This contract applies only when `$aquarium:release-qa` finds a Design Gate registry already owned by the target repository. Resolve the authoritative current and retired registry paths from repository authority, using `docs/gating-rules.md` and `docs/gating-rules-retired.md` only as defaults. Aquarium does not create, update, require, or enroll these registries.

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

If a repository has never enrolled a registry, `release-qa` runs only its release-delta matrix and reports `Design Gate not enrolled`. Once the registry exists in history, its absence from the candidate is a contract finding, not opt-out. Active gates form the candidate-wide gate matrix; gate additions, changes, reactivations, and retirements are also part of the release delta.

## Release QA Evidence

The coordinator reads the exact candidate registry and records every active gate ID in `active_design_gates`. The `design_gate_matrix` has one row per ID, with `gate`, non-empty `positive_scenarios`, and non-empty `failure_scenarios` referencing retained worker scenario IDs. Assign every required procedure and its evidence to a fresh scenario worker; an unavailable procedure or missing observation is a `gap`, not a pass.

An unenrolled repository records both lists as empty. An enrolled registry with no active gates may also have empty lists; enrollment and active inventory are separate facts. Gate scenarios cannot also supply the commit or surface release-delta matrices. A registry change still needs its own delta inspection.

Freeze the enrollment state, exact active inventory, and matrix in the full-pass record and preserve them unchanged in the confirmation manifest. Confirmation reruns every retained positive and failure scenario, including unchanged gates, under the same offline isolation rules. Missing or altered gate coverage makes the workflow `INCOMPLETE`; if such evidence reaches an admitted finish, the helper settles `REJECTED` and consumes that claim. A verified failure is a finding. The helper validates the closed matrix and retained references, not arbitrary registry prose or the truth of caller observations.
