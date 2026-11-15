# Development Without the Shared Channel

Host development uses supported installed releases. The candidate advertises no bundled MCP server and contains no `aquarium-dev` manager, launcher or installer. Installed consumers remain a separate native transition and cleanup responsibility; source removal does not establish inactivity.

The managed adapter retains one host-only builder in [candidate_artifact.py](../../tests/vm/candidate_artifact.py), called by [host_bundle.py](../../tests/vm/host_bundle.py). It materializes the committed marketplace and plugin tree from a clean disposable local-`main` clone at the selected SHA, preserves executable modes, changes only the copied manifest version to `<version>-dev.<sha12>`, and emits the original artifact schema and digest. It has no installed runtime, hook, selector, service or MCP dependency.

Current host code, sealed Git-visible recipe snapshot, committed payload and installed guest are separate identities. TASK-101's finite retained-guest observations keep their original scope after the temporary case is retired. The active combination suite retains exact installed identity, preservation and handoff assertions. Native collection/export and cleanup remain distinct from consumer preservation. TASK-102 qualifies the changed installation and upgrade; missing results remain open.

Production state, caller-selected account homes, authentication, Vault and supported services remain outside channel removal. [ADR-0007](../architecture-decision-records/0007-host-local-immutable-development-artifacts.md) and [ADR-0008](../architecture-decision-records/0008-separate-development-and-production-environments.md) retain historical design and production separation. The [runbook](../ops/development-channel.md) owns host sequencing.

Durable retirement and qualification facts stay with the existing specification,
operations and [VM verification owner](../../tests/vm/README.md#accepted-source-and-acceptance-binding).
Runtime exports, role reports and native identities remain with their producing
tools. Canonical outcomes and Git history identify the accepted source and acceptance
boundary. A timeout retains its native outcome. No replacement state registry is
introduced.
