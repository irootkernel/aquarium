# Privacy

Root Kernel Dev Skills contains instructions for Codex. The plugin does not operate a hosted service or collect telemetry itself.

Some instructed workflows can invoke local or third-party tools after explicit user approval:

- Sanho can contact a configured documentation Git remote.
- Mulgae can transmit an explicitly preflighted review target to providers configured by the user. `dev-setup` does not run reviews or transmit source.
- Lora installation contacts npm and GitHub and writes selected skills to the Codex user-global skill directory.
- Gaori stores local test logs and summaries under `.gaori/`; raw logs can contain sensitive process output.
- Podway stores workspace configuration and local task history under `.podway/` and operates a same-user local daemon. It does not transmit source or evidence over the network; release installation contacts GitHub.

Those tools and services have their own data handling policies. The skills instruct Codex not to read, print, copy, or persist credentials and not to transmit source during setup. Users should inspect proposed commands, capture sets, exclusions, and provider routing before approval.

Project configuration and generated evidence remain in the locations owned by each tool. This plugin does not create a central Root Kernel project-state file.

Root Kernel procedures instruct agents to record bounded summaries, revisions, exit statuses, and digests in Podway rather than source contents, credentials, raw provider payloads, or full logs. Podway actor labels are correlation metadata, not authentication.
