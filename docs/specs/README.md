# Specifications

This directory is the maintainer-facing catalog of Aquarium's implemented
behavior and explicitly frozen delivery contracts. Each document states whether
its interfaces are shipped or reserved and links the exact authority; a summary
never overrides its owning skill, reference, Procedure, script, manifest, or
test runner.

## Version Scope

The plugin manifest owns the current package version and the root CHANGELOG owns
release history and the one open candidate when present. Specifications describe
the implemented checkout without duplicating release state. An active roadmap
task may freeze a reserved interface here only when the document labels it
unimplemented and a later task is assigned to ship or revise the same contract.

## Detailed Specifications

- [Capabilities](capabilities.md) inventories Aquarium's public and delegated skills, bundled MCP tools, and CLI entrypoints with their effect boundaries.
- [Workflow contracts](workflow-contracts.md) explains shape, task, epic, validation, setup, and release lifecycles.
- [Tool integrations](tool-integrations.md) records supported versions, platforms, readiness dimensions, and ownership boundaries.
- [Local interfaces](local-interfaces.md) catalogs Procedure IDs, local CLIs, hooks, and JSON schemas.
- [Safety and evidence](safety-and-evidence.md) defines authority, approval, review, and evidence-residency behavior.
- [Development channel](development-channel.md) specifies producer, enrollment, publication, and inherited-environment launcher behavior.
- [Production setup status](production-status.md) links to the shipped authority for the user-global setup ledger, reporter, recorder, retention, and installation contracts.
- [Workflow review routing](review-routing.md) defines the shipped selection, recovery, evidence, and waiver contract for Mulgae, Herdr, Subagent Review, and coordinator-waived review in Task, Epic, and validation workflows.
- [Supervised agent orchestration](agent-orchestration.md) catalogs ordinary v2 roles, reports and recovery and preserves formal v1 mappings, Procedures and bounded qualification; distribution and repository activation remain separate.

## Adaptive Procedures

The [shared adaptive contract](../../plugins/aquarium/references/adaptive-procedures.md)
owns goal-specific selection, bounded source preparation, self-contained
whole/fragment composition, structural qualification, suitability for the exact
candidate and ignored local retention. Task, Goal, Validation, Design and Diagnosis use the
[mapped execution adapter](../../plugins/aquarium/references/adaptive-execution.md)
with exact native-tuple recovery and consented atomic supersede. Existing
ordinary v2 reports, selected reviews and acceptance authority remain applicable.

[Whole/fragment preservation](../../plugins/aquarium/references/procedure-promotion.md)
requires specific content consent and applies after original finalization.
Consent may be obtained at closeout; committing needs a separate matching grant.
[TESTING](../../TESTING.md#adaptive-acceptance-scenarios) owns the durable acceptance scenarios, and the
[VM contract](../../tests/vm/README.md#adaptive-development-verification) owns
installed verification methods. The
[roadmap](../roadmap/README.md#epic-026-adapt-goal-adaptive-procedure-orchestration)
records delivery status and actual acceptance; source implementation alone
does not establish installed behavior.

## Exact Authorities

| Domain | Exact authority |
| --- | --- |
| Workflow triggers, effects, approval boundaries, and failure behavior | [`plugins/aquarium/skills/*/SKILL.md`](../../plugins/aquarium/skills/) and each skill's linked references |
| Shared workflow, review, evidence, documentation, design, and release contracts | [`plugins/aquarium/references/`](../../plugins/aquarium/references/) |
| Installed Procedure source bytes and declarations | [`plugins/aquarium/assets/podway/procedures/`](../../plugins/aquarium/assets/podway/procedures/) |
| Published plugin metadata and version | [`plugins/aquarium/.codex-plugin/plugin.json`](../../plugins/aquarium/.codex-plugin/plugin.json) |
| Executable test behavior and enrolled test meaning | [`Makefile`](../../Makefile) and [`TESTING.md`](../../TESTING.md) |
| Public behavior, privacy, and authority boundaries | [`README.md`](../../README.md), [`PRIVACY.md`](../../PRIVACY.md), and [`TERMS.md`](../../TERMS.md) |
| Release outcomes and next stable version | [`CHANGELOG.md`](../../CHANGELOG.md) |

Add another specification only for a durable cross-cutting contract with no more
exact shipped owner, or for an explicitly reserved contract under the rule
above. Other planned behavior belongs in the roadmap or TODO until it becomes
current.
