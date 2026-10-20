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

The skill entrypoints form four kinds of component:

- Coordinators own a complete lifecycle, such as `task-handler`, `epic-handler`, `release-handler`, and the three design entrypoints.
- Leaf skills own bounded task phases such as planning, implementation, verification, review, closeout, and commit preparation.
- Auditors produce read-only findings or readiness decisions, including `epic-validator`, `mulgae-review`, `herdr-review`, and `release-qa`. `subagent-review` uses three fresh base reviewers in the Coordinator harness plus a UI/UX specialist when applicable for a selected exact target and owns no Dolgorae, Mulgae, or Herdr runtime.
- Setup skills inspect and optionally configure tools, documentation, and tests while preserving separate proposal and apply approvals.

`task-commit` permits implicit workflow invocation. `herdr-review` may also be selected from an explicit natural-language request that names both the review target and reviewer. `dev-setup` may be selected from an explicit natural-language repository setup request, including Sorage Project registration or binding, and stays within the requested component scope. All other entrypoints require their skill name or an authorized parent-workflow handoff.

## Directory documentation flow

Canonical specifications and architecture remain the source of durable meaning.
The shared [directory guidance contract](../../plugins/aquarium/references/directory-agent-guidance.md)
connects those owners to applicable local instructions. The root documentation
index records adoption scope; local guides carry relative source links and
necessary local rules. Native instruction loading remains the harness's
responsibility.

The root guidance source in `dev-setup` owns discovery rules. `docs-setup` maps
current implementation responsibilities to canonical documents, reconciles local
instructions and applies approved coverage or migration. Task/Epic planning reads
that mapping and its original sources; documentation phases maintain it with the
behavior candidate. This uses existing documentation owners and workflow phases,
without a feature graph or another project-state store.

The documentation inspector and local-reference helper provide bounded structural
checks. Semantic ownership, accurate coverage and preservation through installed
workflows require separate assessment. Ordinary source reads and a passing link
check provide no native-loading telemetry.

## External Tool Boundary

Aquarium defines how an agent may inspect or invoke external tools; it does not absorb their implementation or state. Codex is the primary runtime. Podway owns Procedure execution state, Sanho owns protected Git mutation policy, Mulgae and Gaori own their review and test-run records, Sorage owns Project identity, document Handoffs, and Project Memos, Herdr owns its native pane and agent control, and upstream projects own their installed binaries and skill sources.

This boundary keeps plugin upgrades independent from tool releases and prevents local runtime files from becoming package state.

Standalone Herdr Review delegates pane and agent control to the installed
upstream Herdr skill. Aquarium binds the Git target and Review Brief, checks
the complete report and keeps native operation evidence separate from its
technical verdict and workflow acceptance. The entrypoint and its
[supervision contract](../../plugins/aquarium/references/herdr-supervision.md)
are declarative; they add no runner, copied checkout or synthetic lifecycle store.
