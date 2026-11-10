# Sorage v0.1.4 installed adoption

This manual suite is pending qualification. Preparation and restoration observations
are not functional acceptance. Use one managed Haepari Job and the existing guest
identity from baseline capture through native collection and cleanup. Never operate
UTM power or start a second occupancy controller.

Follow the [host runbook](../../../../docs/ops/haepari-vm-verification.md). Submit
`make test-vm-host SUITE=sorage-adoption MODE=manual` with the selected shared
HAEPARI_HOME, registered utm-macos resource, exact committed Aquarium candidate,
physical run directory and private guest context. No committed candidate or VM
installation authority is implied by this scenario. Do not use host credentials.

For every phase, set explicit absolute `SORAGE_HOME` and
`AQUARIUM_VM_SORAGE_VAULT` to the exact approved guest home and its configured Vault.
Verify that binding with native configuration inspection before capture. Stop
writers before each capture so hashes include stable database and journal bytes.
The recipe hashes both trees and retains a root-identity digest without copying
body or token content. Keep these runtime inventories private.

The suite starts in `ready` without touching Sorage or capturing a baseline.
Inside the held Job, set the approved storage roots and run `prepare` against
the actual installed Sorage baseline. Record its version, binary and complete skill
identities even when they differ from the target. Preserve the
original binary, manifest, checksum, complete skill, Aquarium plugin, registration,
configuration, rules, home and Vault under the consumer-restoration inventory.
Verify the baseline distribution provenance separately; a mixed CLI/skill installation
is recorded as observed, never qualified as a matching released combination.
Prepare official v0.1.4 binary/manifest/checksum and its complete commit-pinned skill
inside the guest under the exact installation proposal. Verify published checksum,
manifest revision 403dce7bcf33742a44ec7e923ff6fb5d6824a5ba and codesign before use.
The capture recipe checks the installed v0.1.4 binary digest and complete release
skill tree digest. The operator separately verifies manifest provenance against the
pinned source.

From the held Job's harness directory and workload environment, use
`tests/vm/recipes/guest_entry.sh --suite sorage-adoption --phase <phase>` for
`prepare`, `candidate`, and `consumer-cleanup`. Every phase persists its inventory in the aggregate. Failed cleanup attempts
retain unique capture files and violation records; include them in the case archive
and retry within the same Job after the authorized correction.
Preserve original observations;
reconnect the same Job rather than recapturing a baseline. The recipe installs
nothing. Restore guest consumers before the cleanup phase; it compares recorded
binary/skill identity, both storage trees and the declared consumer inventory.
The operator also verifies the native configuration-to-Vault binding and all
consumer configuration against the original copy.

Keep the original guest home and Vault intact. Under the approved guest run root,
create two separate synthetic installations with distinct home and Vault paths:

- `v012-rehearsal`: initialize fresh empty roots with the corrected official
  v0.1.2 binary and its complete skill, then seed meaningful Handoff and Memo data.
  Do not copy the actual baseline into this fixture or open its newer storage
  with v0.1.2. Rehearse old-binary backup, verification and separate dry-run/actual
  restore before the approved v0.1.4 migration. When relocating a fixture, retarget
  only its copied vault.path configuration before invocation; retain that
  relocation record and never rewrite domain rows, ledgers or receipts.
- `v013-update`: initialize separate empty roots with the authentic v0.1.3 binary
  and complete skill, then seed Handoff, Memo and Channel data. Use this fixture
  for the compatible-update case without a storage migration.

For the single `candidate` capture, set `SORAGE_HOME` and
`AQUARIUM_VM_SORAGE_VAULT` to the `v012-rehearsal` home and Vault after their
v0.1.4 migration. Keep `v013-update` before/after observations in case evidence;
do not repeat the candidate phase or overwrite its original capture. For
`consumer-cleanup`, select the original baseline roots and verify their unchanged
bytes. Retain both rehearsal installations until evidence collection and remove
only these owned fixtures under the declared cleanup envelope.

