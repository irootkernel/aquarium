# Mulgae v0.1.27 installed adoption

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
`v0.1.27` CLI (`go install github.com/irootkernel/mulgae@v0.1.27`) from release
commit `c611e2ba16d0f0e873e948b2251f5bc5bda84cad` and its complete six-file
`skills/use-mulgae/` subtree (`01a202819ec58cf1adbb4d88dcf92ab0bc85d446`,
`aquarium-skill-tree-sha256/v1`
`a3d11762fa5f1069df60cd64ef9cf2efd538e8e1ebd1b60e61a717c7e4697085`). Retain
installation provenance, module verification, binary digest and full skill
digest. The recipe checks the complete release skill digest and version; it does
not certify build provenance.

Use the saved workload environment and parent context from the runbook. Run
`tests/vm/recipes/guest_entry.sh --suite mulgae-adoption --phase <phase>` for
`prepare`, `candidate`, and `consumer-cleanup`. Prepare observes the released
Mulgae `v0.1.26` baseline matching the host's released combination before the
separately authorized candidate installation (if the guest still holds `v0.1.25`,
observe that actual starting inventory and obtain separate baseline-preparation
authority before upgrading it to `v0.1.26`; never relabel `v0.1.25` or silently
upgrade it). Preserve original captures and historical `v0.1.25`/`v0.1.26`
observations. Before candidate capture, independently verify that the installed
Aquarium payload matches the sealed committed candidate and that native discovery
loads its skill paths. Preserve those original public observations in case evidence.
The recipes measure tool and consumer identities; functional verdicts come from
actual cases and native manual completion.

All guest live reviews use a disposable isolated guest Haepari controller/root
and capacity-one `mulgae-review` (`advisory-lock/v1`) resource with adequate
native hold budgets, existing stub-provider fixtures for fault probes and only
expressly authorized guest identities for real calls. Never reacquire the
occupied parent `utm-macos` resource or start a second controller against the
shared host installation.

## Required manual cases

- released-baseline: record meaningful released `v0.1.26` review evidence,
  unchanged Config v5 policy, staged/unstaged sentinels, complete skill and
  installed plugin identity.
- installed-discovery: verify fresh installed candidate discovery, `v0.1.27` and
  full six-file skill identity, command v23 and Doctor v7. Diagnose the five
  native provider families without requiring unselected providers. Keep
  authentication gaps explicit.
- native-lock-exclusions: on the public Go-install `v0.1.27` binary, verify that
  provider-free `--preflight`, receipt-bound inspection (`runs status/show/findings`),
  and no-change reviews succeed without controller contact or lock acquisition,
  and that a coordinated review path refuses an invalid or mismatched
  `HAEPARI_LOCK_GRANT` (`haepari_borrowed_grant_invalid`) or unavailable
  controller without silent direct provider execution. Reuse the producer's
  `c611e2ba16d0f0e873e948b2251f5bc5bda84cad` native contention, replay,
  cancel/grant race, borrower, loss/drain and partial-role suites within their
  declared coverage rather than replaying a full fault matrix.
- native-input: automatically derive original Task/Epic due criteria and selected
  owners. Verify native preflight v11, `requirements_assessment: v1`, exact input
  digest, independent Git binding and identical CLI/MCP dispatch arguments.
  Exercise all five target preflights and owner, limit, unsafe path and binding
  refusals. Non-Git requirements execution must refuse without a new invocation.
- native-results: consume independent finding and requirements pages and complete
  content chunks under one receipt. Exercise no-change derived unverified rows,
  historical unavailable support, missing/corrupt support and receipt mismatch on
  disposable fixtures. Preserve original verdicts and reasons even with no findings.
- completion-review: run an authenticated review using an authorized guest provider
  and an isolated guest `HAEPARI_HOME` with capacity-one `mulgae-review`. Observe
  four actual installed caller paths (Task handler, Epic handler, standalone
  `mulgae-review` and remediation confirmation), retaining each caller's original
  authority and criterion-owner mapping, prepared requirements path and digest,
  preflight/dispatch identity, receipt-bound native v3 requirement assessment
  pages/content and original role report reads. Keep change review objective-only.
  Verify that accepted role assessments survive extraction as native v3 answers
  without the retired `v0.1.26` report-based `answer_omitted` override: any
  derived `answer_omitted` row in a new supported run remains `unverified`
  because native coverage is missing. Never convert it into an Aquarium `met` judgment.
  Preserve explicit native negative (`unmet` and `partially_met`) answers,
  legitimate `not-applicable` dispositions from original authority, and historical
  `v0.1.26` native rows and recorded judgments. Verify that incomplete native
  coverage and unresolved provider conflicts block completion, using the same
  caller observations without another provider matrix. Reuse a single native result only
  when all actual target, input, roles, authority, coverage and dependencies
  match. Retain the owning workflow's required independent reports at their
  checkpoints, using a persistent native session for any required Epic Validator
  assessments.
- failure-recovery: preserve one invocation through start/await interruption and
  supported same-operation recovery. Verify extraction-disabled results do not
  change configuration or cause automatic reruns. For remediation confirmation,
  submit and confirm only the invalidated/affected criterion subset while
  preserving unchanged criteria, ordinal accounting and recovery rules. Clean up
  unchanged caller-owned temporary input after terminal consumption; preserve
  changed/replaced files and pending inputs with explicit recovery references.
- consumer-restoration: settle run-owned handles and the isolated guest Haepari
  controller, restore the approved released `v0.1.26` binary, complete skill,
  plugin and declared consumers, and compare configuration, Git state and
  retained native runtime with baseline. Remove only run-owned fixtures.

Archive original case evidence and its identity index in
`results/mulgae-adoption/case-evidence.tar`. Complete consumer restoration before
revision-fenced native manual completion and collection/cleanup. A recipe pass
covers restoration observations only. Master's functional assessment and the
release's separate combined acceptance remain distinct from this scoped result.
