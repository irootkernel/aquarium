# Haepari VM Verification and Development-Channel Retirement

## Authority and implementation state

Consumer epic: `EPIC-019`. The [canonical roadmap](../roadmap/README.md) alone owns task IDs, execution order, dependencies, and lifecycle status. This dossier owns the detailed scope and acceptance for `TASK-086` through `TASK-102`. Every checklist below is planned acceptance, not evidence of completed implementation.

The external producer is Haepari, an independent Go CLI and resource-aware local daemon. Its v0.1.0 requirements, architecture, ADRs, contracts, roadmap, and request templates are supplied in the Haepari development package. That package is a design input; it does not satisfy the implemented-product dependency. `TASK-086` must accept the exact Haepari release and capability handoff before Aquarium implementation begins.

This epic adopts project-owned VM tests, delegates external review-lease integration to Mulgae, and retires the old development channel in stages. Haepari design revision 2 supplies both managed and external execution contracts; the product target remains v0.1.0. This epic does not implement Haepari or edit producer repositories. No Sorage message has been sent by creating this plan. No host runtime, hook, service, skill, or development directory has been removed.

The [old development dossier](TODO-AQUARIUM-DEV.md) is retained as a migration reference. Its completed history remains valid; unfinished expansion is withdrawn in the roadmap. Its installed behavior continues to be owned by the existing [development contract](../../plugins/aquarium/references/development-contract.md) until the approved cutover changes that owner.

## Goal

Keep stable Aquarium and tools available on the host while candidate installation, installed-skill behavior, hands-on work, migration, and regression are verified in an exclusively allocated macOS VM. Every product owns its test scenarios. Haepari owns admission, waiting, managed VM lifecycle, evidence transport, reset, and resource recovery. Ordinary Mulgae reviews use a separate external resource: Haepari grants capacity, while Mulgae and its caller own native execution, retry, source retention and result composition. Both execution modes share Haepari's scheduler and global occupancy limit.

Aquarium adopts the arrangement first, then coordinates the following producers through Sorage in this exact order:

`Podway -> Mulgae -> Gaori -> Sorage -> Sanho -> Dolgorae -> Gul -> Seongge -> Gaebokchi`.

Each producer must return accepted implementation and verification evidence before the next producer is dispatched. After the final return, Aquarium reconciles the full environment, retires shared legacy infrastructure, and completes its own cold validation and documentation closeout.

## Scope and exclusions

Aquarium owns its Make targets, tests, guest installation recipes, profile definitions, skill integration, setup guidance, release-gate wiring, coordination requests, returned-evidence review, and final shared-channel retirement. The producers own their source, local roadmap IDs, installation units, migrations, tests, and product-specific legacy detachment.

Do not implement a central integration-test repository, another queue, a competing Podway scheduler, or a product compatibility registry inside Haepari. Do not add VM or paid-provider dependencies to the ordinary local `make test` gate without a separately adopted contract change. Do not automatically publish a release, change a model/provider account, or update host tools when a VM test passes.

Do not remove native `use-*` skills, external global skills, `dev-setup`, `dev-setup-global`, or generic development capabilities merely because their names contain `dev`. The obsolete feature is the `aquarium-dev` runtime, CLI/MCP registration, enrollment/hook/publication machinery, and producer-specific integration proved exclusive to that channel. The current channel does not have a paired `aquarium-dev` skill to delete indiscriminately.

## Shared implementation contracts

### Project-owned entrypoints and immutable input

Every adopting project exposes `make test-vm SUITE=install|migration|regression|all MODE=auto|manual`, or a documented equivalent adapter satisfying the same contract. Its host wrapper freezes candidate and test bytes, submits once through the supported Haepari CLI, reports the Job reference, blocks on that same job, and returns a truthful result. It never controls UTM directly or falls back to installing a candidate on the host.

The guest entrypoint is distinct, such as `make test-vm-guest` or `tests/vm/run.sh`. It verifies guest/lease identity before installation and never recursively submits a job. Development snapshots may include selected dirty-worktree bytes; their content digest is the candidate identity. Release evidence must satisfy the existing exact committed/distributed candidate policy. Queue waiting must not cause later worktree changes to alter the admitted candidate.

The all suite submits separate install and migration/regression jobs as required, using the same fixed candidate. Reset between independent jobs, but never reset between old-state creation and assertions inside one migration job. Retain all Job results and report skipped or unobserved required suites rather than returning aggregate success.

