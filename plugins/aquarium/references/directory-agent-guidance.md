# Directory agent guidance

Directory `AGENTS.md` files connect implementation areas to their canonical
documents and local working instructions. Durable requirements, design rationale
and delivery status stay in their existing owners. Use paths relative to
the guide, with stable section links where they help the reader find the exact
contract. Code-adjacent and legacy authorities remain valid targets; a guide need
not route every link through `docs/`.

This contract defines ownership and lifecycle. `dev-setup` and `new-project`
apply their boundaries below. Directory adoption in `docs-setup`, delivery
integration and installed observations have separate implementation and
verification work; this contract alone does not establish those outcomes.

## Ownership and instruction scope

[Development setup](../skills/dev-setup/SKILL.md) owns root discovery and
maintenance rules for documentation, including the root guidance template. It
does not discover every feature or create nested guides during ordinary setup.
[Documentation setup](../skills/docs-setup/SKILL.md) owns explicit directory-guide
adoption, reconciliation and canonical-document migration. Ordinary delivery
owns maintenance of the affected canonical documents and applicable guides.
[New-project](../skills/new-project/SKILL.md) creates the first documentation index
and role owners without declaring directory-guide adoption or creating guides.
Later explicit adoption belongs to `docs-setup`.

Respect the selected harness's native instruction scope and precedence. A guide
describes its directory's responsibility, links the relevant specifications,
architecture, ADRs, implementation tips or operations guidance, and explains
when those sources matter. Add local instructions only where the area needs
them. The full root guidance structure is for the root. Repository-wide Project
Configuration, evidence-root declarations, release policy and commit authority
remain with root guidance and their canonical owners.

Preserve existing useful READMEs, local exceptions, stricter instructions and
tool-managed blocks, including their markers. Inventory applicable instruction
formats, including nested `CLAUDE.md`, and report loading conflicts against the
selected harness's actual contract. Do not migrate or remove another format
unless that operation is explicitly selected. Keep `dev-setup`'s root CLAUDE
migration and loading-blocker rules intact; route nested-guide work to
`docs-setup`. Resolve a semantic conflict at its exact owning authority before
applying the affected proposal. A generic template cannot override an unresolved
local exception.

## Source discovery and feature boundaries

Establish feature boundaries from current implementation responsibilities,
package boundaries, existing guidance and canonical architecture. A directory
name alone is insufficient. Place guides at independently meaningful boundaries;
ordinary nested folders can use applicable ancestor guidance. Do not invent
directories or guides for predicted implementation.

Read ordinary implementation sources needed to establish the mapping. Separate
ordinary authentication implementation from credential-bearing files: this
contract grants no access to secrets. Exclude generated, vendored and ignored
runtime material unless the selected repository scope explicitly makes it
relevant. Do not follow links to widen write scope, edit another repository or
create a central Aquarium state file. If a guide would enter a distributed
package, assess that shipped-content effect in the adoption proposal.

Identify the canonical documents relevant to the change even when guidance is
missing. Reading original sources and observing a harness load instructions are
separate evidence claims. Do not assume every harness automatically loads every
descendant guide; discover applicable instructions from the affected paths and
report actual loading only for the named harness and observed session.

## Explicit adoption and coverage

Record approved coverage in the existing root documentation index,
`docs/README.md` or its adopted legacy equivalent. Declare whole-repository
coverage or named implementation areas, distinguish completed coverage from
remaining gaps, and identify the next area when adoption is partial. The
declaration records documentation scope. Keep delivery state in the roadmap and
do not add a generated feature graph. Resume from the declaration after checking
the current implementation and guidance. Area completion cannot establish
whole-project coverage.

Whole-repository coverage includes later feature boundaries. Named-area coverage
includes later features within those areas. Root setup alone does not adopt
directory guides. Without a declaration, maintain existing applicable guidance
but do not generate missing guides through routine delivery. Coverage expansion
requires an explicit `docs-setup` operation and its complete proposal.

The documentation operations retain these distinct effects:

- `audit` reports existing guidance, source mappings, conflicts, gaps and
  unverifiable facts without writing.
- `bootstrap` establishes documentation authorities and guides for existing
  implementation boundaries when the repository lacks documentation authority.
- `adopt` preserves valid paths, identities and local instructions while
  proposing missing or inconsistent directory guidance.
- `migrate` updates affected guide links with the approved canonical-document
  migration and preserves unrelated guide content.

For greenfield work, establish root rules and canonical document ownership
first. After `new-project`, explicit `docs-setup` adoption may declare coverage
before implementation exists, but it creates no predicted directories or guides.
Later authorized delivery adds guides for new feature boundaries within that
coverage.

For brownfield work, inventory existing authorities and instructions, inspect
the selected implementation scope, and prepare the complete source mapping and
file diff before application. A large scope may use named areas and resumable
adoption. Preserve unrelated dirty work and recheck affected snapshots under
the existing documentation-approval contract.

## Maintenance during delivery

Planning identifies applicable root and directory guidance, the adoption
declaration and relevant canonical sources. Update changed behavior in its exact
owner, then maintain affected guide links and local instructions. Within adopted
coverage, add a guide for a new independently meaningful feature boundary as
part of the authorized Task. Outside coverage, report the gap without unrelated
backfill. Existing applicable guides need maintenance wherever they live.
Missing guidance alone does not block an otherwise valid legacy workflow.

A feature move maintains its existing guide and affected links under the
authorized move, including a move across an adoption boundary. It does not
implicitly expand adoption or backfill surrounding areas. Changes to common
discovery or maintenance rules may require a root-guidance change through its
existing owner. Uncovered effects keep the owning workflow's approval boundary.

Finish affected documentation and required final prose passes before candidate
review. Review implementation, tests, canonical documents and guide changes as
one candidate. Unaffected guidance needs no artificial edit. Review corrections
follow existing finding-disposition and affected-evidence rules; they do not
automatically add another provider review. Commit the accepted composition
without appending unreviewed semantic guidance. Final Epic integration and cold
validation check consistency across affected feature boundaries and Tasks.

Task-handler delivery uses its documentation phase. Epic-handler delivery applies
the obligation in its own flow without invoking Task-handler phase skills.
Adaptive phase selection accounts for affected canonical documents or applicable
guides when deciding whether documentation work is due. These responsibilities
add no new review stage and do not run setup for every Task.

## Compatibility and verification

The capability is additive: adoption is explicit, existing projects remain
usable, and guide absence adds no prerequisite. Preserve admitted sessions and
installed managed Procedure copies. A required migration, runtime-contract
change or companion-tool update requires a revised breaking-change decision.
Plugin installation alone does not rewrite repository guidance; repository
adoption and changes to other repositories require their own authorized scope.

Structural checks establish only objective structure and executable-helper
behavior. They cannot establish semantic completeness, source selection,
multi-step skill behavior or actual harness loading. Keep manual scenarios with
the testing authority and actual observations separate from release acceptance.
Installation-dependent verification uses the exact candidate and installed
combination in the dedicated UTM VM; host candidate installation is outside
development verification.
