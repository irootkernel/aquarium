# Components

Aquarium is a declarative orchestration plugin. Most product behavior is expressed in skill instructions and shared Markdown contracts; small local programs inspect structure, normalize inputs, or enforce narrow gates.

## Package Map

| Component | Location | Responsibility |
| --- | --- | --- |
| Plugin metadata | [`plugin.json`](../../plugins/aquarium/.codex-plugin/plugin.json) | Published identity, stable version, discovery metadata, and plugin interfaces |
| Workflow entrypoints | [`skills/`](../../plugins/aquarium/skills/) | Trigger rules, lifecycle steps, approvals, stop conditions, and handoffs |
| Shared contracts | [`references/`](../../plugins/aquarium/references/) | Cross-skill review, evidence, design, documentation, Podway, Ouroboros, and release rules |
| Procedure assets | [`assets/podway/procedures/`](../../plugins/aquarium/assets/podway/procedures/) | Exact project-owned Procedure v2 sources installed into target repositories |
| Local helpers | Skill-local `scripts/` directories | Read-only inspectors, schema normalizers, publication observers, and the task commit gate |
| Verification | [`tests/`](../../tests/) and [`Makefile`](../../Makefile) | Static invariants, unit behavior, approved legacy integration boundaries, and black-box scenarios |
| Public product surface | Root README, privacy, terms, testing, and changelog files | Installation, user-visible behavior, disclosures, test meaning, and release history |
| Canonical maintainer docs | [`docs/`](../) | Current specifications, architecture, decisions, implementation guidance, and delivery identity |

## Skill Layer

The 23 skill entrypoints form four kinds of component:

- Orchestrators own a complete lifecycle, such as `task-handler`, `epic-handler`, `release-handler`, and the three design entrypoints.
- Leaf skills own bounded task phases such as planning, implementation, verification, review, closeout, and commit preparation.
- Auditors produce read-only findings or readiness decisions, including `epic-validator`, `independent-review`, `orca-review`, and `release-qa`.
- Setup skills inspect and optionally configure tools, documentation, and tests while preserving separate proposal and apply approvals.

Only `task-commit` permits implicit invocation. All other entrypoints require an explicit matching request or an authorized parent-workflow handoff.

## External Tool Boundary

Aquarium defines how an agent may inspect or invoke external tools; it does not absorb their implementation or state. Codex is the primary runtime. Podway owns Procedure execution state, Sanho owns protected Git mutation policy, Mulgae and Gaori own their review and test-run records, Orca owns delegated terminal execution, and upstream projects own their installed binaries and skill sources.

This boundary keeps plugin upgrades independent from tool releases and prevents local runtime files from becoming package state.
