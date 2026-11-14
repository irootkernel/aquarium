# Development Without the Shared Channel

Host development uses supported installed releases. The candidate advertises no bundled MCP server and contains no `aquarium-dev` manager, launcher or installer. Installed consumers remain a separate native transition and cleanup responsibility; source removal does not establish inactivity.

The managed adapter retains one host-only builder in [candidate_artifact.py](../../tests/vm/candidate_artifact.py), called by [host_bundle.py](../../tests/vm/host_bundle.py). It materializes the committed marketplace and plugin tree from a clean disposable local-`main` clone at the selected SHA, preserves executable modes, changes only the copied manifest version to `<version>-dev.<sha12>`, and emits the original artifact schema and digest. It has no installed runtime, hook, selector, service or MCP dependency.

Current host code, sealed Git-visible recipe snapshot, committed payload and installed guest are separate identities. The non-installing retirement smoke observes pinned binaries, complete skills, plugin registration and protected guest state within one guarded Haepari Job. Native collection/export and cleanup remain distinct from consumer preservation. TASK-102 still qualifies the final changed installation.

Production state, caller-selected account homes, authentication, Vault and supported services remain outside channel removal. [ADR-0007](../architecture-decision-records/0007-host-local-immutable-development-artifacts.md) and [ADR-0008](../architecture-decision-records/0008-separate-development-and-production-environments.md) retain historical design and production separation. The [runbook](../ops/development-channel.md) owns host sequencing.
