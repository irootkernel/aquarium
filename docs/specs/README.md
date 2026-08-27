# Specifications

This directory is the maintainer-facing catalog of Aquarium's implemented behavior. Each document summarizes current contracts and links the exact shipped authority; a summary never overrides its owning skill, reference, Procedure, script, manifest, or test runner.

## Version Scope

The plugin manifest owns the current package version and the root CHANGELOG owns release history and the one open candidate when present. Specifications describe the implemented checkout without duplicating release state.

## Detailed Specifications

- [Capabilities](capabilities.md) inventories every public and delegated Aquarium skill and its effect boundary.
- [Workflow contracts](workflow-contracts.md) explains shape, task, epic, validation, setup, and release lifecycles.
- [Tool integrations](tool-integrations.md) records supported versions, platforms, readiness dimensions, and ownership boundaries.
- [Local interfaces](local-interfaces.md) catalogs Procedure IDs, local CLIs, hooks, and JSON schemas.
- [Safety and evidence](safety-and-evidence.md) defines authority, approval, review, and evidence-residency behavior.

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

Add another specification only for a durable cross-cutting contract with no more exact shipped owner. Planned behavior belongs in the roadmap or TODO until it becomes current.
