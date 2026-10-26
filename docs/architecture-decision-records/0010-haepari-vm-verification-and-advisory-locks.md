# ADR-0010: Use Haepari for managed VM verification and advisory locks

**Status:** `Accepted`

**Recorded:** `2026-10-26`

**Acceptance scope:** TASK-090's Coordinator-delegated acceptance records the
Aquarium adapter and release-policy cutover. Master's overall EPIC-019 acceptance,
release publication and host activation remain separate.

## Context

Aquarium needs durable occupancy across candidate installation, manual workflow
observations, evidence collection and restoration of a persistent verification
guest. A caller disconnect or timeout must preserve the admitted work and its
identity. Job cleanup alone cannot establish that guest installation changes
were restored.

Haepari v0.1.0 supplies managed Jobs, same-key admission, blocking observation,
collection, owned Job cleanup and advisory named locks. Its public contract
does not supply external leases or VM power and reset operations. Aquarium owns
the consumer adapter, immutable test profiles and guest assertions.

## Decision

Use the checksum-verified released Haepari CLI and complete same-release
`use-haepari` skill. Participating callers select one shared per-user controller
and one registered capacity-one `utm-macos` resource. Native registration and
private machine configuration retain their existing owners; Aquarium adds no
controller, scheduler or central project-state file.

Aquarium's release policy selects `make test-vm-host` with
`MODE=manual SUITE=release-acceptance`. One outer Job holds the guest from
baseline observation through candidate installation, all required scenarios,
evidence staging and verified consumer cleanup. Guest entrypoints and nested
handler fixtures execute inside that allocation without acquiring it again.
Other repositories select their own verification environment.

Seal committed plugin bytes, executable harness, fixed profiles, test inputs and
budgets before admission. Persist the request key and spec before submission;
reconnect the returned Job rather than creating a replacement. Keep native
workload outcome, evidence completeness, Job cleanup and recipe-owned consumer
restoration as separate results. Missing observations prevent PASS. Cancellation
acknowledgment is followed by the actual immutable terminal disposition.

Consumer cleanup precedes manual completion. Restore the declared prior release
or product-absent state, preserve unrelated settings and historical generations,
and verify the post-cleanup inventory. Submit truthful manual observations with
the current revision, then await native collection, cleanup and verified export.
Keep machine identities, Job IDs, private paths and raw observations in runtime
evidence; canonical documents retain reviewed outcomes and reusable interfaces.

The [tool catalog](../../plugins/aquarium/references/tool-catalog.md#haepari)
owns supported release and setup policy. The
[consumer contract](../../plugins/aquarium/references/haepari-integration.md)
owns submission, result and recovery boundaries. The
[VM guide](../../tests/vm/README.md#qualified-pilot-and-limits) identifies the
qualified profile and actual limits, and the
[operations runbook](../ops/haepari-vm-verification.md) owns the operator sequence.

## Consequences and qualification limits

- Aquarium maintainers complete the shared-controller and registered-resource
  transition before the next release containing the cutover. Existing managed
  status runtimes also need their normal approved update before terminal
  repository setup. Haepari setup remains optional; installation, configuration
  and host activation retain separate approval.
- The exact installed pilot passed upgrade, Task/Epic startup, stale-skill
  detection and restoration in one uninterrupted release-acceptance Job. The
  final-harness pilot also exercised contention, disconnect/reconnect,
  cancellation, missing-output collection and a genuinely stopped VM. Expected
  negative results remain negative; the VM guide records their distinctions.
- Startup qualification stops at the declared first-member semantic boundaries.
  It does not establish complete fixture Task/Epic delivery, release-role
  orchestration, producer rollout or whole-combination acceptance.
- Haepari's frozen capability output still has an empty `qualified_backends`
  array. The accepted producer qualification and Aquarium's observed combination
  are separate evidence; neither rewrites that advertised array.
- One observer reconnect reported `UNKNOWN` when local teardown returned
  `EPERM`. The original uncertainty remains; subsequent same-Job terminal and
  export observations are separate. Its cause is unproven. Callers reconcile
  the original Job before further effects.
- Shared occupancy coordinates callers using the selected controller/resource.
  It does not exclude direct callers that bypass it. Master controls VM power;
  agents neither power nor reset the guest.
- Advisory locks follow Haepari's native owner/borrower contract. Mulgae's
  released lock integration, producer migration and combined qualification stay
  with EPIC-032 and EPIC-033. No external-lease API is implied.
- Each release still needs exact-candidate installed verification and final
  distribution identity checks. The qualified development stamp does not
  establish publication readiness for another artifact. Host legacy detachment
  and shared retirement remain with TASK-101 under their own authority.

## Rejected alternatives

- A second scheduler or project registry would duplicate native authority and
  obscure which owner holds the guest.
- A new Job after an uncertain submit or disconnect could duplicate effects.
- Native cleanup, an acknowledgment or a successful local Make gate alone
  cannot prove consumer restoration or actual installed workflow behavior.
- Resetting the guest would erase the meaningful prior state needed to verify
  preservation and upgrade behavior.

## References

- [Verification architecture](../architecture/verification.md)
- [Tool integrations](../specs/tool-integrations.md#haepari)
- [Testing authority](../../TESTING.md#host-submitted-managed-vm-suites)
- [Separate effect approvals](0005-separate-effect-approvals.md)
