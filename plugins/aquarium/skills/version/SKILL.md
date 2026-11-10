---
name: version
description: "Report the current Aquarium plugin and supported tools' installed versions alongside their official GitHub latest stable releases. Use for $aquarium:version or requests to check Aquarium and tool versions."
---

# Aquarium versions

Resolve this skill's directory and run:

```text
python3 <skill-directory>/scripts/inspect_versions.py
```

Before running, disclose the read-only official GitHub release, tag and commit
metadata requests. Invocation authorizes those reads for the catalogued sources;
it does not authorize downloads, installation, configuration or upgrades. For an
offline request, append `--offline`. The helper needs only Python's standard library
and does not require setup or the `aquarium-status` runtime.

Present the JSON result as a table with Component, Local version, GitHub latest
version and Comparison columns. Include the observation time, official source links
and local executable or skill paths. Keep individual failures visible while
reporting the remaining rows. Exit zero means a report was produced, not that every
probe succeeded. Show safe failure reason codes and any exit/HTTP status; do not
print raw exception text or command stderr. `no_release` with reason
`no_stable_release` means no published stable Release, including prerelease-only
repositories. Do not display an Aquarium supported-version column.

The local Aquarium row reports the manifest of the package containing this
invoked skill. Label it installed only when the host identifies this skill as
belonging to its installed plugin. For an explicit development-source invocation,
label the row Aquarium (source package). If neither origin is established, label
it Aquarium (package origin unknown). A .git directory or cache-like path alone
does not establish origin. Never select another cached package or a working
checkout as a substitute. `aquarium-status` reporter versions describe
that separately installed runtime's originating plugin, not the active plugin.

CLI rows describe the executable selected on PATH, not attached MCP servers or
running services. Skill rows inspect the active Codex home and shared skill root;
missing version metadata or ambiguous copies remain version-unverifiable. Do not
infer a version from presence, modification time or the upstream latest release.

GitHub latest means the official latest non-draft, non-prerelease Release, without
limiting it to Aquarium's supported release line. Lora uses its newest stable tag,
or a disclosed main commit when none exists. Deslop uses its upstream main commit.
Label commits as source references rather than versions and leave their comparison
unverifiable. Preserve prerelease and build identifiers; unequal non-stable local
versions remain comparison-unverifiable. Release absence, lookup failure and
offline/not-requested are separate states.

The [tool catalog](../../references/tool-catalog.md) owns official sources and
installation locations. This skill inventories versions; it does not assess live
health or compatibility, run setup diagnostics, read the setup ledger, invoke
providers, install tools, modify state, stage changes or publish anything. Route
requested upgrades through the host's plugin management for Aquarium and
`aquarium:dev-setup-global` for its owned tools. Herdr keeps its upstream setup
ownership.
