# Combined Haepari qualification and legacy retirement

## Authority and implementation state

The sole active consumer of this dossier is `EPIC-033`, with existing `TASK-100` through `TASK-102`. The [canonical roadmap](../roadmap/README.md) owns identity, ordering, dependencies and lifecycle; this dossier owns detailed qualification and retirement acceptance. EPIC-032 must be completed before entry; EPIC-019 and EPIC-031 are completed prerequisites through that chain.

This plan claims no runtime result and authorizes no implementation, host deletion, broker operation, commit, installation or publication. Shared host removal has its own explicit scope and approval within later execution. Candidate installation and installation-dependent verification remain confined to the dedicated UTM VM.

## Goal and canonical inputs

Qualify the full accepted tool/skill combination and its upgrade path, then retire common aquarium-dev source and approved host state after all consumers detach. Individual pilot and producer acceptance remain their original facts; they do not prove the combined candidate. Final verification does not reopen earlier Epics or transfer unfinished criteria from them.

Read EPIC-019, EPIC-031 and EPIC-032 Canonical Outcomes plus current [tool specifications](../specs/tool-integrations.md), [tool catalog](../../plugins/aquarium/references/tool-catalog.md#haepari), [Haepari integration](../../plugins/aquarium/references/haepari-integration.md), [workflow specifications](../specs/workflow-contracts.md), [architecture](../architecture/README.md), [TESTING.md](../../TESTING.md), [tests/vm/README.md](../../tests/vm/README.md), and [Haepari VM operations](../ops/haepari-vm-verification.md). Require the promoted adapter/profile/cleanup contract, release-role assessment contract, accepted per-producer identity/verification/detachment inventory and the durable Sorage producer coordination protocol. Earlier temporary dossiers must already have been settled and deleted at their own closeout; no input depends on retaining them.

Use exact intended binary/plugin/skill/configuration identities and meaningful prior accepted state in the VM. Exercise the original Job/result/consumer-cleanup handoff through release roles, shared-VM contention and Mulgae's released native advisory lock. Preserve native role concurrency and distinguish advisory expiry from managed unknown-execution containment. Use guest-only stub fault cases by default; real installed and any authorized live observations keep their own evidence. Consumer recipes verify their starting state and cleanup; Haepari never resets the VM or rolls back arbitrary guest changes. Missing required manual or combined evidence prevents acceptance.

The [legacy development dossier](TODO-AQUARIUM-DEV.md) remains a historical/migration reference for this Epic alone as its active retirement consumer. EPIC-002's Cancelled lifecycle and completed history stay intact. Shared source cleanup, host detachment/deletion, publication and host activation are separate effects.

## Combination failures and correction ownership

TASK-100 owns bounded corrections needed to qualify the combined candidate. Aquarium-side defects use the Epic's approved owned-correction path. For a producer-attributable failure, use the promoted Sorage protocol under the execution envelope's broker/correction authority: send a scoped EPIC-033 correction request with the failing combination and original requirement, reconcile an uncertain send, and accept a correlated corrected implementation return with the required released artifacts and exact binary/skill/profile identities. The producer owns its source, local work IDs and publication authority; Aquarium does not edit that source or infer permission to publish.

Re-verify the affected installation/upgrade, inter-tool behavior and release-assessment evidence against the corrected exact combination before TASK-100 can pass. This is a new EPIC-033 correction of a newly observed integration failure, not a reversal of the earlier individual acceptance or an obligation to reopen EPIC-032. Missing producer corrections or mandatory evidence keep EPIC-033 incomplete, or Blocked for the named external condition under the native workflow. A material scope change needs the applicable authority before proceeding. Keep the original failure and evidence; never delete it or claim whole-combination PASS from individual returns.

## Staged legacy retirement

The roadmap withdraws unfinished expansion of `EPIC-002`, preserving all completed records. During the transition, stop adding new legacy enrollments, but do not remove a manager still required by existing producers. Preserve its recovery path until actual detachment is complete.

Each producer inventories its current source and host references. Once its VM path passes, detach only the exact owned post-commit marker before removing the producer targets that marker invokes. Drain/stop and retire producer-owned development services through their native contract before deleting selected artifacts. Preserve foreign hook bytes, generic dev features, stable binaries and native skills. A changed source file is not proof that a live hook or service has been removed.

Aquarium's pilot can detach its own legacy enrollment under the corresponding authority, while retaining the shared manager for remaining tools. In TASK-090's read-only audit, Aquarium's own enrollment record pointed to another checkout, while the active checkout had no post-commit hook (`core.hooksPath` unset), so live `~/.aquarium-dev` detachment was deferred to TASK-101 under Master's `~/.aquarium-dev` non-mutation boundary. Final shared retirement occurs only after every producer return shows successful migration and either completed host detachment or verified absence of an enrollment.

Before deleting `~/.aquarium-dev/`, perform a fresh inventory of enrollments, queued requests, active workers, generation leases, development services, hooks, launchers, symlinks, shell PATH/config references, plugin MCP declarations, and status/setup consumers. Resolve in-flight users and the chosen evidence/backup policy. Shared launcher/runtime removal and the final directory deletion are explicit host effects, separate from repository source cleanup.

Preserve `~/.aquarium/`, production tool state, active Codex homes, unrelated skills, Sorage's coordination database/Vault, and unrelated Git hooks. Reconcile `aquarium-status` legacy enrollment reporting without deleting its production ledger. Retain minimal compatibility only while a real consumer needs it; do not replace aquarium-dev with another permanent dual-runtime channel.

## Task acceptance checklists

### TASK-100: Reconcile the full combination and upgrade path

Implement and document:

- [ ] Reconcile all nine accepted returns with the same frozen Haepari contract and current Aquarium candidate, rejecting inconsistent identities, missing skill sources and stale profiles.
- [ ] Resolve combined-candidate failures through this Epic's owned-correction or durable producer correction protocol. Accept exact corrected returns and re-verify affected cases; do not reopen earlier Epics or remove shared legacy infrastructure while qualification remains incomplete.
- [ ] Build the complete intended installation combination and verify clean install plus previous accepted combination to target migration, including fresh-session skills, representative inter-tool behavior and declared consumer cleanup.
- [ ] Verify prescribed update ordering and busy-work handling without rerunning every producer's internal unit suite as a substitute for integration.
- [ ] Exercise two participating project callers sharing the VM resource and two CLI/MCP callers sharing the review lock. Verify independent managed/lock accounting, no competing VM execution, serialized reviews with native role concurrency retained, renewal/release and return-before-user-wait. Preserve original invocation recovery, authorized new acquisitions and provider-free publication reconciliation without an outer lock wrapper.
- [ ] Verify the completed EPIC-031 assessment contracts against original Haepari evidence and the combined candidate. Use isolated guest fixtures/stub providers for failure tests and distinguish those results from actual installed/native observations.

Do not:

- [ ] Do not infer combined compatibility from individual passes, accept acknowledgements in place of returns, silently upgrade unrelated components or conflate candidate and release artifacts.

Verify and complete:

- [ ] Required per-product and whole-combination observations are complete; known findings and manual gaps are settled under the actual release policy.
- [ ] Inventory shows every former producer detached or demonstrably not enrolled, making shared retirement safe to plan.

### TASK-101: Retire shared legacy source and approved host state

Implement and document:

- [ ] Remove the obsolete manager/launcher/MCP declaration, development-channel setup/status consumers, producer-only helpers and obsolete tests only after confirming no remaining consumer needs them.
- [ ] Reconcile `aquarium-status` and existing persisted metadata without deleting production ledger/history. Preserve ordinary setup skills and the new Haepari integration.
- [ ] Reconcile the documentation inspector with the roadmap's permitted `Cancelled` epic lifecycle, using objective lifecycle tests. The planning inspection reported `epic_lifecycle_unverifiable` for EPIC-002. Do not label withdrawn work as completed to avoid the warning.
- [ ] Prepare and execute the separately approved host detachment/removal plan: fresh references/processes/leases/services, exact owned markers, preservation decision, launcher/runtime and final `~/.aquarium-dev/` removal.
- [ ] Promote actual new behavior into current specifications, architecture, ADRs, runbooks and relevant public documentation. Supersede prior ADRs only as the implemented boundary changes.

Do not:

- [ ] Do not use broad name-based process kills or recursive deletion before quiescence/ownership checks; do not delete stable skills, active account homes, Sorage data or unrelated hooks.

Verify and complete:

- [ ] Current non-historical source and live launch paths no longer depend on aquarium-dev. Historical release notes and completed task evidence remain intact.
- [ ] A new host development operation uses stable releases and Haepari VM tests without missing-command errors, implicit reinstalls or modification of protected production state.

### TASK-102: Cold-validate, promote documentation and close out

Implement and document:

- [ ] Perform fresh end-to-end acceptance of project-owned tests, fixed profiles, skills, meaningful migration, ordered producer returns, final host state and Haepari recovery independence. Include managed VM occupancy and the released native Mulgae advisory lock; preserve incomplete reviews, grant disposition, cleanup and assessment outcomes as separate facts.
- [ ] Reconcile all remaining durable statements with their canonical owners and collect Master's actual overall acceptance and required hands-on results.
- [ ] Promote durable setup/integration requirements to tool specifications/catalog and operations, release ownership to workflow specifications/architecture and native skill references, and scenarios/limits to testing authorities. Consume EPIC-019, EPIC-031 and EPIC-032 Canonical Outcomes without reopening their completed work or restoring their deleted dossiers.
- [ ] Settle this dossier and the retained legacy dossier after promoting required history and retirement outcomes. Inventory and replace EPIC-002's historical Detailed SOT and all remaining references without changing its Cancelled status or completed Task history. Replace EPIC-033's Detailed SOT with valid Canonical Outcomes, update documentation/TODO indexes and delete only under the approved final-closeout envelope; do not archive duplicates or recreate earlier Epics' dossiers.

Do not:

- [ ] Do not complete the epic from task status alone, manufacture observed results, change unrelated EPIC-018/EPIC-012 work, commit or publish outside the current authority, or delete a dossier still needed by another consumer.

Verify and complete:

- [ ] All producer return criteria, combined installed/migration checks, cleanup and non-regression requirements are met with exact evidence.
- [ ] Documentation/link checks pass and all accepted runtime facts are accurately classified. Any required unresolved evidence keeps the epic incomplete.

## Epic completion and dossier deletion

- [ ] The exact combined installed and upgrade/regression candidate passes required cases with actual manual observations, independent whole-Epic validation and truthful native/consumer cleanup results.
- [ ] All actual legacy consumers are detached or proved absent before common removal. Approved source and host cleanup are independently verified; production state, supported tools and historical acceptance remain intact.
- [ ] Durable combined compatibility, recovery, retirement and verification limits are promoted to their canonical owners. Earlier Epic outcomes remain usable without temporary dossiers or local runtime reports.
- [ ] Obtain Master's actual overall acceptance and replace EPIC-033's Detailed SOT with valid Canonical Outcomes. Settle the legacy dossier's historical roadmap references, including EPIC-002, without relabeling withdrawn work as completed.
- [ ] Replace all temporary links, remove this dossier and the settled legacy dossier's TODO entries, and delete those exact files only under the approved final-closeout envelope after their references and consumers are resolved. No duplicate archive is created.