### Managed VM execution and external review leases

UTM tests use Haepari-managed execution, including manual hands-on ownership. Ordinary reviews use a separately configured `mulgae-review` external resource, not a managed Job wrapper. `auto/manual` is a test-mode distinction; `managed/external` names the execution owner. The same scheduler accounts for reserved, active and unresolved occupancy in both resource queues. One external review segment consumes one slot regardless of its native role/provider count.

The external request must atomically grant or queue. Accepted admission is not a grant, and a grant is not native execution or user authorization. A single caller executor activates the grant and records a first-claim-only execution intent before each native CLI/MCP mutation. Replayed admission or begin cannot authorize a second native call. Use blocking wait/events, stable request/operation keys and protected owner material. No silent unqueued fallback is allowed when the selected queue path is unavailable.

A logical review may span several native runs and Haepari leases. Within existing native/user recovery authority, an immediate exact rerun stays under the current lease with a new execution intent; never recursively acquire while holding that operation's lease. If native execution has terminated but a user decision or long external delay is required, retain native recovery sources, settle the execution and return with `awaiting_user` or `deferred`. Keep no slot or speculative queued request during that wait. On later authorization use a new request key and lease, the same opaque operation reference and an exact released-parent link. Admission uses ordinary FIFO, not the old queue position.

Haepari must fence stale releases and reject concurrent continuation branches. The caller also owns a minimal durable single-executor dispatch/recovery checkpoint; admission deduplication does not make non-idempotent native starts safe to repeat. Unknown starts, lost process-local invocation handles, observer timeouts and unconfirmed cancellation retain occupancy in reconciliation. Only supported native termination/no-start evidence permits return. Direct CLI/MCP callers outside the integration remain outside this advisory limit.

For six selected roles with five accepted and one failed, preserve the exact root target, accepted results, failed attempt and rerun lineage. Later recovery runs only the missing role and uses native compose; complete coverage, publication, findings/CI and returned capacity remain separate facts. Do not mix results for different targets, drop a failed selected optional role, switch providers automatically, reconstruct purged native sources, or add role/result state to Haepari.

TASK-092 delegates this implementation to the Mulgae project, including its owned `use-mulgae` skill and any minimal required native helper. Aquarium accepts the returned capability and updates only its own affected review integration references, without wrapping the producer with a second lease layer. Haepari's standalone fixture evidence does not prove native Mulgae behavior. Tests of the new integration inside a managed VM use an isolated Haepari instance/test resource, never the parent controller's already occupied VM or global slot. The Aquarium-first pilot does not depend on the not-yet-delivered Mulgae integration.

### Baselines, profiles, and release combinations

Aquarium's native tool catalog continues to own support ranges and installation rules. A project-owned test profile selects exact binary, daemon, plugin, skill, rules, and effective configuration identities within those policies. It is immutable test input, not a second account-wide setup registry. Machine-local VM registration, package paths, SSH identity, and resource state belong to Haepari/operator configuration.

Normal development uses an explicitly accepted stable combination and overrides the selected product's entire declared candidate unit. A skill-only change can override its skill tree while retaining the binary. A next-release integration can select a named candidate combination. Resolve any default/latest alias before admission and retain its exact profile digest; never fetch latest while an admitted job executes.

Aquarium's final installed VM release gate applies the complete intended tool/skill combination, including unchanged pinned components. Candidate integration evidence and final official-distribution evidence remain distinct. If final binary or skill bytes change, prior evidence cannot silently qualify the new bytes.

### Complete skill and configuration identity

Compare complete incoming and installed skill trees, not only `SKILL.md` or an inspector's minimum file list. Include references, scripts, assets, executable bits, added/removed files, native source provenance, and effective connection settings. Binary and skill identities are separate; preserve independently pinned skills and same-release pairings according to the current native contract.

Honor the selected upstream installation scope, including shared `~/.agents/skills`, the active `<CODEX_HOME>/skills`, per-home rules, plugin-owned resources, and project discovery roots. Check duplicate/shadowing copies that the selected native client can load. Do not unify these roots or copy the host's active home into the VM.

Installation correctness, discovery in a fresh native process/session, observed skill behavior, and restoration are separate evidence classes. Pasting skill text into a prompt or executing a binary directly cannot qualify installed-skill discovery. Preserve missing manual observations as unverified; neither Haepari nor Aquarium invents a human pass.

