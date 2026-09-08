# Aquarium Development Channel Contract

This reference is the shared contract for `aquarium-dev` producers and the host manager. The initial platform is Darwin arm64. Development artifacts are local integration evidence, never stable release or distribution evidence.

## Distribution and invocation

Aquarium bundles the Python manager, CLI, and stdio MCP server under `tools/aquarium-dev/`. There is no `aquarium-dev` skill. Use this channel only on an explicit development-channel request. Tool descriptions and server instructions explain when to call each operation. The manager validates inputs and approvals before applying changes.

The plugin's `.mcp.json` registers one server. It exposes `aquarium_dev_diagnose`, `aquarium_dev_enroll`, `aquarium_dev_repair_hook`, `aquarium_dev_rebuild`, `aquarium_dev_service_plan`, and `aquarium_dev_service_apply`. Inputs use absolute repository paths, supported project IDs, approval booleans, and the exact native service token as applicable. Unknown fields and wrongly typed approvals are rejected before dispatch. A boolean records user consent; tool availability never supplies it. Worker and cleanup operations are internal CLI operations, not MCP tools.

Both interfaces use the same operation dispatcher. MCP returns the CLI envelope as structured content and serialized text, and sets `isError` on failures. Invalid arguments retain exit code 2; unexpected execution exceptions return `internal_error` in the same error envelope with exit code 1. Process-exit and interrupt signals propagate. MCP runs blocking operations outside the protocol event loop. After any effect, diagnose again. If a call is interrupted or reports an internal error, inspect the current state before retrying. An error or missing response does not establish whether effects occurred.

The public CLI supports the existing manager commands as `aquarium-dev <operation> [options]` and preserves `aquarium-dev <tool> [args...]` for the five supported executable producers. `aquarium-dev version` reports the installed runtime receipt. `aquarium-dev mcp` starts that installed runtime's stdio server.

### Explicit runtime installation and updates

The existing `dev-setup-global` skill owns optional runtime setup. The bundled `tools/aquarium-dev/install.py diagnose` reads installed-versus-bundled identity without creating host state. `install.py install --approve-install --approve-launcher` installs or updates only after separate runtime and launcher approvals. It requires Python 3.11 or newer, downloads exact hash-verified binary wheels from PyPI into a private virtual environment, verifies the SDK and copied source, and then selects the new runtime. It never enrolls a repository or migrates hooks during installation.

The runtime source digest covers the Aquarium plugin version, every packaged Python source file, and the dependency lock. Installed generations live at `manager/versions/<source-sha256>-py<major>.<minor>/`, each with `runtime.json` and `venv/`. Recovery generations append `-r<32-lowercase-hex-UUID>` to that directory name and use the same receipt schema. Installation reuses a generation only after validating its receipt, source, and environment, including the same venv path checks used at startup. It preserves damaged directories and prepares a separate recovery generation with an atomic receipt write. `manager/current` selects a validated generation. The regular-file entry at `~/.local/bin/aquarium-dev` resolves that selector without depending on a plugin cache path. A failed update restores the prior launcher and selector. Prior generations remain available for admitted workers and existing MCP sessions. CLI and MCP bootstrap interpreters ignore ambient Python settings and user-site packages before selecting the installed runtime. Worker and cleanup subprocesses retain that isolation and disabled bytecode writes. These interpreter options preserve the environment variables inherited by producer commands.

Plugin updates never install or select a runtime automatically. The plugin MCP launcher rejects a source-identity mismatch with setup guidance; the installed CLI and hooks bound to the stable entry continue using their runtime until an explicit update. Legacy hooks depend on their recorded script path and need approved migration if an update removes that script. Restart Codex after installation or update. Do not add a duplicate global MCP registration or a replacement paired skill. Setup diagnostics use `aquarium-dev-runtime-inspection/v1`, receipts use `aquarium-dev-runtime/v1`, and setup/startup errors use `aquarium-dev-runtime-error/v1`.

Environment verification failures retain the child exit code and the last 4 KiB of stderr in the diagnosis. Failed installation cleanup preserves the original installation error; an unremovable, unselected generation may remain and is not reused unless it passes full validation.

Both runtime installation and `install-launcher` require the launcher itself to be a regular file or absent, and reject dangling links. Its parent directories may be symbolic links. The manager runtime tree keeps its stricter non-symbolic path checks.

