---
name: task-commit
description: "Create one authorized commit for an approved Aquarium handler handoff, an explicit $aquarium:task-commit request, or a direct commit subject to the repository's Aquarium roadmap gate. Preserve unrelated work and reconcile task lifecycle only when applicable."
---

# Task Commit

Read [commit-attribution.md](../../references/commit-attribution.md) for message formatting and change origins, within this skill's existing effect boundaries.

Create one authorized commit through a shared roadmap-aware boundary. Read [evidence-residency.md](../../references/evidence-residency.md), [finding-disposition.md](../../references/finding-disposition.md), and [release-notes.md](../../references/release-notes.md). This skill owns commit preparation and execution, including one release-note hunk accepted as exact text through direct approval or a valid handler handoff, not implementation evidence, task completion judgment, Podway mutation, publication, or release.

## Establish the Commit Boundary

1. Resolve the Git root and read all applicable instructions, commit conventions, branch and upstream state, staged, unstaged, untracked, and conflicted changes.
2. Establish roadmap enrollment from tracked candidates: paths whose basename or directory contains `roadmap` and whose content defines lifecycle states such as `In Progress`, `In Review`, `Completed`, `Blocked`, or `Deferred`. Read the relevant task entries and their exact vocabulary.
3. Resolve effective Git identity under the repository's rules. In a repository with a roadmap, require non-empty winning `user.name` and `user.email` values from `local` or `worktree` scope; matching system, global, or command values do not satisfy that requirement. Record their exact values, scopes, and origins. Without a roadmap, follow native Git and repository identity rules, including permitted global configuration, and snapshot the resolved author and committer identities. Do not create `.aquarium`, another identity file, or a duplicate configuration owner.
4. Inspect the current Codex goal. When Podway was not explicitly opted out for the managed workflow, inspect only the bounded current-session facts needed to reconcile the commit with active Aquarium work. The commit boundary itself does not mutate Podway, but the same Aquarium caller may record the verified post-commit disposition immediately afterward.
5. Record the requested commit scope and authority. A request to commit authorizes neither amend, push, PR changes, release work, destructive actions, nor unrelated staging.
6. Inspect Project Configuration for the exact `Aquarium release notes: <repository-relative-path>` declaration. When enrolled, run the release-handler's read-only inspector and require exactly one structurally valid open target unless the commit is the release commit that closes it or the separately approved post-release commit that opens its successor.

When a commit belongs to active Podway-managed Aquarium work, require an explicit commit handoff from the current Aquarium execution context. Accept it regardless of which Aquarium skill started or advanced the session; never require returning to a prior skill. A standalone `task-handler` or `task-close` handoff uses actual user acceptance and direct one-commit authority under its existing Task workflow, even when the Task belongs to an Epic.

For normal completion of a member Task executed under an approved `epic-handler` envelope, require that unchanged envelope's member grant and the coordinator's delegated acceptance of the exact candidate. For an owned correction, including a reopened Task or pre-validation correction, require that envelope's explicit correction grant or separate direct authority. Final Epic closeout requires actual user acceptance of the complete Epic result and exact closeout candidate plus the envelope's conditional closeout grant or direct authority. Preserve the acceptance source, authority reference, exact candidate, and applicable unconsumed grant. Never record a delegated acceptance as a user decision, reuse a consumed grant, or ask for another commit approval when the handoff already carries current acceptance and authority.

For a validation-remediation commit, require the invoking workflow's explicit one-commit grant for the owned correction group: the continuing Epic execution envelope's correction grant, the independently approved `epic-validator` envelope, or separate direct authority. Require acceptance of its exact verified diff by the user or under their current delegation. Bind it to the active validation session, source audit or review findings, owner, affected checks, and pending whole-Epic confirmation. A correction commit precedes that confirmation and does not establish completed Epic acceptance. A normal member-Task grant alone cannot authorize it.

## Reconcile Roadmap Context

When the commit is outside managed workflow work:

- If no roadmap candidate exists, follow repository commit rules without inventing a task relationship or lifecycle edit.
- If no `In Progress` or `In Review` task exists, do not invent one. Preserve existing terminal states and proceed only with the user's commit scope.
- If one or more `In Progress` or `In Review` tasks exist, always ask whether the commit belongs to one exact task or is unrelated to every listed task. Never infer the relationship from changed files, branch names, commit text, goals, or conversation context. With multiple candidates, require an exact task ID. Allow the user to cancel. The initial commit request does not satisfy this dedicated confirmation, even when it already names a task or checkpoint; first show the current candidates, status, and exact proposed scope.
- For an unrelated commit, preserve every task status exactly and exclude unrelated roadmap edits from the commit unless separately authorized.
- For a selected task already in a roadmap-defined terminal state, preserve that state. For a selected non-terminal task, show the exact current status and require the user to select one roadmap-defined terminal state, explicitly authorize a checkpoint commit that preserves the exact current status, or cancel. Offer only terminal states the roadmap actually defines, including `Completed`, `Blocked`, or `Deferred` when present. Never choose a terminal state for the user. When the roadmap defines none, offer only the explicit checkpoint and cancel paths.
- Treat checkpoint authorization as one-commit authority only. Report that the task remains active, do not represent the checkpoint as closeout, and reconcile lifecycle state again on every later commit request.

