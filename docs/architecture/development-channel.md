# Development Channel Architecture

The development channel separates repository production from host-local consumption:

1. A native post-commit marker queues only a completed canonical local-`main` SHA.
2. One project publisher serializes requests, builds committed bytes into fresh staging, validates the producer manifest and checksum, and promotes an immutable generation.
3. An atomic `current/<project-id>` selector exposes only a completely validated generation.
4. A launcher acquires a shared generation lease before execution. Publication and cleanup use exclusive leases, so a running process cannot change beneath itself.
5. Approved Aquarium configuration leases the exact plugin marketplace, installs it into `~/.aquarium/codex`, and uses that installed manager to resolve enrolled MCP tool generations at process launch.

All owned host state is below `~/.aquarium/`: enrollment records, queues, bounded diagnostics, immutable artifacts, selectors, locks, runtime state, and the isolated Codex home. Repositories keep only the producer targets and an exact Aquarium marker inside their native hook. No `.aquarium` repository state is created.

The Aquarium marketplace artifact contains committed marketplace metadata and the complete committed plugin tree. Only the copied plugin manifest is derived: its stable version gains `-dev.<sha12>`. The manifest checksum covers the resulting canonical directory tree, binding plugin code and bundled skills to one generation. MCP launch commands point to that installed generation's manager, which resolves and leases the external tool artifact independently.

The stable Codex environment is outside this graph. Every Codex subprocess receives an explicit isolated `CODEX_HOME`; no stable configuration or credentials are inputs. A failed build or configuration leaves Git history and the prior current artifact intact and produces bounded recovery information.
