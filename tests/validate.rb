# frozen_string_literal: true

require "json"
require "pathname"
require "yaml"

ROOT = Pathname.new(__dir__).parent
PLUGIN = ROOT.join("plugins/aquarium")

def assert(condition, message)
  raise message unless condition
end

def assert_png(path, width, height)
  bytes = path.binread(24)
  assert(bytes.start_with?("\x89PNG\r\n\x1a\n".b), "asset must be a PNG: #{path}")
  actual_width, actual_height = bytes.byteslice(16, 8).unpack("NN")
  assert([actual_width, actual_height] == [width, height],
         "asset dimensions are incorrect: #{path} (#{actual_width}x#{actual_height})")
end

def assert_no_hard_wrap(path)
  in_fence = false
  in_frontmatter = false
  previous_prose = false

  path.readlines.each_with_index do |line, index|
    stripped = line.strip

    if index.zero? && stripped == "---"
      in_frontmatter = true
      previous_prose = false
      next
    end

    if in_frontmatter
      in_frontmatter = false if stripped == "---"
      previous_prose = false
      next
    end

    if stripped.start_with?("```")
      in_fence = !in_fence
      previous_prose = false
      next
    end

    structural = stripped.empty? || stripped.match?(/\A(?:\#{1,6}\s|[-*+]\s|\d+\.\s|>|\||<)/)
    prose = !in_fence && !structural
    assert(!(previous_prose && prose), "hard-wrapped prose near #{path}:#{index + 1}")
    previous_prose = prose
  end
end

skill_paths = Dir[PLUGIN.join("skills/*/SKILL.md")].sort.map { |path| Pathname.new(path) }
expected_skill_names = %w[
  design-qa
  dev-setup-bundle
  dev-setup
  epic-handler
  epic-validator
  independent-review
  new-feature
  new-project
  refactor
  release-qa
  task-close
  task-commit
  task-document
  task-handler
  task-implement
  task-plan
  task-refine
  task-review
  task-verify
  war-room
]
assert(skill_paths.map { |path| path.dirname.basename.to_s } == expected_skill_names,
       "plugin skill set does not match the expected skills")
implicit_invocation_skills = %w[task-commit]

skill_paths.each do |path|
  body = path.read
  frontmatter = body.match(/\A---\n(.*?)\n---\n/m)
  assert(frontmatter, "missing frontmatter: #{path}")

  metadata = YAML.safe_load(frontmatter[1], aliases: false)
  assert(metadata.keys.sort == %w[description name], "unexpected frontmatter keys: #{path}")
  assert(metadata.fetch("name") == path.dirname.basename.to_s, "skill name/path mismatch: #{path}")
  assert(metadata.fetch("description").include?("Use when"), "description lacks trigger: #{path}")

  ui_path = path.dirname.join("agents/openai.yaml")
  ui = YAML.safe_load(ui_path.read, aliases: false)
  prompt = ui.fetch("interface").fetch("default_prompt")
  assert(prompt.include?("$aquarium:#{metadata.fetch('name')}"), "default prompt lacks skill name: #{ui_path}")
  assert(prompt.length <= 128, "default prompt exceeds 128 characters: #{ui_path}")

  expected_implicit = implicit_invocation_skills.include?(metadata.fetch("name"))
  assert(ui.dig("policy", "allow_implicit_invocation") == expected_implicit,
         "allow_implicit_invocation must be #{expected_implicit}: #{ui_path}")
end

manifest = JSON.parse(PLUGIN.join(".codex-plugin/plugin.json").read)
assert(manifest.fetch("license") == "MIT", "plugin license must be MIT")
assert((%w[design deslop lora lore orchestration ouroboros podway release qa] - manifest.fetch("keywords")).empty?, "plugin discovery keywords are missing")
assert(manifest.fetch("version") == "0.1.9", "plugin version must be 0.1.9")
release_tag = ENV.fetch("RELEASE_TAG", "")
unless release_tag.empty?
  assert(release_tag == "v#{manifest.fetch('version')}",
         "release tag #{release_tag} must match plugin version v#{manifest.fetch('version')}")
end
assert(manifest.fetch("homepage") == "https://home.rootkernel.xyz", "plugin homepage is incorrect")
assert(manifest.dig("interface", "longDescription").include?("release-candidate QA") &&
       manifest.dig("interface", "longDescription").include?("Design Gates"),
       "plugin description must advertise release QA and Design Gates")
assert(manifest.dig("author", "url") == manifest.fetch("homepage"), "author URL must match the homepage")
assert(manifest.dig("author", "email") == "cs@rootkernel.xyz", "support email is incorrect")
prompts = manifest.fetch("interface").fetch("defaultPrompt")
assert(prompts.is_a?(Array) && prompts.length == 2, "plugin defaultPrompt must contain two prompts")
assert(prompts.any? { |prompt| prompt.include?("$aquarium:dev-setup") },
       "plugin defaultPrompt must retain development-tool discovery")
%w[websiteURL privacyPolicyURL termsOfServiceURL].each do |key|
  assert(manifest.fetch("interface").fetch(key).start_with?("https://"), "missing interface #{key}")
end
interface = manifest.fetch("interface")
assert(interface.fetch("websiteURL") == manifest.fetch("homepage"), "interface website must match the homepage")
assert(interface.fetch("brandColor") == "#10C4BE", "plugin brand color is incorrect")

expected_assets = {
  "composerIcon" => ["./assets/logo-small.png", 389, 142],
  "logo" => ["./assets/logo-white.png", 1024, 1024]
}
expected_assets.each do |key, (relative_path, expected_width, expected_height)|
  assert(interface.fetch(key) == relative_path, "plugin #{key} path is incorrect")
  assert_png(PLUGIN.join(relative_path.delete_prefix("./")), expected_width, expected_height)
end
assert(PLUGIN.join("assets/logo-black.png").file?, "dark-theme README logo is missing")
assert_png(PLUGIN.join("assets/logo-black.png"), 1024, 1024)

marketplace = JSON.parse(ROOT.join(".agents/plugins/marketplace.json").read)
assert(marketplace.fetch("name") == "aquarium", "marketplace name is incorrect")
assert(!marketplace.dig("interface", "displayName").to_s.empty?, "marketplace interface displayName is missing")
marketplace_plugins = marketplace.fetch("plugins")
assert(marketplace_plugins.is_a?(Array) && marketplace_plugins.length == 1,
       "marketplace must publish exactly one plugin")
marketplace_plugin = marketplace_plugins.fetch(0)
assert(marketplace_plugin.fetch("name") == manifest.fetch("name"),
       "marketplace plugin name must match the plugin manifest name")
assert(marketplace_plugin.dig("source", "source") == "local", "marketplace plugin source must be local")
marketplace_plugin_path = marketplace_plugin.dig("source", "path")
assert(marketplace_plugin_path == "./plugins/aquarium", "marketplace plugin source path is incorrect")
assert(ROOT.join(marketplace_plugin_path, ".codex-plugin/plugin.json").file?,
       "marketplace plugin source path does not contain the plugin manifest")
assert(marketplace_plugin.dig("policy", "installation") == "AVAILABLE",
       "marketplace installation policy must be AVAILABLE")
assert(marketplace_plugin.dig("policy", "authentication") == "ON_INSTALL",
       "marketplace authentication policy must be ON_INSTALL")

dev_setup = PLUGIN.join("skills/dev-setup/SKILL.md").read
dev_setup_script = PLUGIN.join("skills/dev-setup/scripts/inspect_tools.py")
dev_setup_bundle = PLUGIN.join("skills/dev-setup-bundle/SKILL.md").read
dev_setup_bundle_manifest = PLUGIN.join("skills/dev-setup-bundle/references/manifest.md").read
dev_setup_bundle_script = PLUGIN.join("skills/dev-setup-bundle/scripts/normalize_manifest.py")
agents_reference = PLUGIN.join("skills/dev-setup/references/agents-guidance.md").read
tool_catalog = PLUGIN.join("skills/dev-setup/references/tool-catalog.md").read
sanho_catalog = tool_catalog[/^## Sanho\n.*?(?=^## )/m]
mulgae_catalog = tool_catalog[/^## Mulgae\n.*?(?=^## )/m]
gaori_catalog = tool_catalog[/^## Gaori\n.*?(?=^## )/m]
deslop_catalog = tool_catalog[/^## Cursor Team Kit \/ Deslop\n.*?(?=^## )/m]
ouroboros_catalog = tool_catalog[/^## Ouroboros\n.*\z/m]
epic_handler = PLUGIN.join("skills/epic-handler/SKILL.md").read
epic_validator = PLUGIN.join("skills/epic-validator/SKILL.md").read
task_handler = PLUGIN.join("skills/task-handler/SKILL.md").read
independent_review = PLUGIN.join("skills/independent-review/SKILL.md").read
release_qa = PLUGIN.join("skills/release-qa/SKILL.md").read
task_plan = PLUGIN.join("skills/task-plan/SKILL.md").read
task_implement = PLUGIN.join("skills/task-implement/SKILL.md").read
task_verify = PLUGIN.join("skills/task-verify/SKILL.md").read
task_refine = PLUGIN.join("skills/task-refine/SKILL.md").read
task_document = PLUGIN.join("skills/task-document/SKILL.md").read
task_review = PLUGIN.join("skills/task-review/SKILL.md").read
task_close = PLUGIN.join("skills/task-close/SKILL.md").read
task_commit = PLUGIN.join("skills/task-commit/SKILL.md").read
design_qa = PLUGIN.join("skills/design-qa/SKILL.md").read
new_project = PLUGIN.join("skills/new-project/SKILL.md").read
new_feature = PLUGIN.join("skills/new-feature/SKILL.md").read
refactor = PLUGIN.join("skills/refactor/SKILL.md").read
war_room = PLUGIN.join("skills/war-room/SKILL.md").read
ouroboros_contract = PLUGIN.join("references/ouroboros-integration.md").read
design_gate_contract = PLUGIN.join("references/design-gates.md").read
plan_handoff_path = PLUGIN.join("references/plan-handoff.md")
assert(plan_handoff_path.file?, "shared plan-handoff contract is missing")
plan_handoff_contract = plan_handoff_path.read

assert(dev_setup.include?("request_user_input"), "dev-setup must prefer Codex ask/answer")
assert(dev_setup.include?("Podway"), "dev-setup description must trigger for Podway setup")
assert(dev_setup.include?("scripts/inspect_tools.py"), "dev-setup must use deterministic local inspection")
assert(dev_setup_script.file?, "dev-setup inspection script is missing")
assert(dev_setup.include?("default inspection omits Podway and Ouroboros completely") &&
       dev_setup.include?("--include-podway") &&
       dev_setup.include?("--include-ouroboros"),
       "dev-setup must probe Podway and Ouroboros only after explicit selection")
assert(dev_setup.include?("A `dev-setup-bundle` handoff is a preselected multi-tool setup request") &&
       dev_setup.include?("never the manifest path or contents") &&
       dev_setup.include?("already verified exact tag") &&
       dev_setup.include?("target result of `ready`, `partial`, `failed`, `declined`, or `skipped`"),
       "dev-setup must accept bounded bundle handoffs without weakening setup authority")

assert(dev_setup_bundle_script.file?, "dev-setup-bundle manifest normalizer is missing")
assert(dev_setup_bundle.include?("python3 <skill-directory>/scripts/normalize_manifest.py --manifest <path>") &&
       dev_setup_bundle.include?("Python 3.10 or newer and PyYAML 6.x") &&
       dev_setup_bundle.include?("do not install or upgrade either dependency") &&
       dev_setup_bundle.include?("do not parse the manifest approximately") &&
       dev_setup_bundle.include?("canonical Git roots") &&
       dev_setup_bundle.include?("continue with the remaining `ready` targets") &&
       dev_setup_bundle.include?("Never pass the manifest path") &&
       dev_setup_bundle.include?("Do not roll back successful actions automatically") &&
       dev_setup_bundle.include?("Before the first mutation and before each later target"),
       "dev-setup-bundle workflow must preserve manifest, continuation, and partial-failure boundaries")
assert(dev_setup_bundle_manifest.include?("schema: aquarium.dev-setup-bundle/v1") &&
       dev_setup_bundle_manifest.include?("defaults.tools` plus `include` minus `exclude`") &&
       dev_setup_bundle_manifest.include?("project MCP supports only `mulgae` and `gaori`") &&
       dev_setup_bundle_manifest.include?("same canonical Git root or shared Git common directory") &&
       dev_setup_bundle_manifest.include?("YAML merge key") &&
       dev_setup_bundle_manifest.include?("Do not put credentials"),
       "dev-setup-bundle manifest contract is incomplete")

assert(dev_setup.include?(">=0.51.1,<0.52.0") &&
       dev_setup.include?("uv tool install ouroboros-ai==<exact-version>") &&
       dev_setup.include?("ooo codex refresh") &&
       dev_setup.include?("ooo setup --runtime codex --non-interactive --mcp-mode auto") &&
       dev_setup.include?("three separate persistent mutations") &&
       dev_setup.include?("must not call an Ouroboros provider"),
       "dev-setup must separate pinned Ouroboros installation, Codex refresh, runtime setup, and provider authority")
assert(ouroboros_catalog &&
       ouroboros_catalog.include?("ooo --version") &&
       ouroboros_catalog.include?("ooo codex doctor") &&
       ouroboros_catalog.include?("ooo mcp doctor --json") &&
       ouroboros_catalog.include?("codex mcp get ouroboros --json") &&
       ouroboros_catalog.include?("Registration is `configured` only") &&
       ouroboros_catalog.include?("`missing` only for Codex's definite named-server-not-found response") &&
       ouroboros_catalog.include?("never expose raw registration stderr") &&
       ouroboros_catalog.include?("local and read-only") &&
       ouroboros_catalog.include?("do not contact a provider, initiate authentication, or make a network request"),
       "Ouroboros catalog must diagnose CLI, Codex integration, runtime, and registration independently")
assert(dev_setup.include?("Sanho, Mulgae, Gaori, and Podway selection choices") &&
       dev_setup.include?("Ouroboros CLI and version support, Codex rules and skills, MCP runtime"),
       "dev-setup must keep freshness authorization and Ouroboros reporting boundaries explicit")
assert(dev_setup.include?("Aquarium does not bundle Lora, Lore, or Deslop source") &&
       dev_setup.include?("temporary detached checkout") &&
       dev_setup.include?("one regular non-symlink installation") &&
       dev_setup.include?("exact repository, roadmap, and task prompt"),
       "dev-setup must install third-party skills from exact upstream sources")
proposal_index = dev_setup.index("Ask whether to prepare")
diff_index = dev_setup.index("Display the exact target path")
apply_index = dev_setup.index("Apply exactly this diff")
assert(proposal_index && diff_index && apply_index && proposal_index < diff_index && diff_index < apply_index,
       "AGENTS proposal and apply approvals are not ordered")
assert(dev_setup.include?("If it changed, discard the approval"), "stale AGENTS approval guard is missing")
assert(dev_setup.include?("the directory containing this `SKILL.md`"),
       "dev-setup must resolve its bundled references relative to its own skill directory")
assert(dev_setup.include?("treat it as scoped intake"),
       "dev-setup must scope a narrow request instead of widening it")
assert(dev_setup.include?("Do not use for routine supported Procedure v2 session observation") &&
       dev_setup.include?("Reject a handoff whose only requested action is routine supported Procedure v2") &&
       dev_setup.include?("without starting broad setup discovery") &&
       dev_setup.include?("legacy `podway reset --all` path is a setup-recovery exception"),
       "dev-setup must reject routine Procedure v2 lifecycle cleanup but keep legacy recovery")
assert(dev_setup.include?("Do not create or read `.aquarium`"),
       "dev-setup must not create shadow orchestration state")
selection_disclosure_index = dev_setup.index("Disclose in the Sanho, Mulgae, Gaori, and Podway selection choices")
comparison_index = dev_setup.index("## Compare Selected Agent Skills First")
action_approval_index = dev_setup.index("Obtain separate explicit ask/answer approval for the displayed action")
assert(selection_disclosure_index && comparison_index && action_approval_index &&
       selection_disclosure_index < comparison_index && comparison_index < action_approval_index,
       "dev-setup must disclose and perform selected-skill comparison before mutation approval")
assert(dev_setup.include?("either `Install and configure` or `Diagnose only`") &&
       dev_setup.include?("Do not fetch or compare a skipped or not-yet-selected tool") &&
       dev_setup.include?("do not widen a scoped continuation to the other three tools") &&
       dev_setup.include?("except for the exact selected-skill freshness comparison authorized below"),
       "dev-setup must compare only explicitly selected Sanho, Mulgae, Gaori, or Podway skills")
assert(dev_setup.include?("newest non-draft, non-prerelease tag within the tool's supported release line") &&
       dev_setup.include?("Fetch only `SKILL.md`, `references/lifecycle.md`, `references/authoring.md`, and `references/recovery.md`") &&
       dev_setup.include?("compute their SHA-256 digests") &&
       dev_setup.include?("Never execute fetched content"),
       "dev-setup must bound and verify the automatic skill payload")
assert(dev_setup.include?("against exactly `~/.agents/skills/<skill-name>` as complete directory trees") &&
       dev_setup.include?("any extra local files as differences") &&
       dev_setup.include?("Other Codex skill roots remain diagnostic evidence only"),
       "dev-setup must compare the exact user skill target without mutating duplicate roots")
assert(dev_setup.include?("`current` status without asking an update question") &&
       dev_setup.include?("ask separately whether to install it") &&
       dev_setup.include?("complete file-set diff including additions and deletions") &&
       dev_setup.include?("One skill target requires one explicit installation or replacement approval"),
       "dev-setup must distinguish matching, missing, and drifted selected skills")
assert(dev_setup.include?("report `freshness_unverifiable`") &&
       dev_setup.include?("Do not propose an installation or replacement from an unverified payload") &&
       dev_setup.include?("every other network operation retain their normal disclosure and explicit approval requirements"),
       "dev-setup must fail freshness checks closed without widening the approval exception")
assert(dev_setup.include?("require it to match the absence or complete digest snapshot") &&
       dev_setup.include?("If it changed, discard the approval") &&
       dev_setup.include?("Clean up every ephemeral payload") &&
       dev_setup.include?("each selected paired skill's comparison tag"),
       "dev-setup must invalidate stale skill approvals and clean temporary payloads")
assert(tool_catalog.include?("No separate approval is required for that comparison") &&
       tool_catalog.include?("network operation outside this exact exception") &&
       tool_catalog.scan("automatically fetched and verified").length == 4 &&
       tool_catalog.scan("comparison fetch itself needs no separate approval").length == 4,
       "tool catalog must apply the same bounded comparison exception to all four paired skills")
backup_policy_index = dev_setup.index("Choose a Backup Policy for Existing State")
assert(backup_policy_index && backup_policy_index < action_approval_index &&
       dev_setup.include?("Create and verify backups") &&
       dev_setup.include?("Proceed without backups") &&
       dev_setup.include?("current setup request") &&
       dev_setup.include?("The policy does not authorize any mutation") &&
       dev_setup.include?("Do not ask about backups for diagnosis or a new installation") &&
       dev_setup.include?("Never persist the choice") &&
       dev_setup.include?("existing state backed up or deliberately left without a backup"),
       "dev-setup must keep backup choice request-scoped and separate from mutation approval")
assert(dev_setup.include?("does not recover local modifications") &&
       dev_setup.include?("private configuration, untracked files, and runtime history may be permanently lost") &&
       dev_setup.include?("incoming payload in a temporary location is not a backup"),
       "dev-setup must disclose no-backup recovery limits without skipping payload validation")
assert(tool_catalog.include?("every approved action that overwrites or removes") &&
       tool_catalog.include?("no retained copy of the replaced state") &&
       tool_catalog.include?("incoming payload staging is not a backup") &&
       tool_catalog.scan("follow the shared backup policy").length >= 4 &&
       !tool_catalog.include?("preserve a recoverable sibling backup"),
       "tool replacement guidance must support the shared no-backup policy")
assert(ROOT.join("README.md").read.include?("automatically reads that tool's official GitHub release metadata") &&
       ROOT.join("README.md").read.include?("Unselected tools and other network operations are not covered") &&
       ROOT.join("PRIVACY.md").read.include?("Two bounded read-only network operations") &&
       ROOT.join("PRIVACY.md").read.include?("sends no repository or local skill content") &&
       ROOT.join("PRIVACY.md").read.scan("selected-skill freshness comparison contacts GitHub automatically").length == 4,
       "public documentation must disclose automatic selected-skill comparison and its privacy boundary")
assert(ROOT.join("README.md").read.include?("Invoking `release-qa` authorizes read-only queries") &&
       ROOT.join("README.md").read.include?("existing ambient authentication for private repositories") &&
       ROOT.join("PRIVACY.md").read.include?("Explicitly invoking `release-qa` automatically queries") &&
       ROOT.join("PRIVACY.md").read.include?("unavailable access leaves the QA result incomplete"),
       "public documentation must disclose release-qa network and private-repository authentication boundaries")
assert(ROOT.join("PRIVACY.md").read.include?("The selected `ooo --version`") &&
       ROOT.join("PRIVACY.md").read.include?("do not contact a provider, initiate authentication, or make a network request") &&
       ROOT.join("PRIVACY.md").read.include?("without exposing credential material"),
       "privacy policy must disclose the local Ouroboros diagnosis boundary")
assert(ROOT.join("PRIVACY.md").read.include?("Cursor Team Kit Deslop installation contacts GitHub and npm") &&
       ROOT.join("PRIVACY.md").read.include?("writes the upstream `SKILL.md` and MIT LICENSE") &&
       ROOT.join("PRIVACY.md").read.include?("does not bundle Lora, Ouroboros, or Cursor Team Kit skill or documentation sources"),
       "privacy policy must disclose third-party skill installation and no-vendoring boundaries")
assert(ROOT.join("TERMS.md").read.include?("does not bundle the Lora, Ouroboros, or Cursor Team Kit skill and documentation sources") &&
       !ROOT.join("TERMS.md").read.include?("bundled `deslop`"),
       "terms must preserve upstream ownership without claiming a bundled Deslop copy")
assert(agents_reference.include?("Repository-specific rules below override"), "override precedence is missing")
assert(agents_reference.include?("$aquarium:epic-handler") &&
       agents_reference.include?("$aquarium:epic-validator"),
       "AGENTS reference guidance must distinguish epic delivery and validation")

assert(tool_catalog.include?("--skill lore-commits"), "Lora commit skill is missing")
assert(tool_catalog.include?("--skill lore-query"), "Lora query skill is missing")
assert(!tool_catalog.include?("--skill lore-setup"), "Lora setup skill must not be installed")
assert(tool_catalog.include?("--global") && tool_catalog.include?("--agent codex"), "Lora scope must be global Codex")
assert(tool_catalog.include?("git -C <temporary-source-root>/lora checkout --detach FETCH_HEAD") &&
       tool_catalog.include?("npx skills add <temporary-source-root>/lora") &&
       !tool_catalog.include?("tmdgusya/lora#<tag-or-full-sha>"),
       "Lora must install from an exact detached upstream checkout")
assert(tool_catalog.include?("Before updating an existing `lore-commits` or `lore-query`") &&
       tool_catalog.include?("apply the shared backup policy before the approved `npx skills add` action"),
       "Lora skill updates must follow the request-scoped backup policy")
assert(deslop_catalog &&
       deslop_catalog.include?("https://github.com/cursor/plugins") &&
       deslop_catalog.include?("--skill deslop") &&
       deslop_catalog.include?("<approved-full-sha>") &&
       deslop_catalog.include?("cursor-team-kit/LICENSE ~/.agents/skills/deslop/LICENSE") &&
       deslop_catalog.include?("byte-identical") &&
       deslop_catalog.include?("no duplicate or symlink installation"),
       "Deslop must install with its license from one exact Cursor upstream commit")
assert(tool_catalog.include?("stable `v0.2.5` through `v0.2.x`") &&
       tool_catalog.include?("same exact tag") &&
       tool_catalog.include?("raw.githubusercontent.com/irootkernel/podway/<tag>/skills/use-podway/"),
       "Podway CLI, daemon, and use-podway must share the supported approved release")
assert(tool_catalog.include?("shasum -a 256 -c"), "Podway checksum verification is missing")
assert(tool_catalog.include?("podway.output/v3") &&
       tool_catalog.include?("podway.status-result/v3") &&
       tool_catalog.include?("podway.compact-status-result/v3") &&
       tool_catalog.include?("podway.observation-result/v2") &&
       tool_catalog.include?("podway.session-start-result/v3") &&
       tool_catalog.include?("podway.session-begin-result/v1") &&
       tool_catalog.include?("podway.terminal-disposition-result/v1") &&
       tool_catalog.include?("podway.session-reset-result/v1") &&
       tool_catalog.include?("podway.job-result/v4") &&
       tool_catalog.include?("podway.job-lookup-result/v4"),
       "Podway v0.2.5 JSON contracts are missing")
assert(tool_catalog.include?("prepared revision-0 session") &&
       tool_catalog.include?("session.begin") &&
       tool_catalog.include?("Terminal sessions expose a disposition template") &&
       tool_catalog.include?("start --replace-eligible") &&
       tool_catalog.include?("Never substitute force reset or force replacement"),
       "Podway v0.2.5 prepared lifecycle and eligible replacement guidance is missing")
assert(tool_catalog.include?("Treat that bounded inventory as readiness evidence only") &&
       tool_catalog.include?("Never use dev-setup to observe, cancel, discard, or reset") &&
       tool_catalog.include?("only session-state reset exception"),
       "Podway setup catalog must exclude routine Procedure v2 lifecycle operations")
assert(tool_catalog.include?("same approved command") &&
       tool_catalog.include?("no `--socket` override") &&
       tool_catalog.include?("prior launchd label to unload"),
       "Podway v0.2.5 LaunchAgent replacement recovery is missing")
assert(tool_catalog.include?("migrated reset-receipt read-back") &&
       tool_catalog.include?("degraded-store reset recovery") &&
       tool_catalog.include?("podway.daemon-log/v1") &&
       tool_catalog.include?("ten 1-MiB daemon-log files") &&
       tool_catalog.include?("LaunchAgent standard output and error go to `/dev/null`") &&
       tool_catalog.include?("disposable full-store openability or internal-codec inspection fails") &&
       tool_catalog.include?("recoverability never grants deletion authority"),
       "Podway v0.2.5 recovery and bounded logging guidance is missing")
assert(tool_catalog.include?("LEGACY_PROCEDURE_STATE_UNSUPPORTED") &&
       tool_catalog.include?("podway reset --all") &&
       tool_catalog.include?("separate explicit approval") &&
       tool_catalog.include?("permanently deletes the legacy runtime history") &&
       tool_catalog.include?("Git cannot restore it"),
       "Podway legacy-state recovery boundary is missing")
assert(tool_catalog.include?("aquarium-task-v2") &&
       tool_catalog.include?("aquarium-goal-v2") &&
       tool_catalog.include?("aquarium-validation-v2"),
       "Podway managed procedures are missing")
assert(tool_catalog.include?("migration_required=true") &&
       tool_catalog.include?("root-kernel-task-v2.yaml") &&
       tool_catalog.include?("root-kernel-goal-v2.yaml") &&
       tool_catalog.include?("root-kernel-validation-v2.yaml"),
       "Podway product-rename migration contract is missing")
assert(tool_catalog.include?("readiness_status=not_configured") &&
       tool_catalog.include?("readiness_status=ready") &&
       tool_catalog.include?("--include-podway") &&
       !tool_catalog.include?("integration_status"),
       "Podway setup diagnostics must expose readiness without activation semantics")
assert(tool_catalog.include?("https://github.com/irootkernel/podway"), "Podway source URL is missing")
assert(tool_catalog.include?("mulgae-doctor-result.v2") &&
       tool_catalog.include?("configured_readiness.state=ready") &&
       tool_catalog.include?("binary_available") &&
       tool_catalog.include?("cli_compatible") &&
       tool_catalog.include?("required_unverifiable") &&
       tool_catalog.include?("absence alone is not a mismatch") &&
       !tool_catalog.include?("provider_static_admission") &&
       !tool_catalog.include?("live_review"),
       "Mulgae setup diagnostics must use Doctor v2 and preserve Codex output capability")
assert(dev_setup.include?("Do not expose static admission, heartbeat") &&
       dev_setup.include?("Never authenticate a provider, inspect a prior run") &&
       dev_setup.include?("--require-mulgae-mcp"),
       "Mulgae setup reporting must preserve offline and optional-MCP boundaries")
assert(ROOT.join("README.md").read.include?("v0.2.5 through v0.2.x") &&
       ROOT.join("README.md").read.include?("optional `use-podway` user skill"),
       "public Podway support and optional skill guidance are missing")
assert(ROOT.join("README.md").read.include?("Git-backed design workflows use") &&
       ROOT.join("README.md").read.include?("selects Podway by default") &&
       ROOT.join("README.md").read.include?("opt the current Git-backed workflow out") &&
       ROOT.join("README.md").read.include?("before its first managed-session mutation"),
       "public Podway guidance must document default use and pre-session opt-out")
assert(ROOT.join("README.md").read.include?("Degraded readiness routes to `dev-setup` repair") &&
       ROOT.join("README.md").read.include?("undisposed terminal nonmatching session is a lifecycle conflict") &&
       ROOT.join("README.md").read.include?("atomically replaced by the approved successor") &&
       ROOT.join("README.md").read.include?("reset is not a prerequisite"),
       "public Podway guidance must separate setup repair from session lifecycle")
assert(ROOT.join("README.md").read.include?("leave the session active for later resumption") &&
       ROOT.join("README.md").read.include?("cancel the task while preserving history") &&
       ROOT.join("README.md").read.include?("reset the session and delete its history"),
       "public Podway guidance must distinguish pause, cancel, and reset")
assert(ROOT.join("README.md").read.include?("starts as prepared") &&
       ROOT.join("README.md").read.include?("uses `begin`") &&
       ROOT.join("README.md").read.include?("exact authoritative external result") &&
       ROOT.join("README.md").read.include?("leaves the terminal session undisposed") &&
       ROOT.join("README.md").read.include?("never chooses force reset or force replacement"),
       "public Podway v0.2.5 lifecycle and disposition policy is incomplete")
assert(ROOT.join("PRIVACY.md").read.include?("use-podway") &&
       ROOT.join("PRIVACY.md").read.include?("~/.agents/skills/use-podway"),
       "privacy policy must disclose Podway skill installation")
assert(gaori_catalog, "Gaori tool catalog section is missing")
assert(gaori_catalog.include?("gaori version --json"), "Gaori JSON version probe is missing")
assert(gaori_catalog.include?("stable `v0.1.14` through `v0.1.x`") &&
       gaori_catalog.include?("same exact tag") &&
       gaori_catalog.include?("raw.githubusercontent.com/irootkernel/gaori/<tag>/skills/use-gaori/") &&
       dev_setup.include?("stable `v0.1.14` through `v0.1.x`") &&
       ROOT.join("README.md").read.include?("Aquarium supports stable v0.1.14 through v0.1.x"),
       "Gaori CLI and use-gaori must share the supported approved release")
assert(gaori_catalog.include?("gaori --json config check") &&
       gaori_catalog.include?("gaori --json config check --sample <raw-log>") &&
       gaori_catalog.include?("gaori --json parsers list") &&
       gaori_catalog.include?("gaori --json parsers detect <raw-log>") &&
       gaori_catalog.include?("`dotnet-test` and `gradle-test` are Experimental") &&
       gaori_catalog.include?("!.gaori/tester.yaml") &&
       gaori_catalog.include?("!.gaori/tester/rules/*.yaml"),
       "Gaori portable config and non-executing validation guidance is incomplete")
assert(gaori_catalog.include?("gaori --json runs list") &&
       gaori_catalog.include?("gaori --json rules proposals") &&
       gaori_catalog.include?("gaori rules show --proposal <name>"),
       "Gaori read-only evidence and proposal discovery guidance is incomplete")
assert(gaori_catalog.include?("[mcp_servers.gaori]") &&
       gaori_catalog.include?("tool_timeout_sec = 3601") &&
       gaori_catalog.include?("codex mcp get gaori --json") &&
       gaori_catalog.include?("terminal-only `await_run`") &&
       gaori_catalog.include?("at least 3601 seconds") &&
       gaori_catalog.include?("read-only `list_runs`") &&
       gaori_catalog.include?("cannot recover an invocation ID or reattach"),
       "Gaori project-local MCP setup and verification guidance is incomplete")
assert(sanho_catalog, "Sanho tool catalog section is missing")
assert(sanho_catalog.include?("stable `v0.2.7` through `v0.2.x`") &&
       sanho_catalog.include?("same exact tag") &&
       sanho_catalog.include?("raw.githubusercontent.com/irootkernel/sanho/<tag>/skills/use-sanho/") &&
       dev_setup.include?("stable `v0.2.7` through `v0.2.x`") &&
       ROOT.join("README.md").read.include?("Aquarium supports stable v0.2.7 through v0.2.x"),
       "Sanho CLI and use-sanho must share the supported approved release")
assert(sanho_catalog.include?("sanho check --require-clean") &&
       sanho_catalog.include?("sanho diff --refresh") &&
       sanho_catalog.include?("sanho workspace forget <workspace-id>") &&
       sanho_catalog.include?("sanho doctor --fix"),
       "Sanho v0.2.7 diagnosis and repair guidance is incomplete")
assert(sanho_catalog.include?("sanho preview --json") &&
       sanho_catalog.include?("`blocked` and `verdict`") &&
       sanho_catalog.include?("reports a blocked push at exit 0") &&
       sanho_catalog.include?("never grants push authority"),
       "Sanho push-preview guidance is incomplete")
assert(sanho_catalog.include?("sanho log") &&
       sanho_catalog.include?("sanho show <commit>") &&
       sanho_catalog.include?("an `external` entry has `source: null`") &&
       sanho_catalog.include?("`too_large`") &&
       sanho_catalog.include?("`invalid_arguments` error envelope"),
       "Sanho history, recovery, and JSON error guidance is incomplete")
assert(agents_reference.include?("$use-sanho") &&
       agents_reference.include?("only the corresponding CLI is installed"),
       "AGENTS guidance must conditionally reference use-sanho")
assert(dev_setup.include?("CLI installation or upgrade") &&
       dev_setup.include?("user-scoped skill installation or replacement") &&
       dev_setup.include?("separate approval boundaries"),
       "dev-setup must separate Sanho CLI, skill, workspace, and repair approvals")
assert(dev_setup.include?("use-gaori") &&
       dev_setup.include?("project-local MCP configuration") &&
       dev_setup.include?("Never start a Gaori run or MCP test command during setup"),
       "dev-setup must separate Gaori CLI, skill, config, and MCP boundaries")
assert(agents_reference.include?("$use-gaori") &&
       agents_reference.include?("only the corresponding CLI is installed"),
       "AGENTS guidance must conditionally reference use-gaori")

assert(mulgae_catalog, "Mulgae tool catalog section is missing")
assert(mulgae_catalog.include?("stable `v0.1.17` through `v0.1.x`") &&
       mulgae_catalog.include?("Go `1.26.6` or newer") &&
       mulgae_catalog.include?("same exact tag") &&
       mulgae_catalog.include?("raw.githubusercontent.com/irootkernel/mulgae/<tag>/skills/use-mulgae/") &&
       mulgae_catalog.include?("~/.agents/skills/use-mulgae") &&
       dev_setup.include?("stable `v0.1.17` through `v0.1.x`") &&
       ROOT.join("README.md").read.include?("stable v0.1.17 through v0.1.x"),
       "Mulgae CLI and use-mulgae must share the supported approved release and user scope")
assert(mulgae_catalog.include?(".mulgae/local.yaml") &&
       mulgae_catalog.include?("mode-`0600`") &&
       mulgae_catalog.include?("!/.mulgae/config.yaml") &&
       mulgae_catalog.include?("mulgae init --refresh-local --output json") &&
       mulgae_catalog.include?("execution.workspace_access: none"),
       "Mulgae split Config v3 setup and ignore guidance is incomplete")
assert(mulgae_catalog.include?("mulgae-command-result.v5") &&
       mulgae_catalog.include?("mulgae-doctor-result.v2") &&
       mulgae_catalog.include?("mulgae-provider-heartbeat-result.v1") &&
       mulgae_catalog.include?("authentication_failure") &&
       mulgae_catalog.include?("malformed_response") &&
       mulgae_catalog.include?("mulgae-review-preflight.v3") &&
       mulgae_catalog.include?("Config v1 and v2 are unsupported") &&
       mulgae_catalog.include?("no automatic migration"),
       "Mulgae v0.1.17 contracts and legacy-config guidance are incomplete")
assert(mulgae_catalog.include?("validation.extraction.enabled: true") &&
       mulgae_catalog.include?("disabled/defaulted") &&
       mulgae_catalog.include?("changes shared project policy") &&
       mulgae_catalog.include?("every collaborator and automation") &&
       mulgae_catalog.include?("Mulgae v0.1.16 or newer") &&
       mulgae_catalog.include?("v0.1.15 rejects the unknown field"),
       "Mulgae structured-extraction Config v3 compatibility guidance is incomplete")
assert(mulgae_catalog.include?("accepted Markdown report byte-for-byte") &&
       mulgae_catalog.include?("`002-extract`") &&
       mulgae_catalog.include?("single second provider-invocation slot") &&
       mulgae_catalog.include?("does not increase the existing invocation budget") &&
       mulgae_catalog.include?("structured_extraction_status") &&
       mulgae_catalog.include?("`structured`") &&
       mulgae_catalog.include?("`mixed`") &&
       mulgae_catalog.include?("`reports_only`") &&
       mulgae_catalog.include?("not itself a failure"),
       "Mulgae structured-extraction evidence contract is incomplete")
assert(mulgae_catalog.include?("Codex CLI `0.147.0` or newer") &&
       mulgae_catalog.include?("default_credential_profile") &&
       mulgae_catalog.include?("credential_homes") &&
       mulgae_catalog.include?("auth.json") &&
       mulgae_catalog.include?("active setup session") &&
       mulgae_catalog.include?("role-to-profile aliases"),
       "Mulgae Codex credential-profile guidance is incomplete")
assert(mulgae_catalog.include?("mode-`0700` backup directory") &&
       mulgae_catalog.include?("cp -p") &&
       mulgae_catalog.include?("restoration commands") &&
       mulgae_catalog.include?("Under the no-backup policy") &&
       mulgae_catalog.include?("no rollback copy is available") &&
       mulgae_catalog.include?("If Config v3 initialization fails"),
       "Mulgae legacy-config backup choice and rollback guidance is incomplete")
assert(mulgae_catalog.include?("[mcp_servers.mulgae]") &&
       mulgae_catalog.include?("required = true") &&
       mulgae_catalog.include?("startup_timeout_sec = 30") &&
       mulgae_catalog.include?("tool_timeout_sec = 7501") &&
       mulgae_catalog.include?("codex mcp get mulgae --json") &&
       mulgae_catalog.include?("`start_review`, `await_review`, `cancel_review`") &&
       mulgae_catalog.include?("preserve any larger existing value"),
       "Mulgae project-local MCP setup and verification guidance is incomplete")
assert(dev_setup.include?("use-mulgae") &&
       dev_setup.include?("project Config v3 and ignore changes") &&
       dev_setup.include?("Codex credential-profile mapping") &&
       dev_setup.include?("start a Mulgae heartbeat, review, qualification, preflight capture, live provider request") &&
       dev_setup.include?("source transmission, or MCP server during setup"),
       "dev-setup must separate Mulgae CLI, skill, Config v3, Codex profile, and MCP boundaries")
assert(agents_reference.include?("$use-mulgae") &&
       agents_reference.include?("only the corresponding CLI is installed"),
       "AGENTS guidance must conditionally reference use-mulgae")

{
  "task-handler" => task_handler,
  "task-review" => task_review,
  "epic-handler" => epic_handler,
  "epic-validator" => epic_validator,
}.each do |name, body|
  assert(body.include?("$use-mulgae"), "#{name} must route Mulgae reviews through use-mulgae")
end
assert(task_review.include?("use the CLI fallback below") &&
       task_review.include?("Do not start a second MCP server") &&
       task_review.include?("mulgae-review-preflight.v3") &&
       task_review.include?("mulgae-command-result.v5") &&
       task_review.include?("start exactly once") &&
       task_review.include?("await_cancelled") &&
       task_review.include?("never repeat `start_review`") &&
       task_review.include?("mulgae status --run r_... --output json") &&
       task_review.include?("mulgae findings --run r_... --severity low --output json") &&
       task_review.include?("at most 20 highest-severity records") &&
       task_review.include?("complete provider stdout and stderr") &&
       task_review.include?("accepted Markdown report byte-for-byte") &&
       task_review.include?("private internal `002-extract` artifact") &&
       task_review.include?("single second provider-invocation slot") &&
       task_review.include?("never run that artifact manually"),
       "task-review must preserve the optional use-mulgae and MCP fallback boundaries")
assert(ROOT.join("PRIVACY.md").read.include?("~/.agents/skills/use-mulgae") &&
       ROOT.join("PRIVACY.md").read.include?("complete provider stdout and stderr") &&
       ROOT.join("PRIVACY.md").read.include?("auth.json") &&
       ROOT.join("PRIVACY.md").read.include?("does not run reviews, start the MCP server"),
       "privacy policy must disclose Mulgae skill installation and MCP boundaries")

{
  "task-handler" => task_handler,
  "task-verify" => task_verify,
  "epic-handler" => epic_handler,
  "epic-validator" => epic_validator,
}.each do |name, body|
  assert(body.include?("$use-gaori"), "#{name} must route selected Gaori checks through use-gaori")
end
assert(task_verify.include?("original documented test command directly") &&
       task_verify.include?("Gaori evidence compression was unavailable") &&
       task_verify.include?("artifact `status`, `extractor_status`, and truncation") &&
       task_verify.include?("read-only `list_runs`") &&
       task_verify.include?("followed by `await_run` on the same invocation") &&
       task_verify.include?("Never repeat the start") &&
       !task_verify.include?("all six connected MCP tools"),
       "task-verify must preserve Gaori fallback and evidence boundaries")
assert(ROOT.join("PRIVACY.md").read.include?("use-gaori") &&
       ROOT.join("PRIVACY.md").read.include?("intentionally unredacted"),
       "privacy policy must disclose Gaori skill installation and raw-log handling")

{
  "task-handler" => task_handler,
  "task-document" => task_document,
  "task-commit" => task_commit,
  "epic-handler" => epic_handler,
  "epic-validator" => epic_validator,
}.each do |name, body|
  assert(body.include?("$use-sanho"), "#{name} must route relevant Sanho boundaries through use-sanho")
end
assert(task_commit.include?("After the commit and its hooks"),
       "task-commit must refresh Sanho evidence after hooks")

assert(epic_handler.include?("one canonical roadmap path inside that repository") &&
       epic_handler.include?("exactly one epic ID"),
       "epic-handler must require one repository roadmap and epic")
approval_index = epic_handler.index("Ask once for explicit approval")
task_goal_index = epic_handler.index("For each non-terminal task in order")
epic_goal_index = epic_handler.index("one final epic closeout goal")
assert(approval_index && task_goal_index && epic_goal_index && approval_index < task_goal_index && task_goal_index < epic_goal_index,
       "epic-handler must approve once, serialize task goals, then create the closeout goal")
assert(epic_handler.include?("Do not invoke `$aquarium:task-handler` or its phase skills") &&
       epic_handler.include?("sequence of goal-centered task executions") &&
       epic_handler.include?("do not manufacture phase artifacts"),
       "epic-handler must remain independent and goal-centered")
assert(epic_handler.include?("latest complete task target") &&
       epic_handler.include?("audit again from scratch"),
       "epic-handler must require task and convergent epic Mulgae review")
assert(epic_handler.include?("at most two operationally complete Mulgae review rounds") &&
       epic_handler.include?("Round one is `remediation-eligible`; round two is `hardening-deferral-eligible`") &&
       epic_handler.include?("Reconstruct member ordinals from verbose goal Procedure history for the current revision") &&
       epic_handler.include?("preserve the count across rework and resumption") &&
       epic_handler.include?("requires user authorization for exactly one extra full-target `hardening-deferral-eligible` review") &&
       epic_handler.include?("Apply the second-round disposition to that authorized extra review") &&
       epic_handler.include?("never silently run a third review or defer stale evidence") &&
       epic_handler.include?("deferred-for-hardening") &&
       epic_handler.include?("at most three whole-epic Mulgae review-and-remediation rounds") &&
       epic_handler.include?("one fourth `confirmation-only` review") &&
       epic_handler.include?("ask the user to authorize one additional fix-and-confirmation budget") &&
       epic_handler.include?("ask again rather than restoring an unbounded loop") &&
       epic_handler.include?("Do not use `followup`, `delta`, or `rerun`") &&
       !epic_handler.include?("review the changed target again until no valid finding remains"),
       "epic-handler must bound member-task and epic-hardening review convergence")
assert(epic_handler.include?("It does not authorize amend, push, PR or release changes"),
       "epic-handler must preserve publication boundaries")
assert(epic_handler.include?("$aquarium:task-commit") &&
       epic_handler.include?("Never commit independently"),
       "epic-handler must hand actual commits to task-commit")
assert(epic_handler.include?("Do not create or read `.aquarium`"),
       "epic-handler must not create shadow orchestration state")
assert(epic_handler.include?("dependency DAG") && epic_handler.include?("exact revision") &&
       epic_handler.include?("explicit external prerequisite") && epic_handler.include?("report its nodes, owners, and missing authority"),
       "epic-handler must gate roadmap-explicit external dependencies")
internal_order_index = epic_handler.index("An incomplete member-task predecessor determines execution order and does not block initial approval")
dependent_gate_index = epic_handler.index("member-task predecessor is successfully terminal with its required commit and evidence", task_goal_index)
assert(internal_order_index && dependent_gate_index &&
       internal_order_index < task_goal_index && task_goal_index < dependent_gate_index &&
       epic_handler.include?("recheck any pre-epic or external prerequisite at its exact revision"),
       "epic-handler must order internal dependencies and gate them immediately before dependent task goals")
assert(epic_handler.include?("violation owned by one task") && epic_handler.include?("epic seam invariant") &&
       epic_handler.include?("Work requiring another repository is external") && epic_handler.include?("canonical requirement owner") &&
       epic_handler.include?("external blocker is resolved"),
       "epic-handler must route remediation by ownership")
assert(epic_handler.include?("coverage_status=complete") && epic_handler.include?("publication_status=committed") &&
       epic_handler.include?("findings query succeeds") && epic_handler.include?("untracked, generated, and derived files"),
       "epic-handler must require complete Mulgae evidence")
assert(epic_handler.include?("Commit and upstream publication are separate states") &&
       epic_handler.include?("status-only roadmap transition is the sole exception"),
       "epic-handler must separate lifecycle evidence and invalidate stale review")
assert(epic_handler.lines.length < 120, "epic-handler must remain orchestration-focused")

assert(epic_validator.include?("one canonical roadmap path inside it") &&
       epic_validator.include?("exactly one epic ID"),
       "epic-validator must require one repository roadmap and epic")
validator_approval_index = epic_validator.index("Ask once for explicit approval")
validator_audit_index = epic_validator.index("## Audit the Epic Directly")
validator_goal_index = epic_validator.index("## Group and Complete Remediation Goals")
validator_reaudit_index = epic_validator.index("## Re-audit to Convergence")
assert(validator_approval_index && validator_audit_index && validator_goal_index && validator_reaudit_index &&
       validator_approval_index < validator_audit_index && validator_audit_index < validator_goal_index &&
       validator_goal_index < validator_reaudit_index,
       "epic-validator must approve once, audit, remediate, then re-audit")
assert(epic_validator.include?("every member task is in a roadmap-defined successful state") &&
       epic_validator.include?("committed evidence-backed baseline") &&
       epic_validator.include?("Stop when the epic baseline is uncommitted"),
       "epic-validator must start from completed committed delivery")
assert(epic_validator.include?("Do not invoke `$aquarium:task-handler`, `$aquarium:epic-handler`") &&
       epic_validator.include?("Do not add new roadmap tasks or invent task IDs"),
       "epic-validator must remediate directly without handler delegation or new tasks")
assert(epic_validator.include?("gap owned by one existing task") &&
       epic_validator.include?("cross-task seam or omitted epic-level design requirement") &&
       epic_validator.include?("For work owned by another repository") &&
       epic_validator.include?("Never run two remediation goals concurrently"),
       "epic-validator must route and serialize remediation by canonical owner")
assert(epic_validator.include?("If the roadmap defines a reopen state") &&
       epic_validator.include?("otherwise preserve the successful state") &&
       epic_validator.include?("do not create a new task entry") &&
       epic_validator.include?("Record resulting remediation commit IDs in the final validation record"),
       "epic-validator must preserve lifecycle vocabulary and remediation notes")
assert(epic_validator.include?("Mulgae on the latest complete remediation target") &&
       epic_validator.include?("whole-epic Mulgae review") &&
       epic_validator.include?("coverage_status=complete") &&
       epic_validator.include?("publication_status=committed") &&
       epic_validator.include?("findings query succeeds"),
       "epic-validator must require complete per-goal and final Mulgae evidence")
assert(epic_validator.include?("next positive ordinal for the current validation goal revision") &&
       epic_validator.include?("exact committed run ID") &&
       epic_validator.include?("`remediation-eligible` mode") &&
       epic_validator.include?("an unprovable ordinal stops before review") &&
       epic_validator.include?("never selects `confirmation-only` or `hardening-deferral-eligible` mode"),
       "epic-validator must durably number cold whole-epic root reviews")
assert(epic_validator.include?("status or validation-record-only roadmap change is the sole exception") &&
       epic_validator.include?("never duplicate an equivalent record or create an empty commit"),
       "epic-validator must invalidate stale evidence and avoid empty closeout commits")
assert(epic_validator.include?("$aquarium:task-commit") &&
       epic_validator.include?("Never commit independently"),
       "epic-validator must hand actual commits to task-commit")
assert(epic_validator.include?("Commit is not upstream publication") &&
       epic_validator.include?("Do not create or read `.aquarium`") &&
       epic_validator.include?("byte-for-byte snapshot verification"),
       "epic-validator must preserve publication and shadow-state boundaries")
assert(epic_validator.lines.length < 120, "epic-validator must remain orchestration-focused")

assert(task_handler.include?("$aquarium:dev-setup"), "task-handler must route missing setup")
assert(!task_handler.include?("$aquarium:epic-handler"),
       "task-handler must remain independent from epic-handler")
assert(task_handler.include?("Strengthen execution of one roadmap task goal"),
       "task-handler must be goal-centered and procedure-strengthening")
assert(epic_handler.include?("requests without one canonical roadmap epic identity") &&
       task_handler.include?("requests without one canonical roadmap task identity") &&
       !epic_handler.include?("free-form") && !task_handler.include?("free-form"),
       "handlers must express applicability through canonical roadmap identities")
phase_names = %w[task-plan task-implement task-verify task-refine task-document task-review task-close]
phase_section_index = task_handler.index("Resolve every phase skill")
phase_indexes = phase_names.map { |name| task_handler.index("$aquarium:#{name}", phase_section_index) }
assert(phase_indexes.all? && phase_indexes.each_cons(2).all? { |left, right| left < right },
       "task-handler phase skills are missing or misordered")
assert(task_handler.include?("A leaf skill's report is a handoff summary, not proof by itself"),
       "task-handler must verify leaf postconditions independently")
assert(task_handler.include?("Resume at the earliest phase whose postcondition is not currently proven"),
       "task-handler must reconstruct safe resume state")
assert(task_handler.include?("Immediately after plan approval and before implementation") &&
       task_handler.include?("change it to `In Progress` only when that exact state is defined") &&
       task_handler.include?("ask whether to reopen it"),
       "task-handler must establish the roadmap active state before implementation")
assert(task_handler.include?("podway observe --json --wait-for-idle") &&
       task_handler.include?("guidance.allowed_actions") &&
       task_handler.include?("mutation_templates"),
       "task-handler must consume the authoritative Podway observation")
assert(task_handler.include?("re-enter the earliest phase that owns the requested change"),
       "task-handler must route rework to the owning phase")
assert(task_handler.include?("Do not create or read `.aquarium`"),
       "task-handler must not create shadow orchestration state")
assert(task_handler.include?("missing or unhealthy tooling or readiness prerequisite") &&
       task_handler.include?("Do not classify a healthy conflicting Procedure v2 session as a setup prerequisite"),
       "task-handler must not reinterpret a healthy session conflict as setup readiness")
assert(task_handler.lines.length < 110, "task-handler must remain orchestration-focused")

assert(task_handler.include?("`execute` by default") &&
       task_handler.include?("`plan-only`") &&
       task_handler.include?("`plan-handoff`") &&
       task_handler.include?("`resume`") &&
       task_handler.include?("plan-handoff.md") &&
       epic_handler.include?("`execute` by default") &&
       epic_handler.include?("`plan-only`") &&
       epic_handler.include?("`plan-handoff`") &&
       epic_handler.include?("`resume`") &&
       epic_handler.include?("plan-handoff.md"),
       "task-handler and epic-handler must expose the shared four-mode handoff contract")
assert(plan_handoff_contract.include?("Treat an unqualified request to \"plan only\" as `plan-only`") &&
       plan_handoff_contract.include?("another AI or agent will continue") &&
       plan_handoff_contract.include?("requires the default Podway path") &&
       plan_handoff_contract.include?("Do not create the handoff file, a Codex goal, or a Podway session before") &&
       plan_handoff_contract.include?(".podway/runtime/handoffs/<initial-session-id>/plan.md") &&
       plan_handoff_contract.include?("Never accept a caller-supplied file name") &&
       plan_handoff_contract.include?("65,536 UTF-8 bytes") &&
       plan_handoff_contract.include?("Never overwrite different bytes") &&
       plan_handoff_contract.include?("SHA-256 and byte size") &&
       plan_handoff_contract.include?("The session ID is mandatory output") &&
       plan_handoff_contract.include?("exactly one running session") &&
       plan_handoff_contract.include?("without suspend, cancel, reset, replacement") &&
       plan_handoff_contract.include?("remove only that exact handoff file"),
       "plan handoff must be opt-in, session-derived, bounded, verifiable, resumable, and narrowly cleaned up")
assert(task_handler.include?("stop at `implement`") &&
       epic_handler.include?("stop with required work items unset") &&
       epic_handler.include?("every successor session") &&
       epic_handler.include?("validation baseline"),
       "handlers must stop before work and preserve the plan across their owned session topology")
{
  "epic-validator" => epic_validator,
  "new-project" => new_project,
  "new-feature" => new_feature,
  "refactor" => refactor,
  "war-room" => war_room,
  "design-qa" => design_qa,
}.each do |name, body|
  assert(!body.include?("mode=plan-handoff") && !body.include?("plan-handoff.md"),
         "plan handoff mode must not be exposed by #{name}")
end
assert(ROOT.join("README.md").read.include?("The other Aquarium workflows do not expose these modes") &&
       ROOT.join("PRIVACY.md").read.include?("does not create this file for ordinary execution or plan-only requests") &&
       ROOT.join("PRIVACY.md").read.include?("Podway records only its local path, SHA-256, byte size, and media type"),
       "public documentation must bound plan-handoff scope and local data handling")

{
  "new-project" => new_project,
  "new-feature" => new_feature,
  "refactor" => refactor,
  "war-room" => war_room,
  "design-qa" => design_qa,
}.each do |name, body|
  assert(body.include?("ouroboros-integration.md") && body.include?("design-gates.md"),
         "#{name} must use the shared Ouroboros and Design Gate contracts")
  assert(body.include?("exact") && body.match?(/explicit approval/i),
         "#{name} must gate durable document changes on exact-diff approval")
end
assert(new_project.include?("PRD and an initial roadmap") &&
       new_project.include?("non-Git project") &&
       new_project.include?("skip Podway completely") &&
       new_project.include?("gate creation requires a later explicit"),
       "new-project must stop at PRD and roadmap and keep non-Git work Podway-free")
assert(new_feature.include?("exactly one feature epic") &&
       refactor.include?("exactly one refactor epic") &&
       refactor.include?("compatibility") && refactor.include?("rollback"),
       "feature and refactor skills must produce one bounded epic")
assert(war_room.include?("Do not implement a fix") &&
       war_room.include?("bounded task") && war_room.include?("multi-work-unit epic") &&
       war_room.include?("investigation incomplete") &&
       war_room.include?("record its adjudicated result at `quality`") &&
       war_room.include?("zero unresolved locally valid findings"),
       "war-room must stop at diagnosis and one work-unit classification")
assert(design_qa.include?("docs/gating-rules.md") &&
       design_qa.include?("docs/gating-rules-retired.md") &&
       design_qa.include?("authoritative current and retired registry paths") &&
       design_qa.include?("concise title") &&
       design_qa.include?("local offline") &&
       design_qa.include?("tombstone") &&
       design_qa.include?("impacted roadmap-marker diff") &&
       design_qa.include?("retain the retired history"),
       "design-qa must own executable current gates and retired bodies")
assert(ouroboros_contract.include?("Support only Ouroboros `>=0.51.1,<0.52.0`") &&
       ouroboros_contract.include?("blocks these Ouroboros-assisted workflows") &&
       ouroboros_contract.include?("<owner-skill>:<canonical-identity>") &&
       ouroboros_contract.include?("Do not let Ouroboros create or edit repository files directly") &&
       ouroboros_contract.include?("`auto`, `run`, `ralph`, or `evolve`") &&
       ouroboros_contract.include?("Podway-blind") &&
       ouroboros_contract.include?("full provider prompts, transcripts"),
       "shared Ouroboros contract must bound versions, execution, writes, Podway, and stored evidence")
assert(design_gate_contract.include?("Design Gate impact") &&
       design_gate_contract.include?("authoritative current and retired registry paths together") &&
       design_gate_contract.include?("derive the retired path as its sibling") &&
       design_gate_contract.include?("Every newly authored implementation work unit") &&
       design_gate_contract.include?("inherit its parent epic's marker") &&
       design_gate_contract.include?("missing effective marker is a contract gap") &&
       design_gate_contract.include?("leaves the source repository unchanged") &&
       design_gate_contract.include?("Reactivation replaces") &&
       design_gate_contract.include?("must never have both an active body and a current tombstone") &&
       design_gate_contract.include?("`Pending` blocks implementation") &&
       design_gate_contract.include?("Only `$aquarium:design-qa`") &&
       design_gate_contract.include?("Design Gate not enrolled") &&
       design_gate_contract.include?("absence from the candidate is a contract finding"),
       "Design Gate contract must define ownership, implementation blocking, and gradual enrollment")
assert(task_handler.include?("Resolve the effective `Design Gate impact` from the task first and then its parent epic") &&
       task_handler.include?("Stop before plan approval or implementation when the effective marker is missing or `Pending`") &&
       epic_handler.include?("Resolve every member task's effective `Design Gate impact` from the task first and then the epic") &&
       task_verify.include?("For every inherited or task-explicit resolved active `GATE-*` ID") &&
       task_verify.include?("source-repository status is unchanged") &&
       epic_validator.include?("integration seam") &&
       task_document.include?("must not create, change, reactivate, retire"),
       "delivery workflows must consume Design Gates without taking registry ownership")

podway_reference = PLUGIN.join("references/podway-integration.md")
assert(podway_reference.file?, "shared Podway integration contract is missing")
podway_contract = podway_reference.read
assert(podway_contract.include?("The canonical roadmap owns") &&
       podway_contract.include?("Podway owns") &&
       podway_contract.include?("temporary projection"),
       "Podway authority separation is missing")
assert(podway_contract.include?("MUTATION_OUTCOME_UNKNOWN") &&
       podway_contract.include?("job lookup") &&
       podway_contract.include?("podway.job-lookup-result/v4") &&
       podway_contract.include?("idempotency key"),
       "Podway mutation reconciliation is missing")
assert(podway_contract.include?("podway.observation-result/v2") &&
       podway_contract.include?("podway.status-result/v3") &&
       podway_contract.include?("prepared revision-0 session") &&
       podway_contract.include?("session.begin") &&
       podway_contract.include?("podway.session-start-result/v3") &&
       podway_contract.include?("podway.session-begin-result/v1") &&
       podway_contract.include?("podway.terminal-disposition-result/v1") &&
       podway_contract.include?("podway.session-reset-result/v1") &&
       podway_contract.include?("Do not record evidence") &&
       podway_contract.include?("matching prepared session is recoverable workflow state"),
       "Podway v0.2.5 prepared-session contract is missing")
assert(podway_contract.include?("## Record Terminal Ownership Conservatively") &&
       podway_contract.include?("Use `handed_off` only when an exact authoritative external result already exists") &&
       podway_contract.include?("exact commit SHA") &&
       podway_contract.include?("Use `not_required` only for a disclosed internal Aquarium boundary") &&
       podway_contract.include?("leave the terminal revision undisposed") &&
       podway_contract.include?("never choose force reset or force replacement automatically") &&
       podway_contract.include?("start --replace-eligible"),
       "Podway terminal disposition and eligible replacement policy is incomplete")
assert(podway_contract.include?("## Hand Off Across Workflow Owners") &&
       podway_contract.include?("replace-after-disposition, never automatic resume") &&
       podway_contract.include?("stable artifact reference") &&
       podway_contract.include?("successor includes replacement") &&
       podway_contract.include?("current eligible `session.start_replace` template") &&
       podway_contract.include?("never force replacement"),
       "Podway cross-owner handoff must be explicit, verified, and fenced")
assert(podway_contract.include?("Only `task-handler`, `epic-handler`, `epic-validator`, `new-project`, `new-feature`, `refactor`, `war-room`, and `design-qa` may own or advance") &&
       podway_contract.include?("standalone user request that explicitly invokes `$use-podway`") &&
       podway_contract.include?("may inspect only the bounded session facts needed for readiness diagnosis") &&
       podway_contract.include?("`$aquarium:task-commit` may inspect only bounded read-only current-session facts") &&
       podway_contract.include?("must never advance or mutate Podway"),
       "Podway workflow ownership and standalone lifecycle authority are not separated")
assert(podway_contract.include?("$use-podway") &&
       podway_contract.include?("optional skill is unavailable or invalid") &&
       podway_contract.include?("Aquarium roadmap authority"),
       "Podway optional-skill precedence and fallback are missing")
assert(podway_contract.include?("readiness_status=not_configured") &&
       podway_contract.include?("LEGACY_PROCEDURE_STATE_UNSUPPORTED"),
       "Podway readiness absence and legacy runtime state are not distinguished")
assert(podway_contract.include?("Select Podway by default for every Git-backed invocation") &&
       podway_contract.include?("before its managed session starts") &&
       podway_contract.include?("never carry an opt-out forward implicitly"),
       "Podway must be default-selected with a workflow-local pre-session opt-out")
assert(podway_contract.include?("owning Aquarium invocation selects Podway by default") &&
       podway_contract.include?("invisible to that workflow"),
       "Podway availability must remain separate from handler selection")
assert(podway_contract.include?("choose between repair") &&
       podway_contract.include?("Do not silently fall back"),
       "Podway readiness failures must require a repair-or-opt-out decision")
assert(podway_contract.include?("prepared, running, incomplete, or undisposed terminal session is a blocking lifecycle conflict") &&
       podway_contract.include?("disposed terminal session is an eligible successor candidate") &&
       podway_contract.include?("Never route it to `$aquarium:dev-setup` repair") &&
       podway_contract.include?("Resume unfinished work through its matching owner") &&
       podway_contract.include?("standalone explicit `$use-podway` request") &&
       podway_contract.include?("without a separate reset") &&
       podway_contract.include?("Reset is deletion, not preparation for a successor workflow"),
       "healthy Podway session conflicts must route to lifecycle ownership, not setup repair")
assert(podway_contract.include?("current-session discard flow") &&
       podway_contract.include?("After the session starts, do not abandon it") &&
       podway_contract.include?("Never cancel, reset, force-replace, reopen, or reinterpret a blocking lifecycle conflict automatically"),
       "Podway sessions must not be abandoned or cleaned up automatically")
assert(podway_contract.include?("## Handle In-Progress Stop Requests") &&
       podway_contract.include?("**Resume later:**") &&
       podway_contract.include?("**Abandon and preserve history:**") &&
       podway_contract.include?("**Delete the session:**"),
       "Podway stop requests must distinguish leave-active, cancel, and reset dispositions")
assert(podway_contract.include?("cancelled session never reactivates") &&
       podway_contract.include?("preview the fenced reset with `--dry-run`") &&
       podway_contract.include?("obtain separate explicit authorization") &&
       podway_contract.include?("verify `SESSION_NOT_FOUND`"),
       "Podway cancel and destructive reset semantics must remain explicit")
assert(podway_contract.include?("None of these dispositions commits work, changes roadmap state, or proves the goal achieved") &&
       podway_contract.include?("start a new explicitly opted-out workflow") &&
       podway_contract.include?("never switch the current workflow in place"),
       "Podway lifecycle disposition must remain separate from Aquarium completion and opt-out restart")
{ "task-handler" => task_handler, "epic-handler" => epic_handler, "epic-validator" => epic_validator }.each do |name, body|
  assert(body.include?("Use Podway by default") &&
         body.include?("explicit pre-session opt-out") &&
         body.include?("On degraded readiness") &&
         body.include?("`$aquarium:dev-setup` repair") &&
         body.include?("shared lifecycle-conflict route") &&
         body.include?("explicit cancellation or deletion to `$use-podway`") &&
         body.include?("disposed terminal session with verified handoff evidence") &&
         body.include?("use `start --replace-eligible` without a separate reset") &&
         body.include?("Never describe that conflict as setup repair") &&
         !body.include?("on degraded readiness or") &&
         body.include?("shared `Handle In-Progress Stop Requests` flow") &&
         body.include?("never assume pause, cancel, reset") &&
         body.include?("separate fenced `begin`"),
         "#{name} must separate readiness repair, lifecycle conflicts, opt-out, and in-progress stops")
end
assert(task_handler.include?("exact required commit SHA") &&
       task_handler.include?("leave the session undisposed") &&
       task_handler.include?("Never reset the final task session automatically"),
       "task-handler must bind handoff to a verified task commit without cleanup")
assert(epic_handler.include?("Record `handed_off` with the exact task commit SHA") &&
       epic_handler.include?("fresh eligible replacement template") &&
       epic_handler.include?("record `not_required` only after verifying") &&
       epic_handler.include?("leave the final terminal session intact"),
       "epic-handler must sequence v0.2.5 dispositions and eligible replacements")
assert(epic_validator.include?("validation-record commit") &&
       epic_validator.include?("record `handed_off` with that exact commit SHA") &&
       epic_validator.include?("leave the final terminal session intact") &&
       epic_validator.include?("leave it undisposed rather than inventing a reference"),
       "epic-validator must hand off only a verified durable validation result")
assert(agents_reference.include?("$use-podway") &&
       agents_reference.include?("only the corresponding CLI is installed"),
       "AGENTS guidance must conditionally reference use-podway")
assert(agents_reference.include?("use Podway by default") &&
       agents_reference.include?("opts out before the first managed-session mutation") &&
       agents_reference.include?("cancellation, or current-session discard flow") &&
       agents_reference.include?("$aquarium:new-project") &&
       agents_reference.include?("$aquarium:war-room") &&
       agents_reference.include?("$aquarium:design-qa") &&
       agents_reference.include?("Keep each owner opt-out local"),
       "AGENTS guidance must preserve default use and workflow-local opt-out")

required_evidence = ->(*nodes) { nodes.map { |node| [node, true] } }
expected_procedure_graphs = {
  "aquarium-task-v2.yaml" => {
    "id" => "aquarium-task-v2",
    "entry" => "record-plan",
    "manual_targets" => %w[implement verify refine document review],
    "evidence" => {
      "decide-verification" => required_evidence.call("implement", "verify"),
      "decide-review" => required_evidence.call("review"),
      "assess-goal" => required_evidence.call("record-plan", "implement", "verify", "refine", "document", "review"),
      "approve-closeout" => required_evidence.call("assess-goal", "record-outcome")
    },
    "nodes" => {
      "record-plan" => { "next" => "implement" },
      "implement" => { "next" => "verify" },
      "verify" => { "next" => "decide-verification" },
      "decide-verification" => { "routes" => { "passed" => %w[refine advance], "failed" => %w[implement rework] } },
      "refine" => { "next" => "document" },
      "document" => { "next" => "review" },
      "review" => { "next" => "decide-review" },
      "decide-review" => { "routes" => { "approved" => %w[assess-goal advance], "changes-requested" => %w[refine rework] } },
      "assess-goal" => { "routes" => { "achieved" => %w[record-outcome advance], "not-achieved" => %w[record-outcome advance], "superseded" => %w[record-outcome advance] } },
      "record-outcome" => { "next" => "approve-closeout" },
      "approve-closeout" => { "routes" => { "approved" => %w[closeout advance], "changes-requested" => %w[refine rework] } },
      "closeout" => { "terminal" => true }
    }
  },
  "aquarium-goal-v2.yaml" => {
    "id" => "aquarium-goal-v2",
    "entry" => "complete-work",
    "manual_targets" => %w[complete-work record-evidence],
    "evidence" => {
      "decide-evidence" => required_evidence.call("complete-work", "record-evidence"),
      "assess-goal" => [["complete-work", true], ["record-evidence", true], ["record-hardening-deferral", false]]
    },
    "nodes" => {
      "complete-work" => { "next" => "record-evidence" },
      "record-evidence" => { "next" => "decide-evidence" },
      "decide-evidence" => { "routes" => { "supported" => %w[assess-goal advance], "deferred-for-hardening" => %w[record-hardening-deferral advance], "rework-required" => %w[complete-work rework] } },
      "record-hardening-deferral" => { "next" => "assess-goal" },
      "assess-goal" => { "routes" => { "achieved" => %w[closeout advance], "not-achieved" => %w[closeout advance], "superseded" => %w[closeout advance] } },
      "closeout" => { "terminal" => true }
    }
  },
  "aquarium-validation-v2.yaml" => {
    "id" => "aquarium-validation-v2",
    "entry" => "capture-baseline",
    "manual_targets" => %w[audit remediate re-audit final-review],
    "evidence" => {
      "decide-gaps" => required_evidence.call("audit"),
      "decide-re-audit" => required_evidence.call("remediate", "re-audit"),
      "decide-final-review" => required_evidence.call("final-review"),
      "assess-goal" => required_evidence.call("capture-baseline", "final-review")
    },
    "nodes" => {
      "capture-baseline" => { "next" => "audit" },
      "audit" => { "next" => "decide-gaps" },
      "decide-gaps" => { "routes" => { "clean" => %w[final-review advance], "gaps-found" => %w[remediate advance] } },
      "remediate" => { "next" => "re-audit" },
      "re-audit" => { "next" => "decide-re-audit" },
      "decide-re-audit" => { "routes" => { "clean" => %w[final-review advance], "gaps-found" => %w[remediate rework] } },
      "final-review" => { "next" => "decide-final-review" },
      "decide-final-review" => { "routes" => { "validated" => %w[assess-goal advance], "rework-required" => %w[audit rework] } },
      "assess-goal" => { "routes" => { "achieved" => %w[closeout advance], "not-achieved" => %w[closeout advance], "superseded" => %w[closeout advance] } },
      "closeout" => { "terminal" => true }
    }
  },
  "aquarium-design-v2.yaml" => {
    "id" => "aquarium-design-v2",
    "entry" => "capture-context",
    "manual_targets" => %w[discover draft quality approve-diff],
    "evidence" => {
      "decide-quality" => required_evidence.call("draft", "quality"),
      "approve-diff" => required_evidence.call("draft", "quality"),
      "assess-goal" => required_evidence.call("capture-context", "apply-documents")
    },
    "nodes" => {
      "capture-context" => { "next" => "discover" },
      "discover" => { "next" => "draft" },
      "draft" => { "next" => "quality" },
      "quality" => { "next" => "decide-quality" },
      "decide-quality" => { "routes" => { "passed" => %w[approve-diff advance], "revise" => %w[draft rework] } },
      "approve-diff" => { "routes" => { "approved" => %w[apply-documents advance], "changes-requested" => %w[draft rework] } },
      "apply-documents" => { "next" => "assess-goal" },
      "assess-goal" => { "routes" => { "achieved" => %w[closeout advance], "not-achieved" => %w[closeout advance], "superseded" => %w[closeout advance] } },
      "closeout" => { "terminal" => true }
    }
  },
  "aquarium-war-room-v2.yaml" => {
    "id" => "aquarium-war-room-v2",
    "entry" => "capture-baseline",
    "manual_targets" => %w[investigate draft-task draft-epic draft-incomplete],
    "evidence" => {
      "decide-cause" => required_evidence.call("investigate"),
      "classify-scope" => required_evidence.call("investigate", "decide-cause"),
      "quality" => %w[draft-task draft-epic draft-incomplete].map { |node| [node, false] },
      "decide-quality" => %w[draft-task draft-epic draft-incomplete].map { |node| [node, false] } + [["quality", true]],
      "approve-diff" => %w[draft-task draft-epic draft-incomplete].map { |node| [node, false] } + [["quality", true]],
      "assess-goal" => [["investigate", true], ["document", false], ["record-rejection", false]]
    },
    "nodes" => {
      "capture-baseline" => { "next" => "investigate" },
      "investigate" => { "next" => "decide-cause" },
      "decide-cause" => { "routes" => { "established" => %w[classify-scope advance], "investigate-more" => %w[investigate rework], "blocked" => %w[draft-incomplete advance] } },
      "classify-scope" => { "routes" => { "task" => %w[draft-task advance], "epic" => %w[draft-epic advance], "incomplete" => %w[draft-incomplete advance] } },
      "draft-task" => { "next" => "quality" },
      "draft-epic" => { "next" => "quality" },
      "draft-incomplete" => { "next" => "quality" },
      "quality" => { "next" => "decide-quality" },
      "decide-quality" => { "routes" => { "passed" => %w[approve-diff advance], "revise" => %w[investigate rework] } },
      "approve-diff" => { "routes" => { "approved" => %w[document advance], "changes-requested" => %w[record-rejection advance] } },
      "document" => { "next" => "assess-goal" },
      "record-rejection" => { "next" => "assess-goal" },
      "assess-goal" => { "routes" => { "achieved" => %w[closeout advance], "not-achieved" => %w[closeout advance], "superseded" => %w[closeout advance] } },
      "closeout" => { "terminal" => true }
    }
  }
}
procedures_directory = PLUGIN.join("assets/podway/procedures")
assert(Dir[procedures_directory.join("*")].map { |path| File.basename(path) }.sort == expected_procedure_graphs.keys.sort,
       "managed Podway procedure directory must contain exactly the expected procedures")
expected_procedure_graphs.each do |filename, expected|
  path = procedures_directory.join(filename)
  assert(path.file?, "managed Podway procedure is missing: #{filename}")
  procedure = YAML.safe_load(path.read, aliases: false)
  assert(procedure.fetch("schema") == "podway.procedure/v2", "managed procedure must use v2: #{filename}")
  assert(procedure.fetch("id") == expected.fetch("id"), "managed procedure ID mismatch: #{filename}")
  expected_version = %w[aquarium-task-v2.yaml aquarium-goal-v2.yaml aquarium-validation-v2.yaml].include?(filename) ? "2" : "1"
  assert(procedure.fetch("version") == expected_version, "managed procedure version drifted: #{filename}")
  assert(procedure.fetch("goal_tracking") == true, "managed procedure must track goals: #{filename}")
  assert(procedure.dig("graph", "entry") == expected.fetch("entry"), "managed procedure entry drifted: #{filename}")
  assert(procedure.fetch("manual_rework").fetch("allowed_targets") == expected.fetch("manual_targets"),
         "managed procedure manual rework targets drifted: #{filename}")
  actual_nodes = procedure.dig("graph", "nodes").each_with_object({}) do |node, index|
    spec = {}
    spec["next"] = node["next"] if node.key?("next")
    spec["terminal"] = node["terminal"] if node.key?("terminal")
    if node.key?("routes")
      spec["routes"] = node["routes"].transform_values { |route| [route.fetch("to"), route.fetch("effect")] }
    end
    index[node.fetch("id")] = spec
  end
  assert(actual_nodes == expected.fetch("nodes"),
         "managed procedure graph transitions drifted: #{filename}")
  actual_evidence = procedure.dig("graph", "nodes").filter_map do |node|
    next unless node.key?("evidence_from")
    entries = node.fetch("evidence_from").map { |entry| [entry.fetch("node"), entry.fetch("required", true)] }
    [node.fetch("id"), entries]
  end.to_h
  assert(actual_evidence == expected.fetch("evidence"),
         "managed procedure evidence bindings drifted: #{filename}")
end

task_procedure_path = procedures_directory.join("aquarium-task-v2.yaml")
task_procedure_text = task_procedure_path.read
task_procedure = YAML.safe_load(task_procedure_text, aliases: false)
task_procedure_nodes = task_procedure.dig("graph", "nodes").each_with_object({}) do |node, index|
  index[node.fetch("id")] = node
end
task_assess_evidence = task_procedure_nodes.fetch("assess-goal").fetch("evidence_from").map { |entry| [entry.fetch("node"), entry.fetch("required")] }
assert(task_assess_evidence == %w[record-plan implement verify refine document review].map { |node| [node, true] },
       "task procedure assess-goal must draw required evidence from the full phase trail")
assert(task_procedure_text.include?("must reach implementation through manual rework"),
       "task procedure must document the manual-rework escape to implementation")

review_item_index = lambda do |procedure, definition|
  procedure.dig("node_definitions", definition, "items").to_h { |item| [item.fetch("id"), item] }
end
plan_handoff_item = lambda do |procedure, definition|
  item = review_item_index.call(procedure, definition).fetch("plan-handoff-artifact")
  assert(item.fetch("type") == "artifact" &&
         item.fetch("required") == false &&
         item.fetch("allowed_media_types") == ["text/markdown"],
         "#{procedure.fetch('id')} #{definition} must expose one optional Markdown plan artifact")
end
plan_handoff_item.call(task_procedure, "plan-record")
task_review_items = review_item_index.call(task_procedure, "review-record")
assert(task_review_items.fetch("review-round").fetch("type") == "integer" &&
       task_review_items.fetch("review-mode").fetch("choices") == %w[remediation-eligible confirmation-only] &&
       task_review_items.fetch("review-run-id").fetch("type") == "text",
       "task procedure must record the Mulgae root review ordinal, mode, and exact run")
assert(task_procedure_text.include?("leave a confirmation-only review with valid findings undecided") &&
       task_procedure_text.include?("Select no option while a confirmation-only review retains a valid finding"),
       "task procedure must represent the confirmation-only user hold")
assert(task_procedure_text.include?("Review is incomplete, CI failed, or a remediation-eligible valid finding"),
       "task procedure must route a failing-CI review to rework even with zero findings")

validation_procedure_text = procedures_directory.join("aquarium-validation-v2.yaml").read
validation_procedure = YAML.safe_load(validation_procedure_text, aliases: false)
plan_handoff_item.call(validation_procedure, "baseline-record")
validation_review_items = review_item_index.call(validation_procedure, "final-review-record")
assert(validation_review_items.fetch("review-round").fetch("type") == "integer" &&
       validation_review_items.fetch("review-mode").fetch("choices") == %w[remediation-eligible confirmation-only] &&
       validation_review_items.fetch("review-run-id").fetch("type") == "text" &&
       validation_procedure_text.include?("leave a confirmation-only review with valid findings undecided") &&
       validation_procedure_text.include?("Evidence is stale or incomplete, CI failed"),
       "validation procedure must record bounded whole-epic review state and its user hold")

goal_procedure = YAML.safe_load(procedures_directory.join("aquarium-goal-v2.yaml").read, aliases: false)
plan_handoff_item.call(goal_procedure, "work-record")
goal_review_items = review_item_index.call(goal_procedure, "evidence-record")
assert(goal_review_items.fetch("review-round").fetch("type") == "integer" &&
       goal_review_items.fetch("review-mode").fetch("choices") == %w[remediation-eligible hardening-deferral-eligible] &&
       goal_review_items.fetch("review-run-id").fetch("type") == "text",
       "goal procedure must record the member-task review ordinal, mode, and exact run")
goal_procedure_text = procedures_directory.join("aquarium-goal-v2.yaml").read
assert(goal_procedure_text.include?("Required checks and review are complete, CI passed") &&
       goal_procedure_text.include?("Evidence or CI failed"),
       "goal procedure must require passing CI for support and route failure to rework")
goal_deferral_items = review_item_index.call(goal_procedure, "hardening-deferral-record")
assert(goal_deferral_items.fetch("hardening-deferral-run-id").fetch("type") == "text" &&
       goal_deferral_items.fetch("hardening-deferral-finding-ids").fetch("type") == "list" &&
       goal_deferral_items.fetch("hardening-deferral-finding-ids").fetch("unique") == true &&
       goal_deferral_items.fetch("hardening-deferral-finding-ids").fetch("max_items") == 200,
       "goal procedure must separate the exact deferred Mulgae run and finding identities")
goal_procedure_nodes = goal_procedure.dig("graph", "nodes").to_h { |node| [node.fetch("id"), node] }
goal_assess_evidence = goal_procedure_nodes.fetch("assess-goal").fetch("evidence_from").map do |entry|
  [entry.fetch("node"), entry.fetch("required")]
end
assert(goal_assess_evidence == [["complete-work", true], ["record-evidence", true], ["record-hardening-deferral", false]],
       "goal procedure must include optional hardening-deferral evidence in assessment")

procedure_nodes = expected_procedure_graphs.transform_values { |spec| spec.fetch("nodes").keys }
skill_procedure_owners = {
  "task-handler" => %w[aquarium-task-v2.yaml],
  "task-plan" => %w[aquarium-task-v2.yaml],
  "task-implement" => %w[aquarium-task-v2.yaml],
  "task-verify" => %w[aquarium-task-v2.yaml],
  "task-refine" => %w[aquarium-task-v2.yaml],
  "task-document" => %w[aquarium-task-v2.yaml],
  "task-review" => %w[aquarium-task-v2.yaml],
  "task-close" => %w[aquarium-task-v2.yaml],
  "epic-handler" => %w[aquarium-goal-v2.yaml aquarium-validation-v2.yaml],
  "epic-validator" => %w[aquarium-validation-v2.yaml],
  "new-project" => %w[aquarium-design-v2.yaml],
  "new-feature" => %w[aquarium-design-v2.yaml],
  "refactor" => %w[aquarium-design-v2.yaml],
  "design-qa" => %w[aquarium-design-v2.yaml],
  "war-room" => %w[aquarium-war-room-v2.yaml]
}
skill_procedure_owners.each do |skill_name, owners|
  assert(expected_skill_names.include?(skill_name),
         "Procedure ownership names an unknown skill: #{skill_name}")
  owners.each do |owner|
    assert(procedure_nodes.key?(owner),
           "Procedure ownership names an unknown Procedure: #{skill_name} -> #{owner}")
  end
end
skill_paths.each do |path|
  body = path.read
  node_ids = (body.scan(/session is at `([a-z][a-z0-9-]*)`/) + body.scan(/approved plan at `([a-z][a-z0-9-]*)`/)).flatten
  next if node_ids.empty?

  skill_name = path.dirname.basename.to_s
  owners = skill_procedure_owners[skill_name]
  assert(owners, "skill with Podway node references has no Procedure ownership: #{path}")
  node_ids.each do |node_id|
    assert(owners.any? { |owner| procedure_nodes.fetch(owner).include?(node_id) },
           "skill references a node outside its owned Procedures #{owners.join(', ')}: #{path} -> #{node_id}")
  end
end

assert(task_handler.include?("only after an `achieved` goal assessment") &&
       task_handler.include?("record no decision"),
       "task-handler must gate success on the goal assessment and skip decisions on holds")
assert(task_review.include?("only a pass with no file changes supports `approved`"),
       "task-review must route review-phase fixes through the rework path")
assert(task_handler.include?("In rounds one through three") &&
       task_handler.include?("Round four is confirmation-only") &&
       task_handler.include?("Reset the ordinal only for an explicitly approved new goal revision") &&
       task_handler.include?("Do not use `followup`, `delta`, or `rerun`") &&
       task_handler.include?("never use `latest`, objective inference, or an uncertain candidate") &&
       task_review.include?("handler-provided positive review ordinal") &&
       task_review.include?("do not change files") &&
       task_review.include?("Do not invoke `followup`, `delta`, `rerun`") &&
       task_review.include?("failing decision or `request_changes` outcome still consumes the ordinal"),
       "task-handler must stop early and escalate after bounded Mulgae remediation")
assert(task_handler.include?("A session created from an earlier version of this managed Procedure is not migrated") &&
       epic_handler.include?("Sessions created from an earlier version of this managed Procedure are not migrated") &&
       !task_handler.include?("Legacy Procedure v1") &&
       !epic_handler.include?("Existing immutable Procedure v1"),
       "handlers must describe compatibility by managed Procedure version rather than a stale v1 label")

podway_blind_skills = %w[
  task-plan task-implement task-verify task-refine task-document task-review task-close
  independent-review release-qa
]
podway_blind_skills.each do |name|
  body = PLUGIN.join("skills/#{name}/SKILL.md").read
  assert(!body.match?(/podway/i), "leaf and utility skill must remain Podway-blind: #{name}")
end
assert(independent_review.include?("Return the target and snapshot, independent reviewer verdict") &&
       task_refine.include?("Return deslop actions, optimization reasoning") &&
       task_close.include?("Return the three answers, final roadmap state"),
       "Podway-blind review, refinement, and closeout must return native evidence")
assert(epic_validator.include?("ignore every Podway readiness or session state"),
       "opted-out epic validation must ignore every Podway state")
assert(task_handler.include?("Immediately before each phase delegation") &&
       epic_handler.include?("before each bounded work delegation") &&
       epic_validator.include?("before each bounded audit or remediation delegation"),
       "Podway owners must validate expected state before delegation and record verified native evidence afterward")

assert(epic_handler.include?("do not invoke `$aquarium:independent-review`") &&
       independent_review.include?("user explicitly invokes"),
       "independent-review must remain user-invoked only")
assert(independent_review.include?("skills get orca-cli") && independent_review.include?("skills get orchestration"),
       "independent-review must load version-matched Orca guides")
assert(independent_review.include?("--worktree current --agent codex"),
       "independent-review must use a fresh Codex in the current worktree")
assert(independent_review.include?("Never substitute a generic subagent"),
       "independent-review must fail closed when Orca is unavailable")
assert(independent_review.include?("Do not rerun tests") && independent_review.include?("Do not implement a proposed response"),
       "independent-review must remain review-only")
assert(independent_review.include?("Keep technical review evidence and Orca lifecycle settlement as separate statuses"),
       "independent-review must separate findings from lifecycle settlement")
assert(independent_review.include?("Valid") && independent_review.include?("Invalid") &&
       independent_review.include?("Needs confirmation"),
       "independent-review must adjudicate reviewer findings")
assert(!independent_review.include?("owning Aquarium workflow requested"),
       "independent-review must not reintroduce the removed owning-workflow qualifier")

assert(release_qa.include?("user explicitly invokes") &&
       release_qa.include?("The previous release is assumed to work") &&
       release_qa.include?("Map every commit"),
       "release-qa must remain explicit and cover the complete release delta")
assert(release_qa.include?("prospective release identifier, not as a required value in candidate files") &&
       release_qa.include?("committed version metadata still names the previous release or already names the intended version") &&
       release_qa.include?("Neither state is an `INCOMPLETE` condition or finding by itself") &&
       release_qa.include?("Define the delta solely from Git history") &&
       release_qa.include?("whether the files still say `v0.2.3` or already say `v0.2.4`"),
       "release-qa must accept candidates before or after target-version metadata is committed")
assert(release_qa.include?("A dirty worktree still prevents an exact committed candidate") &&
       release_qa.include?("When remediation adds commits") &&
       release_qa.include?("rerun release QA over the complete previous-release-to-candidate delta") &&
       release_qa.include?("its timing never narrows the delta"),
       "release-qa must distinguish version timing from candidate identity and re-QA remediated candidates")
assert(release_qa.include?("Do not run existing automated tests") &&
       release_qa.include?("mktemp -d /tmp/release-qa.XXXXXX") &&
       release_qa.include?("fresh subagents"),
       "release-qa must use isolated scenarios without duplicating existing tests")
assert(release_qa.include?("already-configured ambient authentication") &&
       release_qa.include?("existing ambient authentication for private repositories") &&
       release_qa.include?("never initiate an authentication flow") &&
       release_qa.include?("networked or live product scenarios"),
       "release-qa must separate authorized release discovery from credentials and networked scenarios")
assert(release_qa.include?("Do not replace an unavailable, failed, or timed-out fresh worker") &&
       release_qa.include?("source repository read-only") &&
       release_qa.include?("Do not edit source files") &&
       release_qa.include?("release-readiness decisions"),
       "release-qa must fail incomplete instead of weakening isolation")
assert(release_qa.include?("`PASS`") && release_qa.include?("`FINDINGS`") &&
       release_qa.include?("`INCOMPLETE`") && release_qa.include?("propose fixes"),
       "release-qa must report evidence without remediation")
assert(release_qa.include?("## Establish Design Gate Enrollment") &&
       release_qa.include?("authoritative current and retired registry paths") &&
       release_qa.include?("concise title") &&
       release_qa.include?("Design Gate not enrolled") &&
       release_qa.include?("existed in history but the candidate is missing") &&
       release_qa.include?("every active gate") &&
       release_qa.include?("under the disposable-project isolation regime below") &&
       release_qa.include?("stop with `INCOMPLETE` on mutation") &&
       release_qa.include?("sole exception is an exact local offline procedure") &&
       release_qa.include?("both applicable matrices"),
       "release-qa must combine gradual Design Gate enrollment with a separate release-delta matrix")

assert(task_plan.include?("decision-complete plan"), "task-plan must own decision-complete planning")
assert(task_plan.include?("Do not create a goal"), "task-plan must remain mutation-free")
assert(task_plan.include?("## Produce and Approve the Plan"),
       "task-plan must own an explicit plan approval section")
assert(task_plan.include?("If approval is refused, withheld, or given for a different action, stop"),
       "task-plan must stop on refused, withheld, or mismatched approval")
assert(task_implement.include?("smallest maintainable change"), "task-implement must bound implementation")
assert(task_implement.include?("Do not stage"), "task-implement must leave staging to later phases")
assert(task_verify.include?("requirement-to-test matrix"), "task-verify must map requirements to evidence")
assert(task_verify.include?("do not rerun the same check merely to duplicate it"),
       "task-verify must avoid duplicating current user-run tests")
assert(task_verify.include?("Stop and escalate to the orchestrator when a required gate is permanently blocked"),
       "task-verify must escalate a permanently blocked gate")
assert(task_verify.include?("when Gaori or another evidence-compression wrapper is used"),
       "task-verify must trust the underlying exit status behind evidence wrappers")

deslop_index = task_refine.index("Load and follow the separately installed upstream `$deslop`")
optimization_stage_index = task_refine.index("stage the current task-owned changes as the optimization baseline")
optimization_index = task_refine.index("## Optimize")
assert(deslop_index && optimization_stage_index && optimization_index &&
       deslop_index < optimization_stage_index && optimization_stage_index < optimization_index,
       "task-refine must stage the post-deslop task diff before optimization")
assert(task_refine.include?("use that staged snapshot as the sole optimization source of truth"),
       "task-refine must optimize against the staged task snapshot")
assert(task_refine.include?("Keep optimization edits unstaged during the pass"),
       "task-refine must isolate the optimization delta from its staged baseline")
assert(task_refine.include?("preserve all pre-existing staged content"),
       "task-refine must protect existing staged work")
assert(task_refine.include?("stage only the confirmed task-owned optimization delta"),
       "task-refine must refresh the staged task diff after verification")
assert(task_refine.include?("never reconstruct or skip it") &&
       task_handler.include?("Require one valid upstream `$deslop` installation before plan approval") &&
       task_handler.include?("missing, duplicated, symlinked, lacks the upstream LICENSE, or has invalid frontmatter") &&
       task_handler.include?("Never substitute an Aquarium-owned copy"),
       "task delivery must require the separately installed upstream Deslop skill")
assert(task_refine.include?("tracing callers and consumers"),
       "task-refine must verify whether task-introduced abstractions are necessary")
assert(task_refine.include?("Remove an abstraction when it only adds indirection"),
       "task-refine must remove verified unnecessary abstractions")
assert(task_refine.include?("Do not manufacture an edit"),
       "task-refine must allow a no-change optimization pass")
assert(task_refine.include?("Quantitative benchmarks are unnecessary"),
       "task-refine must not require numeric optimization proof by default")
assert(task_refine.include?("never report an unmeasured performance gain as measured fact"),
       "task-refine must distinguish qualitative reasoning from measured performance")

assert(task_document.include?("preferring `In Review` only when that value is defined"),
       "task-document must use the roadmap's review vocabulary")
handoff_semantics_index = task_document.index("## Handoff Semantics")
sync_documentation_index = task_document.index("## Synchronize and Validate")
assert(handoff_semantics_index && sync_documentation_index && handoff_semantics_index < sync_documentation_index,
       "task-document must define handoff semantics before synchronization")
assert(task_document.include?("**Internal handoff:**") &&
       task_document.include?("Name every consuming task") &&
       task_document.include?("authoritative source or starting point") &&
       task_document.include?("required and prohibited actions") &&
       task_document.include?("invalidates existing evidence or requires revalidation") &&
       task_document.include?("remove or update the entry after use") &&
       task_document.include?("Never accumulate Internal handoffs as permanent completed-task history"),
       "task-document must define the Internal handoff consumer and lifecycle")
assert(task_document.include?("**External handoff:**") &&
       task_document.include?("stable cross-epic dependency or constraint") &&
       task_document.include?("downstream epic, task, consumer, or subsystem") &&
       task_document.include?("removal or update when the underlying contract changes") &&
       task_document.include?("no External handoff is currently required or omitting the section"),
       "task-document must define the External handoff threshold and lifecycle")
assert(task_document.include?("When no actionable Internal or External instruction exists, create no repository handoff") &&
       task_document.include?("update only the affected durable documentation and lifecycle state"),
       "task-document must allow lifecycle-only completion without a handoff")
assert(task_document.include?("Will this instruction materially reduce the next development AI's analysis time or risk of an incorrect implementation?") &&
       ["Reference this", "Be careful about this", "You must do this", "You must not do this", "Revalidate when this changes"].all? { |category| task_document.include?(category) },
       "task-document must apply the downstream usefulness test and actionable categories")
assert(task_document.include?("task completion report") &&
       task_document.include?("Git log substitute") &&
       task_document.include?("managed-session export") &&
       task_document.include?("test report") &&
       task_document.include?("list of files or commands changed") &&
       task_document.include?("prefer a link to the authoritative source"),
       "task-document must reject evidence-log handoffs and prefer canonical references")
assert(task_document.include?("required for downstream correctness, compatibility, or reproducibility") &&
       task_document.include?("why the next task needs it") &&
       task_document.include?("when it becomes stale") &&
       task_document.include?("what must be revalidated after it changes"),
       "task-document must bound exact evidence with staleness and revalidation rules")
assert(task_document.include?("This phase report is orchestration evidence, not a repository handoff") &&
       task_document.include?("Do not copy it into durable documentation unless an item independently passes the downstream usefulness test"),
       "task-document must keep its complete phase report separate from durable handoffs")
assert(task_handler.include?("every repository handoff is actionable for a named future consumer") &&
       task_handler.include?("clear Internal or External lifecycle") &&
       task_handler.include?("completion evidence is not duplicated as handoff prose") &&
       task_handler.include?("consumed or stale Internal entries are removed or updated") &&
       task_handler.include?("documentation validation has current evidence"),
       "task-handler must enforce the durable repository handoff postcondition")
assert(task_handler.include?("a leaf skill's phase handoff summary to the orchestrator") &&
       task_handler.include?("Podway evidence recorded for session recovery") &&
       task_handler.include?("a durable repository handoff for future development agents") &&
       task_handler.include?("Only the last belongs in project documentation"),
       "task-handler must separate orchestration, Podway, and repository handoff evidence")
assert(task_handler.include?("Reject or rework documentation") &&
       task_handler.include?("primarily an audit log, completion summary, or collection of evidence"),
       "task-handler must return evidence-log documentation for rework")
assert(task_review.include?("Select exactly one target that contains the complete task diff"),
       "task-review must isolate one complete Mulgae target")
assert(task_review.include?("Treat every finding as an advisory hypothesis"),
       "task-review must verify Mulgae findings")
assert(task_review.include?("to the handler when delegated") &&
       task_review.include?("to the invoking user with the exact `$aquarium:task-handler` continuation"),
       "direct task-review must return remediation through the owning handler workflow")

terminal_status_index = task_close.index("Treat `Completed`, `Blocked`, and `Deferred` as terminal")
status_choice_index = task_close.index("ask the user to select", terminal_status_index)
approval_start_index = task_close.index("## Ask for Final Approval", status_choice_index)
ask_index = task_close.index("request_user_input", approval_start_index)
tests_confirmation_index = task_close.index("Evidence accepted", ask_index)
docs_confirmation_index = task_close.index("Docs approved", ask_index)
implementation_confirmation_index = task_close.index("Approve and commit", ask_index)
non_commit_confirmation_index = task_close.index("Approve and close without commit", ask_index)
non_commit_transition_index = task_close.index("do not stage or commit anything", approval_start_index)
handoff_index = task_close.index("invoke `$aquarium:task-commit`", non_commit_transition_index)
assert(terminal_status_index && status_choice_index && approval_start_index && ask_index &&
       tests_confirmation_index && docs_confirmation_index && implementation_confirmation_index &&
       non_commit_confirmation_index && non_commit_transition_index && handoff_index &&
       terminal_status_index < status_choice_index && status_choice_index < approval_start_index &&
       approval_start_index < ask_index && ask_index < tests_confirmation_index &&
       tests_confirmation_index < docs_confirmation_index && docs_confirmation_index < implementation_confirmation_index &&
       implementation_confirmation_index < non_commit_transition_index && non_commit_transition_index < handoff_index,
       "task-close terminal-state commit and non-commit gates are missing or misordered")
assert(task_close.include?("do not stage or commit anything") &&
       task_close.include?("This path is unavailable when repository authority requires a commit for completion"),
       "task-close must support a safe non-commit closeout path")
assert(task_close.include?("including who ran each check") && !task_close.include?("personally run"),
       "task-close must accept evidence with explicit agent or user provenance")
assert(task_close.include?("any other task-owned code, test, documentation, or roadmap change does"),
       "task-close must invalidate stale confirmations")
assert(task_close.include?("The approved status-only edit does not invalidate approval"),
       "task-close must keep the approved status transition actionable")
assert(task_close.include?("Do not rerun user-confirmed tests or documentation checks solely"),
       "task-close must avoid redundant closeout verification")
assert(task_close.include?("Never infer approval from silence"),
       "task-close must require explicit approval")
assert(task_close.include?("If structured ask/answer is unavailable"),
       "task-close must define an ask/answer fallback")
assert(task_close.include?("This path is unavailable when repository authority requires a commit for completion"),
       "task-close must bound the non-commit path by repository authority")
assert(task_close.include?("Only `Approve and commit` and `Approve and close without commit` are affirmative implementation answers"),
       "task-close must enumerate the affirmative implementation answers")
assert(task_close.include?("Never select a terminal state") &&
       task_close.include?("When only one terminal state exists, ask for confirmation") &&
       task_close.include?("Do not stage or commit independently"),
       "task-close must leave lifecycle choice to the user and commit execution to task-commit")

assert(task_commit.include?("always ask whether the commit belongs to one exact task") &&
       task_commit.include?("Never infer the relationship") &&
       task_commit.include?("require an exact task ID") &&
       task_commit.include?("The initial commit request does not satisfy this dedicated confirmation") &&
       task_commit.include?("Never choose a terminal state for the user") &&
       task_commit.include?("explicitly authorize a checkpoint commit") &&
       task_commit.include?("reconcile lifecycle state again on every later commit request"),
       "task-commit must require explicit task relationship and lifecycle decisions")
assert(task_commit.include?("active matching `task-handler`, `epic-handler`, `epic-validator`") &&
       task_commit.include?("only from that owner's explicit commit handoff") &&
       task_commit.include?("lifecycle decision as either an exact approved edit or an explicit statement") &&
       task_commit.include?("record decision as either an exact approved edit or an explicit statement") &&
       task_commit.include?("review run when applicable") &&
       task_commit.include?("Do not offer an independent path"),
       "task-commit must not bypass an active managed workflow")
assert(task_commit.include?("Mulgae-Deferred-Run: r_...") &&
       task_commit.include?("Mulgae-Deferred-Finding: F...") &&
       task_commit.include?("one repeated `Mulgae-Deferred-Finding: F...` trailer per unique finding") &&
       task_commit.include?("Do not copy finding descriptions, severity, paths, reports, or private Mulgae artifacts") &&
       task_commit.include?("verify any expected deferral trailers from the committed message") &&
       epic_handler.include?("enumerate `Mulgae-Deferred-Run` and every repeated `Mulgae-Deferred-Finding` trailer"),
       "epic deferrals must use exact Mulgae identities in bounded custom commit trailers")
assert(task_commit.include?("AQUARIUM_COMMIT_GATE=task-commit-v1 git commit") &&
       task_commit.include?("Never export it globally") &&
       task_commit.include?("indirect commits performed by other tools may not pass"),
       "task-commit must scope and disclose the direct-command hook marker")
assert(task_commit.include?("$lore-commits") &&
       task_commit.include?("git log -5 --format=fuller") &&
       task_commit.include?("$aquarium:dev-setup") &&
       task_commit.include?("After the commit and its hooks"),
       "task-commit must own Lore, setup escalation, and post-hook verification")

MULGAE_EXTRACTION_EVIDENCE_SENTENCE =
  "Record `structured_extraction_status` independently as `structured`, `mixed`, or `reports_only`. " \
  "`reports_only` is not itself a failure and does not replace or relax any completion condition above; " \
  "the accepted reports remain authoritative, and every extracted finding remains an advisory hypothesis " \
  "that requires local verification."
{
  "epic-handler" => epic_handler,
  "epic-validator" => epic_validator,
  "task-review" => task_review
}.each do |name, body|
  assert(body.include?("`coverage_status=complete`") &&
         body.include?("`ci_decision=pass`") &&
         body.include?("`publication_status=committed`") &&
         body.include?("findings query") &&
         body.include?("zero unresolved valid findings") &&
         body.include?("Provider success or exit status alone is insufficient"),
         "Mulgae review approval conditions have drifted: #{name}")
  assert(body.include?(MULGAE_EXTRACTION_EVIDENCE_SENTENCE),
         "canonical Mulgae extraction-evidence sentence has drifted: #{name}")
end
assert(epic_handler.include?("failing CI decision consumes the ordinal but cannot approve") &&
       task_review.include?("failing decision or `request_changes` outcome still consumes the ordinal"),
       "bounded review rounds must separate operational completion from approval")

approval_precondition = "Do not create a goal, edit files, invoke providers, stage, commit, or alter external state before approval."
{ "epic-handler" => epic_handler, "epic-validator" => epic_validator }.each do |name, body|
  assert(body.include?(approval_precondition), "pre-approval mutation ban is missing: #{name}")
end

{
  "dev-setup SKILL" => dev_setup,
  "dev-setup tool catalog" => tool_catalog,
  "Podway integration contract" => podway_contract
}.each do |name, body|
  assert(body.include?("stable `v0.2.5` through `v0.2.x`"),
         "Podway supported release line has drifted: #{name}")
end

phase_names.each do |name|
  body = PLUGIN.join("skills/#{name}/SKILL.md").read
  assert(body.include?("to the orchestrator"), "leaf skill must return its report to the orchestrator: #{name}")
end

assert(!PLUGIN.join("skills/deslop").exist?,
       "Aquarium must not bundle the third-party Deslop skill or license")

%w[LICENSE README.md PRIVACY.md TERMS.md .github/workflows/validate.yml].each do |relative_path|
  assert(ROOT.join(relative_path).file?, "distribution file is missing: #{relative_path}")
end
[PLUGIN.join("skills"), PLUGIN.join("hooks"), PLUGIN.join("references"), PLUGIN.join("assets/podway/procedures")].each do |path|
  assert(path.directory?, "distribution directory is missing: #{path}")
end
assert(manifest.fetch("skills") == "./skills/", "plugin manifest skills path is incorrect")

hooks_path = PLUGIN.join("hooks/hooks.json")
hook_script = PLUGIN.join("hooks/task_commit_gate.py")
assert(hooks_path.file? && hook_script.file?, "roadmap commit hook files are missing")
hooks = JSON.parse(hooks_path.read)
pre_tool_hooks = hooks.fetch("hooks").fetch("PreToolUse")
assert(pre_tool_hooks.length == 1 && pre_tool_hooks.fetch(0).fetch("matcher") == "^Bash$",
       "roadmap commit hook must target Bash PreToolUse")
hook_command = pre_tool_hooks.fetch(0).fetch("hooks").fetch(0).fetch("command")
assert(hook_command == 'python3 "${PLUGIN_ROOT}/hooks/task_commit_gate.py"',
       "roadmap commit hook must resolve its script through PLUGIN_ROOT")
assert(hook_script.read.include?('git_output(root, "ls-files", "-z")') &&
       hook_script.read.include?("AQUARIUM_COMMIT_GATE=task-commit-v1") &&
       !hook_script.read.match?(/https?:\/\//),
       "roadmap commit hook must remain local and use the task-commit marker")
assert(ROOT.join("README.md").read.include?("open `/hooks` and explicitly trust") &&
       ROOT.join("README.md").read.include?("indirectly by another tool may not pass") &&
       ROOT.join("PRIVACY.md").read.include?("reads up to two million characters") &&
       ROOT.join("TERMS.md").read.include?("not a security boundary or complete enforcement mechanism"),
       "public policies must disclose hook trust, local inspection, and enforcement limits")

workflow = ROOT.join(".github/workflows/validate.yml").read
assert(workflow.include?("ruby/setup-ruby@v1"), "CI must configure Ruby explicitly")
assert(workflow.include?("actions/setup-python@v5"), "CI must configure Python explicitly")
assert(workflow.include?('python -m pip install "PyYAML==6.0.3"'),
       "CI must install the pinned supported PyYAML version")
assert(workflow.include?("tests/test_inspect_tools.py tests/test_task_commit_gate.py tests/test_normalize_manifest.py"),
       "CI must run inspection, commit-hook, and bundle-normalizer tests")
assert(workflow.include?("ruby tests/validate.rb"), "CI must run repository validation")
assert(workflow.include?("astral-sh/ruff-action@v4.1.0") &&
       workflow.include?("plugins/aquarium/hooks/task_commit_gate.py") &&
       workflow.include?("plugins/aquarium/skills/dev-setup-bundle/scripts/normalize_manifest.py") &&
       workflow.include?("tests/test_normalize_manifest.py"),
       "CI must lint the roadmap commit hook and bundle normalizer")
assert(workflow.include?("git diff --check"), "CI must reject whitespace damage")

readme = ROOT.join("README.md").read
assert(readme.include?("plugins/aquarium/assets/logo-white.png"), "README light-theme logo is missing")
assert(readme.include?("plugins/aquarium/assets/logo-black.png"), "README dark-theme logo is missing")
assert(readme.include?("https://home.rootkernel.xyz"), "README homepage is missing")
assert(readme.include?("mailto:cs@rootkernel.xyz"), "README support email is missing")
assert(readme.include?("codex plugin marketplace add irootkernel/aquarium --ref main"),
       "README marketplace install command is missing")
assert(readme.include?("codex plugin add aquarium@aquarium"),
       "README plugin install command is missing")
assert(readme.include?("By [Root Kernel](https://home.rootkernel.xyz)"),
       "README Root Kernel byline is missing")
assert(readme.include?("codex plugin remove root-kernel") &&
       readme.include?("codex plugin marketplace remove root-kernel-dev-skills") &&
       readme.include?("$aquarium:dev-setup"),
       "README product-rename migration is missing")
expected_skill_names.each do |name|
  assert(readme.include?("`#{name}`"), "README skill entry is missing: #{name}")
end
readme_table_names = readme.lines.filter_map { |line| line[/\A\| `([a-z-]+)` \|/, 1] }
assert(readme_table_names.sort == expected_skill_names.sort,
       "README tables must list exactly the expected skills once each")
%w[epic-handler epic-validator task-handler task-commit release-qa dev-setup dev-setup-bundle independent-review new-project new-feature refactor war-room design-qa].each do |name|
  assert(readme.include?("$aquarium:#{name}"), "README invocation token is missing: #{name}")
end
assert(!readme.include?("$aquarium:deslop") &&
       readme.include?("upstream `$deslop` skill is a required prerequisite") &&
       readme.include?("## Thanks") &&
       readme.include?("does not vendor their skill or documentation sources") &&
       readme.include?("Lora declares MIT in its README"),
       "README must document external Deslop and thank all third-party skill sources")
%w[
  https://github.com/irootkernel/sanho
  https://github.com/irootkernel/mulgae
  https://github.com/irootkernel/gaori
  https://github.com/tmdgusya/lora
  https://github.com/cursor/plugins/tree/main/cursor-team-kit
  https://github.com/irootkernel/podway
  https://github.com/Q00/ouroboros
].each do |url|
  assert(readme.include?(url), "README tool URL is missing: #{url}")
end

markdown_paths = Dir[ROOT.join("**/*.md")].map { |path| Pathname.new(path) }.sort
document_paths = markdown_paths.dup
document_paths << ROOT.join("LICENSE")
document_paths.uniq.each { |path| assert_no_hard_wrap(path) }

markdown_paths.each do |path|
  in_fence = false
  path.read.lines.each do |line|
    in_fence = !in_fence if line.lstrip.start_with?("```", "~~~")
    next if in_fence

    line.scan(/\]\(([^)]+)\)/).each do |(target)|
      target = target.strip.sub(/\s+"[^"]*"\z/, "")
      next if target.start_with?("http://", "https://", "mailto:", "#")

      relative_target = target.split("#", 2).first
      next if relative_target.nil? || relative_target.empty?

      assert(path.dirname.join(relative_target).exist?,
             "relative Markdown link does not resolve: #{path} -> #{target}")
    end
  end
end

skill_paths.each do |path|
  lines = path.read.lines.map(&:chomp)
  frontmatter_end = lines[1..].index("---")
  assert(frontmatter_end, "missing closing frontmatter delimiter: #{path}")
  lines[(frontmatter_end + 2)..].each_with_index do |line, offset|
    assert(line.length <= 560,
           "skill body line exceeds 560 characters: #{path}:#{frontmatter_end + 3 + offset} (#{line.length})")
  end
end

assert(Dir[ROOT.join("**/.aquarium")].empty?, "central project-state file must not exist")

puts "validated #{skill_paths.length} skills, marketplace and plugin metadata, managed procedures, cross-file pins, and documentation invariants"
