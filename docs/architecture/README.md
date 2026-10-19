# Architecture

Aquarium is distributed as one Codex plugin whose declarative workflows coordinate independently installed tools while preserving repository-local authority and explicit mutation boundaries. These documents describe the current implementation; they do not override the linked executable sources.

## Detailed Architecture

- [Components](components.md) maps the plugin package, workflow layer, local helpers, tools, and public surfaces.
- [Workflow runtime](workflow-runtime.md) follows invocation through discovery, approval, execution, and handoff.
- [State and evidence](state-and-evidence.md) separates roadmap, Procedure, Git, host, and durable evidence planes.
- [Verification](verification.md) explains the layered test architecture and the limits of each proof.
- [Development channel](development-channel.md) traces exact-main production, immutable publication, atomic executable selection, and inherited-environment launch.

## Core Boundaries

- Aquarium coordinates Codex, Dolgorae, Herdr, Podway, Sanho, Mulgae, Gaori, Sorage, Ouroboros, Lora, Deslop, Humanizer, and im-not-ai but does not vendor or own their upstream implementations. Herdr owns native reviewer execution; the [migration contract](../../plugins/aquarium/references/herdr-migration.md) preserves legacy sources, customizations and review evidence without retired dispatch.
- Skills preserve separate authority for diagnosis, network lookup, installation, provider transmission, repository mutation, commits, and publication.
- Podway and native tools own runtime and execution evidence. Sorage owns its Vault, Project identity, Handoffs, Project Memos, and derived inbox marker. Ignored runtime artifacts are not roadmap history, architecture, or durable specifications.
- `aquarium-status` alone owns the private production setup ledger and its installed reporting runtime. Setup skills submit closed terminal-attempt documents; they do not write YAML. Ledger history remains separate from repository authority, live tool health, and `aquarium-dev` enrollment.
- Canonical documentation describes current structure and delivery intent; it does not replace executable source, Git history, external release proof, or runtime activation evidence.

## Adaptive definitions and execution

[EPIC-026: ADAPT](../roadmap/README.md#epic-026-adapt-goal-adaptive-procedure-orchestration)
selects suitable existing Procedures or prepares complete Procedure v2 definitions
before native admission. The
[adaptive contract](../../plugins/aquarium/references/adaptive-procedures.md)
separates definition bindings from existing native execution and progress. It
preserves current role, review and delivery contracts. The definition parser and
declaration-signature helper implement its binding and capability checks without
adding a Podway engine, scheduler or central state.
Selected admission accepts exact known sources, retains complete ignored
bundles atomically and resolves them by native tuple across the worktree.
Retained definitions are self-contained; recovery needs neither mutable origin
libraries nor a central session database. Ordinary-assignment selection and
source-only preparation retain exact ignored candidates separately from adopted
bundles. Composition flattens exact whole/fragment imports and explicit
control/evidence/rework ports before those same fit, storage and native checks.
Namespace expansion preserves native semantic operation identities and declared
formal contracts. Guarded source qualification and exact ordinary pre-start
suitability/bootstrap use the same retained definition boundary. Task, Goal, Validation, Design and Diagnosis consume those definitions through the shared mapped execution adapter. Unexpected topology replacement uses one explicitly consented native preserve-start operation with archived lineage and same-key recovery; it adds no executor or central state.
A running approved-source view preserves original criteria for normal mapped
dispatch. Settled finalization additionally requires current affected Evaluator and
native evidence and returns no dispatch.
Grouped post-use preservation offers and specifically consented post-finalization
library publication use the existing source and authority boundaries. Cross-family
recovery checks and guest tooling cover all seven entrypoints. The
[testing contract](../../TESTING.md#adaptive-acceptance-scenarios) separates their
source and installed evidence. Existing sessions retain their admitted contracts;
managed sources change only through an authorized update.

## Exact Authorities

The package layout and release version come from the [plugin manifest](../../plugins/aquarium/.codex-plugin/plugin.json). Workflow behavior comes from [skill entrypoints](../../plugins/aquarium/skills/) and their linked references. Installed Procedure bytes come from [Procedure assets](../../plugins/aquarium/assets/podway/procedures/). The [Makefile](../../Makefile), [TESTING.md](../../TESTING.md), and tests own executable verification.
