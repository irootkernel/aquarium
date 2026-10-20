# Directory agent guidance

## Purpose and authority

This dossier defines directory `AGENTS.md` documentation indexes for
[EPIC-029](../roadmap/README.md#epic-029-add-directory-agentsmd-documentation-indexes).
The [roadmap](../roadmap/README.md) alone owns Epic and Task identity, ordering,
dependencies and lifecycle state. This file owns the execution requirements and
acceptance contract until the Epic promotes its implemented outcomes.

Implementation proceeds under the approved Epic scope. The
[shared contract](../../plugins/aquarium/references/directory-agent-guidance.md)
now owns directory-guidance ownership, lifecycle and compatibility; `dev-setup`
and `new-project` define the root and initial-documentation source boundaries.
`docs-setup` now defines directory audit, bootstrap, adoption and migration with
source mappings, explicit coverage and preserved local instructions. Task and
Epic delivery now read and maintain affected documents and guides through their
existing review, validation and commit responsibilities. Cross-workflow path
regressions and manual scenarios are prepared under
[the testing authority](../../TESTING.md#directory-guidance-verification);
installed Codex observations cover root setup, scoped adoption, migration and
affected Task/Epic delivery in the dedicated UTM VM. Native automatic loading,
unobserved partial-write recovery and production-scale behavior remain unverified.
Structural checks and agent-run observations do not replace Master's functional
verification or release acceptance. Installation, publication, provider
operations and changes to other projects require authority beyond this dossier's
requirements.

## Problem and selected approach

Canonical documents already preserve requirements, structure, accepted decisions,
implementation guidance and operations knowledge. An agent starting from a
feature's implementation still needs to find the relevant sources. A scoped
`AGENTS.md` provides that entrypoint beside the code.

Keep durable knowledge in its existing owner and use directory guidance to name
what applies to the feature. A separate memory database, background capture,
summary injection and automatic transcript promotion are outside this Epic.
A README remains useful for human-facing explanations when needed; adoption does
not require paired README and AGENTS files with duplicate indexes.

The design assigns directory guidance to documentation setup because building
these indexes requires understanding feature boundaries and canonical documents.
This analysis can be substantial in a large existing repository. It belongs in
an explicitly scoped documentation-adoption job and is not repeated by ordinary
repository development setup.

## Current sources and planned ownership

The [documentation index](../README.md) declares role ownership and precedence.
The [documentation governance contract](../../plugins/aquarium/references/documentation-governance.md)
owns the shared semantic roles. The
[directory guidance contract](../../plugins/aquarium/references/directory-agent-guidance.md)
owns the durable guidance rules. The following responsibilities define the full
Epic outcome; the roadmap records their delivery state:

| Owner | Responsibility |
| --- | --- |
| `dev-setup` | Maintain root `AGENTS.md` rules for finding applicable guidance and keeping documents current. Preserve its tool-setup scope. |
| `docs-setup` | Own the directory-guidance convention, adoption coverage, initial feature discovery, creation, reconciliation and documentation migration. |
| `new-project` | Create the first documentation index and role owners without declaring directory-guide adoption or creating guides. Route later explicit adoption to `docs-setup`. |
| `task-plan` and delivery coordinators | Read applicable guidance and relevant original sources while resolving the affected work. |
| `task-document` | Maintain affected canonical content and directory guidance for Task-handler delivery. |
| `epic-handler` | Apply the same documentation obligation within its own Task completion and Epic integration flow. Do not invoke Task-handler phase skills. |
| Reviewers and Evaluators | Assess the complete applicable candidate, including documentation and guidance, against original requirements. |
| `task-commit` | Verify that the accepted composition matches the staged candidate. Leave semantic documentation authoring with its existing owner. |

Use one shared directory-guidance contract linked by these consumers. Preserve
native instruction scope and precedence, existing user-authored exceptions and
tool-managed blocks. The full root guidance template applies to the root;
directory files contain only their local scope, source links and needed local
instructions. Repository-wide declarations, including Project Configuration, the
evidence root, release policy and commit-message authority, stay with root
guidance and their canonical owners. Directory adoption creates no competing
declarations.

The existing [development setup](../../plugins/aquarium/skills/dev-setup/SKILL.md),
[root guidance standard](../../plugins/aquarium/skills/dev-setup/references/agents-guidance.md),
[documentation setup](../../plugins/aquarium/skills/docs-setup/SKILL.md),
[Task planning](../../plugins/aquarium/skills/task-plan/SKILL.md),
[Task handler](../../plugins/aquarium/skills/task-handler/SKILL.md),
[Task documentation](../../plugins/aquarium/skills/task-document/SKILL.md),
[Epic handler](../../plugins/aquarium/skills/epic-handler/SKILL.md),
[Epic validator](../../plugins/aquarium/skills/epic-validator/SKILL.md),
[new-project](../../plugins/aquarium/skills/new-project/SKILL.md) and
[commit skill](../../plugins/aquarium/skills/task-commit/SKILL.md) are implementation
inputs. Contract and source changes do not establish installation or successful
functional verification.

## Directory guidance contract

A guide identifies the implementation responsibility covered by its directory,
links the relevant canonical specifications, architecture, ADRs, implementation
tips or operations guidance, and explains when each source matters. Include local
working instructions only when that area needs them. Use paths relative to the
guide and useful section links where stable.

Choose feature boundaries from the current implementation, package boundaries,
existing guidance and canonical architecture. Directory names alone do not prove
a feature boundary. Place guides at independently meaningful boundaries; ordinary
nested folders may use the applicable ancestor guidance. Do not create guides for
predicted implementation directories that do not yet exist.

Preserve existing useful READMEs and instructions. Reconcile a local conflict
against the exact owning authority and surface unresolved meaning before applying
the affected proposal. Do not overwrite a local exception with generic text.
Inventory other instruction formats, including nested `CLAUDE.md` files, and
report loading conflicts using the selected harness's actual contract. Preserve
them unless their migration is explicitly selected. Keep the development setup
contract root-scoped and route selected nested-guide work to `docs-setup`.

Keep policy, design rationale and delivery status in their canonical owners.
Link to them without copying their full content into each guide. Existing
code-adjacent authorities, including skill entrypoints and shared contracts,
remain valid canonical targets. Do not force every link through `docs/` when
another file owns the exact contract.

Inspect ordinary implementation sources as needed to establish the mapping.
Exclude generated, vendored and ignored runtime material from feature adoption
unless the selected repository scope explicitly makes it relevant. Distinguish
ordinary authentication implementation from credential-bearing files; this
feature grants no access to secrets. Do not edit outside the selected repository,
follow links to widen write scope, or create a central Aquarium state file.
For implementation directories included in a distributed package, assess whether
adding a guide changes its shipped contents and include that effect in the
approved proposal.

## Root discovery and update rules

The root guidance should express these responsibilities in the repository's
existing style:

```markdown
- Before changing a feature, read the applicable directory AGENTS.md files
  and the canonical documents relevant to the change.
- Read the directory-guide adoption scope in the root documentation index.
  Within that scope, maintain affected guides and add guides for new feature
  boundaries as part of the same task. Report uncovered areas without backfilling
  them. Existing local instructions remain applicable outside adopted coverage.
```

Do not assume that every harness automatically loads every descendant guide.
Integrate discovery with the affected-path planning flow. Relevant source reads
and actual observed loading are separate claims.

## Initial adoption

`docs-setup` records approved directory-guide adoption in the existing root
documentation index (`docs/README.md` or its adopted legacy equivalent), alongside
the guide proposal. Declare whole-repository coverage or named implementation
areas, distinguish completed coverage from remaining gaps, and identify the next
area when adoption is partial. Whole-repository coverage includes later feature
boundaries; named-area coverage includes later features within those areas.
Record documentation scope, not a duplicate roadmap or generated feature graph.
Resume adoption from this declaration and recheck it against current sources.

Without a declaration, root setup alone does not adopt directory guides. Preserve
and maintain existing applicable guidance, but do not start generating missing
guides through ordinary delivery. Expanding coverage is an explicit `docs-setup`
operation with its own complete proposal.

Select documentation operations from the repository's actual documentation state:

- `audit` reports existing guides, feature-to-document mappings, conflicts,
  missing coverage and unverifiable facts without writing files.
- `bootstrap` establishes canonical documentation and guides for existing
  implementation boundaries in a repository without a documentation authority.
- `adopt` preserves valid paths, identities and local instructions while proposing
  missing or inconsistent directory guidance.
- `migrate` updates the affected guide links with the approved canonical-document
  migration. Preserve unrelated guide contents. Feature-path
  moves belong to the delivery Task and maintain affected guides within its
  approved scope.

Greenfield projects establish root rules and document ownership first.
`new-project` creates the initial documentation set without declaring adoption.
An explicit `docs-setup` operation then records coverage and creates guides for
existing implementation boundaries. If implementation has not started, declare
the approved scope without inventing directories or guides. Later feature
creation adds its guide within declared coverage and authorized delivery work.

Brownfield adoption first inventories the existing authorities and guidance,
then verifies feature boundaries and prepares the complete selected mapping and
file diff. A large selected scope may use named areas and resumable work, with
completed and remaining coverage recorded in the root documentation index.
Area completion cannot claim whole-project coverage. Preserve unrelated dirty
work and recheck affected snapshots before application under the existing
document-approval contract.

Initial adoption and later maintenance are different work scopes. Ordinary
`dev-setup` updates root rules without launching full feature discovery. Routine
delivery updates only the affected area and does not backfill unrelated guides.
Missing guidance alone does not block an otherwise valid legacy workflow; the
agent still resolves current canonical requirements.

## Maintenance during delivery

During planning, identify applicable root and directory guidance and the canonical
sources affected by the change. During implementation and documentation, update
behavior in its canonical owner and adjust the affected guide links and local
instructions. Within declared adoption coverage, a new feature may require a new
guide within the approved Task scope. Outside it, report the coverage gap without
creating unrelated guides. Maintain existing applicable guidance wherever it
lives. A feature move updates its existing guide and affected links under the
authorized move, including when it crosses an adoption boundary; do not expand
coverage or backfill its surroundings implicitly. Changes to common discovery or
update rules may require a root edit.
Uncovered effects retain the owning workflow's existing approval boundary.

Finish these updates before candidate review, including any repository-required
final prose pass. Review the implementation, tests, canonical documents and guide
changes as one coherent candidate. If guidance is unaffected, no artificial edit
is required.

Review corrections follow the existing finding-disposition and affected-evidence
rules. They do not automatically require a new provider review. Commit only the
accepted composition; do not append unreviewed semantic guidance while preparing
the commit. Final Epic validation checks cross-Task feature boundaries, links and
instructions for consistency.

`task-handler` uses its existing documentation phase. `epic-handler` implements
the obligation directly in its goal-centered flow. Shared consumers, including
later collaboration workflows, inherit the same documentation contract without
adding a new review stage. On adaptive paths, affected canonical-document or
applicable guide changes make documentation work due; the phase-selection
decision must account for that work. EPIC-029 does not depend on EPIC-027 or
EPIC-028 and does not implement their collaboration runtime.

## Compatibility and rollout

Adoption is explicit. Existing projects remain usable, and guide absence alone
adds no prerequisite. These boundaries make the planned capability additive.
Preserve admitted workflow sessions and installed managed Procedure copies.
A mandatory migration, changed runtime contract or required companion-tool
change exceeds this compatibility assumption and needs a revised breaking-change
decision before implementation proceeds.

An Aquarium release distributes the updated workflows. Each existing repository
then adopts its guidance through an authorized `docs-setup` operation. Multiple
repositories require an explicitly selected list and repository-specific proposals.
Plugin installation alone does not rewrite repository files. Creating a rollout
service or extending development-tool bundle manifests is outside this Epic.

Candidate installation and installation-dependent verification run only in the
dedicated UTM macOS VM against the host's installed release combination. Host
installation is a later released-version operation. Do not apply this Epic's
candidate to Sudal, Podway or other live repositories as part of development.

## Task outcomes

### TASK-157: Define directory guidance ownership and lifecycle

Define the shared contract, root-versus-directory scope, preservation and conflict
handling, discovery, declared adoption coverage, maintenance and explicit adoption.
Keep the greenfield `new-project` boundary explicit. Update the root guidance
template only for its basic documentation rules. Identify the
canonical owners for accepted outcomes and confirm the additive compatibility
boundary before delivering the contract. Include focused checks for any executable
validation changes in this Task.

### TASK-158: Add directory guidance to documentation setup

Implement the four documentation operations against the shared contract. Propose
source-grounded guide mappings and exact file changes, preserve existing rules,
handle missing or competing authorities honestly, and update links in approved
migrations. Record adoption coverage in the existing documentation index, and
resume partial adoption from that declaration. Keep semantic analysis with the
workflow; inspectors report only objective structure and safe path/reference
facts. Include the focused tests needed to accept this Task's executable changes,
including safe paths, missing targets, preserved rules and repeat adoption where
helpers support those behaviors.

### TASK-159: Maintain guidance during Task and Epic delivery

Integrate affected-path discovery and document maintenance into existing planning,
documentation, review and acceptance responsibilities. Include guide changes in
the reviewed candidate and preserve its identity through commit. Cover final Epic
integration and cold validation without adding a new mandatory review stage or
running setup for every Task. Respect declared adoption coverage and include
focused verification for this Task's own executable changes.

### TASK-160: Add cross-workflow regressions and verification scenarios

Add integration regressions for repeated adoption, documentation migration and
affected delivery across the completed workflows. Prepare the manual scenarios,
fixtures and testing-authority updates needed by TASK-161. Each earlier Task
retains the tests needed to accept its own changes; this Task supplies additional
cross-workflow evidence. Use meaningful inputs, outputs and failure paths where
executable helpers exist. Do not assert skill prose, private helper names or exact
sentences, and keep manual semantic checks separate from structural proof.

The existing local-reference helper now has integration regressions for a
canonical-document move to an initially absent destination and a feature move to
a different directory depth. Both exercise valid, stale and repaired references.
[Five manual VM groups](../../tests/vm/directory-agent-guidance.md) map all 13
acceptance scenarios to an independent base fixture, separate greenfield and
bootstrap preparation, actual installed operations and retained evidence.
These definitions do not establish semantic adoption, native instruction loading
or an installed pass; TASK-161 retains those observations. No release-note entry
is due for this test and scenario preparation alone.

### TASK-161: Verify installed workflows and promote canonical documentation

Run installation-dependent scenarios in the dedicated UTM VM with the exact
candidate and installed combination. Observe fresh-session discovery, document
adoption and affected Task/Epic maintenance in a named supported harness.
Record actual results and limits; unsupported or unobserved harness behavior
remains unverified. Promote implemented outcomes to their durable owners and
prepare Epic closeout under actual Master acceptance.

## Acceptance scenarios

These are required future scenarios, not execution results.

| Scenario | Required result | Primary Task |
| --- | --- | --- |
| Root setup boundary | Root documentation rules are updated without whole-repository guide generation or unrelated tool configuration. | TASK-157 |
| Root rules without adoption | Root guidance exists, but ordinary delivery creates no missing guide until explicit adoption; existing applicable instructions remain in force. | TASK-157; TASK-159 |
| Partial coverage during delivery | New features inside a declared area receive guides; a feature outside it produces a coverage report without implicit adoption or backfill. | TASK-158; TASK-159 |
| Existing canonical owners | Guides link the real owners, including legacy paths and code-adjacent contracts. | TASK-158 |
| Greenfield growth | Existing feature roots receive guides; a later feature gains its guide during authorized delivery. | TASK-158; TASK-159 |
| Large brownfield adoption | The selected implementation scope is analyzed, existing rules survive, and partial area work is not reported as complete coverage. | TASK-158 |
| Missing or conflicting meaning | The workflow exposes the exact gap or conflict and does not invent links, authority or successful coverage. | TASK-158 |
| Migration and repeat adoption | Approved path moves update affected references; unchanged repeat adoption produces no unnecessary diff. | TASK-158; TASK-160 |
| Path and content safety | Secret-bearing and unrelated runtime files remain untouched; unsafe write targets are rejected and unrelated dirty work is preserved. | TASK-158; TASK-160 |
| Task and Epic candidate | Affected canonical documents and guides enter review before commit; unaffected guides need no edit. | TASK-159 |
| Review correction | Changed guide content follows the existing affected-evidence and local-settlement rules; no unreviewed semantic update reaches commit. | TASK-159 |
| Fresh installed session | The named harness discovers applicable guidance and follows original canonical sources in the exact installed candidate. | TASK-161 |
| Installed lifecycle | The VM demonstrates adoption, maintenance, recovery and existing-workflow preservation without host candidate installation. | TASK-161 |

Select the focused checks from the [Makefile](../../Makefile) and
[TESTING.md](../../TESTING.md). Automated checks establish objective structure and
executable helper behavior only. They do not prove semantic completeness, correct
source selection or multi-step skill behavior. Do not add an automated LLM gate
to `make test` or treat structural success as Master's functional verification.

## Documentation promotion and closeout

Promote shipped behavior to specifications and exact owning skill contracts,
current boundaries to architecture, accepted rationale to an ADR when warranted,
implementation guidance to implementation tips, and real operational adoption or
recovery instructions to operations. Update public usage only where it changes.
Keep required manual scenarios with the testing authority and actual functional
results separate from release acceptance.

EPIC-029 is the sole consumer of this dossier. At its approved closeout, promote
remaining durable information, replace its `Detailed SOT` with valid canonical
outcomes and settle this TODO entry and dossier under the
[execution-SOT contract](../../plugins/aquarium/references/epic-execution-sot.md).
Do not remove the dossier while a current consumer still needs it. Dossier
registration or a documentation commit is not implementation, functional
acceptance, installation or publication.
