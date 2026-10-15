# Release upgrade and startup scenarios

These planned EPIC-024 cases define acceptance methods, not verified outcomes.
TASK-128 must supply the fixed fixtures and executable helpers before claiming
the `make test-vm` gate is available. Apply the preparation, invocation, result
and cleanup rules in the [VM guide](README.md).

## Shared fixture method

Version a small greeting CLI with existing tests, valid repository guidance,
Make commands, roadmap and the dossier needed by the installed handlers. Use
separate disposable Git repositories for Task and Epic scenarios. The Task asks
for an uppercase option. The Epic has two members: uppercase, then a repeat-count
option. Development verification exercises complete functionality; release
acceptance needs actual first-member progression only.

Record exact fixture inputs and original criteria with the implementation. Grant
the bounded fixture effects through the handler's normal approval boundary.
Observe installed handler calls, real Worker outputs, relevant checks and an
independent Judge assessment. A standalone agent call or fabricated ACK cannot
substitute for the workflow. All cases use manual UTM operation and Codex.

Unavailable incidental executor telemetry is not a required observation in any
case.

## VM-UPGRADE-01: Existing installation accepts the candidate

### Preparation

Match the guest baseline to the host's installed released combination. Before
candidate installation, create meaningful synthetic settings, existing files,
Git work and native session history using released public interfaces. Record
their contents or suitable non-sensitive identities. Exclude credentials and
unrelated private data. A version string alone is not an existing-state fixture.

Include a customized managed Procedure in a separate preservation repository
and an admitted session created through released public interfaces. Record the
custom file and immutable session snapshot before upgrading. Use a released
public path that can create this baseline even when the released handler cannot
start.
Prepare the Task and Epic fixture repositories under the released installation
as well, so their startup checks exercise authorized managed updates rather than
candidate-only clean installations.

### Steps

1. Observe the released installation and fixture state before the upgrade.
2. Install the exact candidate and required released dependencies through the
   supported upgrade path. Record actual installed identities.
3. Perform authorized managed-file updates. Preserve custom files and immutable
   session snapshots; use compatible successor sessions for new source behavior.
4. Compare retained state against the baseline. Confirm candidate source identity
   and open a fresh Codex session for normal installed-plugin discovery.

### Criteria

Pass requires a supported upgrade, preserved relevant state, correct managed
sources and fresh discovery of the intended candidate. Unexpected data loss,
custom-file overwrite, installation incompatibility, stale-source shadowing or
failed discovery fails the case. Missing before-upgrade observations or an
unusable environment leaves it incomplete. Record any unexpected repair needed
to reach startup; do not hide a blocker behind manual repair.

## VM-TASK-START-01: Installed task-handler begins real work

### Preparation

After VM-UPGRADE-01, open a fresh Codex session on the Task fixture. Select its
exact repository root and roadmap Task ID. Discover the installed
`aquarium:task-handler` normally.

### Steps

1. Invoke the installed handler for the fixture Task and pass its ordinary
   entry and approval boundary with the bounded fixture scope.
2. Observe an actual native Worker assignment, meaningful fixture change and
   relevant check result. Collect the actual returned result.
3. Observe an independent Judge assess the original due criteria and artifacts.
4. Confirm the Primary can advance past initial work using the applicable
   evidence and Podway state. Stop at a safe boundary under the cleanup rules.

### Criteria

Pass requires actual Worker/Judge work and semantic progression beyond initial
admission. A plan, session creation or agent success sentence alone cannot pass.
An unexpected prior-qualification gate or demand for inaccessible executor
records fails the case. A genuine fixture defect follows normal rework; it must
not be disguised as a telemetry failure or accepted without correction. Missing
required public native observations leaves the case incomplete.

## VM-EPIC-START-01: Installed epic-handler begins its first member

### Preparation

Use the separate two-member Epic fixture with complete execution SOT. Open a
fresh Codex session, select the exact repository root and roadmap Epic ID, and
discover the installed `aquarium:epic-handler` normally.

### Steps

1. Invoke the installed handler and approve its bounded fixture execution scope
   through the normal boundary.
2. Observe entry into the first member goal with the correct Procedure and
   admitted review route.
3. Observe actual native Worker output and an independent Judge assessment of
   the original due criteria, then the first semantic progression.
4. Settle agents and stop the partial smoke run through supported operations.
   Record the partial state accurately; do not claim full completion.

### Criteria

Pass requires the Epic to start meaningful first-member work without a startup
qualification blocker. Full two-member delivery and Epic closeout are
development-verification obligations, not required repetitions in this release
case. A startup gate that prevents the approved work fails. Missing required
public native observations, uncertain mutator settlement or unresolved cleanup
leaves the case incomplete.
