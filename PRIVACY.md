# Privacy

Aquarium contains instructions for Codex. The plugin does not operate a hosted service or collect telemetry itself.

Some instructed workflows can invoke local or third-party tools after explicit user approval. Two bounded read-only network operations are authorized by an explicit tool selection or skill invocation without a second network prompt.

Selecting Sanho, Mulgae, Gaori, or Podway in `dev-setup` automatically contacts that tool's official GitHub Releases metadata endpoint and `raw.githubusercontent.com`, downloads four public skill files to ephemeral storage, and compares them with the exact `~/.agents/skills/use-*` target. It sends no repository or local skill content, persists no downloaded file without separate approval, and does not authorize any other network operation or mutation.

Explicitly invoking `release-qa` automatically queries the repository's configured Git remote and hosting Release metadata to establish remote `main`, tags, and the latest stable published release. Configured Git and hosting clients may use existing ambient authentication for private repositories, but the skill does not inspect, read, copy, print, persist, refresh, or reconfigure credential material, initiate authentication, upload source, or authorize network access from QA scenarios; unavailable access leaves the QA result incomplete.

- Aquarium's trusted local commit hook receives the proposed shell command and working directory from Codex, resolves the local Git root, lists tracked paths, and reads up to two million characters from tracked roadmap candidates to detect lifecycle states. It writes no project state, stores no telemetry, and transmits none of that command, path, repository, or roadmap content over the network.
- Sanho can contact a configured documentation Git remote. Its selected-skill freshness comparison contacts GitHub automatically, and an approved `use-sanho` installation writes the verified four-file payload to a user-scoped Codex skill directory.
- Mulgae can transmit an explicitly preflighted review target to providers configured by the user and retains complete provider stdout and stderr in private local runtime artifacts. A selected Codex credential profile projects only its `auth.json` into a disposable local runtime; profile homes and credentials remain machine-local and must not be reported or committed. Its selected-skill freshness comparison contacts GitHub automatically, an approved `use-mulgae` installation writes four files below `~/.agents/skills/use-mulgae`, and an optional attached STDIO MCP process remains bound to the selected local repository. `dev-setup` does not run reviews, start the MCP server, capture a review target, invoke a provider, authenticate Codex, or transmit source.
- Lora installation contacts npm and GitHub and writes selected skills to the Codex user-global skill directory.
- Gaori stores local test logs and summaries under `.gaori/`; raw logs are intentionally unredacted and can contain sensitive process output. Its selected-skill freshness comparison contacts GitHub automatically, an approved `use-gaori` installation writes four files to a user-scoped Codex skill directory, and an optional attached STDIO MCP process remains bound to the selected local repository.
- Podway stores workspace configuration and local task history under `.podway/` and operates a same-user local daemon. It does not transmit source or evidence over the network; its selected-skill freshness comparison contacts GitHub automatically, and an approved `use-podway` installation writes four files below `~/.agents/skills/use-podway`.

Those tools and services have their own data handling policies. The skills instruct Codex not to read, print, copy, or persist credentials and not to transmit source during setup. Users should inspect proposed commands, capture sets, exclusions, and provider routing before approval.

Project configuration and generated evidence remain in the locations owned by each tool. This plugin does not create a central Aquarium project-state file.

Aquarium procedures instruct agents to record bounded summaries, revisions, exit statuses, and digests in Podway rather than source contents, credentials, raw provider payloads, or full logs. Podway actor labels are correlation metadata, not authentication.
