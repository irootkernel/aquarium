# Manual installed-system acceptance

Apply the target repository's declared installed-system verification policy.
Use its guest entrypoint and scenario owners when present, such as `make test-vm`,
or its declared managed host adapter, such as `make test-vm-host` over
[Haepari integration](../../../references/haepari-integration.md). When the
target repository's policy selects Haepari, one outer-boundary managed Job holds
the registered shared VM resource from `prepare` through `awaiting_manual`
scenario execution, evidence staging, verified consumer cleanup, revision-fenced
`manual complete`, and native collection/export; guest entrypoints and nested
handler fixtures run inside that held Job without recursive resource acquisition.
The user owns VM selection, power state, access and host transport; do not assume
a personal SSH alias, VM provider, machine model, username or filesystem path.

Complete development functional verification before release preparation. Keep
offline release QA separate. Under the applicable execution and installation
authority, identify the exact candidate, matching committed guest test sources,
installed combination and intended dedicated guest. Verify guest identity before
fixture mutation, installation or native agent dispatch. Never install a candidate
on the host as a fallback.

Observe meaningful state under the existing released combination before
upgrading. Retain original files, settings, Git work, customized managed sources
and admitted session snapshots. Install the exact candidate through its supported
path. Use fresh installed setup skills for separately authorized managed updates;
preserve custom files and use compatible successors without reinterpreting old
sessions.

Run the declared guest gate only under this release workflow or an explicit
user VM-test request. Capture the observations required by the target's scenario
owner. Where applicable, include installed discovery, workflow progression,
native Executor results, independent Evaluator assessments and application checks.
A checklist, fixture preparation or success sentence
cannot establish acceptance. Unavailable private telemetry is not an ordinary
workflow admission requirement.

Preserve real plan and exact-result approval boundaries. An authorized fixture
operator reads the ready proposal or diff and supplies their actual decision;
never manufacture user acceptance from an initial scope grant. Recover through
existing public handles and reconcile uncertain work before replay.

Collect the structured outcome, candidate/test/artifact identities, installed
combination, original baseline and actual case/cleanup observations. For a
managed Haepari Job, persist the request key and exact spec before submission,
wait on or reconnect to that same Job ID, finish recipe-owned consumer cleanup
and stage its verified post-cleanup inventory before revision-fenced
`manual complete`, and verify native collection and exported output digests.
Retain the native export-root `result.json` and `manifest.json` separately from
the producer's suite-declared consumer result and cleanup inventory; their
filenames and required paths follow the target's producer contract.
Distinguish the
committed pre-metadata candidate identity verified inside the guest from the
final distribution commit, tag and archive verified after release-metadata edits
([final distribution identity](../../../references/haepari-integration.md#final-distribution-identity)).
For Aquarium's own release gate, follow `AGENTS.md`, `TESTING.md`,
`tests/vm/README.md`, and `docs/ops/haepari-vm-verification.md` without imposing
Aquarium's `Makefile`, SSH alias or controller on other repositories. Failures,
missing required observations, unverified exports and incomplete cleanup remain
non-passing. Respect the command's actual exit semantics: Make may map a failing
recipe to its own nonzero status. Keep private runtime evidence under the
target's evidence residency contract. VM acceptance does not grant staging,
commits or publication.

## Release-role delivery and recovery

The Coordinator supplies the policy-due boundary, exact candidate/test sources,
controller/resource, admitted installation/manual effects and cleanup owners in
the existing assignment. An authorized bounded Executor returns the persisted
request key/spec and sealed input identities, returned or recovered Job/revisions,
original native envelopes, actual case results, verified consumer inventory and
native collection/cleanup/export evidence. Planning acquires no occupancy and
does not require an idle resource; normal contention follows the native queue.

Before Executor replacement or redispatch, reconcile its commands, descendants
and possible effects, recover that original request/spec/Job and await or reconnect
to the same Job. A lost admission reply may resend only the identical key/spec as
native `error.code` and `error.retry` direct; do not invent a replacement key or
Job. A wait timeout remains pending, does not cancel and does not return capacity.
Preserve actual cancellation, collection and cleanup failures separately.

The independent publication-readiness Evaluator reads policy-due original installed
and case results, consumer cleanup/inventory and native export evidence for the
exact candidate. Include them at QA readiness only when policy makes them due
there. Light mode retains actual exact-SHA confirmation and required prior results;
full mode follows the declared installed boundary. A manual-ready state, smoke
exit or assessment verdict cannot supply missing observations or resource return.
Keep occupancy/disposition, workload outcome, evidence completeness, recipe cleanup,
native cleanup and assessment separate. Later publication/report assembly does
not prolong settled occupancy or reacquire the Job. Reconcile tested pre-metadata
bytes with final distribution under the existing identity contract; any unsupported
payload difference renews affected installed verification before publication.

## Aquarium startup scope

Aquarium's canonical `tests/vm/recipes/scenarios/release-acceptance.md` adds
release-handler plan readiness alongside Task/Epic startup. Its bounded native
preparation and independent assessment stop before settlement commit, pre-QA
execution, QA or publication. The separately authorized `release-orchestration`
development suite covers full feature progression and recovery. Other targets
retain their declared inventory and environment; this adds no universal VM gate.
The fixture operator supplies actual concrete decisions under its real authority.
No startup or fixture status substitutes for full installed/native qualification.