### Migration and regression

A migration scenario begins with the exact prior supported installation combination and creates meaningful synthetic state through its old public interfaces. Verify the old behavior and record preservation invariants before applying the candidate. Keep the same data and configuration through update, then verify reads, new writes, restart, skill discovery, and required existing workflows.

Cover configuration and custom values, binary/service pairing, skill/rules replacement and obsolete-file removal, persistent data/identifiers, and the native busy-work policy. Prove either supported resume or safe refuse/drain before update; do not invent uninterrupted-upgrade support. Include a bounded interrupted migration and its documented recovery or safe failure. A retry must not duplicate logical work.

The immediate prior accepted version/profile is the default required path. Wider advertised upgrade paths require corresponding tests. A first release records the absence of a predecessor with evidence, not a fabricated migration pass. Product downgrade is a separate native promise; restoring the test VM does not prove it.

### Manual, live, and release-QA boundaries

Manual mode prepares the exact candidate environment and holds the same exclusive resource while Master verifies the project checklist. Preparation-ready is not a test pass. Bind the actual observer, scenarios, candidate/profile, observations, and omissions to the result, then collect and reset before resource return.

Offline fixtures are default. Live service/model use requires the exact approved guest endpoints, test identities, and cost/time scope. Never copy host account files or use real Sorage/production data as fixtures. VM restoration does not reverse external writes or charges.

The current `release-qa` is an offline disposable-scenario contract and must not silently gain global installation or live-provider authority. Add a separate installed VM verification step to the release workflow and bind its evidence to the same candidate and fixed environment. Existing automated VM tests do not replace the current release-delta assessment. Keep publication and host activation separate.

### Results, cleanup, and failure

Require Haepari's native distinction between workload outcome, required evidence completeness, cleanup/restoration, and final verdict. A successful workload with failed reset or missing required observations cannot pass. A connection loss does not prove termination; reattach the same Job/run and reconcile uncertain effects instead of starting another test.

Whole-environment reset must restore binaries, skill roots, plugin/configuration state, services, and guest data. Verify the restored inventory. If cleanup is unproven, Haepari quarantines the resource and blocks its next job. Raw runtime IDs, local paths, Sorage metadata, and provider logs remain local evidence unless a reviewed bounded promotion satisfies the existing evidence-residency contract.

## Sorage request and completion protocol

Use the installed native `use-sorage` skill and observed output when this epic's execution envelope explicitly authorizes a broker operation. This plan alone does not authorize a send or discovery. Resolve the actual recipient identity rather than guessing a Project slug from a product name.

A request carries a stable logical correlation key, the immutable request-document digest, exact Haepari and pilot/profile contracts, the producer-specific scope, expected return fields, and the permitted effect boundaries. Allocate the native Handoff once and preserve its real receipt/revision. If a send result is uncertain, reconcile native state before another send; do not manufacture application-level message IDs or edit broker storage.

The producer allocates its own local task/epic IDs and may accept the request or ask for changes through the native review loop. Acceptance of the request means the request was accepted, not that implementation is complete. Aquarium's coordination task remains open while producer implementation or required evidence is pending.

The producer sends a separate completion-report Handoff back to Aquarium after implementation and verification. It references the original logical request, native request/revision, and accepted scope. The producer does not edit Aquarium's sender-owned request or the managed Vault. Aquarium reads the current returned document, checks evidence, requests bounded corrections through native review/revision when needed, and explicitly accepts the completed response only when its criteria are met.

Do not send the next project until this return is accepted. Blocked or unobserved producer work pauses the sequence; a receipt, acknowledgement, commit list, or prose claim is insufficient. No recurring inbox watcher, unrelated inbox scan, or automatic resend is part of the implementation. An authorized waiting operation uses native supported waiting semantics.

### Required producer return

The report must contain the resolved producer/repository and producer-owned work IDs; exact source/candidate/test identities; installation-unit and skill-tree provenance; Haepari executable/runner/capability identity; starting/target profile digests; per-suite Job references and actual observations; old-state migration and regression evidence; manual gaps; cleanup and restored inventory; product-specific legacy source changes; separately evidenced host detachment; released/unreleased status; and remaining limitations.

The Mulgae return additionally identifies the external request/lease generations, operation/continuation references and native root/rerun/attempt/composite results without ownership secrets. Require same-lease immediate retry, return-before-user-wait, fresh-lease continuation, preserved target/coverage, duplicate resume/start rejection and unknown-execution handling. VM-only success cannot complete TASK-092. Other producers do not acquire an external-review implementation obligation merely because this section exists.