A handler commit handoff must include:

- the verified `change-origin` and its fully qualified `workflow-owner` under the shared attribution contract;
- repository, canonical roadmap path, exact task or epic ID, exact commit scope, and the authorization source: direct user one-commit authority; the Epic envelope's applicable member, correction, or conditional closeout grant; or the independent validation envelope's owned-correction grant. An `epic-handler` handoff also names `acceptance-source` (`user` or `epic-delegation`), its recoverable `acceptance-authority`, exact `accepted-target`, and the applicable unconsumed grant;
- the lifecycle decision as either an exact approved edit or an explicit statement that no lifecycle edit applies;
- the record decision as either an exact approved edit or an explicit statement that no record edit applies;
- verification and review evidence identifying command, actor, exit status, exact reviewed and final target identities, verdict, `review-route`, `review-operation`, `review-evidence-reference`, `backend-check-result`, `assessment-provenance`, consumed `assessment-ordinal` and `assessment-kind` when applicable, and waiver summary when applicable. Include a Mulgae run only for the Mulgae route; mark every inapplicable route-specific field explicitly rather than inventing an identity.
- the complete Low-settlement composition defined by the shared finding-disposition contract, or an explicit statement that no accepted Low-only delta applies;
- the release-note decision as exact `entry` text already present in the accepted diff, `intentional no-note`, or `not-enrolled`; delegated Epic acceptance must cover that exact decision and any entry bytes, while final Epic closeout requires actual user acceptance;
- zero or more staged promoted-evidence manifest paths paired with exact `sha256:<64-hex>` manifest digests and the owning workflow's current native-evidence, native-target-digest, and copied-projection validation result, or an explicit statement that no promoted evidence applies;
- for an epic member task with a hardening deferral, the exact current Mulgae run and finding IDs, committed publication, successful findings query, exact finding membership, authoritative native target digest, and promoted-manifest digest used for pre-commit verification. Every Orca, Independent Review, or waiver handoff must instead state explicitly that no hardening deferral applies because those routes cannot supply the required native digest, publication, findings-query, and membership evidence.

Reject a stale, ambiguous, or incomplete handoff rather than reconstructing approval.

A validation-remediation handoff identifies the source assessment separately from the pending assessment of corrected bytes. Before the first delegated review, carry the exact direct-audit evidence and explicitly mark the source review fields inapplicable. After a review, carry its actual route, operation, ordinal, and findings. In both cases, include the exact correction scope, verification, lifecycle and record decisions, release-note decision, candidate acceptance, and remediation commit authority. Do not require a per-group provider review or represent source findings as review coverage of the correction. Final validation acceptance remains pending until the owning workflow completes its whole-Epic assessment.

A design or diagnostic delivery-input handoff uses the same fields, retains its verified `change-origin`, and names its owning workflow and current session when present. If no task or epic applies, record that relationship explicitly instead of inventing an ID; when no roadmap exists, mark its path inapplicable. Preserve the actual design or diagnostic quality evidence and mark Task-review-specific fields inapplicable. Require separate one-commit authority and exact candidate acceptance; this variant carries no member-Task commit grant.

A release-handler commit handoff must retain its verified `change-origin` and name the repository, intended and previous versions, exact operation (`settlement`, `retarget`, `release`, or `next-cycle`), changelog path and approved hunk, exact commit scope, `intentional no-note`, applicable QA and release-gate evidence or their explicit inapplicability, and the user's one-commit authorization. It grants no push, tag, hosted Release, destructive replacement, or later commit authority.

For a direct commit following a separately completed Aquarium workflow, consume its verified `change-origin` without treating that result as commit authority. Recheck the origin against the intended diff and keep its original skill; do not replace setup or design origins with `task-commit`. An unavailable or stale supplied origin must be resolved before committing. Existing direct-commit relationship and release-note approvals still apply.

For a direct commit without a managed-workflow handoff, inspect the complete intended diff and require the user to approve one exact concise entry or `intentional no-note` when release notes are enrolled. If an entry is needed but absent, show one proposed changelog hunk and obtain approval before applying it.

