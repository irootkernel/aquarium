# Bundle Manifest

The manifest is an external, read-only request input. It is not Aquarium project state, a version registry, a discovery root, or authority to mutate a repository. The user may choose any file name and location and must pass its path explicitly to `$aquarium:dev-setup-bundle`.

Runtime normalization requires Python 3.10 or newer and PyYAML 6.x supplied by the user. The skill never installs or upgrades either dependency; a missing or unsupported dependency produces a JSON error before manifest or repository discovery.

## Format

```yaml
schema: aquarium.dev-setup-bundle/v1

defaults:
  tools: [mulgae, gaori, podway, ouroboros, lora, deslop]
  project_mcp: [mulgae, gaori]
  agents_guidance: skip

targets:
  - path: ../dolgorae/gaori

  - path: ../ember-quest/ember-quest
    include: [sanho]
    exclude: [ouroboros]
    project_mcp_include: []
    project_mcp_exclude: [gaori]
    agents_guidance: propose
```

The top-level mapping accepts exactly `schema`, `defaults`, and `targets`. `schema` must be `aquarium.dev-setup-bundle/v1`. `defaults` accepts exactly `tools`, `project_mcp`, and `agents_guidance`; all three are required. `targets` must be a non-empty sequence.

Supported tools are `sanho`, `mulgae`, `gaori`, `podway`, `ouroboros`, `lora`, and `deslop`. `defaults.tools` may be empty only when every target gains at least one effective tool through `include`. A target accepts exactly `path`, `include`, `exclude`, `project_mcp_include`, `project_mcp_exclude`, and `agents_guidance`; only `path` is required, and omitted list overrides are empty.

For each target, effective tools are `defaults.tools` plus `include` minus `exclude`. Effective project MCP selections are `defaults.project_mcp` plus `project_mcp_include` minus `project_mcp_exclude`. The same value may not appear in both sides of one override, project MCP supports only `mulgae` and `gaori`, and every effective MCP selection must also be an effective tool. Each list must contain unique strings.

`agents_guidance` must be `skip` or `propose`. A target value overrides the default. `propose` authorizes only preparation of the existing `dev-setup` AGENTS.md proposal; applying the displayed diff remains separately approved.

Paths may be absolute or relative to the manifest directory. Each must resolve inside a Git worktree; the normalizer returns its canonical Git root. Globs and environment or tilde expansion are not performed. Targets that resolve to the same canonical Git root or shared Git common directory are all invalid so one repository cannot receive ambiguous selections across linked worktrees.

Do not put credentials, provider secrets, private configuration values, a Sanho documentation URL, commands, versions, or arbitrary tool settings in this file. `dev-setup` discovers safe existing values and asks separately for required identifiers or approvals.

## Validation Result

The normalizer emits `aquarium-dev-setup-bundle-plan.v1` JSON with the absolute manifest path and SHA-256, the selected shared-tool union, and ordered targets. A syntactically valid manifest may contain isolated targets with `status: invalid` and bounded `reason_codes`; valid targets remain available. A schema, key, type, alias, YAML merge key, duplicate mapping key, or selection error emits `aquarium-dev-setup-bundle-error.v1` and performs no target discovery. Missing or unsupported Python or PyYAML uses the same error envelope with `runtime_dependency_missing` or `runtime_dependency_unsupported`.
