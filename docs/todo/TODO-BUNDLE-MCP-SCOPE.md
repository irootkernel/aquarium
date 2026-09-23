# Bundle MCP Scope Selection

## Purpose and authority

This dossier is the temporary execution SOT for `TASK-076` under `EPIC-000`.
The [roadmap](../roadmap/README.md#epic-000-independent-tasks)
alone owns its identity, order, dependencies, and lifecycle state. This
dossier owns the planned scope and acceptance until the task promotes the
implemented behavior to the bundle manifest reference, setup skills, and
canonical specifications.

The v1 manifest treats `defaults.project_mcp` and the target include/exclude
lists as requests for project-local registrations in addition to shared global
registration. A target cannot select project-local registration without also
making the same global MCP a bundle prerequisite. Replace that contract with
v2; v1 manifests and fields are no longer accepted.

Planning this work authorizes no MCP registration change, installation,
repository setup, provider invocation, staging, commit, or publication.

## Scope contract

- Replace v1 with `aquarium.dev-setup-bundle/v2`, using required
  `defaults.global_mcp` and optional `targets[*].local_mcp` lists. Each list
  accepts only `mulgae` and `gaori`, with no duplicates. For an effective
  selected tool, membership in the target's `local_mcp` selects the project
  registration; otherwise membership in `global_mcp` selects the shared global
  registration. A tool in neither list has no requested MCP registration.
  `local_mcp` takes precedence when the tool appears in both lists.
- An empty `global_mcp` list is valid for local-only setup. A default global
  entry is ignored for a target that does not select that tool; an explicit
  target `local_mcp` entry for an unselected tool is invalid. If no ready target
  needs one global MCP registration, do not prepare it merely because its name
  appears in `defaults.global_mcp`.
- For example, `global_mcp: [mulgae, gaori]` with no target override uses both
  global registrations. A target with `local_mcp: [mulgae]` uses project-local
  Mulgae and global Gaori. A target with `local_mcp: [mulgae, gaori]` uses both
  project-local registrations. Neither local target depends on global MCP
  readiness for its locally selected tool.
- Reject `aquarium.dev-setup-bundle/v1`, `project_mcp`,
  `project_mcp_include`, `project_mcp_exclude`, and the superseded `mcp`
  mappings. Emit only the v2 normalized result with effective MCP selections
  per target and a separate union of required global MCP registrations.
  Remove v1-only parsing, routing, and tests rather than maintaining a
  compatibility path.
- Prepare selected CLIs, paired skills, and other shared global components
  once. Prepare a Mulgae or Gaori global MCP registration only when at least
  one ready target inherits that tool from `global_mcp`. A locally selected
  target requires its own project registration and must not depend on global
  MCP readiness for that tool. Where both scopes occur across targets, inspect
  and report each target's selected effective registration separately.
- Preserve unrelated Codex configuration and existing registrations. Scope
  selection does not authorize deletion of an existing global or project-local
  registration, migration of a live Codex session, or implicit workspace
  discovery. Keep registration changes under the existing action-specific
  approval boundaries.
- Compare requested scope with the effective Codex registration, not just the
  presence of a valid registration somewhere. A local registration shadowing a
  requested global one, or a global registration exposed when local was
  requested but is missing, is a scope mismatch and cannot be reported ready.
  Diagnose the exact conflicting entry and propose a bounded correction under
  the existing approval rules; do not silently delete or replace it. A tool in
  neither MCP list is unrequested, not disabled: preserve any existing
  registration and do not claim that its tools are hidden from Codex.
- Keep registration correctness separate from live tool exposure in the
  current Codex session. A configured registration does not prove that the
  session has reloaded it.
- Add optional `targets[*].sorage_project_slug` as the exact intended Sorage
  Project slug for a target that selects `sorage`. Validate it against Sorage's
  supported slug shape, compare it with the native Project resolution, and
  treat a different existing binding as a mismatch requiring a bounded
  proposal. The slug supplies identity intent, not permission to create,
  rebind, unarchive, inspect Handoffs, or touch the Vault. Reject a slug on a
  target that does not select `sorage`. An omitted slug retains native
  discovery and the existing identifier/approval flow.
- Add `defaults.mulgae_artist: false` and optional
  `targets[*].mulgae_artist: true|false`. The effective boolean selects whether
  the Mulgae `artist` role is required. `true` requires an enabled artist role;
  `false` requires the six non-UI roles without artist. Do not add provider,
  model, credential, or role-assignment settings to the manifest. Reject an
  explicit target override when `mulgae` is not an effective tool. For an
  existing valid Mulgae configuration that differs, propose an exact native
  configuration change under its existing approval boundary; never edit it
  silently or infer that a UI project exists from its path.
- Keep the reusable root manifest template as a placeholder-only example.
  Update it to v2 and show an MCP override, a Sorage slug, and an artist-role
  override. Update the ignored `.targets.yaml` request to v2 only after the
  normalizer and routing support it, preserve all 20 target identities and
  tool selections, and verify its exact normalized target list and selected
  Sorage and artist intent. The external request remains untracked and is
  never included in the task commit.
- Update the bundle, global setup, and repository setup skill contracts plus
  the manifest reference and affected canonical specifications. Update public
  descriptions that explicitly call the format v1. Do not re-register MCPs
  across the 20 target repositories as part of this contract change.

## Acceptance

1. A mixed-scope v2 fixture proves global registration is prepared once for
   targets choosing `global`, while a project-only tool requires no global MCP
   registration and reaches its own local setup path. Existing registrations
   with the wrong effective scope are reported as mismatches.
2. Normalization rejects unsupported MCP names, non-list values, duplicate
   entries or keys, local MCP selections outside effective tools, v1 schemas,
   obsolete scope fields, invalid Sorage slugs, and artist overrides on
   non-Mulgae targets without altering any manifest or repository. Tests
   exercise the v2 contract rather than preserving v1 output fixtures.
3. The exact 20-target `.targets.yaml` request and the reusable template parse
   under v2; the external request's target identities and selected tools are
   unchanged. The request records the intended slug for every selected Sorage
   Project and the artist requirement for UI targets. Neither file contains
   credentials or private configuration.
4. Focused normalizer and inspector checks, repository documentation checks,
   and `git --no-pager diff --check` pass. Master performs separate manual
   skill-behavior verification; automated checks do not claim to prove it.
