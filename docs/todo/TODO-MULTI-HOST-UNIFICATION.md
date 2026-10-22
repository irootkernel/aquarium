# Multi-host unification dossier

## Authority and implementation state

The sole consumer is `EPIC-030`. The [roadmap](../roadmap/README.md#epic-030-unify-aquarium-delivery-across-five-agent-hosts)
alone owns Epic and Task identity, order, dependencies and lifecycle status.
This temporary execution SOT owns detailed scope, approach and acceptance under
the [Epic Execution SOT contract](../../plugins/aquarium/references/epic-execution-sot.md).
Checklists below specify required evidence; they do not record completed work.

The current authorization registers this plan in documentation. It does not
implement the Epic, install candidates, change managed files, commit, publish or
archive repositories. Herdr planning discussions with Claude Opus and AGY Argon
informed this scope. Their design agreement does not replace Master's acceptance,
native capability evidence or installed functional verification.

## Goal and acceptance

Maintain and distribute Aquarium from one repository for Codex, Claude Code,
Grok, ZCode/GLM and AGY. Maintainers should change a shared workflow once and
adjust host-specific implementations only where native behavior differs. Users
receive self-contained packages with explicit host selection and documented
migration from existing editions.

Epic acceptance requires shared workflow contracts, reproducible packages for all
five hosts, preserved Codex behavior, actual five-host qualification, an authorized
distribution cutover and accepted durable documentation. Separate edition source
and distribution repositories must no longer require independent maintenance at
completion. Temporary generated mirrors or redirects may support the transition;
final retention preserves history and tags through authorized archival or read-only
status. Missing upstream capabilities or installation feasibility block acceptance
unless Master explicitly changes the accepted scope.

## Planning baseline

These source observations identify the planning inputs, not supported minimum
versions or installed qualification. TASK-162 must refresh them before execution.

| Source | Observed identity | Use |
| --- | --- | --- |
| `aquarium` | `f2993a11b78e20920db11738be0ceb7e4a3d9920` | Current planning checkout; v0.1.21 release source is `822061685552d8846f28ef31ec607027118b472c`. |
| `aquarium-for-claude` | `031e88cd439549059e8b1b092c85d60593b7c21d` | Edition generated from the v0.1.21 source; inspect its generator, overrides and additions. |
| `aquarium-for-grok` | `f7a78d20ce6907d5058679b6fe18cfec2fc68923` | Older edition generated from `e026d903f0e93fda4fba9b3eb27b2b920b7c5572` (v0.1.17). |
| `aquarium-for-glm` | `9af63ecb37de53312d669170bcb80612468a9ee3` | Older edition generated from the same v0.1.17 source; distinguish upstream drift from host requirements. |
| AGY | Local native documentation and CLI v1.4.5 | New host integration; no existing Aquarium package qualification. |

Classify edition differences as common corrections, native host behavior or
obsolete migration machinery. Re-derive common fixes against current owners.
Candidates include retired-invocation reference checks and Git inspection that
avoids executing repository filters while still reporting submodule changes.
The existing orphan skill check already covers part of reference validation.
Neither an old override nor an earlier missing-feature claim proves a current
host limitation.

## Design boundaries

Shared sources own workflow intent, roles, authority, evidence, reusable phase
instructions and portable helpers. Host implementations own native invocation,
question and goal APIs, agent creation and lifecycle, model settings, configuration,
MCP and skill roots, hooks and package layout. Installation differences alone do
not justify copying the whole workflow.

Define entrypoint invocation, implicit selection and authorized delegation without
making Codex sidecars the semantic owner for other hosts. A user-facing skill may
be gated while its reusable role instructions remain available through an
authorized subordinate transition. Preserve native denials; do not route around
them by reading a gated skill path or inventing universal delegation notes.
Preserve public skill and phase names, standalone resume, and the original grant
through every transition.

Generate deterministic packages from explicit shared and host-owned sources.
Each output must install without a generator, submodule or sibling checkout.
Do not rewrite human prose or Python function bodies with literal substitution.
Allocate package roots, marketplace entries, plugin identities and collision rules
for all hosts before their separate integration Tasks. Co-installed host roots
must not trigger false duplicate-install errors.

Keep `plugins/aquarium/.codex-plugin/plugin.json` as the version owner until an
explicitly reviewed migration changes it. All host manifests and generated
outputs must agree with that owner. Extend full and light release version checks,
`RELEASE_TAG` validation and metadata-only allowlists to every shipped output.

Preserve byte-pinned Procedure YAML, adaptive digests, admitted sessions and
retained formal v1 records. Keep ordinary host mappings in ordinary orchestration
and host references; `native-agent-mappings.md` remains a formal v1 authority.
Any necessary managed-source change requires its authorized update and compatible
successor path. Candidate development must not edit installed managed copies.

Keep the present ownership and behavior of `aquarium-dev` and `status`; this Epic
does not automatically expand either to five hosts. EPIC-033 retirement and
EPIC-027/EPIC-028 collaboration retain their separate scope. ZCode's native roles
follow verified capabilities; the global Herdr ZCode Executor-only rule applies
when that integration is used, not as a product-wide ZCode restriction.

If this Epic's installed checks use Aquarium's shared VM after the accepted
Haepari cutover, follow the current canonical managed-occupancy contract at the
outer host boundary. Guest entrypoints stay within that Job. This does not make
EPIC-019 a whole-Epic prerequisite or transfer VM scheduling into this Epic.

Exclude a generalized provider framework, new orchestrator, central Aquarium
state, custom installer product, forced feature parity, universal quotas and
vendored third-party skills. Retire existing edition `upgrade` generators after
promoting their useful maintenance knowledge.

## Breaking change and migration

This Epic is **breaking**: existing edition users need marketplace, installation
or other manual migration steps. Unchanged Codex paths are a preservation goal,
not evidence that the migration is nonbreaking. Do not choose a release version
in this dossier.

Record prior and target package identity, installed combination, supported native
selection or explicit local-package-root route, user actions, state preservation,
failure detection and restoration for each host. Test supported recovery rather
than promising a universal downgrade. Keep existing sessions, recovery material,
settings, root guidance and third-party tool state unless a specific migration
action is authorized. External publication, redirects, repository settings and
archival need grants covering their named effects; Task commit authority alone
does not supply them.

## Task objectives and acceptance

### TASK-162: Freeze host capabilities and migration acceptance

- [ ] Refresh source provenance and record exact CLI/runtime and paired-tool versions for all five hosts.
- [ ] Map native entrypoint gates, implicit selection, delegation, questions/goals, agents, hooks, MCP, skill roots and package discovery to primary native sources and observed behavior.
- [ ] Confirm dedicated UTM installation, authentication and session feasibility, including a supported explicit local-root route where needed.
- [ ] Record availability of required paired skills and tools, including Podway, Mulgae, Gaori, Sanho, Sorage and Ouroboros. Missing prerequisites remain explicit blockers; do not vendor or silently substitute them.
- [ ] Classify edition differences and define per-host support scope, migration scenarios, blockers and candidate-bound acceptance evidence.

### TASK-163: Separate shared instructions from host invocation

- [ ] Define entrypoint, implicit-selection and authorized-delegation semantics with reusable role/phase sources separate from gated user-facing skills.
- [ ] Verify direct entry, subordinate progression, denial, standalone resume and grant preservation for affected workflows; preserve public names.
- [ ] Preserve Procedure bytes, digest domains, admitted sessions and retained formal records, or obtain authority for a necessary compatible successor.
- [ ] Factor instructions around demonstrated native limits. AGY v1.4.5 reports a validator warning above 24 KB of skill body; runtime consequences remain unverified and this is not an Aquarium-wide size quota.

### TASK-164: Build host packages and preserve Codex behavior

- [ ] Allocate all five output roots, plugin IDs, marketplace entries and coexistence rules before host integration starts.
- [ ] Build repeatable self-contained outputs from explicit sources; verify shared asset identity, host isolation and operation without sibling repositories or an installation-time generator.
- [ ] Preserve Codex discovery, invocation, progression, recovery and authority behavior with focused regressions and required installed observations.
- [ ] Extend version consistency, full/light release checks and metadata allowlists across outputs; keep the version owner explicit.
- [ ] Promote confirmed common edition fixes to their shared owners without expanding policy or hiding repository changes.

### TASK-165: Integrate Claude Code

- [ ] Implement native selection and delegation, agents/model settings, hooks, MCP and host-scoped skill roots.
- [ ] Verify authorized shared-instruction access under native gates, coexistence and actual failure behavior.
- [ ] Keep `DELEGATION_NOTE` and gated `SKILL.md` path workarounds out of universal shared semantics; assess each claimed limitation against the frozen native baseline.

### TASK-166: Integrate Grok

- [ ] Implement native invocation, setup, hooks, agent lifecycle and scoped configuration from verified contracts.
- [ ] Verify discovery and coexistence, including Claude auto-discovery and name collisions, plus direct/delegated progression and recovery.

### TASK-167: Integrate ZCode

- [ ] Implement native packaging, setup, discovery and supported role behavior with focused checks and installed observations.
- [ ] Preserve native Coordinator use where supported; apply the Herdr ZCode policy only when using that integration.

### TASK-168: Integrate AGY

- [ ] Establish native plugin layout, staging/import behavior, hooks, configuration, delegation and instruction limits against exact versions.
- [ ] Verify direct/delegated progression, skill discovery, coexistence and recovery; do not assume Claude package compatibility.

### TASK-169: Qualify five-host installation and recovery

- [ ] Qualify all five real host packages in the dedicated UTM VM against exact candidate/source identities and the declared installed tool combination.
- [ ] Cover fresh discovery, direct and delegated instructions, Executor/Evaluator progression, negative assessments, commit-gate allow/deny behavior and session recovery.
- [ ] Cover each prior edition's upgrade, meaningful existing-state preservation, co-installed hosts and supported restoration after failure.
- [ ] Retain bounded structured evidence and actual limits under the existing evidence-residency contract; source checks and prepared scenarios are not installed passes.

### TASK-170: Cut over single-repository distribution

- [ ] Extend release-handler, testing authority, manual VM scenarios and root release policy to the shipped packages within the approved implementation scope.
- [ ] Complete the authorized actual release through `aquarium:release-handler`, preserving full/light separation and exact-candidate installed acceptance.
- [ ] Publish migration guidance and native routing or supported explicit local-package-root instructions without creating a custom installer.
- [ ] Perform authorized legacy distribution changes, temporary mirrors/redirects if needed, then archival or read-only retention with tags and history intact.
- [ ] Leave cutover pending or Blocked under the roadmap's rules if required external authority or capability is unavailable; do not report the final goal complete.

### TASK-171: Promote canonical documentation and close the Epic

- [ ] Promote accepted outcomes to the durable owners below and reconcile current behavior, release guidance and migration instructions.
- [ ] Obtain Master's actual overall acceptance separately from design consensus, delegated assessments, technical checks and release acceptance.
- [ ] Replace the roadmap's `Detailed SOT` with valid `Canonical Outcomes` and replace the planned pointer in `docs/README.md`.
- [ ] Remove the TODO index entry and delete this exact dossier only after all consumers are successfully terminal, no other canonical references or consumers remain, and the approved final-closeout deletion envelope includes it. Do not archive a copy.

## Verification and review

Every implementation Task owns focused checks for its changes and any necessary
installed observations. TASK-169 integrates those results. Shared logic receives
common checks and independent review. Changes to host-specific behavior receive
that host's review and native evidence. Routine features need not convene all
five models. Initial Epic qualification requires all five hosts. Later release coverage follows the
accepted affected-host contract, with shared changes assessed for wider impact.

Ordinary tests cover objective package structure, deterministic generation,
executable helper behavior and preservation invariants. They must not pin prose
or claim to verify skill decisions. Do not add paid automated LLM evaluation or
candidate installation to ordinary `make test`. Master performs skill functional
verification separately; candidate installation and its functional checks run
only in the dedicated UTM VM against candidate-matched scenario sources.

Use the host's installed release combination as the VM upgrade baseline and bind
observations to exact package/source identities. No host installation, live
five-host qualification, migration or recovery pass is recorded by this plan.
Missing native capability, authentication, upstream support or required evidence
is a blocker, not a waiver or a passing result.

Claude, Grok, ZCode and AGY may be integrated in that preferred order after shared
packaging. Their roadmap dependencies permit independent work. Use one active
Writer for a shared checkout and coordinate overlapping common-source edits.

## Durable promotion and deletion

| Accepted content | Durable owner |
| --- | --- |
| Host support, invocation, authority, integration and evidence contracts | [Specifications index](../specs/README.md), including `capabilities.md`, `workflow-contracts.md`, `tool-integrations.md`, `local-interfaces.md` and `safety-and-evidence.md`; exact workflow and native references remain code-adjacent owners. |
| Shared sources, host implementations, packaging and runtime flow | [Architecture index](../architecture/README.md), including `components.md` and `workflow-runtime.md`. |
| Accepted design rationale | [ADR registry](../architecture-decision-records/README.md), after acceptance; preserve ADR-0001's still-valid upstream-toolchain and no-vendoring principles in any supersession. |
| Skill, inspector, generation and release maintenance | [Implementation tips](../implementation-tips/README.md), including `changing-skills.md`, `changing-inspectors.md` and `testing-and-releasing.md`. |
| Installation, migration, coexistence and recovery | [Operations index](../ops/README.md) and its accepted runbooks; public instructions in the root README and maintained Korean translation. |
| Executable checks and installed acceptance | `Makefile`, [TESTING.md](../../TESTING.md), candidate-matched `tests/vm/` sources and the applicable release contracts. |

Promote accepted content during each Task, keeping this dossier useful for the
remaining work. Current canonical documents must describe shipped behavior and
identify planned changes as planned. At final closeout,
settle every durable statement, remove or replace every remaining link to this
file, and delete it within the approved envelope. Git history retains the plan.
