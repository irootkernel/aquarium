# Development Channel Specification

The explicit-only `$aquarium:dev-aquarium` workflow manages one canonical local-`main` checkout per supported project on Darwin arm64. Diagnosis is read-only. Enrollment metadata, a native hook marker, an initial or recovery build, and isolated Codex configuration are separate effects with separate approvals.

Every producer owns `make aquarium-dev-describe` and `make aquarium-dev-build AQUARIUM_DEV_OUTPUT=<absolute-empty-directory>`. A build admits only a clean checkout whose `HEAD` is local `main`, consumes committed bytes, emits one exact-SHA manifest, and writes only into the supplied staging directory. Aquarium's producer packages the committed Root Kernel marketplace and Aquarium plugin, including its bundled skills, and gives the derived plugin version the exact `-dev.<sha12>` identity.

The manager validates the declared identity, version, path containment, and canonical checksum before immutable promotion. The current selector advances atomically. Resolution fails closed for any broken enrollment, pins one validated generation with a shared operating-system lease, and never re-resolves during the child lifetime. Stable fallback is available only when no enrollment exists.

Approved Codex configuration operates only with `CODEX_HOME=~/.aquarium/codex`. It installs the exact leased Aquarium marketplace generation and therefore its bundled skills together, then wires enrolled Mulgae and Gaori MCP servers through the installed generation's manager. Podway and Sanho remain CLI integrations. Every external invocation resolves that project's current enrolled artifact at launch. Missing isolated authentication produces an exact user login action and never reads or copies stable-home state.

The diagnostic result covers the selected checkout and hook, current artifact, isolated plugin and bundled-skill generation, MCP server names, login readiness, and every supported project's enrolled artifact identity. Host-local development evidence is neither stable installation nor release or distribution proof.

Exact executable behavior is owned by the [`dev-aquarium` skill](../../plugins/aquarium/skills/dev-aquarium/SKILL.md), its [development contract](../../plugins/aquarium/skills/dev-aquarium/references/development-contract.md), the [manager](../../plugins/aquarium/skills/dev-aquarium/scripts/dev_manager.py), the [Aquarium producer](../../plugins/aquarium/skills/dev-aquarium/scripts/build_aquarium_artifact.py), and the repository [Makefile](../../Makefile).
