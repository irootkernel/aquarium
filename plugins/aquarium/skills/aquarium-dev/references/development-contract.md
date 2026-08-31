# Aquarium Development Channel Contract

This reference is the shared contract for `aquarium-dev` producers and the host manager. The initial platform is Darwin arm64. Development artifacts are local integration evidence, never stable release or distribution evidence.

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

One project ID owns at most one canonical checkout. Same-checkout enrollment is idempotent while the manager block is current. A different checkout transfer or same-checkout migration from a recorded legacy manager path requires explicit re-enrollment approval and replaces only the exact recorded hook block. Every touched hook and enrollment record is restored on failure. Symbolic hooks, external `core.hooksPath`, malformed markers, changed owned bytes, or ambiguous state fail closed.

Publication validates the producer description, manifest, Git identity, artifact containment, entrypoints, and checksum before sealing a generation. Foreground executables atomically advance `current/<project-id>` immediately. Managed services atomically advance only `pending/<project-id>` and keep the old command/controller/service generation active while busy. Under the generic service lock, an approved controller apply must report the exact target identity without recovery debt and a matching ready or busy status before Aquarium atomically advances `current`, exposes the command, clears pending, and cleans the superseded generation when its leases permit. Failure preserves the prior selected generation and pending recovery target. Every consumer holds a shared generation lease for its complete process lifetime; managed-service consumers also hold the shared service-generation lock. Cleanup never removes current or pending generations. Plugin generations are retained until a lease-aware plugin consumer owns their complete use lifetime.

The controller protocol is closed and producer-owned:

```text
libexec/aquarium-dev-service status --json --runtime-root <absolute-root>
libexec/aquarium-dev-service plan --json --runtime-root <absolute-root> --generation-root <absolute-generation>
libexec/aquarium-dev-service apply --json --runtime-root <absolute-root> --generation-root <absolute-generation> --plan-token <exact-token>
```

Results use `aquarium-dev-service-status/v1`, `aquarium-dev-service-plan/v1`, and `aquarium-dev-service-result/v1`. Aquarium owns only immutable publication, generic locks, active/pending selection, strict result validation, and the approval boundary. The producer owns LaunchAgents, daemon arguments, sockets, registries, logs, service recovery, and every tool-specific state transition.

The native `post-commit` marker queues only the completed local-main SHA and starts the per-project worker. A failed request remains recoverable and records one bounded diagnostic. Git history is never rewritten or rolled back.

## Launcher and environment

The separately approved user-local launcher is installed only at `~/.local/bin/aquarium-dev`. `aquarium-dev <tool> [args...]` accepts only `podway`, `mulgae`, `gaori`, `sanho`, or `dolgorae`, copies the current environment, preserves `CODEX_HOME` byte-for-byte when present, and prepends `~/.aquarium-dev/bin` to the child `PATH`. A selected foreground generation is leased and executed exactly; an absent foreground tool alone resolves from the caller's original global `PATH` after excluding `~/.aquarium` and `~/.aquarium-dev`. A managed-service command executes only when its strict controller status reports the same active generation as ready or busy while the launcher holds both generation and service locks. Missing, pending, invalid, mismatched, stopped, or recovering managed-service state fails closed without production fallback. The producer's command entrypoint owns tool-specific development arguments such as Podway's `--dev`; Aquarium does not synthesize them. Lease descriptors survive `exec` and are released only when that process exits. The launcher does not read or mutate Codex authentication, plugins, skills, apps, or MCP configuration.

Dolgorae remains unenrolled until its repository creates and validates the approved producer commit, enrolls that canonical checkout, and publishes the exact committed generation. Before enrollment, the launcher resolves the required global Dolgorae; if neither generation exists, it fails closed and requests `$aquarium:dev-setup`. Podway is the first required managed service and never falls back from `aquarium-dev` to the stable production CLI. Its v0.2.8 producer/controller and real service lifecycle remain an external `TASK-011` handoff blocker. Aquarium production workflows retain their separate global-release consumer contracts and never substitute a development generation. Sanho remains explicitly optional.
