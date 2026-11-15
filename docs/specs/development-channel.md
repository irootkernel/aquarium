# Development Channel Retirement

The candidate no longer ships the shared `aquarium-dev` manager, launcher, installer, MCP declaration or producer targets. Global setup does not select or install that component. Source removal does not disable an already installed declaration or settle existing clients, services, hooks, workers or recovery consumers.

Use supported installed tool releases for host development and disposable fixtures for source checks. Installation-dependent verification stays in the dedicated UTM VM. The host-only [candidate builder](../../tests/vm/candidate_artifact.py), called by [host bundle preparation](../../tests/vm/host_bundle.py), consumes a clean disposable local-`main` clone at the selected committed SHA. It preserves the `aquarium-dev-artifact-manifest/v1` data schema, version stamp, file bytes/modes and canonical digest. That historical schema name is not an active channel dependency or distribution proof.

Record host source, sealed recipe harness, transported committed payload and
installed guest identities separately. TASK-101's original non-installing
observations retain their finite scope in the
[operations record](../ops/haepari-vm-verification.md#task-101-observed-retirement-scope).
The temporary check has no current entrypoint after its cold-integration source
consumers finish. TASK-102 qualifies the changed installation and upgrade before
release and preserves any missing evidence as an open obligation. The
[runbook](../ops/development-channel.md) owns separately approved native host
transition and cleanup. Historical decisions retain their original meaning, including EPIC-002's
Cancelled status and completed Task history. Settled dossier references resolve
to these canonical owners; deleting a dossier never relabels withdrawn work.

The [qualification and source binding](../../tests/vm/README.md#accepted-source-and-acceptance-binding)
retains the exact installed candidate, applicable original cases, negative and
recovery outcomes, actual functional observations and overall acceptance state.
The [dated host observation](../ops/haepari-vm-verification.md#task-102-bounded-host-observation)
is a bounded check of the released host, not guest acceptance or host activation.
Later release readiness must resolve accepted source/closeout ancestry and
inspect intervening retirement-affecting changes. It cannot transfer an earlier
installed or host result to changed payload bytes.
