# Independent Review Contract

Use this contract for one static, read-only review through `$aquarium:independent-review` or its `$aquarium:orca-review` provider extension.

## Exact Target

Every review has one exact Git target and one review focus. Supported targets are:

- `staged`: `HEAD` plus the current index diff;
- `commit`: one resolved commit and its change;
- `range`: one explicit `A..B` or `A...B` expression;
- `task` or `epic`: the identifier's authorities plus one exact staged, commit, or range target;
- `special request`: a roadmap-independent question paired with a user-confirmed staged, `HEAD`, commit, or range target.

Dirty working-tree content is never a target. Define the dirty remainder as unstaged tracked files plus non-ignored untracked files. An unresolved conflict always stops target selection.

Run the canonical target inspector from the `independent-review` skill directory:

```text
python3 <independent-review-skill-directory>/scripts/inspect_review_target.py --repository <git-root> <target-option>
```

Use `--staged`, `--head`, `--commit <revision>`, or `--range <A..B|A...B>`. Its JSON proves Git structure and digests only; it does not establish task ownership, requirement coverage, or runtime behavior.

A staged review uses the live index in the original worktree, not an immutable snapshot. The inspector digest records the index observed before Dispatch; it is not a completion-time identity. Continue reviewing if the index changes after Dispatch, and do not detect drift or invalidate the result solely because later staged content differs from that digest. Content remains excluded while it is unstaged, and any content the user stages during the review may become visible as part of the live staged target.

For a task or epic, inspect the roadmap, requirements, decisions, handoffs, and commit references. Use an exact target without asking only when those authorities identify one unambiguous staged candidate, commit, or range. Otherwise present the concrete candidates and ask. Do not silently broaden the target to unrelated repository history.

For a special request, always ask the user to confirm staged, `HEAD`, one commit, or one range, even when the request suggests a likely target. Hide an unavailable staged choice. Preserve the user's two-dot or three-dot range semantics.

## Dirty Decision

When a selected staged target has a dirty remainder, show its exact paths and ask the user to choose:

- stage all displayed paths or an explicitly named subset and review the resulting index;
- exclude the dirty remainder and review the current index only; or
- cancel.

Prefer structured ask/answer and fall back to one focused conversational question when that surface is unavailable. Before staging, record the index diff digest and the approved paths. Recompute both immediately before mutation. Drift invalidates approval.

Stage only the approved paths with `git add -- <paths>`. Never use an unbounded `git add -A`, include ignored files, or infer approval for another path. Leave the approved index changes staged after the review and report them. Staging authorization grants no edit, commit, push, or publication authority.

For commit, range, and confirmed `HEAD` targets, exclude dirty content automatically and report it. For an excluded dirty remainder in the current checkout, instruct the reviewer to use index or commit blobs rather than working-tree copies. Disclose that a same-user reviewer can technically read excluded working-tree bytes even though they are outside its authorized scope.

## Consent and Review Focus

An explicit invocation that names an exact target and reviewer authorizes transmitting that review scope to that reviewer. A target-selection or reviewer-selection answer supplies the missing authorization. Ask again only when the target, included paths, reviewer, or execution scope changes before Dispatch. Do not require separate preparation and transmission approvals.

The review is static. Every participant remains read-only and runs no tests, builds, generators, formatters, linters, provider reviews, authentication commands, or unrelated network operations. Existing tests may be read as specifications. Treat a user's statement that tests passed as context, not independent evidence.

For a functionality question, trace requirements, production callers, state, persistence, concurrency, failure paths, tests, and documentation. Report whether the implementation is statically supported and label behavior requiring execution as `runtime unverified`; never convert static inspection into runtime proof.

## Result Contract

Require only verified actionable findings. Each finding includes severity, exact `path:line`, triggering scenario, violated authority, impact, and smallest remediation. Omit praise, style preferences, speculation, and duplicates. Return `APPROVE` only when no actionable finding remains, while still reporting scope and reviewer identity.

The coordinator independently checks every finding against the exact target and authority without running checks or changing files:

- **Valid**: confirmed and actionable;
- **Invalid**: contradicted by exact evidence;
- **Needs confirmation**: dependent on missing authority or runtime evidence.

Return the target kind and digest, included and excluded state, review focus, reviewer and backend, reviewer verdict, adjudicated findings, rejected count, confirmation needs, recommended responses, modified-file status, and separate backend lifecycle status. A lifecycle failure or wrong scope is operationally incomplete, never `APPROVE`.