Apply no other documentation change, re-run the release-notes inspector and applicable documentation check, and treat the resulting hunk as part of the final commit scope. Exact-candidate approval that did not include those bytes is stale. For an unenrolled repository record `not-enrolled` and do not create or infer an authority.

## Prepare the Exact Commit

Apply only the lifecycle or record edit explicitly selected by the user or supplied by a valid handler handoff. Preserve the selected task's exact current state for an approved checkpoint. Any candidate change after acceptance or its handoff makes that exact-candidate acceptance stale. For delegated Epic work, return the changed candidate to `epic-handler` for fresh evidence and acceptance within the current grant; do not demand user acceptance merely because the candidate changed. Direct user acceptance and final Epic acceptance must be renewed by the user when their accepted candidate changes.

Require the release-note decision to match the final diff. An `entry` must appear exactly once under the current open target in the authorized changelog path. `intentional no-note` normally permits no changelog edit, and `not-enrolled` is valid only when no authority is declared.

With an exact `$aquarium:release-handler` handoff, `intentional no-note` may include only the approved settlement, open-target retarget, release heading transition with unchanged entry bytes, or empty next-cycle section. Reject a stale target, missing decision, mismatched entry, self-referential settlement entry, unapproved note edit, or rewrite of completed release history.

Stage only the authorized paths or hunks. Preserve unrelated staged and unstaged work; stop if the commit scope cannot be isolated safely. Immediately before committing, re-read the staged roadmap entry, `git diff --cached`, staged tree and blob identities, and full Git status. Confirm that:

- the applicable identity snapshot still matches: repository-specific `user.name` and `user.email` with scopes and origins when a roadmap is present, otherwise the resolved native author and committer identities;
- the selected task relationship and approved terminal or unchanged-checkpoint status still match the user's answer;
- the handler handoff's lifecycle or record edit, including an explicit absence, still matches the staged snapshot;
- a declared unrelated commit contains no unintended task lifecycle transition;
- for a completion commit, the reviewed implementation plus any exact accepted and locally verified Low-only delta, accepted lifecycle or record decision, and accepted post-review promoted-evidence packages equal the staged diff; for a validation-remediation commit, the accepted verified correction and its explicitly approved decisions equal that diff while whole-Epic confirmation remains pending;
- unrelated pre-existing staged content is absent from the intended commit.

For an explicitly authorized amend, inspect the existing HEAD's parent, author, message, complete diff, and live remote publication state. Require one unambiguous unpublished HEAD whose existing content and staged delta both belong to the approved replacement. Record the intended full staged tree, parent, author, and message before amending. Stop if publication cannot be ruled out, the existing commit includes unrelated work, or the replacement scope is unclear.

An accepted Low-only composition may differ from the provider-reviewed target only
by its enumerated verified delta. Do not require or launch another provider review
for that difference. Reject an unknown source basis, nonzero pending disposition or
current blocker count, failed or stale local check, mismatched final target, or any
extra path or hunk. This commit skill never owns review dispatch.

Before a non-trivial commit, reference `$lore-commits` and follow it when available. Repository-required IDs and prefixes override Lore, which never grants commit authority. If Lore is required but unavailable, stop and return an exact `$aquarium:dev-setup-global` continuation request. Otherwise report its absence once and use the shared message format with the three required attribution trailers; history does not choose a conflicting format.

When a handler handoff includes one or more promoted-evidence packages:

- Resolve the evidence root from the applicable repository `AGENTS.md` Project Configuration or use `evidence/aquarium/` when none is declared. Require one unambiguous repository-relative tracked root; reject ignored, outside-repository, or symlinked roots and paths.
- Require each manifest to use `aquarium.promoted-evidence/v1`, contain no runtime identity, match an approved purpose and work unit, bind the owning workflow's supplied verified native target SHA-256 and capture-time Git object ID, and list only staged regular non-symlink payloads beneath its package directory. Reject a missing, stale, or mismatched owning-workflow validation result and prohibited private content under the shared contract.
- Recompute every staged payload digest and the staged manifest digest. Require the supplied digest to use exactly one `sha256:` prefix and match the exact `manifest.json` bytes. Reject any path, byte, target, schema, content, or digest mismatch.
- Reject any staged modification, replacement, move, or deletion of an existing tracked package. A changed package uses a new directory named by the verified native target digest.
- Add one repeatable `Aquarium-Evidence: <repository-relative-manifest-path> sha256:<64-hex-manifest-digest>` Lore trailer per unique package in supplied order.