## Producer contract

Every producer implements:

```text
make aquarium-dev-describe
make aquarium-dev-build AQUARIUM_DEV_OUTPUT=<absolute-empty-directory>
```

The describe target emits one supported `aquarium-dev-producer-description` JSON object. The build target accepts only a clean local `main`, consumes committed bytes, writes only below the supplied directory, and emits the matching exact-SHA `aquarium-dev-artifact-manifest` object. Supported project IDs are `aquarium`, `podway`, `mulgae`, `gaori`, `sanho`, and `dolgorae`.

Contract v1 remains frozen for Aquarium's one `codex-plugin` and foreground tools' one `executable` at `bin/<project-id>`. Podway no longer admits v1 because its daemon-backed development runtime requires the v2 `managed-service` contract. Other tool IDs may adopt v2 later without changing the manager lifecycle.

Contract v2 describes one bundle at `artifact_path: bundle`, a public development-safe command at `command_path: bin/<project-id>`, and a producer-owned controller at `controller_path: libexec/aquarium-dev-service`. Manifests additionally bind the full lowercase Git SHA, `v<next>-dev.<sha12>` development version, and canonical bundle `sha256:` digest. Every path is normalized and contained; the command and controller are regular executable files inside the bundle. The controller may own one or more internal daemons without exposing their paths to Aquarium.

The canonical plugin-directory digest visits regular files in ascending UTF-8 artifact-relative POSIX-path order and hashes each path, one NUL byte, the file's raw SHA-256 digest, and one newline. Empty directories contribute nothing. Symlinks and special files are invalid.

## Manager interface

Successful commands emit one `aquarium-dev-manager-result/v1` object. Operations are `diagnose`, `enroll`, `rebuild`, `publish`, `repair`, `install-launcher`, `service-plan`, and `service-apply`; statuses are `success`, `no-change`, and `diagnosed`. Rejections emit one `aquarium-dev-error/v1` object and fail closed.

Diagnosis, controller `status`, and controller `plan` are read-only. Enrollment, hook mutation, build, managed-service `apply`, and launcher installation remain independent approvals. A service plan binds `install`, `activate`, `repair`, `defer`, or `no-change` to the observed active generation, exact target generation, busy state, and a confirmation token for every applicable mutation. `service-apply` re-runs the plan and rejects an absent or stale token. The manager does not resolve or install production tools and has no Codex-home configuration, authentication, plugin installation, or MCP configuration operation.

## Host layout

All development state is below `~/.aquarium-dev/`:

```text
manager/versions/<source-sha256>-py<major>.<minor>/
manager/current
manager/install.lock
enrollments/<project-id>.json
artifacts/<project-id>/<full-git-sha>/
current/<project-id>
pending/<project-id>
bin/<project-id>
runtime/<project-id>/
locks/publisher/<project-id>.lock
locks/artifacts/<project-id>/<full-git-sha>.lock
locks/services/<project-id>.lock
queue/<project-id>/<full-git-sha>.json
diagnostics/<project-id>/latest.json
```

Executable and activated managed-service producers receive a `bin/<project-id>` entry. It is a stable relative symlink through `current/<project-id>` to the command inside the selected immutable generation. A newly published managed-service generation remains under `pending/<project-id>` until its producer controller activates the exact service generation. Plugin artifacts have no command entry. Generic managed-service runtime is contained below `runtime/<project-id>`; Aquarium never interprets or edits its producer-owned contents. No development state is written below `~/.aquarium`, and no `codex/` runtime exists.

## Enrollment, publication, and cleanup

One project ID owns at most one canonical checkout. Same-checkout enrollment is idempotent while the manager block is current. Read-only diagnosis reports `hook: outdated` when the exact recorded block is intact but differs from the current manager; `owned` requires both to match. Installed managers bind the stable `~/.local/bin/aquarium-dev` entry in the recorded hook, so runtime updates do not change its bytes. Legacy blocks bind resolved Python and manager-script paths. A different checkout transfer or same-checkout migration from a recorded legacy manager path or background-request block requires explicit re-enrollment approval and replaces only the exact recorded hook block. Migration uses `aquarium-dev enroll --repository <absolute-git-root> --approve-enrollment --approve-hook --approve-reenrollment`; `repair-hook` restores only a block that already matches that manager. Every touched hook and enrollment record is restored on failure. Symbolic hooks, external `core.hooksPath`, malformed markers, changed owned bytes, or ambiguous state fail closed.

