# Review strategies and goal preservation

Use this contract when recommending a route, assigning reviewer focus or
adjudicating findings. [Routing](review-routing-contract.md) owns selection and
lifecycle; [review intent](review-intent-contract.md) owns the Brief and criteria.

## Recommend from the actual work

At Task/Epic handler or validator startup, read the original goal, scope and due
obligations. When no route is already selected, recommend one with a concrete
reason in the existing plan or validation envelope:

| Route | Starting point and purpose |
| --- | --- |
| `mulgae` | Small, bounded work. Narrow specialist scopes let economical models focus; aggregate assigned coverage against the whole goal. |
| `subagent-review` | Medium work needing independent judgment from fresh reviewers of similar capability in the Coordinator's current harness. |
| `herdr` | Large work, difficult integration or consequential uncertainty where another AI family's judgment justifies coordination cost. Prefer Codex to Claude or Claude to Codex. |

Adjust for difficulty, consequences, uncertainty and purpose. A small critical
change can justify Herdr; broad mechanical work can justify a lighter route.
File count, lines changed and domain labels alone do not decide. Role count
establishes neither model diversity nor greater assurance.

The user chooses through existing plan or envelope approval. Honor an explicit
route, reviewer, supported model and effort, and repository authority. An
explicitly named same-family Herdr reviewer remains usable; describe the actual
topology without claiming cross-family review. Check only the selected route's
prerequisites and preserve the selection across checkpoints. Unavailability
uses existing recovery or authorized switching, not automatic fallback.
Standalone invocation already selects its named route.

## Preserve the intended outcome

Give reviewers the original Epic/Task goal, due requirements and accepted
constraints. Treat findings as hypotheses until readable source, contract or
other authorized evidence supports an applicable requirement and reachable
failure or user impact. Runtime reproduction is useful when needed, not a
universal admission requirement. Preserve real correctness, security,
data-integrity and native-contract defects and missing required evidence.

Optional future hardening and aesthetic preferences do not become blockers by
being mentioned. Assess the defect separately from its suggested remedy. If a
remedy unnecessarily disables required behavior, retain the valid defect and
seek a correction that preserves the goal. A genuine conflict between required
functionality and a binding constraint needs an explicit product decision;
silently deleting functionality cannot establish completion.

Apply parent-Epic constraints without demanding unfinished future members
prematurely. Use existing disposition and local settlement; do not add another
assessment merely to repeat a settled judgment.

## Add UI/UX expertise where relevant

Determine UI relevance from the actual goal and user interaction, including
navigation, forms, loading, empty and error states, or backend changes affecting
those flows. File extensions alone do not decide.

- Mulgae keeps configured specialist roles and native `artist` when applicable.
  Preserve provider/model choices; Aquarium does not rewrite producer
  configuration or require every role to repeat the full audit.
- Subagent Review keeps three base reviewers and adds one UI/UX specialist.
- Herdr's main reviewer uses multiple native subagents and includes a UI/UX
  specialist in addition to its code-review team when relevant.

Supply original goals, accepted design references, available actual screen
evidence and relevant code. Assess usability and due UI requirements separately
from preference. Report what was read and what remains unavailable; code
inspection alone is not visual verification. Keep code, integration and test
coverage alongside UI expertise. Use native concurrency waves as needed; the
required team remains one operation and one completed assessment ordinal, with
no automatic second route for UI.
