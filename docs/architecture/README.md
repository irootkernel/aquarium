# Architecture

Aquarium is distributed as one Codex plugin whose declarative workflows coordinate independently installed tools while preserving repository-local authority and explicit mutation boundaries. These documents describe the current implementation; they do not override the linked executable sources.

## Detailed Architecture

- [Components](components.md) maps the plugin package, workflow layer, local helpers, tools, and public surfaces.
- [Workflow runtime](workflow-runtime.md) follows invocation through discovery, approval, execution, and handoff.
- [State and evidence](state-and-evidence.md) separates roadmap, Procedure, Git, host, and durable evidence planes.
- [Verification](verification.md) explains the layered test architecture and the limits of each proof.
- [Development channel](development-channel.md) traces exact-main production, immutable publication, leased resolution, and isolated Codex wiring.

## Core Boundaries

- Aquarium coordinates Codex, Dolgorae, Orca, Podway, Sanho, Mulgae, Gaori, Ouroboros, Lora, and Deslop but does not vendor or own their upstream implementations.
- Skills preserve separate authority for diagnosis, network lookup, installation, provider transmission, repository mutation, commits, and publication.
- Podway and native tools own runtime and execution evidence. Ignored runtime artifacts are not roadmap history, architecture, or durable specifications.
- Canonical documentation describes current structure and delivery intent; it does not replace executable source, Git history, external release proof, or runtime activation evidence.

## Exact Authorities

The package layout and release version come from the [plugin manifest](../../plugins/aquarium/.codex-plugin/plugin.json). Workflow behavior comes from [skill entrypoints](../../plugins/aquarium/skills/) and their linked references. Installed Procedure bytes come from [Procedure assets](../../plugins/aquarium/assets/podway/procedures/). The [Makefile](../../Makefile), [TESTING.md](../../TESTING.md), and tests own executable verification.
