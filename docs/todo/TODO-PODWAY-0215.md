# Podway v0.2.15 adoption

## Goal and ownership

EPIC-034 adopts the published Podway v0.2.15 release, generation-2 commands and observation v6. The [roadmap](../roadmap/README.md#epic-034-adopt-podway-v0215-and-contract-generation-2) alone owns task identity, order and lifecycle. This dossier defines implementation and acceptance for TASK-177 through TASK-180. It does not extend TASK-091's planned producer-side Haepari work.

## Implementation and interfaces

- TASK-177 updates the [tool catalog](../../plugins/aquarium/references/tool-catalog.md#podway), [Podway integration](../../plugins/aquarium/references/podway-integration.md) and their current canonical consumers. Support stable releases >=v0.2.15 without an upper bound. Pin the complete upstream `use-podway` tree to release commit `9a3f94c8752298f689832d05aa827a0f6496c1af`; never vendor or replace the host skill during development.
- TASK-178 passes `--contract-generation 2` on current native commands and requires observation v6. Output v4, Error v2, version-result v2, contract-manifest v2 and status v5 remain unchanged. Preserve fences, keys, supported semantic arguments, typed recording and native error details. Local commands reject workspace request options. Do not fall back to generation 1.
- TASK-179 updates the exact official-artifact gate and preserves its complete five-Procedure scenario inventory. Add executable lifecycle templates, fenced start rejection/replay, citation details and v0.2.14 writer refusal/reset. The [testing contract](../../TESTING.md) owns commands and evidence meaning.
- TASK-180 separates the unchanged v0.2.14 baseline from the v0.2.15 candidate in sealed VM inputs and observations. Verify installed setup, fresh skill discovery, actual Task/Epic startup and initial Executor/Evaluator progression. Baseline and original-writer recovery use that release's own grammar. No historical qualification is relabelled as new evidence.

## Breaking upgrade and authority

Finish or explicitly abandon sessions with their original writer before replacing it. v0.2.15 declares no compatible v0.2.14 writer predecessor. Refusal preserves state; an explicitly authorized unfenced reset-all discards runtime history without conversion or backup and preserves reviewable configuration, Procedures and unrelated files. Runtime reset, installation, managed-file updates, commits and publication remain distinct effects.

Keep the installed host combination and this repository's managed `.podway` files unchanged. Installation-dependent checks require release-handler authority or Master's explicit VM-test authority and run only in the dedicated UTM VM. Master controls VM power. One Haepari Job owns occupancy through baseline, upgrade, manual observations and verified cleanup. Retain the original baseline and restore the declared consumer inventory before completion.

## Acceptance

- Focused behavior tests and the complete applicable local gate pass; prose matching and automated LLM evaluations do not establish skill correctness.
- Verify the official Apple Silicon archive checksum, source commit, manifest and executable identities. Bind the complete compatibility result to the exact clean committed Aquarium candidate. Dirty-tree scenario runs are development evidence only.
- Complete three fresh independent static reviewer reports through the explicitly selected Subagent Review route; settle material findings against current bytes.
- Complete the exact installed-candidate VM verification, including writer mismatch, no-effect refusal, explicitly scoped reset, source preservation, setup, discovery and handler progression. Keep Master's actual functional outcome separate from automatic checks.
- Add the shipped outcome to Aquarium v0.1.22 without changing completed release entries or publication metadata. Preserve unrelated `uv.lock`.

## Closeout

Keep acceptance open until exact-candidate, VM and functional evidence is complete. Promote accepted behavior and operations into canonical owners before review. Only after actual overall acceptance replace this dossier's roadmap link with Canonical Outcomes and remove the dossier and TODO entry under the approved deletion boundary.
