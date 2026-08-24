---
name: release-handler
description: "Prepare, validate, publish, or retarget one stable release with cumulative changelog settlement. Use when the user explicitly invokes $aquarium:release-handler for one intended version or planned next version."
---

# Release Handler

Own one stable release lifecycle without weakening repository release policy. Read [evidence-residency.md](../../references/evidence-residency.md), [release-notes.md](../../references/release-notes.md), and the repository's complete release instructions. Use `$aquarium:release-qa` for scenario QA and `$aquarium:task-commit` for every actual commit; neither leaf grants this workflow publication authority.

Explicit invocation authorizes read-only release discovery against the configured Git remote and hosting Releases through already-configured ambient authentication. It does not authorize credential inspection or changes, authentication, staging, commits, pushes, tags, hosted Releases, destructive tag or Release changes, or post-release next-cycle publication. Obtain each required authority at its actual boundary.

## Establish the Release

1. Resolve one Git root and inspect the worktree, conflicts, branch, `HEAD`, local and remote `main`, upstream, tags, hosted Releases, version authority, release-notes declaration, and repository release policy. Reconcile tags, hosted Releases, and completed release notes to establish the latest published stable version; stop when they do not identify one unambiguous latest stable baseline.
   Never fetch, merge, switch, stash, clean, or repair state while establishing the candidate. When a conforming target release commit or any matching publication object already exists, read [publication-recovery.md](references/publication-recovery.md) and classify it before applying ordinary pre-release stop rules.
2. Require one intended stable SemVer version greater than the established latest stable version. When the request is only to retarget the open cycle, verify that the target remains greater than that latest stable version and that no tag or Release exists for either target, show the exact changelog heading edit, obtain approval, apply only that edit, and run the release-notes inspector and documentation checks.
   Request separate commit and push authority, use `$aquarium:task-commit` with `intentional no-note` for the exact heading edit, and stop without QA or publication when either authority is withheld.
3. For publication, select the repository-defined full or light mode and obtain every confirmation its policy requires. Stop on a dirty or ambiguous candidate, divergent release refs, a conflicting target tag or Release, a target version not greater than the latest stable version, a baseline outside the candidate, or an unenrolled or invalid release-notes authority. A matching partial publication follows the recovery reference instead of restarting QA or recreating an existing object.
4. Resolve this skill's directory and run the release-notes inspector with `--expected-version <version>` plus exactly one established baseline: `--previous-release <latest-stable-tag>`, or `--first-release` after the user confirms that no stable tag or completed release exists. Treat its JSON as structural evidence only; independently inspect semantic coverage.

## Settle the Candidate Before QA

Compare every commit and material changed surface after the previous stable release with the open changelog section. For a confirmed first release, use the complete reachable history and current public surface with no regression baseline. Present one exact diff that merges duplicates and adds, edits, or removes only entries needed to describe shipped outcomes.

Obtain approval before applying it. When this creates a change, validate it and commit the exact approved preparation through `$aquarium:task-commit` with `intentional no-note`; the settlement commit must not add an entry about itself.

When the committed candidate is ahead of remote `main`, show its exact SHA and obtain separate pre-QA push authority. Push only `main`, verify that local, upstream, and remote refs agree, and otherwise stop before release QA. Every remediation candidate must pass the same authorized alignment before confirmation QA.

Require a clean committed `main` candidate where local, upstream, and remote refs agree before invoking `$aquarium:release-qa`. The handler's explicit release request is an authorized handoff for exactly one release-qa pass against the disclosed version and candidate. Preserve every release-qa convergence and confirmation boundary; never reinterpret a finding fix or focused check as a passing candidate.

When remediation changes a shipped outcome, update the open changelog entry in the same reviewed remediation commit. A new candidate follows the release-qa confirmation contract. Stop when QA is incomplete, findings remain, or the permitted confirmation does not pass.

## Create and Publish the Release

After QA passes, re-inspect the exact candidate and confirm that changelog entries are byte-identical to the passing candidate. Apply only repository-authorized release metadata: the published version, pinned validation expectation, the changelog heading's `Unreleased` to publication-date transition, and deterministic release links when the repository uses them. Any entry-text change invalidates QA and returns to candidate settlement.

Before running the selected repository release gate, show its exact commands and obtain separate explicit authority to execute them; selecting `full` or `light` does not itself authorize tests or other gate commands. If authority is withheld, leave the gate unrun and stop as incomplete.

Run only the approved gate commands and all required mismatch checks. Do not commit or publish when a required check fails or is missing. After explicit commit approval, create exactly one repository-conforming release commit through `$aquarium:task-commit` with `intentional no-note`. Preserve the exact QA candidate SHA, release commit and parent, QA result, and release-gate result in the active handler report, then obtain separate push and publication authority.

Publish in this order unless stricter repository policy overrides it:

1. push `main` and verify the exact remote release commit;
2. create an annotated target-version tag on that commit and push it;
3. create the hosted Release using the settled changelog entries as highlights and current gate evidence as a separate validation section;
4. verify remote `main`, the peeled tag, and hosted Release target the intended release commit.

Before every publication mutation and after every successful step, run `scripts/inspect_publication_state.py` with a fresh non-expanding `aquarium-release-publication-observation/v1` JSON observation. Perform only its one returned next action after obtaining that action's authority. A `matching` step is skipped, while `conflict` or `unproven` stops as `INCOMPLETE`. Never rewrite or delete a published tag or Release without explicit destructive-action authorization naming the exact objects.

## Open the Next Cycle

Only after publication verification, ask the user for the next planned stable version. Verify that it is greater than the published version and has no tag, hosted Release, or completed changelog section. The target is provisional and may later be retargeted through this skill with explicit approval.

Show the exact new empty `Unreleased` section and request separate commit authority. If approved, apply and validate it, create one non-release commit through `$aquarium:task-commit` with `intentional no-note`, then request separate push authority. If any authority is withheld, leave the published release complete, make no implied mutation, and report that enrolled commits must wait for an open target.

## Report

Return the intended version, mode, previous release or confirmed first-release baseline, every candidate and release commit SHA, changelog path and decision, release-qa result and evidence root, local gate commands and exit codes, publication-state classification and per-object status, push, tag, hosted Release and peeled-target verification, next planned version and its separate commit or gap, current Git state, and any remaining uncertainty.
