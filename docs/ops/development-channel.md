# Development Channel Runbook

## Target and Prerequisites

This runbook is for an Aquarium maintainer operating a named canonical checkout on Apple Silicon macOS. The checkout must be a regular Git root on local `main` and expose both development producer Make targets. Use Aquarium's bundled MCP tools or the `aquarium-dev` CLI; the [development contract](../../plugins/aquarium/references/development-contract.md) owns approvals and command behavior.

Development setup changes only the named checkout's Aquarium hook marker and host-local state below `~/.aquarium-dev/`. Enrollment, hook mutation, build, managed-service activation, and installation of `~/.local/bin/aquarium-dev` each require separate approval. The workflow does not configure Codex, authentication, plugins, or MCP servers.

## Install the Manager

Ask `$aquarium:dev-setup-global` to install or update only `aquarium-dev`. It diagnoses the bundled and installed versions before proposing an effect. For direct use, replace `<plugin-root>` with the exact installed Aquarium plugin directory:

```text
python3 <plugin-root>/tools/aquarium-dev/install.py diagnose
python3 <plugin-root>/tools/aquarium-dev/install.py install --approve-install --approve-launcher
```

The second command requires prior runtime and launcher approval. It downloads hash-pinned Python wheels, creates a private runtime below `~/.aquarium-dev/manager/`, and installs `~/.local/bin/aquarium-dev`. Put `~/.local/bin` on the caller's `PATH`, or use the absolute executable path. Installation does not enroll a checkout or change its hook. Restart Codex after installation to load the plugin's MCP tools; no separate `aquarium-dev` skill or global MCP registration is needed.

Use the same explicit install command after an Aquarium plugin update. Until then the installed CLI and hooks bound to `~/.local/bin/aquarium-dev` keep their runtime, and a mismatched plugin MCP server reports that an update is required. Legacy hooks still depend on their recorded Python and manager-script paths. If an update removes that script, build requests fail until the approved migration described below. Previous runtime generations remain available for already admitted workers and sessions. If installation was interrupted or a generation is damaged, repeat the explicit install command: it prepares a separate recovery generation and preserves existing directories, the launcher, and the selector until the replacement is verified.

## Diagnose and Establish

1. Ask Aquarium to diagnose the development channel for the exact checkout, or run `aquarium-dev diagnose --repository <absolute-git-root>`, and review the read-only result.
2. Resolve any reported non-main, dirty-tree, identity, producer, enrollment, or hook condition before approving an effect.
3. Approve enrollment and the exact native hook marker independently. Re-enrollment additionally requires approval to transfer ownership from the displayed old checkout or migrate a recorded legacy block on the same checkout.
4. Approve the initial build. A foreground producer advances its current generation immediately; a managed-service producer publishes one pending generation while preserving its active command and service.
5. For a managed service, inspect the read-only service plan and separately approve application of its exact plan token. Success requires the producer-owned controller to report the target generation ready before Aquarium advances current.
6. Re-run diagnosis after each effect and confirm the current or pending generation.
7. Run `aquarium-dev <tool> [args...]` and confirm that a selected command resolves from `~/.aquarium-dev/bin`, an absent foreground generation resolves only that tool from the caller's global PATH outside both Aquarium roots, and the caller's remaining environment is unchanged. A managed service must match the selected generation and must fail closed without production fallback when absent, pending, stopped, mismatched, or recovering. Unknown commands and invalid selected generations must fail.

Success means enrollment and the owned hook are healthy, the atomic current selector and stable command indirection resolve one validated generation, every managed service reports that exact generation ready or busy, and the launcher preserves the caller's selected `CODEX_HOME`. Each tool repository performs this enrollment when its approved producer commit is created. Dolgorae production reviews continue to require the verified global release even after a development generation is enrolled. Production readiness separately requires supported global Podway, Mulgae, Gaori, and Dolgorae binaries; Sanho is optional.

## Updates and Repair

The `post-commit` hook on enrolled canonical local `main` waits for the exact-SHA request to reach the queue and for the detached worker to start. The build continues after the commit command returns. Admission and worker-launch failures appear on stderr without undoing the commit; a worker-launch failure also leaves the request in the queue and attempts to save a diagnostic. Use diagnosis to confirm publication. An `owned` hook matches both the enrollment record and the current manager; it does not prove that a request ran or a build succeeded. An `outdated` hook matches the record but needs migration to the current manager.

Diagnosis reports `outdated` for intact recorded hooks from an older manager, including hooks that background `request`. After approving enrollment, hook replacement, and same-checkout migration, use the updated manager's `enroll --repository <git-root> --approve-enrollment --approve-hook --approve-reenrollment`. This replaces only the exact recorded block, preserves other hook content and permissions, and restores the hook and record if migration fails. `repair-hook` does not migrate an older block.

After build approval, run `aquarium-dev rebuild --repository <absolute-git-root> --approve-build` to recover a missed build without another commit. Successful publication removes only a valid queued request for that exact project, checkout, and SHA. Failed builds preserve the request. If queue cleanup fails after publication, the error states that publication completed; restore queue access and repeat the approved rebuild. For Podway, a recovered build publishes a pending generation; activation still requires a separately approved service plan. Never edit enrollment JSON, selectors, manifests, locks, or hook markers manually.

The generated hook silently skips feature branches and detached HEAD. Direct `request` commands still reject them. Each producer description or build-target probe has a 30-second timeout, followed by bounded process cleanup; a blocked probe reports `producer_build_timeout`. Queue storage failures report `worker_failed` without claiming admission succeeded. If diagnostic storage also fails, stderr retains the original structured error and explains that the diagnostic could not be saved.

A failed build or service activation preserves the previous current artifact. A managed-service build may remain pending while the producer reports busy. A missing or corrupt artifact, checkout mismatch, invalid enrollment, controller failure, or service-generation mismatch fails closed. Stop and follow the machine-reported action. Escalate when repair would require replacing ambiguous hook content, selecting another canonical checkout, changing producer code, or touching state outside the displayed Aquarium-owned paths.

Do not place development state under `~/.aquarium/`, and do not treat a successful development run as release QA or distribution evidence.
