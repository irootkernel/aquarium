# Haepari adoption across integrated tools

## Authority and implementation state

The sole consumer is `EPIC-032`, with existing `TASK-091` through `TASK-099`. The [canonical roadmap](../roadmap/README.md) owns identity, ordering, dependencies and lifecycle; this dossier owns detailed rollout scope and acceptance. EPIC-019 and EPIC-031 must be completed before this Epic starts. Task IDs remain unchanged and each Task has one owning Epic.

This is planning only. Producer implementations, installed verification, broker operations, host changes, commits and publication require their applicable execution authority. No implementation or runtime result is claimed.

## Goal, inputs and boundaries

Apply the accepted Aquarium/Haepari contract to the producers through Sorage in this order:

`Podway -> Mulgae -> Gaori -> Sorage -> Sanho -> Dolgorae -> Gul -> Seongge -> Gaebokchi`.

Accept each real implementation return before dispatching the next. Aquarium owns coordination and its integration changes; each producer owns its source, roadmap IDs, installation unit, skills, migrations and native legacy detachment. A request acknowledgement is not completion. Keep the stable host Sorage broker as the rollout control plane, including while testing a Sorage candidate in the guest.

Read EPIC-019 and EPIC-031 Canonical Outcomes and the current [tool specifications](../specs/tool-integrations.md), [tool catalog](../../plugins/aquarium/references/tool-catalog.md#haepari), [Haepari integration](../../plugins/aquarium/references/haepari-integration.md), [workflow contracts](../specs/workflow-contracts.md), [Haepari VM operations](../ops/haepari-vm-verification.md), [TESTING.md](../../TESTING.md), and [tests/vm/README.md](../../tests/vm/README.md). EPIC-019 must already have promoted the shared setup, VM adapter, sealed-input/profile, complete skill/configuration, migration, manual-completion, pre-submission versus returned Job/result handoff, and cleanup contracts. EPIC-031 must already have promoted release roles and assessment/result handoffs. Missing required durable inputs block the affected work; do not recover them from deleted dossiers or raw review logs.

Carry exact accepted component and profile identities into each packet. Preserve immutable admitted bytes and original Job reconnect, complete skill-tree/fresh-session checks, meaningful prior-version state, actual manual observations, cleanup inventories and qualified backend limits. Haepari records opaque consumer profiles and cleans only owned Job files; recipes still own installation and fixture cleanup. Automatic workloads finish recipe cleanup before exit; manual operators stage evidence and finish cleanup/inventory while awaiting_manual, before manual complete starts native collection. Native Job, review, evidence, cleanup, capacity and assessment outcomes remain separate.

Keep candidate installation in the dedicated UTM VM, use isolated guest controllers and stub providers for fault tests, and preserve live/provider authority. No host account files, production data, recursive parent-VM acquisition, outer review-lock wrapper or automatic release/activation is introduced. Adoption is breaking and needs exact installed verification before any applicable release.

Detach only producer-owned legacy hooks/services whose identity and exclusive channel use are proved. Preserve foreign hooks, stable binaries/skills and common infrastructure still needed by consumers. EPIC-033 alone owns final shared-channel removal; this Epic's completion does not wait for that removal or the final combined environment pass.

## Native Mulgae advisory-lock contract

TASK-092 asks Mulgae to acquire `mulgae-review` exactly once in the native path shared by CLI and foreground/asynchronous MCP reviews. Save the acquisition key and payload before acquisition. Queue waiting belongs inside the existing review invocation and precedes live provider qualification, role work and extraction requests. Local preflight and receipt-bound inspection need no grant. Renew within the review process and choose the registered maximum hold to cover its admitted execution/cleanup budget. Release after protected work ends on success, failure or cancellation, before waiting for a user decision.

Keep one acquisition across observation timeouts and replays. Cancel an abandoned queued request through its native request ID; native cancellation also handles a raced grant. A valid inherited `HAEPARI_LOCK_GRANT` is borrowed only after read-only installation/lock/grant/generation/state/deadline validation. The borrower never renews, cancels or releases the owner's grant and never silently reacquires an invalid reference. Aquarium and `use-mulgae` add no outer lock wrapper.

An unavailable controller or invalid grant fails the coordinated execution path without silent direct execution. On renewal loss, Mulgae stops new provider dispatch, requests native cancellation/drain and reports the actual outcome. Native run IDs and uncertain-start recovery remain Mulgae responsibilities; replaying a lock request grants no permission to repeat a review. A new authorized current-source review gets a new FIFO acquisition without inherited queue position or lease-continuation semantics.

Advisory grants expire after lost renewal or maximum hold. Expiry does not terminate native work, so overlap remains possible if work outlives its grant. Serialization reduces competing reviews; it cannot eliminate provider rate limits or police uncoordinated callers. Keep native coverage, publication, findings/CI and grant disposition separate. Preserve partial-role reports as historical evidence without rerun, compose, provider substitution or mixed-run coverage authority.

Mulgae owns its implementation, native configuration and release-matched `use-mulgae` changes. Aquarium accepts the actual released integration and then updates its supported Mulgae floor and affected contracts. Haepari fixtures alone do not prove Mulgae integration. Guest integration tests use an isolated test controller/resource and stub providers; never acquire the occupied parent VM or use isolated locks to justify concurrent live calls on a shared production account. Real provider checks retain their selected scope and authority.

## Sorage request and completion protocol

Use the installed native `use-sorage` skill and observed output when this epic's execution envelope explicitly authorizes a broker operation. This plan alone does not authorize a send or discovery. Resolve the actual recipient identity rather than guessing a Project slug from a product name.

A request carries a stable logical correlation key, the immutable request-document digest, exact Haepari and pilot/profile contracts, the producer-specific scope, expected return fields, and the permitted effect boundaries. Allocate the native Handoff once and preserve its real receipt/revision. If a send result is uncertain, reconcile native state before another send; do not manufacture application-level message IDs or edit broker storage.

The producer allocates its own local task/epic IDs and may accept the request or ask for changes through the native review loop. Acceptance of the request means the request was accepted, not that implementation is complete. Aquarium's coordination task remains open while producer implementation or required evidence is pending.

The producer sends a separate completion-report Handoff back to Aquarium after implementation and verification. It references the original logical request, native request/revision, and accepted scope. The producer does not edit Aquarium's sender-owned request or the managed Vault. Aquarium reads the current returned document, checks evidence, requests bounded corrections through native review/revision when needed, and explicitly accepts the completed response only when its criteria are met.

Do not send the next project until this return is accepted. Blocked or unobserved producer work pauses the sequence; a receipt, acknowledgement, commit list, or prose claim is insufficient. No recurring inbox watcher, unrelated inbox scan, or automatic resend is part of the implementation. An authorized waiting operation uses native supported waiting semantics.

### Required producer return

The report must contain the resolved producer/repository and producer-owned work IDs; exact source/candidate/test identities; installation-unit and skill-tree provenance; Haepari executable/runner/capability identity; starting/target profile digests; per-suite Job references and actual observations; old-state migration and regression evidence; manual gaps; cleanup and restored inventory; product-specific legacy source changes; separately evidenced host detachment; released/unreleased status; and remaining limitations.

The Mulgae return additionally identifies the released CLI/skill, shared CLI/MCP acquisition path, lock installation/request/grant/generation references and original native run/publication results. Include renewal, queued cancellation and raced grants, borrower validation, terminal release, renewal-loss handling and observed advisory limits. A new review requires native execution authority even when a lock was acquired. Preserve partial-role evidence and original invocation recovery without mixed-run coverage. VM-only success cannot complete TASK-092; other producers gain no review-lock implementation obligation from this section.

A missing prior release or native skill uses evidence-backed `not_applicable`. Do not invent a `use-gul`, `use-seongge`, or `use-gaebokchi` merely to satisfy a template. A candidate using an API beyond the frozen Haepari contract is a dependency change that must be resolved before acceptance.

## Task acceptance checklists

### Common acceptance for TASK-091 through TASK-099

Each task is Aquarium-owned coordination work with a separately owned producer implementation. Its normal final commit records only accepted Aquarium-owned integration/documentation changes. Intermediate transport state stays in Sorage and permitted local evidence; do not manufacture a repository commit for every poll or message.

- [ ] Read the current prerequisite acceptance and resolve the next exact recipient.
- [ ] Send one authorized, versioned request with the common contract and product-specific criteria. Reconcile an uncertain send before retrying.
- [ ] Obtain the producer's own work-ID mapping and a correlated completed implementation report, not merely a request acknowledgement.
- [ ] Verify exact candidate/test/profile/binary/skill identities, installation, real old-state migration where applicable, regression, manual observations, failure recovery, owned cleanup and reusable guest state.
- [ ] Review actual obsolete source removal and separately evidenced native hook/service detachment or proven absence. Preserve shared infrastructure until TASK-101.
- [ ] Return corrections through Sorage when acceptance is incomplete; do not edit producer source from Aquarium.
- [ ] Accept the final returned Handoff using current native revision/row fences, promote only permitted bounded evidence, and only then allow the next task.

### TASK-091: Freeze producer packets and accept Podway

- [ ] Read completed EPIC-019 and EPIC-031 Canonical Outcomes and their current durable owners. Freeze the producer request/completion packets against the accepted adapter, profiles and release-role contracts before the first send. Include Mulgae managed-VM and native advisory-lock scope, original-invocation recovery, partial-role terminal handling and live-source consistency limits.
- [ ] Apply the common acceptance protocol to Podway.
- [ ] Require matching CLI and any shipped runtime identity under Podway's current native contract, the independently declared full `use-podway` tree, workspace/configuration/history preservation, Procedure compatibility, restart/recovery and the native busy-work update policy.
- [ ] Detach only legacy producer/controller/development-service interfaces proved exclusive to aquarium-dev. Preserve supported native runtime modes and generic features still used independently.
- [ ] Verify migration does not drop workspace identity, historical records, logical retry state or active-work obligations. Accept only actual product evidence and restored VM state.

### TASK-092: Delegate and accept Mulgae

- [ ] Apply the common acceptance protocol to Mulgae after Podway acceptance. Send the revised two-part request through Sorage; the producer allocates its own implementation tasks and changes its own source/skill.
- [ ] Require installed review execution/result retrieval, native provider/role configuration, existing review/configuration migration and complete `use-mulgae` verification across the actual CLI/MCP transport.
- [ ] Require a published producer release and complete paired skill implementing one `mulgae-review` acquisition in the CLI/MCP common path before live qualification, role execution and extraction. Wait inside the original invocation, renew in process and release on every terminal path after protected work ends.
- [ ] Verify CLI versus asynchronous/foreground MCP contention across project roots using one installation and capacity-one lock. Native roles within the admitted review remain parallel; review-level serialization makes no universal rate-limit guarantee.
- [ ] Verify persisted key/payload replay, queue observation timeout, abandoned-request cancellation and the grant/cancel race without duplicate review dispatch. Preserve the original native invocation/run on uncertain execution.
- [ ] Verify owner/borrower identity and deadline checks; a borrower neither reacquires nor mutates its parent's grant. Reject stale/mismatched references without silently bypassing Haepari or releasing a successor's grant.
- [ ] Verify renewal failure, maximum hold, caller loss and controller restart. Stop new provider dispatch and drain/cancel native work when the grant is lost; report that advisory expiry can still overlap continuing work. Do not describe a lock as managed unknown-execution containment.
- [ ] Verify a partial-role failure preserves historical accepted reports and releases after native termination, before asking the user. An unrelated queued review can proceed while the original result remains incomplete. A new full current-source review needs explicit execution authority and a new acquisition; no rerun/compose or linked external continuation is introduced.
- [ ] Use synthetic targets, an isolated test controller/resource and stub providers for guest fault tests without acquiring the parent's occupied VM. Actual installed CLI/MCP integration and any selected live checks retain their own evidence and authority; fixtures alone do not complete this task.
- [ ] Verify release-matched `use-mulgae` discovery, native configuration migration, consumer cleanup and the advisory limits of direct unqueued calls. Read-only inspect/preflight remains provider-free and requires no grant.
- [ ] After accepting the actual released producer return, update Aquarium's supported Mulgae floor and affected contracts. Do not edit producer source from this task or add an outer lock wrapper to Aquarium or `use-mulgae`.
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
- [ ] Verify Haepari remains able to observe its Job, collect evidence and perform owned cleanup when the Dolgorae candidate cannot supervise work.
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

After the final accepted producer return, prepare an inventory of accepted implementation, source/binary/skill/profile identities, per-product verification limits and separately observed legacy detachment or absence. Promote it with the producer contracts before EPIC-032 closeout. EPIC-033 performs whole-combination verification; individual producer passes do not establish that result.

## Epic acceptance, handoff and dossier deletion

- [ ] All nine producer requests have correlated accepted implementation returns in the required order, including complete applicable skills, meaningful migration/regression, required manual observations, recovery, consumer cleanup and native detachment or evidenced absence.
- [ ] TASK-092 includes the actual released Mulgae CLI/skill and native CLI/MCP lock integration. Queue/replay/renewal/cancel-race/borrower/terminal-loss cases and advisory limits are observed; Haepari fixtures alone are insufficient.
- [ ] Independently validate the entire rollout obligation and its returned evidence. Missing producer criteria keep this Epic incomplete; whole-combination and common-removal work belong to EPIC-033.
- [ ] Promote accepted per-product contracts, supported floors, component/profile inventories, detachment facts and verification limits into tool specifications/catalog, architecture, testing and operations. Promote the Sorage producer request/completion/correction/acceptance protocol to a durable operations owner indexed by `docs/ops/README.md`, including identity fences, uncertain-send reconciliation, producer ownership, returned artifact/release identity and correction revalidation. EPIC-033 must be able to use it after this dossier is deleted. Promote bounded non-sensitive evidence only where the evidence-residency contract requires it; raw broker/provider/runtime reports remain local.
- [ ] Give EPIC-033 stable canonical inputs for every accepted producer and any preserved shared legacy dependency. No incomplete producer implementation is handed to EPIC-033 as deferred work.
- [ ] Obtain Master's actual overall acceptance, replace EPIC-032's Detailed SOT with valid Canonical Outcomes, replace temporary navigation pointers, remove this TODO entry and delete this dossier under its closeout envelope. EPIC-033 consumes durable outcomes and does not retain this dossier.