A missing prior release or native skill uses evidence-backed `not_applicable`. Do not invent a `use-gul`, `use-seongge`, or `use-gaebokchi` merely to satisfy a template. A candidate using an API beyond the frozen Haepari contract is a dependency change that must be resolved before acceptance.

## Staged legacy retirement

The roadmap withdraws unfinished expansion of `EPIC-002`, preserving all completed records. During the transition, stop adding new legacy enrollments, but do not remove a manager still required by existing producers. Preserve its recovery path until actual detachment is complete.

Each producer inventories its current source and host references. Once its VM path passes, detach only the exact owned post-commit marker before removing the producer targets that marker invokes. Drain/stop and retire producer-owned development services through their native contract before deleting selected artifacts. Preserve foreign hook bytes, generic dev features, stable binaries and native skills. A changed source file is not proof that a live hook or service has been removed.

Aquarium's pilot can detach its own legacy enrollment under the corresponding authority, while retaining the shared manager for remaining tools. Final shared retirement occurs only after every producer return shows successful migration and either completed host detachment or verified absence of an enrollment.

Before deleting `~/.aquarium-dev/`, perform a fresh inventory of enrollments, queued requests, active workers, generation leases, development services, hooks, launchers, symlinks, shell PATH/config references, plugin MCP declarations, and status/setup consumers. Resolve in-flight users and the chosen evidence/backup policy. Shared launcher/runtime removal and the final directory deletion are explicit host effects, separate from repository source cleanup.

Preserve `~/.aquarium/`, production tool state, active Codex homes, unrelated skills, Sorage's coordination database/Vault, and unrelated Git hooks. Reconcile `aquarium-status` legacy enrollment reporting without deleting its production ledger. Retain minimal compatibility only while a real consumer needs it; do not replace aquarium-dev with another permanent dual-runtime channel.

## Task acceptance checklists

### TASK-086: Accept Haepari and freeze the consumer contract

Implement and document:

- [ ] Verify Haepari's exact producer handoff, official release/artifact and full skill identities, supported platforms, runner compatibility, schemas, blocking wait, manual results, migration example and real UTM reset evidence. The default is an official release; an explicitly selected exact candidate needs the same artifact/capability evidence and must retain its candidate evidence class.
- [ ] Freeze the project submission/result contract and read current Aquarium test, setup, tool-catalog, evidence, release, and Sorage authorities.
- [ ] Require exact managed/external resource capabilities, atomic grant/queue, single-executor activation and first-claim dispatch, native-reference settlement, safe release and linked continuation. Accept Haepari's independent E01 through E20 fixture evidence without making actual Mulgae adoption a producer prerequisite.
- [ ] Define the explicit test-profile exception to the no-shadow-global-registry policy and identify durable specification/architecture/ADR owners for later promotion.

Do not:

- [ ] Do not start consumer implementation on a design-only Haepari promise, assume a version implies capabilities, send producer requests, or install/update the host without its applicable authority.

Verify and complete:

- [ ] Parse valid and invalid managed and external input/result fixtures and demonstrate supported wait/reconnect through the exact installed test release. Verify a stale lease cannot return a successor's capacity and an uncertain native start cannot be re-dispatched from a replay.
- [ ] The handoff is sufficient without a circular dependency on Aquarium adoption; all missing prerequisite evidence keeps this task incomplete.

### TASK-087: Define fixed profiles and complete installation inventories

Implement and document:

- [ ] Add Aquarium-owned test-profile inputs, native component/skill pin mapping, exact host-runtime/client identity, candidate overrides, and before/candidate/restored inventory contracts.
- [ ] Define product-absent install and prior-version migration starting profiles, next-release whole-combination selection, private machine-local baseline registration and supported upgrade edges.

Do not:

- [ ] Do not vendor upstream skills, commit credentials/local VM registrations, duplicate tool-catalog support authority, or resolve latest after admission.

Verify and complete:

- [ ] Validate full-tree skill-only and independently pinned cases, duplicate locations, stale files, settings drift and profile digest changes.
- [ ] Profile definitions are reproducible test inputs and do not claim an actual VM was provisioned or a migration passed.

### TASK-088: Implement Aquarium's project-owned VM suites

Implement and document:

