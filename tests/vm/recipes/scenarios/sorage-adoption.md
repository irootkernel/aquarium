# Sorage v0.1.3 installed adoption

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
installed released Sorage v0.1.2. Preserve the
original binary, manifest, checksum, complete skill, Aquarium plugin, registration,
configuration, rules, home and Vault under the consumer-restoration inventory.
Verify the corrected official v0.1.2 distribution identity before the baseline.
Prepare official v0.1.3 binary/manifest/checksum and its complete commit-pinned skill
inside the guest under the exact installation proposal. Verify published checksum,
manifest revision 9bf079f07728387c21450a7e1d5eab4b8f821b1d and codesign before use.
The capture recipe checks the installed v0.1.3 binary digest and complete release
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

Keep the original guest home and Vault intact. Rehearse the upgrade and rollback
on separately confined copies, retargeting only the copied vault.path configuration
before any CLI invocation. Record that fixture relocation separately; never rewrite
domain rows, ledgers or receipts. The candidate capture selects the upgraded copy;
consumer-cleanup selects the original roots and verifies their unchanged bytes.
Retain rehearsal roots until evidence collection and remove only these owned copies
under the declared cleanup envelope.

## Required manual cases

- released-baseline: observe meaningful Handoff and Memo state under the released
  combination and record exact binary, skill, configuration and candidate identities.
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
  a bundle selecting Sorage and a bundle with no MCP request. Registration alone
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
  managed state, and denied writes do not trigger configuration/permission changes.
- consumer-restoration: restore the declared consumer inventory, compare it with
  the baseline, retain original case evidence and complete the cleanup phase.

Archive original non-sensitive case evidence and its identity index as
`results/sorage-adoption/case-evidence.tar`. Native manual completion must assess
each required case against that evidence and the exact committed candidate. The
recipe's pass covers restoration observations only; it cannot establish skill
behavior, full home/Vault restoration or overall acceptance. Use revision-fenced
manual completion and native collection/cleanup from the runbook, preserving original
failed observations and applicable evidence boundaries.
