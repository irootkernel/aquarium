# Changing Procedures

Procedure assets are installed source artifacts, not examples. A graph change can alter active lifecycle behavior, recovery compatibility, and the evidence expected by owning skills.

## Ownership

The canonical files are under [`plugins/aquarium/assets/podway/procedures/`](../../plugins/aquarium/assets/podway/procedures/). Each Procedure declares its stable ID and integer version. The owning skill and shared Podway contract define how that graph is selected, installed, activated, observed, and advanced.

Do not edit an installed copy in a target repository as the source change. Update the plugin asset and then prove installation or compatibility separately where the workflow requires it.

This repository is also a target. Its `.podway/procedures/` copies follow the Aquarium release installed on the host, so do not copy changed assets into them. After the new release is installed, update the copies through an authorized `$aquarium:dev-setup` managed update. `tests/validate.rb` accepts only copies that match a released package source.

## Change Checklist

1. Map the changed node, transition, result, or guard to the owning skill behavior.
2. Increase the Procedure version when the installed graph contract changes. Keep the stable Procedure ID unless a genuinely separate lifecycle is being introduced.
3. Update every skill, reference, fixture, validator assertion, and public claim that depends on the prior graph or version.
4. Check recovery paths for sessions created by the previously supported Podway release. Never translate unknown interrupted work into an automatic replay.
5. Verify the serialized asset bytes and relevant Podway compatibility scenarios.

Repository setup reports each installed managed file's `source_state` separately
from `handler_contract_status` and `handler_contract_reasons`. Native validation
establishes that Podway accepts a same-ID customization; it does not establish
that current Aquarium handlers can supply and consume its required nodes,
evidence items, and routes. An incompatible customization remains untouched and
keeps setup degraded until its owner approves an exact update.

Use the [Herdr migration runbook](../ops/herdr-migration.md) for Orca-era sources
and snapshots. Updating source files affects successors only; preserve old
evidence and custom bytes, reject retired dispatch, and establish a legacy
worker's safe state before an authorized transition. Current source identity,
native validity, handler compatibility and route membership remain separate.

Podway v0.2.14 permits at most 1,024 definitions and 1,024 graph placements, eight `evidence_from` references per placement, and 16 items per reference. Split a large selection into multiple references for the same source node while staying within both reference limits; otherwise keep a single reference.

The Task Procedure's `confirm-goal-assessment-core` and `confirm-stopped-goal-assessment-core` placements consume the implementation evidence before `assess-goal` or `assess-stopped-goal`. The assessment placements consume the carried completion assessment and applicable user direction. Check each placement's current references before changing its evidence budget.

## Adaptive Procedure maintenance

The [adaptive contract](../../plugins/aquarium/references/adaptive-procedures.md)
and [mapped execution contract](../../plugins/aquarium/references/adaptive-execution.md)
own selected-source admission and execution. Preserve canonical/custom/formal
sources and admitted snapshots under their original supported contracts. Managed
host assets still require their authorized update.

Derive success from native session-goal outcomes and verify due assessment,
review, acceptance and effect-order relationships. Capability signatures recognize
equivalent structures without authenticating agents or requiring canonical
layouts. Keep Aquarium binding/fragment metadata outside native schemas and
validate complete flattened instances with Podway.

Resolve adopted definitions by native ID/version/digest across approved roots.
Keep bundles atomic, local, ignored and self-contained so recovery does not need
mutable origin libraries. Preserve adopted customization obligations while
keeping optional templates distinct. Task phase applicability follows actual work
and repository requirements.

Unexpected active-topology replacement needs actual consent before native atomic
preserve-start with current fences and same-key outcome recovery. Normal rework
and approved terminal successors retain their existing authority. Never emulate
the atomic transition with cancel-then-start, reset or deletion.

Pin canonical sources in fixed VM regressions. Adaptive checks use the admitted
mapping, actual work and fixture oracle. Commit driver/fixture changes before
installed use; permitted local helper checks remain separate from clean-candidate
gates. Candidate installation stays guest-only. Follow the
[acceptance scenarios](../../TESTING.md#adaptive-acceptance-scenarios) and
[VM continuation methods](../../tests/vm/README.md#adaptive-development-verification)
through representative delivery, rework, recovery and closeout.

Offer useful whole/fragment preservation at closeout after successful use. Apply
only the specifically accepted library diff after original finalization. Content
consent and its separate promotion commit grant may be requested together; broad
or consumed original-work grants do not cover promotion. Revalidate transformed
definitions and state their runtime limits. Preservation adds no mandatory Judge
round.

## Compatibility Evidence

A local development Podway binary can establish development-contract evidence. It cannot satisfy a release requirement that names an official archive and checksum. When the release policy requires Podway v0.2.14 compatibility, the required invocation is `PODWAY_BIN=<absolute-path-to-extracted-v0.2.14-podway> gaori run test-podway-compat` against the exact Aquarium candidate. The agent performing the check must load `$use-gaori` and follow its transport and waiting policy. Use MCP only when it demonstrably preserves the exact environment input; an agent-shell assignment does not update an already running MCP server. When CLI is required, start it once and await the same process handle. Use the authoritative `make test-podway-compat` target directly only when Gaori is unavailable. Do not start or restart an MCP server or change host configuration to make MCP eligible.

### Maintaining the compatibility matrix

- Register each native scenario exactly once in the centralized wait or terminal inventory. The inventory unit test owns the exact scenario and runtime-root counts.
- Share a runtime only between scenarios that reach terminal disposition. A scenario that returns with an active or otherwise nonterminal session must keep its own runtime root.
- Before each scenario in a reused runtime, restore the canonical Procedure bytes, reset scenario-local state, and renew the scenario deadline. Preserve runtime-level command sequencing and accumulated correction-case evidence.
- Keep the four-runtime concurrency limit unless an official-artifact run proves a different bound and verifies cleanup on both success and failure. Keep the configured Gaori timeout above the observed worst-case duration.
- When receipt fields or their meaning change, increase the receipt schema and update `TESTING.md`, the local-interface catalog, and focused unit assertions in the same change.

Procedure validators prove declaration and graph invariants only. Native scenario
tests cover executable routing and rejection behavior. Agent-observed scenarios
separately cover semantic choices such as review admission, Low settlement,
context recovery, approval boundaries, and owner handoffs. Report these evidence
classes separately and list any unrun observed-agent scenarios.
