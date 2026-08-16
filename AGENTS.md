# Repository Guidance

## Release Policy

When the user asks to release `main`, establish the release mode before making release changes. Ask whether to use `full` or `light` unless the user already selected one explicitly. If the user did not provide a version, propose the next patch version and obtain confirmation before changing version metadata.

Before either mode, inspect the worktree, the local and remote `main` commits, the exact release-candidate SHA, and existing tags and GitHub Releases. Stop on unrelated worktree changes, an ambiguous release target, or a conflicting tag or release rather than including or overwriting it.

### Full Release

Update the plugin manifest version and its pinned validation expectation, then run the complete applicable local release gate:

```bash
python3 -m unittest tests/test_inspect_tools.py
RELEASE_TAG=v<version> ruby tests/validate.rb
ruff check plugins/root-kernel/skills/dev-setup/scripts/inspect_tools.py tests/test_inspect_tools.py
git diff --check <previous-release-tag>
```

Also verify that a deliberately mismatched `RELEASE_TAG` is rejected, and run any additional repository-required or change-specific checks. Do not commit or publish when a required check fails or cannot be completed.

### Light Release

Before changing version metadata, show the exact current release-candidate HEAD SHA and ask whether the user has confirmed the required test results for that SHA. Proceed only after an explicit positive answer. If HEAD or functional code changes after that confirmation, obtain confirmation again or switch to a full release.

A light release may change only release metadata: the plugin manifest version and its pinned validation expectation. Validate only that release delta locally:

```bash
python3 -m json.tool plugins/root-kernel/.codex-plugin/plugin.json >/dev/null
ruby -c tests/validate.rb
RELEASE_TAG=v<version> ruby tests/validate.rb
git diff --check <previous-release-tag>
```

Do not rerun the full Python unit suite or lint unchanged Python files locally in light mode. The release-tag validation is the basic release-contract check. If preparing the release requires functional code changes, stop light mode and ask the user to choose full verification or provide fresh test confirmation for the new candidate.

### Publication

After the selected local gate passes, create one `[REL] Release v<version>` commit. Push `main` first and wait for its full GitHub Actions validation to succeed. Only then create and push an annotated `v<version>` tag, wait for the tag validation to succeed, and create the GitHub Release. Finally verify that remote `main`, the tag, and the GitHub Release resolve to the intended release commit.

If `main` CI fails, do not create or push the tag. If tag CI fails, do not create the GitHub Release and do not rewrite or delete the published tag without explicit user authorization. A light release reduces duplicated local execution; it never bypasses the repository's remote full CI.