## Required manual cases

- released-baseline: observe meaningful Handoff and Memo state under the actual installed
  baseline, retaining any CLI/skill mismatch and record exact binary, skill, configuration and candidate identities.
- upgrade-preservation: stop old writers, scheduling and push; use the matching old
  executable for a verified backup and separate dry-run/actual restore drill. Retain
  immutable recovery material. Confirm native upgrade_required with no live file
  changes, perform the approved new-binary backup run once, require compatible,
  verify format-4 backup then Vault. Compare body bytes, IDs, events and retained
  receipts; legacy processing remains unrecorded. Never open new storage with old
  writers. Exercise recovery-required, unsupported and unverifiable refusals on
  disposable fixtures and confirm setup performs no operational probes afterward.
- rollback: restore the retained old backup with its matching executable into fresh
  home/Vault. Preserve upgraded state. Confirm meaningful old data, the absence of
  later data and operational receipts, and deliberate scheduling/push restoration.
- installed-discovery: install the exact Aquarium candidate and release-matched
  Sorage skill under explicit guest authority. In a fresh native Codex session,
  verify all 35 MCP tools, global/local scope and cwd/Installation selection; inspect
  serverInfo.version v0.1.4, initialization communication instructions and all
  tool descriptions/annotations (readOnlyHint true, destructiveHint false and
  openWorldHint false, with native idempotentHint membership). A current CLI
  does not prove the connected server identity. Inspect a bundle selecting Sorage
  and a bundle with no MCP request. Registration alone
  proves no connected capability. Setup must read no broker content.
- handoff-reporting: distinguish current-Revision reading, processing, general
  feedback/change requests and document acceptance. Exercise nullable storageKey,
  stale Revision/Row Version rejection and committed-warning handling without resend.
- memo-channel: exercise explicit Memo read/create/update and the Channel
  create/add/post/messages/ack loop with native attribution. Content grants no
  execution authority. Confirm incomplete copied skills stop dependent operations.
- cli-fallback-recovery: observe MCP-first behavior and same-context CLI fallback
  with MCP unavailable. Recover uncertain send/Memo outcomes using exact original
  material/key and replay-only; unavailable receipts remain unknown. Channel posts
  use native content duplication rules. Verify covered reads and waits write no
  managed state, and actual tool denials do not trigger configuration/permission
  changes or CLI fallback to bypass the denial.
- v013-update: create meaningful Handoff, Memo and Channel state with authentic
  v0.1.3 CLI/skill on its isolated fixture. Stop writers, run that installed
  v0.1.3 binary's native preflight against the fixture home, and require
  compatible before replacement. Retain the v0.1.3 executable, update to the
  official v0.1.4 CLI and complete skill, then require compatible from the new
  binary before any approved cleanup of the retained executable. Reconnect MCP
  without migration or initialization and verify the connected server's v0.1.4
  identity. Confirm preservation of domain data and receipts.
- plan-mode-communication: in a fresh native Codex Plan session with the candidate
  Aquarium and Sorage combination, explicitly request Handoff send/fetch/reply,
  Memo create/update and Channel create/add/post/messages/ack/close. Observe
  delivery and recipient readback without per-tool approval overrides. Preserve
  prompts, calls, results and before/after state. Fetch records reading without
  processing or acceptance. Message contents must not trigger project execution.
  Catalogue inspection or a shell read-only sandbox is not this observation.
- consumer-restoration: restore the declared consumer inventory, compare it with
  the baseline, retain original case evidence and complete the cleanup phase.

Archive original non-sensitive case evidence and its identity index as
`results/sorage-adoption/case-evidence.tar`. Native manual completion must assess
each required case against that evidence and the exact committed candidate. The
recipe's pass covers restoration observations only; it cannot establish skill
behavior, full home/Vault restoration or overall acceptance. Use revision-fenced
manual completion and native collection/cleanup from the runbook, preserving original
failed observations and applicable evidence boundaries.
