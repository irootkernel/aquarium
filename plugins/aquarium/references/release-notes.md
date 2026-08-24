# Release Notes

Use this contract when a repository declares one canonical release-notes owner with the exact Project Configuration entry `Aquarium release notes: <repository-relative-path>`.

Enrollment is explicit and repository-local. Do not create `.aquarium`, infer an owner from similarly named files, or replace an established changelog without an approved migration. Repositories without the declaration remain unenrolled until an approved guidance change names one regular non-symlink tracked Markdown file.

## Canonical Format

Use one level-two heading for each stable SemVer release:

```markdown
## v0.1.11 - Unreleased

### Added

- Add concise user-facing release-cycle tracking.

## v0.1.10 - 2026-08-23
```

Keep exactly one `Unreleased` section and order it before completed releases. A completed heading uses the publication date in `YYYY-MM-DD` form. The open version is a planned target, not published version metadata, and may change only after the user approves the exact heading edit. Never rewrite a completed release section merely because the next target changes.

Use `Added`, `Changed`, `Fixed`, and `Removed` only when they contain entries. Each entry describes one user-visible, compatibility, security, privacy, or operational outcome in one sentence and at most two Markdown source lines. Exclude file lists, commit subjects, implementation chronology, test counts, validation evidence, and internal refactors that do not change a shipped contract.

## Commit Decision

Every commit in an enrolled repository carries exactly one release-note decision in its workflow handoff:

- `entry`: the exact approved changelog entry is included in the same commit;
- `intentional no-note`: the change has no independently useful shipped outcome;
- `not-enrolled`: no release-notes authority is declared.

A managed delivery workflow settles the decision during documentation, before review and closeout. A direct `$aquarium:task-commit` invocation may prepare only one concise changelog hunk after the user approves its exact text; that hunk becomes part of the final commit snapshot and invalidates any earlier approval that did not include it. Never infer `intentional no-note` from a commit prefix alone.

An exact release-handler settlement, retarget, release-state transition, or next-cycle initialization uses `intentional no-note`: its changelog edit records other commits or release-cycle metadata and must not add a self-referential entry. This exception requires the handler's exact approved hunk and grants no general changelog rewrite authority.

## Release Settlement

Before release QA, compare every commit and material changed surface after the previous release with the open section. For a user-confirmed first release with no stable tag or completed section, use the complete reachable history and current public surface instead. Merge duplicates and add, edit, or remove entries only before establishing the exact QA candidate. Obtain approval for the complete changelog diff and commit it through the repository's normal boundary.

After release QA passes, preserve every entry byte-for-byte. The release commit may replace `Unreleased` with the publication date and update deterministic links or version metadata. Any substantive entry change creates a new candidate and requires release QA again.

Build the hosted Release highlights from the settled changelog entries. Keep validation evidence in a separate hosted Release section instead of copying it into the changelog.

After publication is verified, ask the user for the next planned version. Opening its empty `Unreleased` section is a separate post-release commit and push with separate authority. If the user does not approve that action, finish the published release but report the missing next-cycle authority; later commits in the enrolled repository must stop until one open target exists.