- [ ] Add the host `test-vm` wrapper, separate guest entrypoint, immutable package/test bundle and truthful per-suite result mapping.
- [ ] Add actual candidate plugin installation, initial setup, previous-version synthetic state, upgrade, existing-behavior regression, restart and bounded migration failure/recovery scenarios.
- [ ] Keep UTM/SSH/reset in Haepari and preserve the ordinary local test gate.

Do not:

- [ ] Do not install the candidate on the host, recursively enqueue from the guest, fabricate prior state with the new version, or erase migration state before assertions.

Verify and complete:

- [ ] Demonstrate install and migration as distinct jobs, queued-source immutability, missing-VM failure, guest identity rejection and result/cleanup failure propagation.
- [ ] The actual plugin package, configuration and supported prior behavior are exercised; source-level tests alone do not complete this task.

### TASK-089: Integrate skills, hands-on and the VM release gate

Implement and document:

- [ ] Add complete skill/rules/configuration installation inspection and fresh native session discovery, representative workflow behavior and explicit manual observation records.
- [ ] Connect a separate installed VM release step with candidate/profile-bound evidence to the existing release workflow, preserving current offline release-QA and publication authority.
- [ ] Define full intended release-combination and existing-stable-to-candidate upgrade scenarios, plus final distribution identity checks.

Do not:

- [ ] Do not substitute file hashes or pasted instructions for installed-skill behavior, auto-grade Master, contact providers by default, or broaden the existing release-qa invocation implicitly.

Verify and complete:

- [ ] Observe required actual installed-session and hands-on cases, including duplicate or stale skill failure, and verify cleanup restores the original discovery/configuration state.
- [ ] Missing human/live evidence remains incomplete and cannot be accepted through a successful Make exit alone.

### TASK-090: Qualify the Aquarium pilot and freeze producer packets

Implement and document:

- [ ] Run the complete Aquarium-only pilot with fixed install/migration/regression/manual evidence, disconnect/cancel/reset failure, and a second clean job.
- [ ] Package the accepted consumer contract, Haepari identity, profile examples, producer request template, completion template and per-project acceptance scope. The revised Mulgae packet must cover both managed VM adoption and external `use-mulgae` leases, partial-failure recovery, native compose and explicit advisory limits.
- [ ] Inspect Aquarium's own legacy enrollment and, after explicit approval, detach its owned hook and development use while retaining shared infrastructure required by later producers.

Do not:

- [ ] Do not dispatch external projects before pilot acceptance, delete the shared manager, treat mock-only UTM evidence as sufficient, or label an acknowledgement as producer completion.

Verify and complete:

- [ ] Host stable Aquarium/tools/skills remain usable; runtime changes are confined to approved Haepari/test/own-detachment state.
- [ ] All pilot criteria are accepted, and one precise producer packet can start the ordered delegation without undocumented assumptions.

### Common acceptance for TASK-091 through TASK-099

Each task is Aquarium-owned coordination work with a separately owned producer implementation. Its normal final commit records only accepted Aquarium-owned integration/documentation changes. Intermediate transport state stays in Sorage and permitted local evidence; do not manufacture a repository commit for every poll or message.

- [ ] Read the current prerequisite acceptance and resolve the next exact recipient.
- [ ] Send one authorized, versioned request with the common contract and product-specific criteria. Reconcile an uncertain send before retrying.
- [ ] Obtain the producer's own work-ID mapping and a correlated completed implementation report, not merely a request acknowledgement.
- [ ] Verify exact candidate/test/profile/binary/skill identities, installation, real old-state migration where applicable, regression, manual observations, failure recovery and resource reset.
- [ ] Review actual obsolete source removal and separately evidenced native hook/service detachment or proven absence. Preserve shared infrastructure until TASK-101.
- [ ] Return corrections through Sorage when acceptance is incomplete; do not edit producer source from Aquarium.
- [ ] Accept the final returned Handoff using current native revision/row fences, promote only permitted bounded evidence, and only then allow the next task.

### TASK-091: Delegate and accept Podway

- [ ] Apply the common acceptance protocol to Podway.
- [ ] Require matching CLI/daemon candidate identity, the independently declared full `use-podway` tree, workspace/configuration/history preservation, Procedure compatibility, restart/recovery and the native busy-work update policy.
- [ ] Detach only legacy producer/controller/development-service interfaces proved exclusive to aquarium-dev. Preserve supported native runtime modes and generic features still used independently.
- [ ] Verify migration does not drop workspace identity, historical records, logical retry state or active-work obligations. Accept only actual product evidence and restored VM state.

