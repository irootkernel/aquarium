# ADR-0007: Use Host-Local Immutable Development Artifacts

**Status:** `Superseded`

**Superseded by:** [ADR-0008](0008-separate-development-and-production-environments.md)

**Recorded:** `2026-08-28`

## Context

The Aquarium development channel must let Aquarium and its integrated tools exercise artifacts built from an exact clean local `main` commit without replacing stable global installations. The first supported host is Apple Silicon macOS. The design depends on filesystem atomicity, process-safe leases, cooperative Git hooks, and a Codex home whose configuration and login state cannot leak from the stable environment.

The feasibility suite exercises these assumptions in temporary directories and repositories. It does not enroll a checkout, install a permanent hook, modify a consumer repository, or claim that a development artifact is release-ready.

## Evidence

On Apple Silicon macOS, the feasibility suite proves the following bounded properties:

- BSD `flock(2)`, exposed through Python `fcntl.flock`, permits concurrent shared leases and excludes a publisher or cleanup process while an invocation holds a shared lease.
- A staged immutable artifact directory can be promoted with `os.replace` on one filesystem, and a temporary symbolic-link selector can atomically replace the previous `current` selector.
- An Aquarium-owned marker block can coexist with and preserve a foreign executable `post-commit` hook. A failing request command can write a diagnostic while `git commit` remains successful and the commit object and branch advancement remain complete.
- A child process can retain a shared lease on one immutable artifact while publication advances `current` to a newer artifact. Cleanup cannot take the exclusive lease until that child exits.
- A dedicated `CODEX_HOME` selects only its own `config.toml` and `auth.json`; stable-home files are neither read nor copied by the isolated invocation probe.

`tests/unit/test_aquarium_dev_feasibility_unit.py` is the executable evidence. It fails, rather than skips, outside the supported Darwin/arm64 host so an unsupported machine cannot accidentally satisfy this decision.

The five initial repositories were also inspected read-only during adoption. They used Git's default hook directory and had no existing `post-commit` hook at that point. This observation only establishes the current integration baseline; the implementation must still preserve arbitrary foreign hook bytes and mode and fail closed on ownership conflicts.

## Decision

Use host-local immutable artifacts rooted under `~/.aquarium/`, with no repository-local Aquarium state and no top-level `~/.aquarium/bin/`. Publish only artifacts built from an exact, clean local `main` commit. Promote a completed staging directory within the destination filesystem, then atomically replace a `current` symbolic-link selector.

Use one operating-system lock file per immutable artifact. Invocations acquire a shared lease before resolving and launching the artifact and keep the lease for the complete child-process lifetime. Publication never mutates an artifact. Cleanup requires an exclusive non-blocking lease and may remove a superseded artifact only after the last invocation releases it. Time-based grace periods are not correctness authority.

Integrate with a native `post-commit` hook through one bounded Aquarium-owned marker block. Preserve all unrelated hook bytes and executable mode. Treat symbolic hooks, an external `core.hooksPath`, malformed or duplicate markers, and ownership drift as diagnosis errors requiring repair approval. The hook only records an exact-SHA request and starts asynchronous processing; it never builds synchronously. A request or worker failure must not attempt to rewrite, reset, or roll back the completed Git commit.

Run the development Codex environment with a dedicated `CODEX_HOME` under `~/.aquarium/codex/`. Configure its local Aquarium plugin, paired skills, MCP servers, and resolved tool artifacts without reading or copying the stable Codex configuration or authentication files. If the isolated home is not authenticated, report the exact login action and stop; Aquarium never performs authentication.

These decisions constrain the shared contract in `TASK-006`:

- project identity, full Git SHA, next development version, artifact kind, immutable relative path, and SHA-256 digest are explicit producer data;
- the human-readable development version uses `v<next>-dev.<12-hex>` while the full SHA remains separately authoritative;
- producer output is contained by an explicit absolute staging directory on the destination filesystem;
- enrollment, current selection, locks, requests, diagnostics, runtime state, and isolated Codex state have separate host-local directories;
- no enrollment permits stable fallback, while an enrolled but invalid development state fails closed;
- post-commit publication is asynchronous, serialized per project, and retains the previous current artifact on any build or validation failure.

## Platform Limitations

- The initial contract supports Darwin on arm64 only. Other operating systems and architectures require their own feasibility evidence and a later explicit contract change.
- Atomic replacement is guaranteed only when staging and destination are on the same filesystem.
- The lease contract relies on local BSD advisory locks. Network filesystems and processes that ignore the lock protocol are unsupported.
- Git hook coexistence is limited to a regular, repository-local native hook managed through the agreed marker block. Framework-managed or external hook paths require a future explicit integration.

## Rejected Alternatives

- A mutable shared executable path was rejected because publication could change bytes underneath a running process.
- Process IDs, timestamps, and cleanup grace periods were rejected as lease authority because they cannot prove that an artifact is no longer in use.
- Building inside `post-commit` was rejected because it adds commit latency and couples build failure to Git's command result.
- Replacing the complete hook was rejected because it would destroy unrelated repository automation.
- Falling back to stable tools after an enrolled development state breaks was rejected because it hides integration failures.
- Reusing the stable Codex home or copying its authentication state was rejected because it couples development mutations and credentials to the stable environment.
- Branch names, dirty working-tree bytes, and ahead-of-remote status were rejected as artifact identity. Only a clean local `main` exact commit is accepted; remote publication remains a separate release concern.

## References

- [Aquarium development environment dossier](../todo/TODO-AQUARIUM-DEV.md)
- [No central Aquarium state](0003-no-central-aquarium-state.md)
- [Separate effect approvals](0005-separate-effect-approvals.md)
- [State and evidence architecture](../architecture/state-and-evidence.md)
