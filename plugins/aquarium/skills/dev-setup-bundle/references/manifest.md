# Bundle Manifest

The manifest is an explicit external request, not Aquarium project state or a repository discovery root. Start from the [placeholder template](../../../assets/templates/aquarium-dev-setup-bundle.template.yaml), replace its paths and Project slug, and pass the resulting manifest path to `$aquarium:dev-setup-bundle`. The skill reads it without editing or tracking it. Normalization requires Python 3.10 or newer and PyYAML 6.x.

## Format

```yaml
schema: aquarium.dev-setup-bundle/v2

defaults:
  tools: [mulgae, gaori, sorage]
  global_mcp: [mulgae, gaori]
  mulgae_artist: false
  agents_guidance: skip

targets:
  - path: ../gaori
    local_mcp: [mulgae]
    sorage_project_slug: gaori

  - path: ../ember-quest
    include: [sanho]
    local_mcp: [mulgae, gaori]
    mulgae_artist: true
    agents_guidance: propose
```

The top level accepts exactly `schema`, `defaults`, and `targets`. The schema is v2 only. Defaults require `tools`, `global_mcp`, and `agents_guidance`; `mulgae_artist` is optional and defaults to `false`. Targets require `path` and may contain `include`, `exclude`, `local_mcp`, `sorage_project_slug`, `mulgae_artist`, and `agents_guidance`. v1, `project_mcp`, `project_mcp_include`, `project_mcp_exclude`, and `mcp` mappings are rejected.

Supported tools are `sanho`, `dolgorae`, `mulgae`, `gaori`, `sorage`, `podway`, `ouroboros`, `lora`, `deslop`, `humanizer`, and `im-not-ai`. Effective tools are defaults plus `include` minus `exclude`; every target must select at least one. MCP lists contain only `mulgae` and `gaori`, with no duplicates. `global_mcp` may be empty. A target's `local_mcp` tool must be effective. For each effective tool, local membership selects project registration; otherwise global membership selects shared registration; absence from both requests no MCP registration. A default global entry for a tool the target does not select is ignored. An unrequested registration is preserved and may still be exposed by Codex.

`sorage_project_slug` is allowed only when `sorage` is effective. It must match Sorage's lowercase slug shape: letters or digits joined by hyphens, without a leading or trailing hyphen. The slug identifies the intended Project; it does not authorize creation, rebinding, unarchiving, Handoff access, or Vault access. Omitting it retains native Project discovery and the existing identifier and approval flow.

`mulgae_artist` is a boolean. An explicit target value requires effective `mulgae`; `true` requires the enabled `artist` role in addition to the six non-UI roles, while `false` requires the six non-UI roles without artist. The manifest carries no provider, model, credential, or role-assignment settings. `agents_guidance` is `skip` or `propose`, with a target override of the default.

Paths may be absolute or relative to the manifest directory and must resolve to Git worktrees. Globs, environment expansion, and tilde expansion are not performed. Duplicate canonical roots or shared Git common directories are invalid. The manifest contains no credentials or private configuration.

## Normalized Result

The normalizer emits `aquarium-dev-setup-bundle-plan.v2` with the manifest path and SHA-256, the union of selected `shared_tools`, the `required_global_mcp` union over ready targets, and ordered targets. Each target reports effective tools, `global_mcp`, `local_mcp`, Sorage slug or null, artist boolean, guidance policy, repository, status, and reason codes. A structurally valid manifest may retain isolated invalid targets. Invalid YAML, schema, keys, types, or selections emit `aquarium-dev-setup-bundle-error.v2` before repository discovery. Missing or unsupported Python or PyYAML emits the same error schema with `runtime_dependency_missing` or `runtime_dependency_unsupported` before manifest or repository discovery.
