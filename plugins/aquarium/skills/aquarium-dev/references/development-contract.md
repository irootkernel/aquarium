# Aquarium Development Channel Contract

This reference is the shared contract for `aquarium-dev` producers and the host manager. The initial platform is Darwin arm64. Development artifacts are local integration evidence, never stable release or distribution evidence.

## Producer contract

Every producer implements:

```text
make aquarium-dev-describe
make aquarium-dev-build AQUARIUM_DEV_OUTPUT=<absolute-empty-directory>
```

The describe target emits exactly one `aquarium-dev-producer-description/v1` JSON object. The build target accepts only a clean local `main`, consumes committed bytes, writes only below the supplied directory, and emits exactly one `aquarium-dev-artifact-manifest/v1` object. Supported project IDs are `aquarium`, `podway`, `mulgae`, `gaori`, and `sanho`; Dolgorae is not supported. Aquarium produces one `codex-plugin`; every tool producer emits one `executable` at exactly `bin/<project-id>`.

Descriptions contain exactly `schema`, `project_id`, `next_version`, `artifact_kind`, and `artifact_path`. Manifests additionally bind the full lowercase Git SHA, `v<next>-dev.<sha12>` development version, and canonical `sha256:` digest. Paths are normalized contained relative paths without `.` or `..` components, and the project-specific artifact kind and executable path are enforced in both objects.

The canonical plugin-directory digest visits regular files in ascending UTF-8 artifact-relative POSIX-path order and hashes each path, one NUL byte, the file's raw SHA-256 digest, and one newline. Empty directories contribute nothing. Symlinks and special files are invalid.

## Manager interface

Successful commands emit one `aquarium-dev-manager-result/v1` object. Operations are `diagnose`, `enroll`, `rebuild`, `publish`, `repair`, and `install-launcher`; statuses are `success`, `no-change`, and `diagnosed`. Rejections emit one `aquarium-dev-error/v1` object and fail closed.

Diagnosis is read-only. Enrollment, hook mutation, build, and launcher installation remain independent approvals. The manager does not resolve or install production tools and has no Codex-home configuration, authentication, plugin installation, or MCP configuration operation. The separate launcher owns bounded per-command global fallback.

## Host layout

All development state is below `~/.aquarium-dev/`:

```text
enrollments/<project-id>.json
artifacts/<project-id>/<full-git-sha>/
current/<project-id>
bin/<project-id>
locks/publisher/<project-id>.lock
locks/artifacts/<project-id>/<full-git-sha>.lock
queue/<project-id>/<full-git-sha>.json
diagnostics/<project-id>/latest.json
```

Only executable producers receive a `bin/<project-id>` entry. It is a stable relative symlink through `current/<project-id>` to the executable inside the selected immutable generation. Plugin artifacts have no command entry. No development state is written below `~/.aquarium`, and no `codex/` or tool-specific runtime copy exists.

## Enrollment, publication, and cleanup

One project ID owns at most one canonical checkout. Same-checkout enrollment is idempotent while the manager block is current. A different checkout transfer or same-checkout migration from a recorded legacy manager path requires explicit re-enrollment approval and replaces only the exact recorded hook block. Every touched hook and enrollment record is restored on failure. Symbolic hooks, external `core.hooksPath`, malformed markers, changed owned bytes, or ambiguous state fail closed.

Publication validates the producer description, manifest, Git identity, artifact containment, and checksum before atomically promoting and sealing a generation. It establishes or validates the stable executable indirection, then advances the single `current/<project-id>` generation selector atomically. Failure preserves the previously selected generation. Every executable consumer holds a shared generation lease for its complete process lifetime; cleanup takes the exclusive form of the same lock, never removes the current generation, and defers while any consumer remains active. Plugin generations are retained until a lease-aware plugin consumer owns their complete use lifetime.

The native `post-commit` marker queues only the completed local-main SHA and starts the per-project worker. A failed request remains recoverable and records one bounded diagnostic. Git history is never rewritten or rolled back.

## Launcher and environment

The separately approved user-local launcher is installed only at `~/.local/bin/aquarium-dev`. `aquarium-dev <tool> [args...]` accepts only `podway`, `mulgae`, `gaori`, `sanho`, or `dolgorae`, copies the current environment, preserves `CODEX_HOME` byte-for-byte when present, and prepends `~/.aquarium-dev/bin` to the child `PATH`. A selected development generation is leased and executed exactly; when no generation is selected, only that command resolves from the caller's original global `PATH` after excluding `~/.aquarium` and `~/.aquarium-dev`. An invalid selected generation fails closed. The lease descriptor survives `exec` and is released only when that process exits. It does not read or mutate Codex authentication, plugins, skills, apps, or MCP configuration.

Dolgorae remains excluded from the producer graph in this checkpoint. The launcher can resolve a globally installed Dolgorae for an explicit command, while a missing global installation affects only that invocation. Aquarium production reviews retain their separate Dolgorae consumer contract.
