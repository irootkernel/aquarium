# Safety and Evidence Contract

Aquarium coordinates capable tools without collapsing their authority. It treats user intent, repository state, runtime state, evidence quality, Git history, and publication as separate facts.

## Authority Owners

| Concern | Canonical owner | What it does not prove |
| --- | --- | --- |
| Requirements, epic/task identity, lifecycle, and completion state | Canonical roadmap | Implementation, test success, commit, or publication |
| Current source and durable implementation history | Git worktree, index, commits, and refs | Runtime completion or external deployment |
| Active goal projection | Codex goal | Roadmap status, commit existence, or Podway truth |
| Managed workflow transitions and handoffs | Podway session and immutable Procedure snapshot | Semantic truth of tests, reviews, approvals, or completion |
| Command pass or fail | Child process exit code | Coverage outside the mapped requirement set |
| Review capture and findings | Mulgae or Orca native artifacts | Local validity of a reported finding |
| Compressed test evidence | Gaori native run | A new test gate or altered child result |
| Current product contracts | Specifications, source-owned references, public policies, and executable authorities | Delivery history or transient workflow detail |
| Release state | Version authority, CHANGELOG, exact commit, tag, remote main, and hosted Release | Runtime installation or activation |

## Separate Approval Boundaries

Read-only diagnosis does not authorize network lookup unless the owning workflow explicitly grants a bounded lookup. Lookup does not authorize download, installation, configuration, or execution.

Provider selection and an exact review target authorize only the disclosed source transmission and static review. Authentication, model discovery, retries, tests, remediation, staging, commits, pushes, tags, Releases, and destructive actions retain separate authority.

An approved implementation envelope covers routine bounded decisions inside its stated requirements and checks. It does not widen repository scope, add new product requirements, authorize another repository, or permit destructive or publication effects.

## Evidence Classes

- **Canonical evidence** is current code, tests, specifications, roadmap state, Git history, release metadata, and other repository-owned durable authority.
- **Runtime evidence** is native Mulgae, Gaori, Podway, Orca, provider, or disposable-fixture output used during an active workflow.
- **Promoted evidence** is an exceptional reviewed, bounded, non-sensitive structured projection created only for a named downstream consumer when canonical evidence cannot express the required fact clearly enough.

Ignored runtime logs, excerpts, transcripts, reports, provider stdout or stderr, session identities, timestamps, usernames, home paths, credential paths, and Podway databases never become tracked documentation. A standard promoted package uses schema `aquarium.promoted-evidence/v1` below `evidence/aquarium/` unless repository guidance declares another relative root.

## Review Evidence

A review is operationally complete only when its target digest and kind are exact, coverage is complete, CI decision passes, publication is committed, the findings query succeeds, and every returned finding has a local disposition. Structured extraction status is an independent quality axis and does not replace accepted reports or completion conditions.

Provider findings are hypotheses. Aquarium checks them against current requirements, code, callers, tests, and ownership before remediation or deferral. A changed target makes prior review evidence stale unless the owning contract explicitly permits the narrow change.

## Check Evidence

Repository instructions and task runners select required commands. Gaori may wrap a known command but never chooses an unknown gate, changes authorization, or replaces the child exit code.

Skipped, forbidden, missing, or side-effectful checks remain explicit gaps. A missing prerequisite fails a complete enrolled gate rather than becoming a successful skip.

Development checks establish development-contract evidence. Distribution readiness additionally requires the release owner's exact clean candidate, required distribution gate, reconciled metadata, and verified published artifacts.

## Privacy and Sensitive State

Inspectors exclude known environment, credential, authentication, key, secret, token, binary, oversized, ignored, and symlinked inputs according to their contracts. Reports return normalized status, paths only when necessary, category counts, identifiers, and reason codes rather than raw sensitive contents.

Same-user processes are not operating-system sandboxes. Aquarium's scope restrictions are authorization and instruction boundaries, so repository and organization policies remain authoritative.