Publication validates the producer description, manifest, Git identity, artifact containment, entrypoints, and checksum before sealing a generation. Foreground executables atomically advance `current/<project-id>` immediately. Managed services atomically advance only `pending/<project-id>` and keep the old command/controller/service generation active while busy. Under the generic service lock, an approved controller apply must report the exact target identity without recovery debt and a matching ready or busy status before Aquarium atomically advances `current`, exposes the command, clears pending, and cleans the superseded generation when its leases permit. Failure preserves the prior selected generation and pending recovery target. Every consumer holds a shared generation lease for its complete process lifetime; managed-service consumers also hold the shared service-generation lock. Cleanup never removes current or pending generations. Plugin generations are retained until a lease-aware plugin consumer owns their complete use lifetime.

The controller protocol is closed and producer-owned:

```text
libexec/aquarium-dev-service status --json --runtime-root <absolute-root>
libexec/aquarium-dev-service plan --json --runtime-root <absolute-root> --generation-root <absolute-generation>
libexec/aquarium-dev-service apply --json --runtime-root <absolute-root> --generation-root <absolute-generation> --plan-token <exact-token>
```

Results use `aquarium-dev-service-status/v1`, `aquarium-dev-service-plan/v1`, and `aquarium-dev-service-result/v1`. Aquarium owns only immutable publication, generic locks, active/pending selection, strict result validation, and the approval boundary. The producer owns LaunchAgents, daemon arguments, sockets, registries, logs, service recovery, and every tool-specific state transition.

The native `post-commit` marker silently skips non-main branches and detached HEAD, while explicit `request` commands reject them. On local main it runs request admission synchronously. It records the completed local-main SHA with an atomic queue-file write before starting the per-project worker in a new session with detached standard streams. The hook waits for admission and worker launch, then returns without waiting for the build. It suppresses successful request output, preserves stderr, and reports a request failure without stopping later hook commands or undoing the commit. A worker-launch failure reports `worker_failed`, attempts to save one bounded diagnostic, and leaves the queued request available for an approved rebuild. Queue storage failures also report `worker_failed`, without claiming that the request was admitted. If diagnostic storage fails, the original structured error remains on stderr with the storage failure appended. Git history is never rewritten or rolled back.

Each producer description and build-target probe has a 30-second execution limit. Timeout handling terminates the process group with bounded cleanup and reports `producer_build_timeout`. A successful approved rebuild removes only the valid queued request matching its project, checkout, and SHA, under the publisher lock. Failed publication preserves the request; a cleanup failure after publication reports `publication_failed` and states that the generation was published. Managed-service recovery publishes pending and does not activate the service.

## Launcher and environment

The separately approved user-local launcher is installed only at `~/.local/bin/aquarium-dev`. `aquarium-dev <tool> [args...]` accepts only `podway`, `mulgae`, `gaori`, `sanho`, or `dolgorae`, copies the current environment, preserves `CODEX_HOME` byte-for-byte when present, and prepends `~/.aquarium-dev/bin` to the child `PATH`. A selected foreground generation is leased and executed exactly; an absent foreground tool alone resolves from the caller's original global `PATH` after excluding `~/.aquarium` and `~/.aquarium-dev`. A managed-service command executes only when its strict controller status reports the same active generation as ready or busy while the launcher holds both generation and service locks. Missing, pending, invalid, mismatched, stopped, or recovering managed-service state fails closed without production fallback. The producer's command entrypoint owns tool-specific development arguments such as Podway's `--dev`; Aquarium does not synthesize them. Lease descriptors survive `exec` and are released only when that process exits. The launcher does not read or mutate Codex authentication, plugins, skills, apps, or MCP configuration.

Dolgorae remains unenrolled until its repository creates and validates the approved producer commit, enrolls that canonical checkout, and publishes the exact committed generation. Before enrollment, the launcher resolves the required global Dolgorae; if neither generation exists, it fails closed and requests `$aquarium:dev-setup-global`. Podway is the first required managed service and never falls back from `aquarium-dev` to the stable production CLI. Its v0.2.8 producer/controller and real service lifecycle remain an external `TASK-011` handoff blocker. Aquarium production workflows retain their separate global-release consumer contracts and never substitute a development generation. Sanho remains explicitly optional.
