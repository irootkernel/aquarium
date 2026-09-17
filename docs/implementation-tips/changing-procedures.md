# Changing Procedures

Procedure assets are installed source artifacts, not examples. A graph change can alter active lifecycle behavior, recovery compatibility, and the evidence expected by owning skills.

## Ownership

The canonical files are under [`plugins/aquarium/assets/podway/procedures/`](../../plugins/aquarium/assets/podway/procedures/). Each Procedure declares its stable ID and integer version. The owning skill and shared Podway contract define how that graph is selected, installed, activated, observed, and advanced.

Do not edit an installed copy in a target repository as the source change. Update the plugin asset and then prove installation or compatibility separately where the workflow requires it.

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

Podway v0.2.10 permits at most eight `evidence_from` references per placement and 16 items per reference. Split a large selection into multiple references for the same source node while staying within both limits; otherwise keep a single reference.

The Task Procedure's `assess-goal` placement intentionally consumes the final normalized implementation evidence from `implement` instead of repeating the `prepare-implementation` re-entry summary. That leaves the eighth reference available for user-direction evidence while preserving the implementation result that the assessment actually needs.

## Compatibility Evidence

A local development Podway binary can establish development-contract evidence. It cannot satisfy a release requirement that names an official archive and checksum. When the release policy requires Podway v0.2.10 compatibility, run `PODWAY_BIN=<absolute-path-to-extracted-v0.2.10-podway> make test-podway-compat` against the exact Aquarium candidate.

Procedure validators prove declaration and graph invariants only. Native scenario
tests cover executable routing and rejection behavior. Agent-observed scenarios
separately cover semantic choices such as review admission, Low settlement,
context recovery, approval boundaries, and owner handoffs. Report these evidence
classes separately and list any unrun observed-agent scenarios.
