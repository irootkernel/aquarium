# Commit messages and change origins

This contract applies to every Aquarium skill, including skills added later. It owns the common message format and the change origin carried into a separately authorized commit. Repository and user instructions take precedence; resolve a conflicting local message rule before applying this format. Attribution never grants staging, commit, amend, push, installation, or publication authority.

## Message format

Use one English imperative subject with exactly one header. Choose the header for the commit's primary purpose:

| Header | Purpose |
| --- | --- |
| `[FEAT]` | New user-facing capability |
| `[FIX]` | Defect correction |
| `[DEV]` | Development tools, build configuration, dependencies, or internal integration |
| `[TEST]` | Tests only |
| `[DOC]` | Documentation only |
| `[CI]` | CI configuration only |
| `[REL]` | Release metadata |
| `[INT]` | Internal contracts, refactoring, or other internal changes |

The release metadata subject is exactly `[REL] Release v<version>`. Keep work IDs in the attribution trailers rather than adding task headers or a second conventional-commit prefix. Tool-generated commits retain their native subjects and trailers; never hand-author a tool's synchronization commit or retrofit Aquarium attribution onto it.

Add a body when it explains the change. End the message with one trailer block, separated from the body or subject by one blank line. Do not place blank lines between trailers. Fold a long value onto an indented continuation line. Every developer-authored commit using this contract includes these three trailers, in this order, exactly once:

```text
Aquarium-Workflow: aquarium:<owning-skill-name>
Aquarium-Epic: <canonical-epic-ID-or-none>
Aquarium-Task: <canonical-task-ID-or-none>
```

Use the skill's actual canonical name, without a fixed allowlist. A commit written outside Aquarium uses `Aquarium-Workflow: none`. Use `none` only for a verified absence, never for an unknown or unresolved relationship.

Lore decision trailers remain optional and repeatable, including on small changes. Add only useful facts and preserve any required `Release-note`, `Aquarium-Evidence`, or native provenance trailers such as Sanho's `docs-base` and `docs-base-tree`. Use the dedicated Aquarium fields for the primary owner rather than adding `Task:` or `Task-Relationship:` aliases. `Related:` may identify secondary work units, related commits, or decision context. Respect repository restrictions on personal attribution such as `Co-Authored-By`.

```text
[DOC] Adopt canonical documentation layout

Establish documentation owners and repair their references.

Aquarium-Workflow: aquarium:docs-setup
Aquarium-Epic: none
Aquarium-Task: none
Tested: Documentation checks passed.
```

## Carry the change origin

When a skill applies an approved repository change, retain a `change-origin` in its result and any later handoff. It contains `workflow-owner` (the fully qualified skill name), the repository, the exact changed paths or hunks, the verified candidate identity (the accepted diff or snapshot already used by that workflow), and the established roadmap and owning work unit or their explicit absence. Keep this in the workflow result or handoff; do not create a central state file, a provenance-only repository document, or a commit just to record it. Runtime, provider, reviewer, model, and session identities do not belong in the commit message. Report this context separately from native receipts, manifest schemas, and Podway records; keep their existing fields and vocabularies unchanged.

Choose one owner for the accepted candidate:

- A standalone change-producing skill owns its approved change, including `docs-setup`, `dev-setup`, and `test-setup`. Applying their files does not authorize a commit; preserve their origin when the user later requests one.
- A phase, delegated setup, check, or review continuing a parent's approved candidate inherits that parent's owner. A standalone phase with its own approved candidate uses its own name. Delegating implementation or selecting a reviewer does not change the owner.
- A separately approved workflow with its own candidate owns that change. For example, feature design entered from `epic-handler` records `aquarium:new-feature`; continuing Epic execution and its internal validation record `aquarium:epic-handler`. Standalone cold validation records `aquarium:epic-validator`.
- `task-commit` consumes a verified origin without replacing it with its own name. Use `aquarium:task-commit` only for a direct commit with no original Aquarium workflow. If an origin is supplied but stale, missing its candidate binding, or inconsistent with the intended scope, resolve it before committing instead of falling back to `task-commit` or `none`.

When more than one independent workflow contributed to a candidate, use an established coordinator that owns the complete accepted scope. If none exists, resolve one owner with the user or split the scopes under the applicable commit authority. Never choose whichever skill ran last. A later conversation must receive and recheck the origin against the current candidate before relying on it. Retain the source through subsequent verified corrections within the same workflow; a new independent workflow establishes its own origin.

This contract adds no mutation to report-only skills. An audit, status query, static review, global installation, or other execution with no repository change creates no repository origin or commit. Reviews supply evidence to the change owner; they do not become its author. Global or private runtime changes stay outside Git under their owning contracts.

## Resolve Epic and Task

Use the established work relationship from the accepted handoff or the commit boundary's required user decision. Re-read its canonical roadmap from the intended commit snapshot. For a Task, preserve its exact canonical ID and resolve its parent Epic from that authority, including `EPIC-000` where it is the standing parent. An Epic-owned candidate uses its Epic ID and `Aquarium-Task: none`. A project-wide candidate with no single owning Epic or Task uses `none` for both; IDs merely created or mentioned by the diff are not owners.

Preserve native IDs, suffixes, and required scope qualification, such as `E23`, `E8-T2`, `CTASK-219`, or `EPIC-61-A`. Never renumber them or infer ownership from filenames, branches, subjects, the last active task, or a review target. An unresolved owner, parent, or namespace is a gap to resolve, not absence. Attribution does not bypass the direct-commit Task relationship confirmation or authorize a lifecycle edit.

## Verify the message

Before committing, present the complete message with the exact scope and confirm that its origin and work relationship match the accepted candidate. Parse the prepared message with `git interpret-trailers --parse` and require exactly one occurrence of each Aquarium key with the expected value. Match keys without case sensitivity when checking duplicates, and emit the canonical spelling above. Reject a missing, duplicate, conflicting, or unparsed field before the authorized commit.

After the commit and native hooks, parse the actual committed message again and verify its subject, all three attribution values, and any required evidence trailers. Permit supported hook-added provenance without dropping the Aquarium fields. Combine this with `task-commit`'s existing snapshot and identity checks. A failed post-commit check is an incomplete result with an existing commit; report it and recover only under applicable authority, never with an automatic amend or second commit.

## Manual verification

Master verifies workflow behavior separately. Structural checks and message parsing do not establish these outcomes:

| Scenario | Expected outcome |
| --- | --- |
| Standalone documentation, repository, or test setup followed by a later commit | Preserve `docs-setup`, `dev-setup`, or `test-setup` as the origin after rechecking its candidate. |
| Task phases or bundled setup continue a parent candidate | Preserve the parent's owner; a separately approved independent workflow gets its own owner. |
| Epic delivery, independent validation, and feature design | Preserve their actual owner without assigning internal Epic validation to `epic-validator`. |
| Direct commit without an original Aquarium workflow | Record `task-commit`, after the existing relationship and approval checks. |
| Stale origin or independently mixed scopes | Resolve the origin or coordinator before committing; do not replace it with a fallback. |
| Task checkpoint, Epic closeout, standing Task, or native ID | Resolve the correct parent, preserve canonical IDs and lifecycle decisions, and use `none` only where applicable. |
| Read-only or global-only execution | Create no repository origin or artificial commit. |
| Native hooks add provenance | All Aquarium and required evidence fields remain parseable in the actual commit. |
| Newly added Aquarium skill | Apply the same contract using its canonical name without changing a skill allowlist. |
