# Bundle Manifest

The manifest is an external, read-only request input. It is not Aquarium project state, a version registry, a discovery root, or authority to mutate a repository. The user may choose any file name and location and must pass its path explicitly to `$aquarium:dev-setup-bundle`.

Runtime normalization requires Python 3.10 or newer and PyYAML 6.x supplied by the user. The skill never installs or upgrades either dependency; a missing or unsupported dependency produces a JSON error before manifest or repository discovery.

## Format

```yaml
schema: aquarium.dev-setup-bundle/v1

defaults:
  tools: [dolgorae, mulgae, gaori, podway, ouroboros, lora, deslop]
  project_mcp: []
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

Supported tools are `sanho`, `dolgorae`, `mulgae`, `gaori`, `podway`, `ouroboros`, `lora`, and `deslop`. `defaults.tools` may be empty only when every target gains at least one effective tool through `include`. A target accepts exactly `path`, `include`, `exclude`, `project_mcp_include`, `project_mcp_exclude`, and `agents_guidance`; only `path` is required, and omitted list overrides are empty.

For each target, effective tools are `defaults.tools` plus `include` minus `exclude`. Selected Mulgae and Gaori MCP registrations are user-global by default and are prepared once as shared components. The retained v1 `project_mcp` field is an explicit local-scope override: effective local overrides are `defaults.project_mcp` plus `project_mcp_include` minus `project_mcp_exclude`. Keep the default empty unless repositories intentionally require root-bound MCP registrations. The same value may not appear in both sides of one override, local MCP overrides support only `mulgae` and `gaori`, and every effective override must also be an effective tool. Each list must contain unique strings.

`agents_guidance` must be `skip` or `propose`. A target value overrides the default. `propose` preselects preparation of the complete `dev-setup` repository operating-guidance proposal: the root AGENTS.md structure, mandatory project-specific commit-message rule, evidence-based project index, applicable Aquarium references, and root CLAUDE.md delegation. It does not supply a missing commit-header convention or resolve conflicting existing guidance; `dev-setup` asks for those decisions before finalizing the proposal. Applying the complete displayed diff remains separately approved.

Paths may be absolute or relative to the manifest directory. Each must resolve inside a Git worktree; the normalizer returns its canonical Git root. Globs and environment or tilde expansion are not performed. Targets that resolve to the same canonical Git root or shared Git common directory are all invalid so one repository cannot receive ambiguous selections across linked worktrees.

Do not put credentials, provider secrets, private configuration values, a Sanho documentation URL, commands, versions, or arbitrary tool settings in this file. `dev-setup` discovers safe existing values and asks separately for required identifiers or approvals.

## Validation Result

The normalizer emits `aquarium-dev-setup-bundle-plan.v1` JSON with the absolute manifest path and SHA-256, the selected shared-tool union, and ordered targets. A syntactically valid manifest may contain isolated targets with `status: invalid` and bounded `reason_codes`; valid targets remain available. A schema, key, type, alias, YAML merge key, duplicate mapping key, or selection error emits `aquarium-dev-setup-bundle-error.v1` and performs no target discovery. Missing or unsupported Python or PyYAML uses the same error envelope with `runtime_dependency_missing` or `runtime_dependency_unsupported`.
