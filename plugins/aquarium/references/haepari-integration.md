# Haepari Consumer Contract

TASK-088 ships the project-owned VM suites: the host wrapper (`make test-vm-host`, documented with its sealed inputs, suites and invocation boundary in the repository's `tests/vm/README.md` host-submitted managed VM suites section) implements this contract's submission, observation, collection-ordering and budget rules over the committed EPIC-024 guest scenarios, with sealed inputs, fixed and derived profiles, and recipes that own guest installation, inventories and consumer cleanup. Setup registration and fixed test profiles are shipped: the shared [tool catalog](tool-catalog.md#haepari) owns installation and readiness policy, and the repository's fixed VM profiles hold the immutable test inputs. TASK-089 adds the release-gate integration, the release-acceptance Job with its runbook and approval evidence; TASK-090 the accepted policy cutover. This reference restates no Haepari-owned contract; the release-matched sources at the [v0.1.0 tag](https://github.com/irootkernel/haepari/tree/v0.1.0) are authoritative, and the shared [tool catalog](tool-catalog.md) owns component support policy.

## Scope

Managed automatic and manual Jobs on `local` and `utm-macos` resources, and advisory named locks, per the upstream [CLI and job](https://github.com/irootkernel/haepari/blob/v0.1.0/docs/contracts/cli-and-jobs.md), [resource and runner](https://github.com/irootkernel/haepari/blob/v0.1.0/docs/contracts/resource-and-runner.md), [lock](https://github.com/irootkernel/haepari/blob/v0.1.0/docs/contracts/locks.md), [configuration](https://github.com/irootkernel/haepari/blob/v0.1.0/docs/contracts/configuration.md), [managed transition](https://github.com/irootkernel/haepari/blob/v0.1.0/docs/contracts/managed-transitions.md) and [artifact and profile](https://github.com/irootkernel/haepari/blob/v0.1.0/docs/contracts/artifact-and-profile.md) contracts. The frozen native schemas are the ones the exact release's `help` reports: the `haepari.job` and `haepari.result` v1/v2 families, `haepari.resource` v1/v2, and `haepari.manual-result/v1`. Admission supports only the `development` evidence class; consumer provenance carries the committed source and release/archive identities, and no other evidence class is required or assumed. Excluded: external leases and linked continuation ([deferred upstream](https://github.com/irootkernel/haepari/blob/v0.1.0/docs/contracts/external-leases.md)), any VM power operation (Haepari never starts, stops, clones or resets the VM), Mulgae's native advisory integration (EPIC-032 TASK-092), and host installation authority, which stays with setup under its own approvals.

## Submission

Before the first submission, persist in a private mode-0700 run directory the request key, the exact spec bytes, and the selected installation, resource, and sealed-input identities: controller root, resource ID, and the spec's input inventory digest, plus the installation ID once it is known. Persist the Job ID when it is returned or recovered. Submit once. A lost or uncertain admission reply is recovered by resending the identical key and spec, never a replacement key. Preserve `error.code` and `error.retry`: exit 6 covers both transport and storage uncertainty and does not by itself authorize replay. Act on the native hint: `retry_same_key` resends the identical request, `reconcile` inspects or reconciles the same key, `none` stops.

## Observation and results

Observe through native blocking `wait`, `events`, and `logs`; no wrapper adds a status-polling loop. Terminal mapping: exit 0 PASS, 1 FAIL, 3 INCOMPLETE, 4 CANCELLED. A caller wait timeout (exit 5) reports PENDING and never cancels the Job; an uncertain observation (exit 6) reports UNKNOWN and reconciles the same key. Keep workload outcome, evidence completeness, Haepari-owned cleanup, consumer cleanup, and the native final verdict separate: a successful command with missing required observations or failed consumer cleanup cannot establish acceptance, and no wrapper synthesizes PASS.

## Collection ordering

Stage case evidence; finish consumer cleanup and stage its verified inventory; then end the workload, by automatic exit or `manual complete`; native collection and Haepari-owned cleanup follow; export collected results last. Export is never a prerequisite for consumer cleanup.

## Release transaction

One release-acceptance Job holds the VM continuously from the first baseline observation through candidate installation, scenarios, evidence collection, and owned cleanup. TASK-089 implements that Job; TASK-088's `manual-hold` suite carries the manual-path demonstrations, including same-`RUN_DIR`/same-Job reconnect with receipt-verified export reuse. Independent suites may use separate Jobs only when each checks and establishes its own starting state. `SUITE=all` retains every Job result and reports skipped or unobserved work; it never aggregates partial runs into PASS.

## Profiles and budgets

Consumer profiles are immutable test inputs pinning exact binary, controller, skill, rules, and effective configuration identities inside the tool-catalog support policy; they add no global registry or account-wide exception. Resolve any default or latest alias before admission, retain the exact profile digest, and never resolve latest while an admitted Job executes. Queue waiting must not let later worktree changes alter the admitted candidate: sealed input bytes are the candidate identity. Choose phase budgets, including enough manual time for the cases, evidence staging, and consumer cleanup, before admission; reconnection never extends a deadline.

## Shared-VM occupancy after cutover

After TASK-090's accepted policy cutover, Aquarium-owned installation-dependent checks targeting the registered shared VM use the accepted managed adapter for occupancy, acquired once at the outer host boundary. Guest entrypoints and nested handler fixtures run inside the held Job without recursively acquiring its resource.
