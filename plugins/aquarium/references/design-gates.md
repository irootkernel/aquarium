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
