# Ouroboros Integration Contract

Read this reference whenever `new-project`, `new-feature`, `refactor`, `war-room`, or `design-qa` is explicitly invoked. Aquarium owns repository authority, approvals, exact diffs, Podway orchestration, and final artifact application. Installed upstream Ouroboros skills and MCP tools are leaf capabilities: use them for requirements discovery, PM shaping, and QA, but do not copy, emulate, or silently replace them.

Support only Ouroboros `>=0.51.1,<0.52.0`. Before the first provider-backed operation, establish the installed CLI version, Codex skill health, MCP registration, and runtime readiness independently. A missing or degraded component blocks these Ouroboros-assisted workflows: record the evidence gap and offer repair through `$aquarium:dev-setup` or end the workflow. Do not continue without Ouroboros, install it, or refresh it from this workflow.

## Keep Invocation Explicit

These five Aquarium skills are explicit-only. Their invocation authorizes only the displayed goal, repository or non-repository document scope, proposed provider operations, and proposed local writes. It does not authorize `auto`, `run`, `ralph`, or `evolve`, implementation work, external publication, authentication, installation, or transmission of a wider source set. Obtain fresh approval before widening any of those boundaries.

Use the smallest installed upstream capability that fits the phase: `$interview` for ambiguity and trade-offs, `$pm` for product requirements, `$seed` for a validated work specification when needed, and `$qa` for artifact quality. Do not let Ouroboros create or edit repository files directly. Capture its output as draft evidence, verify it against repository authority, and present Aquarium's exact proposed diff before applying any durable document change.

## Use Podway as the Outer Workflow

For a Git-backed invocation, use Podway by default through [podway-integration.md](podway-integration.md). `new-project`, `new-feature`, `refactor`, and `design-qa` own one `aquarium-design-v2` session; `war-room` owns one `aquarium-war-room-v2` session. Prefix the canonical session identity with its owner as `<owner-skill>:<canonical-identity>` so two owners cannot resume each other's session even when their work-unit IDs match. The Aquarium skill observes and advances the session. Ouroboros remains Podway-blind and returns only leaf evidence to its caller.

A non-Git `new-project` invocation must not inspect, initialize, or mutate Podway and must not create a Git repository merely to enable Podway. It still follows the same approval and exact-diff rules for its requested output files.

Before the first provider call, show one execution envelope containing canonical identity, current authority, bounded source inputs, every planned Ouroboros operation, every planned Podway mutation, target document paths, and excluded actions. Obtain explicit approval, then create or resume the matching prepared session, re-observe it, begin attempt 1 with the approved goal, and mirror only the current actionable goal into the host goal mechanism.

Record bounded identifiers, digests, paths, decisions, and evidence gaps in Podway, not full provider prompts, transcripts, source payloads, or generated documents. Verify every provider result locally before recording it. Complete and disposition a session as `handed_off` only after the exact approved repository artifacts, their digests, current Design Gate state, repository status, and any authoritative commit required by repository policy are verified. Name the next explicit Aquarium skill and include the exact session ID, revision, and stable artifact reference in that handoff. Otherwise leave the terminal session undisposed.

A later `design-qa`, task, epic, or validation owner must not resume the predecessor's owner-prefixed session. It follows the cross-owner protocol in [podway-integration.md](podway-integration.md): disclose replacement in its own envelope, verify the disposed predecessor artifacts again, and use only the fresh eligible replacement template after approval.

## Propose Before Applying

All five workflows must separate draft production from repository mutation:

1. Discover authority and create a draft without repository writes.
2. Run the applicable Ouroboros quality pass and adjudicate its output locally.
3. Show the exact target paths and complete proposed diff.
4. Obtain explicit user approval for that exact diff.
5. Re-read the target snapshot, invalidate approval if it changed, apply only the approved diff, and run document validation.

No approval is implied by skill invocation, provider approval, prior plan approval, or approval of a different file.