### TASK-092: Delegate and accept Mulgae

- [ ] Apply the common acceptance protocol to Mulgae after Podway acceptance. Send the revised two-part request through Sorage; the producer allocates its own implementation tasks and changes its own source/skill.
- [ ] Require installed review execution/result retrieval, native provider/role configuration, existing review/configuration migration and complete `use-mulgae` verification across the actual CLI/MCP transport.
- [ ] Require queue-backed ordinary review execution through external atomic request/wait, single-executor activation, first-claim native begin, terminal settlement and release. Preserve native transport and async completion semantics, not just start acknowledgement.
- [ ] Require a minimal durable ownership/dispatch/recovery checkpoint, stable request keys, opaque operation references, current lease generations and protected owner material. Native mutation response loss remains a reconciliation problem even when Haepari admission is certain.
- [ ] Verify the six-role partial-failure case: five accepted results remain unchanged; authorized immediate exact recovery uses the same lease, with no recursive acquisition or repeated successful role.
- [ ] Verify that failed recovery with confirmed native termination returns the lease before asking the user. An unrelated review must progress while the original logical review remains incomplete.
- [ ] Verify later authorized one-role recovery under a new FIFO request/lease linked to the released segment, exact native source/attempt lineage and immutable compose. Reject concurrent resume branches, duplicate starts, stale return, mixed targets, missing/corrupt recovery sources and selected-role omissions.
- [ ] Verify observer timeout, native cancellation, caller death, controller restart and lost invocation identity cannot free possibly active capacity. Distinguish returned capacity from publication, coverage, findings and CI outcomes.
- [ ] Use synthetic targets and an isolated test Haepari instance/resource in the VM; never acquire the already occupied parent VM/global slot or transmit production repository data merely to satisfy a default test. Live native acceptance retains its separately approved scope.
- [ ] Verify old-to-new installed `use-mulgae` discovery and behavior, whole-environment restoration and the documented advisory limitation of direct unqueued calls. VM-only or generic fixture-only evidence does not complete this task.
- [ ] After accepting the producer return, align only Aquarium-owned affected review contracts/capability references with the exact native result. Do not implement the producer or add an outer lease wrapper around `use-mulgae`.
- [ ] Verify old development references are removed without deleting the stable review runtime or host skill.

### TASK-093: Delegate and accept Gaori

- [ ] Apply the common acceptance protocol to Gaori after Mulgae acceptance.
- [ ] Require configured command execution, native exit status, output/evidence handling, waiting/reconnection and existing configuration/history migration; verify both native Gaori skills where shipped.
- [ ] Confirm Haepari status/cancel/cleanup works when the Gaori candidate fails. Gaori may wrap product checks but cannot own Haepari's resource lease or final recovery.
- [ ] Verify obsolete development integration is retired while normal execution/status skills and stable host behavior remain intact.

### TASK-094: Delegate and accept Sorage

- [ ] Apply the common acceptance protocol to Sorage after Gaori acceptance, using the stable host broker for the real rollout exchange.
- [ ] Require guest-only synthetic Project/Handoff/revision/Review Note/configuration/Vault migration, native recovery and full `use-sorage` installation evidence.
- [ ] Keep VM test traffic separate from real coordination messages. Do not copy, reset, or migrate the host coordination database/Vault as a test fixture.
- [ ] Accept a separately correlated completion report through stable Sorage; Sorage-under-test cannot be the only path for reporting its own failure.

### TASK-095: Delegate and accept Sanho

- [ ] Apply the common acceptance protocol to Sanho after Sorage acceptance.
- [ ] Require current native commit/push policy and configuration/state migration using disposable repositories and local test remotes, plus complete `use-sanho` verification.
- [ ] Preserve unrelated hook content and Git state, and prevent test pushes to real development remotes.
- [ ] Confirm obsolete development services/hooks are safely detached under their own authority before legacy selected artifacts are removed.

### TASK-096: Delegate and accept Dolgorae

- [ ] Apply the common acceptance protocol to Dolgorae after Sanho acceptance.
- [ ] Inspect the current product rather than guessing architecture; require its actual installed controller/broker/CLI contract, durable run/session/configuration migration, supported recovery and complete `use-dolgorae` identity.
- [ ] Verify Haepari remains able to collect and reset when the Dolgorae candidate cannot supervise work.
- [ ] Preserve stable host and provider account state while retiring only obsolete development-channel bindings.

