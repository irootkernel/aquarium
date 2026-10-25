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
