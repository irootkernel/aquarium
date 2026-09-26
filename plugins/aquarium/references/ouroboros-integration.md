# Ouroboros Integration Contract

Read this reference and [evidence-residency.md](evidence-residency.md) whenever `new-project`, `new-feature`, `refactor`, or `war-room` is explicitly invoked, including when Podway is opted out or unavailable. Aquarium owns repository authority, approvals, exact diffs, Podway orchestration, and final artifact application. Installed upstream Ouroboros skills and MCP tools are leaf capabilities: use them for requirements discovery, PM shaping, and QA, but do not copy, emulate, or silently replace them.

Support stable Ouroboros releases `>=0.51.1`. Before the first provider-backed operation, establish the installed CLI version, Codex skill health, MCP registration, and runtime readiness independently. Use the global v3 inspector's `current_home_readiness`, not `all_discovered_homes_readiness`. Require rules and skills in the current Codex home, the matching MCP package, and a `home_binding` to that same home; shared `~/.agents/skills` copies prevent readiness until migrated. A missing or degraded component blocks these Ouroboros-assisted workflows: record the evidence gap and offer repair through `$aquarium:dev-setup-global` or end the workflow. Do not continue without Ouroboros, install it, or refresh it from this workflow.

Configuration checks do not verify an already-running MCP process. After a home switch or registration update, report whether a restart or evidence of the running process's home is still needed. Do not infer quota recovery or clear a persisted pause from a configuration-only success. In 0.53, Seed QA is advisory; preserve the upstream interface without adding a mandatory QA-until-PASS loop.

## Keep Invocation Explicit

These four Aquarium skills are explicit-only. Their invocation authorizes only the displayed goal, repository or non-repository document scope, proposed provider operations, and proposed local writes. It does not authorize `auto`, `run`, `ralph`, or `evolve`, implementation work, external publication, authentication, installation, or transmission of a wider source set. Obtain fresh approval before widening any of those boundaries.

Use the smallest installed upstream capability that fits the phase: `$interview` for ambiguity and trade-offs, `$pm` for product requirements, `$seed` for a validated work specification when needed, and `$qa` for artifact quality. Keep upstream-generated files in the approved draft location outside the repository. Capture its output as draft evidence, verify it against repository authority, and present Aquarium's exact proposed diff before applying any durable document change.

### PM files and clipboard

Before invoking `$pm`, read its installed contract and disclose its native effects in the execution envelope. PM generates a document and seed handoff files, and its completion step copies the PM document to the system clipboard. Document approval alone does not authorize replacing the clipboard. Obtain authority for that distinct effect before invocation; do not read or save the previous clipboard contents.

Use a supported output or working-directory input to direct generated files to an approved disposable location outside the repository. Confirm the selected upstream operation supports that destination before starting. Record the expected files, any native session residue, and the cleanup boundary in the envelope. If the installed capability cannot honor the approved file or clipboard boundaries, stop that invocation and offer a compatible upstream capability or an explicit change to the envelope. Do not patch upstream files, invent a clipboard-disable option, or silently omit a required upstream step.

Treat returned paths as draft locations, verify them against the approved destination, and inspect the output before proposing canonical documents. Report unexpected writes and stop further mutation. After applying accepted text, remove only invocation-owned disposable drafts covered by the approved cleanup scope; leave native session retention to Ouroboros. Follow [evidence-residency.md](evidence-residency.md) for draft and runtime handling.

## Use Podway as the Outer Workflow

For a Git-backed invocation, use Podway by default through [podway-integration.md](podway-integration.md). `new-project`, `new-feature`, and `refactor` use `aquarium-design-v2`; `war-room` uses `aquarium-war-room-v2`. Use the canonical work identity directly without a skill-name prefix. No Aquarium skill owns the session. The current Aquarium invocation observes and advances it while Ouroboros remains Podway-blind and returns only leaf evidence to its caller.

A non-Git `new-project` invocation must not inspect, initialize, or mutate Podway and must not create a Git repository merely to enable Podway. It still follows the same approval and exact-diff rules for its requested output files.

Before the first provider call, show one execution envelope containing canonical identity, current authority, bounded source inputs, every planned Ouroboros operation, every planned Podway mutation, target document paths, and excluded actions. Obtain explicit approval, then create or resume the matching prepared session, re-observe it, begin attempt 1 with the approved goal, and coordinate with an explicitly requested host goal under its own creation and lifecycle rules.

Record bounded identifiers, digests, paths, decisions, and evidence gaps in Podway, not full provider prompts, transcripts, source payloads, or generated documents. Verify every provider result locally before recording it. Complete and disposition a session as `handed_off` only after the exact approved repository artifacts, their digests, repository status, and any authoritative commit required by repository policy are verified. Name the next explicit Aquarium skill when follow-up work is needed and include the exact session ID, revision, and stable artifact reference in that handoff. Otherwise leave the terminal session undisposed.

When a later task, epic, or validation workflow needs a different Podway session, follow the existing-session choice in [podway-integration.md](podway-integration.md). Preserve the current session unless the user explicitly authorizes its lifecycle action, deletion, or eligible replacement; never route by prior skill ownership.

## Propose Before Applying

All four workflows must separate draft production from repository mutation:

1. Discover authority and create a draft without repository writes.
2. Run the applicable Ouroboros quality pass and adjudicate its output locally.
3. Show the exact target paths and complete proposed diff.
4. Obtain explicit user approval for that exact diff.
5. Re-read the target snapshot, invalidate approval if it changed, apply only the approved diff, and run document validation.

No approval is implied by skill invocation, provider approval, prior plan approval, or approval of a different file.

## Interpret QA Outcomes

Keep the upstream artifact verdict and the quality operation outcome separate.
Preserve the raw `PASS`, `REVISE`, or `FAIL` verdict with the exact draft identity
in `quality-summary`. A completed QA operation with output that can be adjudicated
locally records a `pass` check result, including when the artifact verdict is
`REVISE` or `FAIL`.

Record every locally valid unresolved issue in the matching discovery/draft or
investigation/proposal count and list. Select the existing owner route and correct
that evidence or draft before another QA pass. Do not convert artifact `FAIL`
into an operational failure that repeats QA on unchanged input. Zero owner counts
require a documented disposition for every issue; they cannot discard the raw
verdict. Quality acceptance and user approval remain separate.

Failed invocation, missing output, or output that cannot be adjudicated records
`fail` or `inconclusive` with the actual evidence gap. Only supported, authorized
operation recovery may retry unchanged input. A missing recovery path stops the
operation with its exact blocker.

## Commit Approved Delivery Input

After applying the approved documentation diff, report either committed delivery
input or applied documents awaiting commit. If repository policy requires a
commit before delivery, prepare the exact documentation, lifecycle, record, and
release-note candidate and obtain separate one-commit authority. Reuse an existing
grant for that exact candidate; approval of the document diff alone does not
authorize a commit. Hand the accepted candidate to `$aquarium:task-commit` using
its design or diagnostic delivery-input handoff. State explicitly when no task
or epic applies and retain the owning workflow's quality and approval evidence.

Verify the accepted bytes, Git identity, returned commit, and remaining worktree
state before reporting committed delivery input or recording `handed_off`. Without
the required commit authority, preserve the applied documents and leave terminal
disposition pending. The next action is the explicit commit boundary, not
implementation. When repository policy requires no commit, report that boundary
and verify the approved artifacts before disposition. An approved no-change
war-room outcome needs no artificial commit; use `not_required` after verifying
that no durable artifact is owed. Non-Git outputs remain non-Git. A design or diagnostic commit grants no authority to implement, push, or publish.
