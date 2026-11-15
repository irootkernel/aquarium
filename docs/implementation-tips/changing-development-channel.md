# Changing Development Packaging and Retirement

Read the [development specification](../specs/development-channel.md) and [Haepari integration](../../plugins/aquarium/references/haepari-integration.md). Keep the host-only committed builder independent of the removed manager, launcher, installer and MCP server. Do not recreate producer targets or introduce a replacement framework.

Verify clean local-main admission, committed-byte provenance, exact SHA/version, file modes, output containment and checksum. Preserve fixed-payload parity with the original producer. Separately seal current host/recipe source; it cannot masquerade as the committed payload.

Keep package and validator behavior coupled: absent advertised MCP declaration is supported; any advertised declaration still requires objective map, command and path validation. Preserve status-ledger history without enrollment reads. Cancelled Epics retain terminal-withdrawn semantics, valid historical dossier links and completed Task history.

Keep TASK-101's original non-installing results and finite preservation limits in the [retirement record](../ops/haepari-vm-verification.md#task-101-observed-retirement-scope). The one-off case is retired after cold-integration source consumption. Active combination recipes retain same-Job guards, protected inventories, complete identities, mismatch refusal and distinct consumer/native cleanup. Disposable unit tests do not establish installed results. Actual host/VM effects require separate authority; TASK-102 qualifies the changed installation and upgrade.
