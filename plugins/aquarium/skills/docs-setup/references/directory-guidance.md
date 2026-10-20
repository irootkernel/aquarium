# Directory guidance operations

Use the [shared contract](../../../references/directory-agent-guidance.md) for
ownership, instruction scope and later maintenance. These operations establish
or reconcile guidance only in the explicitly selected repository and scope.
Guide absence alone adds no prerequisite to existing delivery workflows.

## Discover the selected scope

Read the existing root documentation index and its adoption declaration. Inventory
applicable root and directory `AGENTS.md`, useful READMEs, other instruction
formats including nested `CLAUDE.md`, local exceptions and tool-managed blocks.
Preserve their content and markers. Report loading conflicts against the selected
harness's native contract; actual observed loading requires separate evidence.
Root CLAUDE migration remains with `dev-setup`. Migrate or remove a nested format
only when that effect is explicitly selected.

Inspect current implementation responsibilities, package boundaries and canonical
architecture within the selected scope. A directory name does not establish a
feature boundary. Map independently meaningful areas to their canonical sources,
including valid legacy and code-adjacent owners. Ordinary nested directories may
use ancestor guidance. Record the source that establishes each mapping, the guide
path and the circumstances in which its linked documents apply. A guide contains
only its local responsibility, relative source links and necessary local rules;
repository-wide declarations remain with their existing owners.

Read ordinary implementation sources needed for that analysis, including
authentication implementation. Keep credential-bearing files and secret values
excluded. The bundled inspector may exclude a Markdown file with an
authentication-related name even when it contains ordinary documentation. Report
that exclusion and the structural coverage it leaves unverified. An independent
workflow read of safely identified ordinary source does not change the
inspector's result.

Report missing canonical targets, competing owners and unresolved instruction
conflicts at their exact paths. For a destination that an approved move will
create, verify its existing source and approved destination content under
[migration.md](migration.md). Resolve meaning with the owning authority before
applying the affected change. Do not invent links, weaken a local exception or
claim completed coverage for an unresolved area. A bounded proposal may leave
that area as an explicit remaining gap without blocking unrelated approved work.

## Operation effects

`audit` reports the existing instruction formats, guide inventory, source mappings,
coverage declaration, conflicts, missing targets and unverifiable areas. It does
not draft guides, add a declaration or write files.

`bootstrap` establishes canonical documentation ownership for a repository that
lacks it. Include explicit guide coverage and proposed guides only for existing
implementation boundaries. A greenfield repository may declare approved coverage
before implementation exists; create no predicted directories or guides.

`adopt` preserves valid document paths, identifiers and useful local guidance.
Reconcile existing guides and propose missing guides within the selected coverage.
For each guide, show the source mapping, complete diff, preserved instructions and
managed blocks. Adoption does not implicitly migrate another instruction format
or widen the selected area.

`migrate` includes affected guide references in the approved canonical-document
mapping and atomic rewrite described in [migration.md](migration.md). Preserve
unrelated guide text and rules. A feature-path move belongs to its delivery Task;
it does not expand adoption or backfill surrounding areas.

## Coverage and resumption

Record coverage in `docs/README.md` or its adopted legacy equivalent as part of
the approved diff. State whole-repository coverage or the exact named
implementation areas, what is complete, what remains and the next area for
partial adoption. Whole-repository coverage includes later feature boundaries;
named-area coverage includes later features in those areas. Keep delivery status
in the roadmap. Do not create a second state file or a generated feature graph.

Resume from that declaration after comparing it with current implementation,
canonical owners and existing guidance. Reuse valid mappings and preserve
completed areas; propose only changes now required in the approved scope. If
the declaration and guides already match current sources, report a no-op and
leave them unchanged. Completing one area does not establish whole-project
coverage. Expanding coverage requires an explicit proposal and approval.

Without a declaration, preserve existing applicable guides and report adoption
as undeclared. Root setup alone does not adopt guides, and routine delivery must
not generate unrelated missing guidance. Initial `new-project` documentation
creation leaves adoption to a later explicit `docs-setup` operation.

## Apply and verify safely

Before approval, show all selected mappings and the complete path-by-path diff,
including preserved content, the coverage declaration, reference rewrites and
any change to distributed package contents.
Record exclusions and unresolved gaps. Snapshot affected tracked and untracked
files, mapping sources, reference inventory and expected absent targets.

Immediately before applying, recheck the selected scope, Git identity, snapshots
and roadmap state under the entrypoint's approval contract. Reject symlinked
targets or ancestors, targets outside the selected repository, nested repositories
and writes that would overwrite unrelated work. Do not follow links to widen
write scope. Drift in an affected source or target requires a fresh proposal;
unrelated dirty work remains untouched.

Apply the approved composition together. If application fails after any write,
stop and report the actual changed and pending paths. Do not declare success,
silently continue from a partial state or overwrite intervening edits to recover.
Reconcile the observed state and obtain approval for any changed recovery diff.

Verify guide links and targets, preserved instructions and managed blocks,
coverage accuracy, and the complete migration mapping where applicable. Run the
inspector and repository-native non-writing checks, and report their structural
results separately from semantic source review.
