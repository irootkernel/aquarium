# Privacy

Root Kernel Dev Skills contains instructions for Codex. The plugin does not operate a hosted service or collect telemetry itself.

Some instructed workflows can invoke local or third-party tools after explicit user approval:

- Sanho can contact a configured documentation Git remote. Sanho release resolution contacts GitHub, and an approved `use-sanho` installation downloads four files from `raw.githubusercontent.com` and writes them to a user-scoped Codex skill directory.
- Mulgae can transmit an explicitly preflighted review target to providers configured by the user. Mulgae release resolution and an approved `use-mulgae` installation contact GitHub, the skill writes four files below `~/.agents/skills/use-mulgae`, and an optional attached STDIO MCP process remains bound to the selected local repository. `dev-setup` does not run reviews, start the MCP server, capture a review target, or transmit source.
- Lora installation contacts npm and GitHub and writes selected skills to the Codex user-global skill directory.
- Gaori stores local test logs and summaries under `.gaori/`; raw logs are intentionally unredacted and can contain sensitive process output. Gaori release resolution and an approved `use-gaori` installation contact GitHub, the skill writes four files to a user-scoped Codex skill directory, and an optional attached STDIO MCP process remains bound to the selected local repository.
- Podway stores workspace configuration and local task history under `.podway/` and operates a same-user local daemon. It does not transmit source or evidence over the network; release resolution and an approved `use-podway` installation contact GitHub, and the skill writes four files below `~/.agents/skills/use-podway`.

Those tools and services have their own data handling policies. The skills instruct Codex not to read, print, copy, or persist credentials and not to transmit source during setup. Users should inspect proposed commands, capture sets, exclusions, and provider routing before approval.

Project configuration and generated evidence remain in the locations owned by each tool. This plugin does not create a central Root Kernel project-state file.

Root Kernel procedures instruct agents to record bounded summaries, revisions, exit statuses, and digests in Podway rather than source contents, credentials, raw provider payloads, or full logs. Podway actor labels are correlation metadata, not authentication.
