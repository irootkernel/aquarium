# Production setup status dossier

## Authority

**Roadmap epic:** `EPIC-013`

The [roadmap](../roadmap/README.md#epic-013-record-and-report-production-setup-status)
owns IDs, ordering, dependencies, and lifecycle. The frozen
[production-status specification](../specs/production-status.md) owns the
ledger, CLI, write timing, concurrency, installation, reporting, retention, and
privacy contract accepted by `TASK-048`.

This dossier now owns only the remaining execution and acceptance scope for
`TASK-049` and `TASK-050`. It is deleted at successful last-consumer epic
closeout after durable implementation guidance has been promoted.

## TASK-049 implementation outcome

- Ship `plugins/aquarium/tools/aquarium-status/` with the frozen show, record,
  forget, storage, report, runtime, diagnosis, installation, and rollback
  contracts.
- Add explicit `$aquarium:status` reporting and approved exact-row removal.
- Include `aquarium-status` in unscoped global setup diagnosis without adding it
  to the production-binary baseline or the bundle manifest v1 tool vocabulary.
- Make `dev-setup` own terminal records for targets that enter it. Make the
  bundle own only targets that settle before entry, using one shared attempt ID
  and suppressing duplicates after a valid receipt.
- Preserve setup success when recording fails, return a partial enclosing result
  with the identical attempt for record-only retry, and never repeat setup
  mutations during that retry.
- Promote shipped behavior to capability, interface, architecture, operations,
  public, privacy, setup, and release-note owners.

## TASK-050 automated acceptance

- Concurrent different-root merge, same-root revision conflict, exact latest
  attempt replay, and stale historical replay rejection.
- Full and scoped outcome transitions, component preservation, corrupt and
  unsafe state, exact output streams and exit classes, and durable rollback for
  validation, lock, write, fsync, replacement, and parent-fsync failures.
- Offline default reporting, successful and failed release refresh, exact source
  root handling, independent freshness, and absent, invalid, or unreadable
  development-enrollment observations.
- Linked worktrees, moved and deleted roots, common-directory path reuse, and
  exact forget without discovery or automatic cleanup.
- Private hash-pinned runtime installation, unknown-launcher rejection,
  managed activation rollback, dependency isolation, and execution after the
  plugin cache is removed.
- Unit, integration, and subprocess E2E coverage enrolled in Makefile and
  TESTING.md, followed by the complete repository test gate.

## TASK-050 manual acceptance

Master separately verifies skill behavior. Automated checks and static review do
not prove these scenarios:

- Plan Mode, diagnosis-only, inspection failure, abandoned work, and unapproved
  proposals leave the ledger unchanged.
- A terminal setup is recorded after its outcome is known and before the final
  report; scoped success requests a later full pass.
- Recording failure keeps setup success, makes the enclosing result partial, and
  supplies an identical record-only retry without repeating mutations.
- Bundle targets are recorded exactly once by the correct owner, and a target
  without canonical Git identity is not recorded.
- Global runtime installation remains a separately displayed and approved
  action; a plugin update does not silently update it.
- `$aquarium:status` is offline by default, refresh contacts only the declared
  release endpoint, reports history rather than live health, and obtains
  approval before exact forget.
- Setup, installation, staging, commit, push, activation, and publication remain
  distinct decisions.

## Exclusions

- No production runtime installation or activation is part of EPIC execution.
- Do not auto-run setup, discover repositories, infer live tool health, attach
  state to `aquarium-dev`, or change EPIC-002 or EPIC-012.
