# Combined Haepari qualification and legacy retirement

## Authority and implementation state

The sole active consumer of this dossier is `EPIC-033`, with existing `TASK-100` through `TASK-102`. The [canonical roadmap](../roadmap/README.md) owns identity, ordering, dependencies and lifecycle; this dossier owns detailed qualification and retirement acceptance. EPIC-032 must be completed before entry; EPIC-019 and EPIC-031 are completed prerequisites through that chain.

This plan claims no runtime result and authorizes no implementation, host deletion, broker operation, commit, installation or publication. Shared host removal has its own explicit scope and approval within later execution. Candidate installation and installation-dependent verification remain confined to the dedicated UTM VM.

## Goal and canonical inputs

Qualify the full accepted tool/skill combination and its upgrade path, then retire common aquarium-dev source and approved host state after all consumers detach. Individual pilot and tool qualification remain their original facts; they do not prove the combined candidate. Final verification does not reopen earlier Epics or transfer unfinished criteria from them.

Aquarium v0.1.23 must not be released until this Epic fulfills the [roadmap release prerequisite](../roadmap/README.md#v0123-release-prerequisite). Both full and light releases require verified consumer detachment, common source removal, separately approved final host cleanup, the required final-candidate observations and actual overall acceptance and closeout. Passing tests or accepting the four early cleanup reports alone cannot satisfy that condition.

Simplify the Haepari integration accumulated across those Epics before final acceptance. Master's requested scope includes unnecessary Aquarium layers, validators and harness code. EPIC-019's functional qualification does not establish that its implementation is minimal. This is planned repository work; immediate Haepari use and host activation are not part of this planning change.

Read EPIC-019, EPIC-031 and EPIC-032 Canonical Outcomes plus current [tool specifications](../specs/tool-integrations.md), [tool catalog](../../plugins/aquarium/references/tool-catalog.md#haepari), [Haepari integration](../../plugins/aquarium/references/haepari-integration.md), [workflow specifications](../specs/workflow-contracts.md), [architecture](../architecture/README.md), [TESTING.md](../../TESTING.md), [tests/vm/README.md](../../tests/vm/README.md), and [Haepari VM operations](../ops/haepari-vm-verification.md). Require the promoted adapter/profile/cleanup contract, release-role assessment contract, accepted tool identity/verification/detachment inventory and the conditional producer-correction protocol. Aquarium supplies routine Haepari guidance and verification; nine producer adoption reports are not required. Earlier temporary dossiers must already have been settled and deleted at their own closeout; no input depends on retaining them.

Use exact intended binary/plugin/skill/configuration identities and meaningful prior accepted state in the VM. Exercise the original Job/result/consumer-cleanup handoff through release roles, shared-VM contention and Mulgae's released native advisory lock. Preserve native role concurrency and distinguish advisory expiry from managed unknown-execution containment. Use guest-only stub fault cases by default; real installed and any authorized live observations keep their own evidence. Consumer recipes verify their starting state and cleanup; Haepari never resets the VM or rolls back arbitrary guest changes. Missing required manual or combined evidence prevents acceptance.

The [legacy development dossier](TODO-AQUARIUM-DEV.md) remains a historical/migration reference for this Epic alone as its active retirement consumer. EPIC-002's Cancelled lifecycle and completed history stay intact. Shared source cleanup, host detachment/deletion, publication and host activation are separate effects.

## Haepari integration simplification

TASK-100 inventories the Aquarium adapters, profile and inventory validators, guest recipes, simulation fixtures and related tests accumulated during adoption and rollout. Identify their actual consumers and requirements, overlap with Haepari's native contract, and code that can be deleted or simplified. Record the before/after decisions in the existing Task report; this work needs no new verifier, registry or harness to judge its own size.

TASK-101 implements those reductions. Remove redundant wrappers, duplicated native policy checks, unused abstractions and speculative failure handling without a supported requirement. Delete obsolete fixtures and tests with their removed behavior; simplify tests that only restate implementation details. Keep the Aquarium-specific installation assertions, result handoff, guest-state protection and consumer cleanup that actual callers need. Haepari retains ownership of admission, scheduling, Job recovery, collection, owned Job cleanup and advisory locks. A line-count reduction alone does not demonstrate a simpler design.

TASK-102 verifies the resulting exact candidate through the supported native path. Cover installation and upgrade, shared occupancy, replay/reconnect, cancellation, truthful incomplete results and both native and consumer cleanup, plus the released review-lock behavior. Reuse existing entrypoints and focused behavioral tests. Candidate-installation checks run in the dedicated UTM VM. Preserve earlier evidence and its limits; changed code requires applicable new observations. Update canonical owners and remove obsolete instructions and test selections with the implementation.

## Combination failures and correction ownership

TASK-100 owns bounded corrections needed to qualify the combined candidate. Aquarium-side defects use the Epic's approved owned-correction path. For a producer-attributable failure, use the promoted Sorage protocol under the execution envelope's broker/correction authority: send a scoped EPIC-033 correction request with the failing combination and original requirement, reconcile an uncertain send, and accept a correlated corrected implementation return with the required released artifacts and exact binary/skill/profile identities. The producer owns its source, local work IDs and publication authority; Aquarium does not edit that source or infer permission to publish.

Re-verify the affected installation/upgrade, inter-tool behavior and release-assessment evidence against the corrected exact combination before TASK-100 can pass. This is a new EPIC-033 correction of a newly observed integration failure, not a reversal of the earlier individual acceptance or an obligation to reopen EPIC-032. Missing producer corrections or mandatory evidence keep EPIC-033 incomplete, or Blocked for the named external condition under the native workflow. A material scope change needs the applicable authority before proceeding. Keep the original failure and evidence; never delete it or claim whole-combination PASS from individual tool results.

## Staged legacy retirement

The roadmap withdraws unfinished expansion of `EPIC-002`, preserving all completed records. During the transition, stop adding new legacy enrollments, but do not remove a manager still required by existing producers. Preserve its recovery path until actual detachment is complete.

Each producer inventories its current source and host references. Podway, Dolgorae, Gaori and Sanho may perform this cleanup in parallel with EPIC-031 under their separately authorized requests. After required verification for that cleanup scope, including installation-dependent VM checks where applicable, detach only the exact owned post-commit marker before removing the producer targets that marker invokes. Drain/stop and retire producer-owned development services through their native contract before deleting selected artifacts. Preserve foreign hook bytes, generic dev features, stable binaries and native skills. A changed source file is not proof that a live hook or service has been removed.

Reuse those original cleanup exchanges and the evidence accepted by EPIC-032. Early completion establishes only its verified scope; it does not waive remaining producer criteria or this Epic's exact combined-candidate checks. Final shared retirement waits for the full accepted consumer inventory, including Aquarium, with no remaining users or recovery obligations.

Aquarium's pilot can detach its own legacy enrollment under the corresponding authority, while retaining the shared manager for remaining tools. In TASK-090's read-only audit, Aquarium's own enrollment record pointed to another checkout, while the active checkout had no post-commit hook (`core.hooksPath` unset), so live `~/.aquarium-dev` detachment was deferred to TASK-101 under Master's `~/.aquarium-dev` non-mutation boundary. Final shared retirement occurs only after every producer return shows successful migration and either completed host detachment or verified absence of an enrollment.

Before deleting `~/.aquarium-dev/`, perform a fresh inventory of enrollments, queued requests, active workers, generation leases, development services, hooks, launchers, symlinks, shell PATH/config references, plugin MCP declarations, and status/setup consumers. Resolve in-flight users and the chosen evidence/backup policy. Shared launcher/runtime removal and the final directory deletion are explicit host effects, separate from repository source cleanup.

Include the previous released Aquarium plugin in that inventory. Follow the roadmap's [installed host transition](../roadmap/README.md#installed-host-transition): TASK-100 identifies and verifies in the VM the supported native way to disable its channel MCP launch path and preserve normal use of released skills, tools and setup/status; TASK-101 obtains separate approval and performs that transition before deleting the shared runtime. Verify the interim released installation with channel activation disabled and its later upgrade to the candidate. Old package bytes may remain unchanged only while their channel references are inactive. No candidate installation on the host or cache patch is permitted. An unavailable transition keeps removal and publication blocked.

Preserve `~/.aquarium/`, production tool state, active Codex homes, unrelated skills, Sorage's coordination database/Vault, and unrelated Git hooks. Reconcile `aquarium-status` legacy enrollment reporting without deleting its production ledger. Retain minimal compatibility only while a real consumer needs it; do not replace aquarium-dev with another permanent dual-runtime channel.

At closeout, promote the accepted source identity, actual acceptance reference and dated host-cleanup observations into the durable Canonical Outcomes under the evidence-residency contract. The later release resolves the closeout commit and applies the roadmap's [release evidence applicability](../roadmap/README.md#release-evidence-applicability) rule to subsequent changes. Host observations remain distinct from Git identities; neither substitutes for the release's exact-candidate gates.

## Task acceptance checklists

### TASK-100: Reconcile the full combination and upgrade path

Implement and document:

- [ ] Reconcile all nine accepted tool-verification scopes with the same frozen Haepari contract and current Aquarium candidate, rejecting inconsistent identities, missing skill sources and stale profiles.
- [ ] Identify redundant Aquarium layers, validators, harness code and tests across the completed adoption and rollout. Give each retained component a concrete consumer requirement and identify deletions or simplifications for TASK-101.
- [ ] Identify the supported native transition for the previous released plugin's channel launch path. Rehearse the disabled-channel interim host combination and its upgrade in the dedicated VM, retaining exact operation, component and verification identities for TASK-101's separate approval.
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

### TASK-101: Retire shared legacy source and simplify Haepari integration

Implement and document:

- [ ] Remove the obsolete manager/launcher/MCP declaration, development-channel setup/status consumers, producer-only helpers and obsolete tests only after confirming no remaining consumer needs them.
- [ ] Remove or simplify the unnecessary Haepari integration layers, validators and harness identified by TASK-100, along with obsolete fixtures and tests. Delegate native responsibilities to Haepari and retain only code justified by current Aquarium consumers and requirements.
- [ ] Record the actual removals, remaining responsibilities and maintenance impact. Update affected contracts, runbooks and test entrypoints; do not replace removed machinery with another general verification framework or waive required behavior checks.
- [ ] Reconcile `aquarium-status` and existing persisted metadata without deleting production ledger/history. Preserve ordinary setup skills and the new Haepari integration.
- [ ] Reconcile the documentation inspector with the roadmap's permitted `Cancelled` epic lifecycle, using objective lifecycle tests. The planning inspection reported `epic_lifecycle_unverifiable` for EPIC-002. Do not label withdrawn work as completed to avoid the warning.
- [ ] Prepare and execute the separately approved host detachment/removal plan: fresh references/processes/leases/services, exact owned markers, preservation decision, launcher/runtime and final `~/.aquarium-dev/` removal.
- [ ] Apply the VM-verified native transition to the installed prior release before deleting the shared launcher/runtime. Verify that no active MCP launch or normal setup/status workflow needs or implicitly reinstalls the channel; preserve the installed package bytes and released skill/tool access.
- [ ] Promote actual new behavior into current specifications, architecture, ADRs, runbooks and relevant public documentation. Supersede prior ADRs only as the implemented boundary changes.

Do not:

- [ ] Do not use broad name-based process kills or recursive deletion before quiescence/ownership checks; do not delete stable skills, active account homes, Sorage data or unrelated hooks.

Verify and complete:

- [ ] Current non-historical source and live launch paths no longer depend on aquarium-dev. Historical release notes and completed task evidence remain intact.
- [ ] The implemented integration reductions match the reviewed decisions, retained components have concrete consumers, and focused behavior checks pass. TASK-102 still qualifies the final installed combination.
- [ ] A new host development operation uses stable releases and Haepari VM tests without missing-command errors, implicit reinstalls or modification of protected production state.

### TASK-102: Cold-validate, promote documentation and close out

Implement and document:

- [ ] Perform fresh end-to-end acceptance of project-owned tests, fixed profiles, skills, meaningful migration, all accepted tool-verification scopes and their actual dependencies, final host state and Haepari recovery independence. Include managed VM occupancy and the released native Mulgae advisory lock; preserve incomplete reviews, grant disposition, cleanup and assessment outcomes as separate facts.
- [ ] Qualify the exact simplified implementation after TASK-101, including required failure and recovery paths. Confirm that removed layers, validators and harness code are absent and remaining behavior works without a replacement framework; earlier candidate results alone do not qualify the changed implementation.
- [ ] Reconcile all remaining durable statements with their canonical owners and collect Master's actual overall acceptance and required hands-on results.
- [ ] Promote durable setup/integration requirements to tool specifications/catalog and operations, release ownership to workflow specifications/architecture and native skill references, and scenarios/limits to testing authorities. Consume EPIC-019, EPIC-031 and EPIC-032 Canonical Outcomes without reopening their completed work or restoring their deleted dossiers.
- [ ] Promote the accepted source and acceptance references, host-cleanup observation and installed-release transition evidence for later release-readiness checks. Preserve the original tested basis through closeout so the release can resolve its ancestry and inspect subsequent retirement-affecting changes without treating documentation commits as new host cleanup.
- [ ] Settle this dossier and the retained legacy dossier after promoting required history and retirement outcomes. Inventory and replace EPIC-002's historical Detailed SOT and all remaining references without changing its Cancelled status or completed Task history. Replace EPIC-033's Detailed SOT with valid Canonical Outcomes, update documentation/TODO indexes and delete only under the approved final-closeout envelope; do not archive duplicates or recreate earlier Epics' dossiers.

Do not:

- [ ] Do not complete the epic from task status alone, manufacture observed results, change unrelated EPIC-018/EPIC-012 work, commit or publish outside the current authority, or delete a dossier still needed by another consumer.

Verify and complete:

- [ ] All producer return criteria, combined installed/migration checks, cleanup and non-regression requirements are met with exact evidence.
- [ ] Documentation/link checks pass and all accepted runtime facts are accurately classified. Any required unresolved evidence keeps the epic incomplete.

## Epic completion and dossier deletion

- [ ] The exact combined installed and upgrade/regression candidate passes required cases with actual manual observations, independent whole-Epic validation and truthful native/consumer cleanup results.
- [ ] Unnecessary Haepari integration layers, validators and harness code are removed or simplified, with documented retention reasons and passing observations for the final implementation. No new verification framework is introduced for this cleanup.
- [ ] All actual legacy consumers are detached or proved absent before common removal. Approved source and host cleanup are independently verified; production state, supported tools and historical acceptance remain intact.
- [ ] Verify every outcome in the roadmap's v0.1.23 release prerequisite. Any missing retirement, required verification or actual acceptance keeps that release blocked in both full and light mode.
- [ ] Durable combined compatibility, recovery, retirement and verification limits are promoted to their canonical owners. Earlier Epic outcomes remain usable without temporary dossiers or local runtime reports.
- [ ] Obtain Master's actual overall acceptance and replace EPIC-033's Detailed SOT with valid Canonical Outcomes. Settle the legacy dossier's historical roadmap references, including EPIC-002, without relabeling withdrawn work as completed.
- [ ] Replace all temporary links, remove this dossier and the settled legacy dossier's TODO entries, and delete those exact files only under the approved final-closeout envelope after their references and consumers are resolved. No duplicate archive is created.
