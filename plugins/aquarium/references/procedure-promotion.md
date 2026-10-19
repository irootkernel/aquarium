# Reusable Procedure preservation

After actual successful use, the Coordinator compares useful whole Procedures and
fragments with the repository's optional library. A successful start, source
check or unit result alone does not establish successful operation or future
usefulness. Use the original ordinary results to explain both, retain observed
limits and normally group candidates at Task or Epic closeout. Preservation is
optional and never blocks the original goal.

The source-only [promotion helper](../shared/promote_adaptive_procedure.py)
prepares the exact content to show Master. It never dispatches agents, advances
Podway, stages or commits. Existing applicable source-review and acceptance
policies still apply; preservation adds no routine Evaluator cycle.

## Closeout callers

At Task closeout, the Coordinator checks actual used definitions for successful
operation and distinct future usefulness, prepares exact eligible whole or
fragment candidates, and invokes `offer` below. Present the grouped content with
the closeout result. An Epic Coordinator normally gathers member, Goal and Validation
candidates for its final presentation instead of interrupting ordinary member
delivery. Design and Diagnosis use their final result presentation. With no
eligible used definition, including a non-Git or opted-out workflow that used no
Procedure, skip preservation before helper or native discovery.

Ask which exact candidates to preserve, allowing no or partial consent, and
whether a separate matching promotion commit is authorized. Keep that answer
separate from original acceptance and carry it in the ordinary closeout handoff.
The offer is read-only; content consent may be obtained at this presentation.
Apply only after the original accepted commit or verified no-commit result and
required native finalization. Declining or a promotion failure preserves original
completion and local recovery. This adds no Evaluator, review team or Procedure node.

## Offer

Run an available supported Python environment with YAML and `jsonschema`:

```text
<python> -B <plugin-root>/shared/promote_adaptive_procedure.py offer --repository <worktree> --input <closeout.json> --podway <supported-binary>
```

`--input -` reads JSON from standard input. The ordinary closeout input contains:

- `origin`: true `workflow`, `epic`, `task` and original assignment `reference`.
  Use the existing `none` relationship when no Task or Epic applies.
- `library_root`: the approved repository-relative reusable source root, normally
  `.podway/procedures/reusable`.
- `candidates`: distinct entry `name`, `kind` (`whole` or `fragment`), `future_use`,
  observed `limits`, and `use` with `outcome: successful`, actual result
  `reference` and operation `evidence`. These remain ordinary evidence for the
  Coordinator to assess; labels cannot authenticate execution or usefulness.
- Each `source` and `binding` reference has `path` and exact `sha256`. A whole
  uses its full source and closed binding. Set `transformed: true` for a changed
  or parameterized whole. A fragment's `binding` belongs to its representative;
  `representative` contains `source` and the exact ordinary composition `draft`
  importing this fragment, including static mapping and parameter inputs.

The offer reads existing entries and diagnoses unrelated damaged material.
Duplicate comparison includes whole source plus binding, or fragment plus static
mapping. Distinct mappings can be distinct candidates. Existing entries are
preserved; the helper publishes a new named entry rather than overwriting one.
Reuse an existing equivalent entry when available. A separate requested library
edit follows its existing exact-diff workflow.

For a whole, the payload is `procedure.yaml` and `binding.json`. A fragment has
`fragment.json`, `mapping.json`, `representative.yaml` and
`representative.binding.json`. The representative must actually flatten the
selected exact fragment and agree with its binding; schema, ports, evidence,
operation identity and native gates apply. Prepared root ID/version allocation
may differ from the composition draft's provisional identity. The released native
text-item default `multiline: true` is equivalent to an omitted field; explicit
`false` remains a material difference. Unchanged whole
sources retain their original byte checks. Transformed sources and fragment
representatives receive format-check, validate, vet, lint with warnings as
errors, check and preview. Native checks establish source admissibility, not
future suitability or runtime operation. State tested parameters and limits;
never inherit a runtime claim from the source Procedure.

The output is `preservation-offer`, with grouped `proposal`, exact files, diff,
checks, duplicate locations and a content ID. Show those exact changes before
asking which candidates to preserve and whether a separate promotion commit is
also authorized. Do not copy native reports, private paths, handles, credentials
or task-specific grants into reusable definitions. Review narrative content for
those concerns; the closed binding does not contain invocation authority.

## Decision and post-finalization application

`apply` uses the same CLI flags with ordinary JSON containing `proposal`,
`decision`, `finalization` and optional `commit_grant`.

`decision` is actual user consent: `source: user`, the exact `proposal_id`, and
`selected`, the accepted candidate names. An empty list returns
`preservation-declined` without writes or a finalization prerequisite. Generic
file-editing or member-commit authority does not substitute for this decision.
Partial consent writes only its selected entries. A changed proposal needs its
own content consent.

Before a nonempty application, finish the original accepted commit or verified
no-commit result and required Podway finalization. `finalization` carries actual
`accepted: true`, acceptance `reference`, and either the existing `commit` or
`no_commit: true`; `native` states whether finalization was `required` and, when
due, `state: completed`, its readback `reference`, and either verified
`disposition: handed_off` or `not_required`, or a concrete `undisposed_reason`
when no disposition is supported. Carry these reconciled records from the
original workflow. The helper
checks that `commit` is a full hexadecimal commit object ID that resolves to
itself; mutable revisions such as `HEAD` or a branch name are rejected. The
owning workflow verifies acceptance,
no-commit and native-finalization provenance before calling it. A terminal name
or lifecycle alone does not prove the original goal was achieved.

The helper prechecks every selected destination, creates invocation-owned
staging directories only under the disclosed library root, rechecks exact native
source/binding, and publishes each complete entry without replacement. It
preserves concurrent/custom targets and rejects ignored or unsafe tracked-library
locations. Failure preserves original completion and local recovery material. Same-proposal
recovery verifies and reuses identical published entries; conflicting content
stops without replacement. It never edits ignore policy or deletes local adopted
bundles. Interrupted `.promotion-*`
staging is reported as `interrupted-staging` in offer diagnostics and excluded
from equivalent library entries. Unknown residue is preserved. A failed owned
cleanup returns `cleanup-failed` with its path and original typed failure.

Content consent permits the disclosed write. It does not grant a commit.
Without a matching `commit_grant`, the result remains uncommitted. A grant must
express `purpose: procedure-library-promotion`, the exact `proposal_id`, accepted
`selected` names, `consumed: false` and its actual `reference`. It produces a
bounded [task-commit](../skills/task-commit/SKILL.md) handoff with original owner
and IDs, exact paths/checks and `lifecycle_edits: []`. Complete applicable review,
settlement, acceptance and release-note fields under that existing contract.
Never amend the original completion commit or consume its member grant. Push,
release and publication remain separate.

A supplied mismatching or consumed commit grant returns exit 2
`commit-authority-required` after consented writes, with `details.applied` naming
the applied paths. Those files remain uncommitted and no task-commit handoff is
produced. Recover with the same exact proposal and a matching grant; do not
repeat original finalization or infer that exit 2 means no effects occurred.

Successful offer, decline and application return exit 0. Typed source, consent,
finalization, path, prerequisite and native failures return JSON with `status`,
`message`, `details` and exit 2; native-invalid and runtime failures remain
separate. The library definition receives current fit, structural qualification
and any due exact suitability when later adopted. Past invocation passes and
grants never transfer.
