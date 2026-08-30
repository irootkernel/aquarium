---
name: docs-setup
description: "Audit, establish, adopt, or migrate a repository's canonical documentation structure and roadmap IDs. Use when the user explicitly invokes $aquarium:docs-setup; do not use for routine task documentation."
---

# Documentation Setup

Establish documentation ownership and roadmap identity for one Git repository. This standalone setup workflow never stages, commits, pushes, publishes, creates Aquarium state, advances Podway, or replaces `$aquarium:task-document`.

Read [documentation-governance.md](../../references/documentation-governance.md) and [operations.md](references/operations.md). Read [profiles.md](references/profiles.md) for `bootstrap` or `adopt`, and [migration.md](references/migration.md) for `migrate`.

## Establish the Repository

1. Resolve one regular non-symlink Git root, read every applicable instruction file, and inspect HEAD, branch, upstream, staged, unstaged, untracked, conflicted, and worktree state.
2. Discover the public root README plus documentation, roadmap, specification, architecture, ADR, implementation, operations, TODO, existing dossier, deferred-feedback, archive, contract, validation, and language authorities before asking the user for facts.
3. Never open `.env*`, authentication, credential, key, secret, or token paths. Do not read ignored runtime evidence or emit repository document contents in the report.
4. Resolve this skill's directory and run `python3 <skill-directory>/scripts/inspect_docs.py --repository <git-root>`. Treat its `aquarium-docs-inspection/v2` JSON as conservative structural discovery only. It reports role ownership, explicit roadmap units and links, exclusions, and unambiguous structural conflicts; it does not interpret prose, decide migration eligibility, certify documentation completeness, or establish current product truth.
5. If Python is unavailable or inspection fails, report the gap and perform bounded read-only discovery manually. Do not install a runtime or dependency.

If more than one plausible canonical roadmap, delivery scope, or profile remains after discovery, use `request_user_input` when available to ask only for the material ownership choice. Recommend `single-scope` for one delivery owner, `multi-scope` for independently delivered surfaces, and `legacy-adopt` when moving established authority is not approved.

## Select One Operation

- `audit`: report the current profile, public-versus-maintainer audience boundary, role owners, operations coverage, roadmap units, declared dossier and completed-outcome references, conflicts, missing roles, and unverifiable facts without drafting or mutation.
- `bootstrap`: propose a complete new documentation tree and first roadmap contract for a repository without an established documentation authority.
- `adopt`: preserve existing paths and identifiers, add or reconcile the root documentation index, and fill only required role gaps approved by the user. Preserve and map existing dossier conventions, but never create or retrofit a work item or execution SOT; route new or revised epic definition to its owning work-definition workflow.
- `migrate`: change an adopted profile, documentation paths, or eligible roadmap identifiers through one reviewed mapping and exact diff.

Do not combine path migration and ID migration merely because both are possible. Include both only when the user selected both and the complete atomic diff is safer than either intermediate state.

## Propose the Change

For every mutating operation, produce one decision-complete proposal containing the selected profile, scopes, public-versus-maintainer audience boundary, role-to-path map, operations ownership, precedence, roadmap namespaces, ID policy, preserved existing dossier conventions, exact target paths, moves versus new files, reference rewrites, validation commands, and exclusions.

Reuse repository content and validation patterns. Do not create placeholders that claim unknown architecture or specifications. A required index may record a bounded documented gap and its owner, but it must not invent product truth.

Use structured ask/answer when available to request `Apply exactly this diff`, `Revise proposal`, or `Do not apply`. Snapshot every affected tracked and untracked path before asking. Immediately before mutation, re-read the snapshots and discard approval if any target, reference inventory, roadmap status, or Git identity changed.

## Apply and Verify

Apply only the approved diff and preserve unrelated work. Do not run a formatter, generator, documentation server, test, or linter that may rewrite unrelated files unless that effect was disclosed and separately authorized where required.

Run the inspector again, repository-owned non-writing documentation checks, and `git --no-pager diff --check`. Report structural results separately from semantic review and runtime or generated-contract proof. An Aquarium inspection does not become repository-native CI and does not prove that documentation matches implementation.

Return the operation, profile, scopes, audience boundary, role owners, operations coverage, canonical roadmaps, ID policy, existing dossier references, migration mapping if any, changed paths, checks with exit codes, unresolved gaps, and separate staging, commit, and publication state.