### TASK-097: Delegate and accept Gul

- [ ] Apply the common acceptance protocol to Gul after Dolgorae acceptance.
- [ ] Require installed application/web assets, test-only backend endpoints, the declared compatible Dolgorae version, configuration migration and representative GUI hands-on behavior.
- [ ] Inventory actual shipped skills and mark absence not_applicable with source evidence; do not invent a skill requirement.
- [ ] Confirm tests do not connect to the host production backend, and report exact legacy cleanup or verified absence.

### TASK-098: Delegate and accept Seongge

- [ ] Apply the common acceptance protocol to Seongge after Gul acceptance.
- [ ] Require current skill-evaluation input/result/configuration behavior, supported backend identity, native package/skill inventory, prior-state migration and explicitly scoped live/manual cases.
- [ ] Preserve meaningful offline fixtures and report missing live evidence rather than starting an unapproved provider campaign.
- [ ] Remove legacy integration only where current source and host evidence show it exists; do not revive withdrawn EPIC-002 expansion.

### TASK-099: Delegate and accept Gaebokchi

- [ ] Apply the common acceptance protocol to Gaebokchi after Seongge acceptance.
- [ ] Require provider/account selection, output and usage-query behavior, existing configuration migration and redaction using synthetic fixtures by default.
- [ ] Live verification uses approved guest test accounts. Never copy host `~/.codex` or alternative account homes into bundles or the baseline.
- [ ] Inventory any native skills and actual legacy references, provide evidence-backed not_applicable where appropriate, and return the final producer packet.

### TASK-100: Reconcile the full combination and upgrade path

Implement and document:

- [ ] Reconcile all nine accepted returns with the same frozen Haepari contract and current Aquarium candidate, rejecting inconsistent identities, missing skill sources and stale profiles.
- [ ] Build the complete intended installation combination and verify clean install plus previous accepted combination to target migration, including fresh-session skills, representative inter-tool behavior and reset.
- [ ] Verify prescribed update ordering and busy-work handling without rerunning every producer's internal unit suite as a substitute for integration.
- [ ] Exercise the accepted queue-backed Mulgae skill alongside managed VM ownership: independent resource queues, shared global occupancy, same-lease failed-role recovery, slot return during user waiting, fresh-lease continuation, native compose and no duplicate resource wrapper. Use isolated fixture resources for guest tests and record actual native/installed-skill evidence separately.

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

- [ ] Perform a fresh end-to-end acceptance of project-owned tests, fixed profiles, skills, meaningful migration, ordered producer returns, final host state and Haepari recovery independence. Include managed/external capacity and accepted Mulgae partial-failure continuation, preserving incomplete native reviews as distinct from released leases.
- [ ] Reconcile all remaining durable statements with their canonical owners and collect Master's actual overall acceptance and required hands-on results.
- [ ] Settle this dossier and the retained legacy dossier according to all canonical consumer references and the explicit deletion envelope; replace Detailed SOT links with valid Canonical Outcomes only when appropriate.

Do not:

- [ ] Do not complete the epic from task status alone, manufacture observed results, change unrelated EPIC-018/EPIC-012 work, commit or publish outside the current authority, or delete a dossier still needed by another consumer.

Verify and complete:

- [ ] All producer return criteria, combined installed/migration checks, cleanup and non-regression requirements are met with exact evidence.
- [ ] Documentation/link checks pass and all accepted runtime facts are accurately classified. Any required unresolved evidence keeps the epic incomplete.

## Epic completion criteria

- [ ] Haepari is independently implemented and its exact managed/external native handoff and independent fixture evidence are accepted.
- [ ] Aquarium's own VM pilot is accepted before the first producer request.
- [ ] Every producer in the requested order has an accepted implementation return, including applicable skill and migration evidence.
- [ ] The complete intended installation combination passes its own installed and upgrade/regression checks, including the producer-owned external `use-mulgae` integration and partial-failure continuation contract.
- [ ] Host stable development remains usable, and shared legacy state is retired only after all actual consumers are detached.
- [ ] Required actual manual observations and final overall acceptance exist.
- [ ] Durable documentation is promoted, temporary dossiers are settled under their ownership rules, and no planning item is misreported as implemented.
