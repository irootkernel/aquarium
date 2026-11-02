# Mulgae v0.1.26 installed adoption

This manual suite is pending qualification. Use one Haepari Job from released
baseline through verified consumer restoration and native collection. Follow the
[host runbook](../../../../docs/ops/haepari-vm-verification.md) with
`make test-vm-host SUITE=mulgae-adoption MODE=manual`, the registered `utm-macos`
resource, shared `HAEPARI_HOME`, exact committed Aquarium candidate, physical
run directory and private guest context. Master controls VM power. Reconnect the
original Job after a timeout; never submit a replacement to obtain progress.

The suite starts in `ready` without installing anything. Preserve the original
CLI, complete skill, plugin cache, registration, configuration, native runtime and
consumer inventory. Use guest accounts already authorized for the scenarios;
never copy host credentials. Inside the held Job, prepare the official Mulgae
`v0.1.26` CLI from release commit `c422590155f62380709c8f6fd08c9ad423badaaa`
and its complete `skills/use-mulgae/` subtree. Retain installation provenance,
module verification, binary digest and full skill digest. The recipe checks the
complete release skill digest and version; it does not certify build provenance.

Use the saved workload environment and parent context from the runbook. Run
`tests/vm/recipes/guest_entry.sh --suite mulgae-adoption --phase <phase>` for
`prepare`, `candidate`, and `consumer-cleanup`. Prepare observes released Mulgae
v0.1.25 before the separately authorized candidate installation. Preserve original
captures. Before candidate capture, independently verify that the installed
Aquarium payload matches the sealed committed candidate and that native discovery
loads its skill paths. Preserve those original public observations in case evidence.
The recipes measure tool and consumer identities; functional verdicts come from
actual cases and native manual completion.

## Required manual cases

- released-baseline: record meaningful released review evidence, unchanged Config
  v5 policy, staged/unstaged sentinels, complete skill and installed plugin identity.
- installed-discovery: verify fresh installed candidate discovery, v0.1.26 and full
  skill identity, command v23 and Doctor v7. Diagnose the five native provider
  families without requiring unselected providers. Keep authentication gaps explicit.
- native-input: automatically derive original Task/Epic due criteria and selected
  owners. Verify native preflight v11, `requirements_assessment: v1`, exact input
  digest, independent Git binding and identical CLI/MCP dispatch arguments.
  Exercise all five target preflights and owner, limit, unsafe path and binding
  refusals. Non-Git requirements execution must refuse without a new invocation.
- native-results: consume independent finding and requirements pages and complete
  content chunks under one receipt. Exercise no-change derived unverified rows,
  historical unavailable support, missing/corrupt support and receipt mismatch on
  disposable fixtures. Preserve original verdicts and reasons even with no findings.
- completion-review: run an authenticated review using an authorized guest provider.
  Observe automatic criteria input through Task, Epic and standalone installed
  callers. Keep change review objective-only. Observe partial/unmet/unverified
  blocking completion and legitimate non-applicability from original authority.
  Reconcile native rows with full role reports; retain all original evidence.
- failure-recovery: preserve one invocation through start/await interruption and
  supported same-operation recovery. Verify extraction-disabled results do not
  change configuration or cause automatic reruns. Confirm remediation checks only
  affected criteria. Clean up unchanged owned input after consumption; preserve
  changed/replaced files and pending inputs with explicit recovery references.
- consumer-restoration: settle run-owned handles, restore the original binary,
  complete skill, plugin and declared consumers, and compare configuration, Git
  state and retained native runtime with baseline. Remove only run-owned fixtures.

Archive original case evidence and its identity index in
`results/mulgae-adoption/case-evidence.tar`. Complete consumer restoration before
revision-fenced native manual completion and collection/cleanup. A recipe pass
covers restoration observations only. Master's functional assessment and the
release's separate combined acceptance remain distinct from this scoped result.