When the same handoff also includes a hardening deferral, reference `$use-mulgae` and use only read-only exact-run status and findings queries. Require committed publication, a successful findings query, exact membership of every supplied finding ID in the supplied run, and equality between the native reviewed target digest and the promoted manifest. Reject an unavailable run, mismatched or duplicate finding, uncertain query, or deferral metadata from any caller other than the owning epic-handler.

Never add new `Mulgae-Deferred-Run` or `Mulgae-Deferred-Finding` trailers. Do not copy finding descriptions, recommendations, severities, paths, reports, provider or model identities, runtime identities, or private native artifacts into the commit message. When the handoff explicitly says that no promoted evidence applies, add no `Aquarium-Evidence` trailer.

Before committing in a Sanho-managed repository, reference `$use-sanho` and follow its commit-boundary workflow when available. If unavailable and required, stop and route the global skill gap to `$aquarium:dev-setup-global`; otherwise use the repository-required check or minimal `sanho status --json` fallback. Sanho status never grants commit authority.

## Prepare the Commit Message

Apply the shared attribution contract to the exact accepted candidate. Preserve the verified originating workflow, resolve the selected Task's parent Epic from the staged canonical roadmap, and show the complete subject, optional body, and single trailer block. Use `none` only for an established absence. A direct commit with no original Aquarium workflow records `aquarium:task-commit`.

Before executing the commit, parse the prepared message with `git interpret-trailers --parse` and require exactly one of each expected `Aquarium-Workflow`, `Aquarium-Epic`, and `Aquarium-Task` value. Keep all required evidence and native provenance in the same final block. Reject an unparsed, duplicate, conflicting, or stale field before committing; never add a commit just to record attribution.

## Commit Through the Gate

In a repository with a roadmap, bind the exact identity snapshot values to task-scoped `aquarium_commit_name` and `aquarium_commit_email` variables. Run exactly one direct commit with all author and committer environment overrides removed, all six Git identity keys pinned to the repository identity at command scope, and the hook marker scoped to that process:

```bash
env \
  -u GIT_AUTHOR_NAME \
  -u GIT_AUTHOR_EMAIL \
  -u GIT_COMMITTER_NAME \
  -u GIT_COMMITTER_EMAIL \
  AQUARIUM_COMMIT_GATE=task-commit-v1 \
  git -c user.name="$aquarium_commit_name" \
      -c user.email="$aquarium_commit_email" \
      -c author.name="$aquarium_commit_name" \
      -c author.email="$aquarium_commit_email" \
      -c committer.name="$aquarium_commit_name" \
      -c committer.email="$aquarium_commit_email" \
      commit ...
```

The explicit `author.*` and `committer.*` pins prevent system, global, local, worktree, or conditional configuration from overriding the repository `user.*` snapshot. Do not pass `--author` or otherwise override the pinned author or committer identity. The marker signals only that this skill completed the checks above. Never export it globally, use it outside this skill, or treat it as authority. Do not amend or push without separate explicit authorization.

Without roadmap enrollment, create the one authorized commit using native Git and the repository's commit rules. Do not impose the roadmap gate's local-identity requirement, identity pins, or marker. Verify its actual author and committer against the previously resolved native identities.

After the commit and its hooks, parse the actual committed message again and verify the expected subject and all three attribution values, permitting supported native provenance additions. A mismatch is an incomplete result with an existing commit; report it without automatically amending or creating another commit. Compare a new commit's diff with the recorded staged diff byte-for-byte. For an amend, compare the replacement tree with the recorded full staged tree and the staged delta with the approved change. Read `%an%x00%ae%x00%cn%x00%ce` from the new commit and require both author and committer to match the identity snapshot exactly. Do not amend an identity mismatch automatically. Also verify the release-note decision and every expected promoted-evidence trailer and committed manifest/payload digest, inspect staged, unstaged, and untracked state for residue or hook changes, and refresh the applicable Sanho status.

For an amend, also verify that the replacement commit has the recorded parent, author, and message.

Finish after the checks above when the current request is limited to a commit or amend. Choosing a commit method neither approves nor cancels later checks. Compare the user's current direction with prior authorization and the owning workflow's requirements. Run a previously approved check when its authority remains current; if the user limits the request to the commit, report the check as pending. A new commit SHA alone does not start a release or compatibility gate.

Report the commit ID, verified workflow, Epic and Task attribution, task relationship, final roadmap state, release-note target and decision, committed paths, checks and evidence inherited from the owner, evidence trailer state when applicable, remaining worktree state, and publication gap.

The bundled hook is a local guardrail, not complete enforcement: it detects direct shell `git commit` invocations in roadmap repositories, while indirect commits performed by other tools may not pass through that boundary.
