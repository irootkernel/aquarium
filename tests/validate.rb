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
  docs-setup
  epic-handler
  epic-validator
  independent-review
  new-feature
  new-project
  orca-review
  refactor
  release-handler
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
  test-setup
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
assert((%w[ai-fleet agentic design documentation deslop graph loop lora lore multi-agent orchestration ouroboros podway release qa workflow] - manifest.fetch("keywords")).empty?, "plugin discovery keywords are missing")
assert(manifest.fetch("version") == "0.1.11", "plugin version must be 0.1.11")
release_tag = ENV.fetch("RELEASE_TAG", "")
unless release_tag.empty?
  assert(release_tag == "v#{manifest.fetch('version')}",
         "release tag #{release_tag} must match plugin version v#{manifest.fetch('version')}")
end
assert(manifest.fetch("homepage") == "https://home.rootkernel.xyz", "plugin homepage is incorrect")
assert(manifest.fetch("description").include?("AI Fleet") &&
       manifest.dig("interface", "shortDescription").include?("AI Fleets") &&
       manifest.dig("interface", "longDescription").include?("fleets of AI agents") &&
       !manifest.fetch("description").start_with?("Ouroboros"),
       "plugin metadata must position Aquarium as an AI Fleet engineering layer")
assert(manifest.dig("interface", "longDescription").include?("release-candidate QA") &&
       manifest.dig("interface", "longDescription").include?("Design Gates") &&
       manifest.dig("interface", "longDescription").include?("test setup"),
       "plugin description must advertise test setup, release QA, and Design Gates")
readme_introduction = ROOT.join("README.md").read.split("## Install", 2).first
assert(readme_introduction.include?("engineering reliable software with AI Fleets") &&
       readme_introduction.include?("Agentic Engineering") &&
       readme_introduction.include?("Loop Engineering") &&
       readme_introduction.include?("Graph Engineering") &&
       readme_introduction.include?("not separate products or a rigid maturity model") &&
       readme_introduction.include?("Codex is Aquarium's primary agent runtime") &&
       readme_introduction.include?("rather than promising provider or framework neutrality") &&
       readme_introduction.include?("Codex, Orca, Podway, Sanho, Mulgae, Gaori, Ouroboros, Lora, and Deslop"),
       "README introduction must lead with Aquarium's AI Fleet engineering identity")
assert(manifest.dig("author", "url") == manifest.fetch("homepage"), "author URL must match the homepage")
assert(manifest.dig("author", "email") == "cs@rootkernel.xyz", "support email is incorrect")
prompts = manifest.fetch("interface").fetch("defaultPrompt")
assert(prompts.is_a?(Array) && prompts.length == 2, "plugin defaultPrompt must contain two prompts")
assert(prompts.any? { |prompt| prompt.include?("$aquarium:dev-setup") },
       "plugin defaultPrompt must retain development-tool discovery")
assert(prompts.any? { |prompt| prompt.include?("$aquarium:test-setup") },
       "plugin defaultPrompt must expose test setup")
assert(prompts.any? { |prompt| prompt.include?("$aquarium:docs-setup") },
       "plugin defaultPrompt must expose documentation setup")
%w[websiteURL privacyPolicyURL termsOfServiceURL].each do |key|
  assert(manifest.fetch("interface").fetch(key).start_with?("https://"), "missing interface #{key}")
end
interface = manifest.fetch("interface")
assert(interface.fetch("websiteURL") == manifest.fetch("homepage"), "interface website must match the homepage")
assert(interface.fetch("brandColor") == "#10C4BE", "plugin brand color is incorrect")

assert(!interface.key?("composerIcon") && !interface.key?("logo"),
       "plugin manifest must not reference removed logo assets")
assert_png(PLUGIN.join("assets/hero.png"), 2172, 724)

marketplace = JSON.parse(ROOT.join(".agents/plugins/marketplace.json").read)
assert(marketplace.fetch("name") == "root-kernel", "marketplace name is incorrect")
assert(marketplace.dig("interface", "displayName") == "Root Kernel",
       "marketplace interface displayName is incorrect")
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
dev_setup_script_body = dev_setup_script.read
dev_setup_bundle = PLUGIN.join("skills/dev-setup-bundle/SKILL.md").read
dev_setup_bundle_manifest = PLUGIN.join("skills/dev-setup-bundle/references/manifest.md").read
dev_setup_bundle_script = PLUGIN.join("skills/dev-setup-bundle/scripts/normalize_manifest.py")
agents_reference = PLUGIN.join("skills/dev-setup/references/agents-guidance.md").read
root_agents = ROOT.join("AGENTS.md").read
root_claude = ROOT.join("CLAUDE.md").read
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
independent_review_script = PLUGIN.join("skills/independent-review/scripts/inspect_review_target.py")
independent_review_script_body = independent_review_script.read
orca_review = PLUGIN.join("skills/orca-review/SKILL.md").read
orca_provider_contracts = PLUGIN.join("skills/orca-review/references/provider-contracts.md").read
orca_terminal_helper = PLUGIN.join("skills/orca-review/scripts/create_provider_terminal.py")
orca_terminal_helper_body = orca_terminal_helper.read
orca_state_helper = PLUGIN.join("skills/orca-review/scripts/inspect_repository_state.py")
orca_state_helper_body = orca_state_helper.read
review_contract = PLUGIN.join("references/review-contract.md").read
orca_supervision = PLUGIN.join("references/orca-supervision.md").read
release_qa = PLUGIN.join("skills/release-qa/SKILL.md").read
release_handler = PLUGIN.join("skills/release-handler/SKILL.md").read
release_gate_convergence = PLUGIN.join("skills/release-handler/references/gate-convergence.md").read
release_recovery = PLUGIN.join("skills/release-handler/references/publication-recovery.md").read
release_publication_script = PLUGIN.join("skills/release-handler/scripts/inspect_publication_state.py")
release_publication_script_body = release_publication_script.read
release_handler_script = PLUGIN.join("skills/release-handler/scripts/inspect_release_notes.py")
release_handler_script_body = release_handler_script.read
task_plan = PLUGIN.join("skills/task-plan/SKILL.md").read
task_implement = PLUGIN.join("skills/task-implement/SKILL.md").read
task_verify = PLUGIN.join("skills/task-verify/SKILL.md").read
task_refine = PLUGIN.join("skills/task-refine/SKILL.md").read
task_document = PLUGIN.join("skills/task-document/SKILL.md").read
task_review = PLUGIN.join("skills/task-review/SKILL.md").read
task_close = PLUGIN.join("skills/task-close/SKILL.md").read
task_commit = PLUGIN.join("skills/task-commit/SKILL.md").read
test_setup = PLUGIN.join("skills/test-setup/SKILL.md").read
test_setup_contract = PLUGIN.join("skills/test-setup/references/contract.md").read
test_setup_profiles = PLUGIN.join("skills/test-setup/references/profiles.md").read
test_setup_script = PLUGIN.join("skills/test-setup/scripts/inspect_testing.py")
test_setup_script_body = test_setup_script.read
docs_setup = PLUGIN.join("skills/docs-setup/SKILL.md").read
docs_setup_profiles = PLUGIN.join("skills/docs-setup/references/profiles.md").read
docs_setup_migration = PLUGIN.join("skills/docs-setup/references/migration.md").read
docs_setup_operations = PLUGIN.join("skills/docs-setup/references/operations.md").read
docs_setup_script = PLUGIN.join("skills/docs-setup/scripts/inspect_docs.py")
docs_setup_script_body = docs_setup_script.read
documentation_index_path = ROOT.join("docs/README.md")
documentation_role_paths = %w[
  architecture
  architecture-decision-records
  deferred-feedback
  implementation-tips
  ops
  roadmap
  specs
  todo
].to_h { |role| [role, ROOT.join("docs", role, "README.md")] }
documentation_detail_paths = {
  "capabilities" => ROOT.join("docs/specs/capabilities.md"),
  "workflow-contracts" => ROOT.join("docs/specs/workflow-contracts.md"),
  "tool-integrations" => ROOT.join("docs/specs/tool-integrations.md"),
  "local-interfaces" => ROOT.join("docs/specs/local-interfaces.md"),
  "safety-and-evidence" => ROOT.join("docs/specs/safety-and-evidence.md"),
  "components" => ROOT.join("docs/architecture/components.md"),
  "workflow-runtime" => ROOT.join("docs/architecture/workflow-runtime.md"),
  "state-and-evidence" => ROOT.join("docs/architecture/state-and-evidence.md"),
  "verification" => ROOT.join("docs/architecture/verification.md"),
  "changing-skills" => ROOT.join("docs/implementation-tips/changing-skills.md"),
  "changing-procedures" => ROOT.join("docs/implementation-tips/changing-procedures.md"),
  "changing-inspectors" => ROOT.join("docs/implementation-tips/changing-inspectors.md"),
  "testing-and-releasing" => ROOT.join("docs/implementation-tips/testing-and-releasing.md"),
  "release-v0.1.12-dossier" => ROOT.join("docs/todo/TODO-RELEASE-v0-1-12.md"),
  "dev-aquarium-dossier" => ROOT.join("docs/todo/TODO-DEV-AQUARIUM.md")
}
documentation_adr_paths = (1..6).map do |number|
  Dir[ROOT.join("docs/architecture-decision-records/%04d-*.md" % number)].map { |path| Pathname.new(path) }
end
assert(documentation_index_path.file?, "canonical documentation index is missing")
documentation_role_paths.each_value do |path|
  assert(path.file?, "canonical documentation role index is missing: #{path.relative_path_from(ROOT)}")
end
documentation_detail_paths.each_value do |path|
  assert(path.file?, "canonical documentation detail is missing: #{path.relative_path_from(ROOT)}")
end
assert(documentation_adr_paths.all? { |matches| matches.length == 1 },
       "canonical ADR sequence must contain exactly ADR-0001 through ADR-0006")
documentation_index = documentation_index_path.read
canonical_roadmap = documentation_role_paths.fetch("roadmap").read
todo_index = documentation_role_paths.fetch("todo").read
ops_index = documentation_role_paths.fetch("ops").read
documentation_details = documentation_detail_paths.transform_values(&:read)
documentation_adrs = documentation_adr_paths.flatten.to_h { |path| [path, path.read] }
design_qa = PLUGIN.join("skills/design-qa/SKILL.md").read
new_project = PLUGIN.join("skills/new-project/SKILL.md").read
new_feature = PLUGIN.join("skills/new-feature/SKILL.md").read
refactor = PLUGIN.join("skills/refactor/SKILL.md").read
war_room = PLUGIN.join("skills/war-room/SKILL.md").read
ouroboros_contract = PLUGIN.join("references/ouroboros-integration.md").read
design_gate_contract = PLUGIN.join("references/design-gates.md").read
documentation_contract = PLUGIN.join("references/documentation-governance.md").read
release_notes_contract = PLUGIN.join("references/release-notes.md").read
plan_handoff_path = PLUGIN.join("references/plan-handoff.md")
assert(plan_handoff_path.file?, "shared plan-handoff contract is missing")
plan_handoff_contract = plan_handoff_path.read
evidence_residency_path = PLUGIN.join("references/evidence-residency.md")
assert(evidence_residency_path.file?, "shared evidence-residency contract is missing")
evidence_residency = evidence_residency_path.read

assert(dev_setup.include?("request_user_input"), "dev-setup must prefer Codex ask/answer")
assert(dev_setup.include?("Podway"), "dev-setup description must trigger for Podway setup")
assert(dev_setup.include?("scripts/inspect_tools.py"), "dev-setup must use deterministic local inspection")
assert(dev_setup_script.file?, "dev-setup inspection script is missing")
assert(dev_setup_script_body.include?('"arguments_match": arguments_match') &&
       dev_setup_script_body.include?("skill_root_symlinked") &&
       dev_setup_script_body.include?('entry["symlinked"]') &&
       dev_setup_script_body.include?("safe_skill_file_state") &&
       dev_setup_script_body.include?("safe_managed_file_state") &&
       dev_setup_script_body.include?("mcp_registration_probe") &&
       dev_setup_script_body.include?('"preferred_scope": "global"') &&
       dev_setup_script_body.include?('"effective_scope"') &&
       dev_setup_script_body.include?('{"CODEX_HOME": str(repository / ".codex")}') &&
       dev_setup_script_body.include?("project_configuration_symlinked") &&
       dev_setup_script_body.include?("re.fullmatch") &&
       dev_setup_script_body.include?("No MCP server named") &&
       dev_setup_script_body.include?("ouroboros_direct_launcher_matches") &&
       dev_setup_script_body.include?('transport.get("args") == ["mcp", "serve"]') &&
       dev_setup_script_body.include?("ouroboros_isolated_launcher_matches") &&
       dev_setup_script_body.include?("isolated_launcher_configured") &&
       dev_setup_script_body.include?("registration_not_supported_launcher") &&
       dev_setup_script_body.include?('probe["reason"] = "registration_mismatch"'),
       "dev-setup inspector must preserve exact tool arguments, isolated launchers, and paired-skill paths")
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
       dev_setup_bundle_manifest.include?("retained v1 `project_mcp` field is an explicit local-scope override") &&
       dev_setup_bundle_manifest.include?("project_mcp: []") &&
       dev_setup_bundle_manifest.include?("same canonical Git root or shared Git common directory") &&
       dev_setup_bundle_manifest.include?("YAML merge key") &&
       dev_setup_bundle_manifest.include?("Do not put credentials"),
       "dev-setup-bundle manifest contract is incomplete")
assert(dev_setup_bundle.include?("complete AGENTS.md operating contract and CLAUDE.md delegation proposal") &&
       dev_setup_bundle.include?("missing commit-header convention") &&
       dev_setup_bundle_manifest.include?("mandatory project-specific commit-message rule") &&
       dev_setup_bundle_manifest.include?("Applying the complete displayed diff remains separately approved"),
       "bundle AGENTS guidance must select the full operating contract without widening apply authority")

assert(dev_setup.include?(">=0.51.1,<0.52.0") &&
       dev_setup.include?("uv tool install ouroboros-ai==<exact-version>") &&
       dev_setup.include?("ooo codex refresh") &&
       dev_setup.include?("ooo setup --runtime codex --non-interactive --mcp-mode auto") &&
       dev_setup.include?("do not run `ooo codex refresh` first") &&
       dev_setup.include?("refresh without full setup") &&
       dev_setup.include?("must not call an Ouroboros provider"),
       "dev-setup must separate pinned Ouroboros installation, mutually exclusive configuration paths, and provider authority")
assert(ouroboros_catalog &&
       ouroboros_catalog.include?("Do not run `ooo codex refresh` before full setup") &&
       ouroboros_catalog.include?("rules-and-skills repair alternative"),
       "Ouroboros catalog must avoid redundant refresh before full setup")
assert(ouroboros_catalog &&
       ouroboros_catalog.include?("ooo --version") &&
       ouroboros_catalog.include?("ooo codex doctor") &&
       ouroboros_catalog.include?("ooo mcp doctor --json") &&
       ouroboros_catalog.include?("codex mcp get ouroboros --json") &&
       ouroboros_catalog.include?("Registration is `configured` only") &&
       ouroboros_catalog.include?('args = ["mcp", "serve"]') &&
       ouroboros_catalog.include?("canonical isolated Codex launcher") &&
       ouroboros_catalog.include?("PATH-selected `uvx`") &&
       ouroboros_catalog.include?("optional supported exact release pin") &&
       ouroboros_catalog.include?("`OUROBOROS_AGENT_RUNTIME=codex`") &&
       ouroboros_catalog.include?("`OUROBOROS_LLM_BACKEND=codex`") &&
       ouroboros_catalog.include?("`--runtime codex --llm-backend codex`") &&
       ouroboros_catalog.include?("registration environment keys outside those three selectors") &&
       ouroboros_catalog.include?("live tool exposure remains separate host evidence") &&
       ouroboros_catalog.include?("`missing` only for Codex's definite named-server-not-found response") &&
       ouroboros_catalog.include?("never expose raw registration stderr") &&
       ouroboros_catalog.include?("local and read-only") &&
       ouroboros_catalog.include?("do not contact a provider, initiate authentication, make a network request, or start an MCP server"),
       "Ouroboros catalog must diagnose CLI, Codex integration, runtime, and registration independently")
assert(dev_setup.include?("Sanho, Mulgae, Gaori, and Podway selection choices") &&
       dev_setup.include?("Ouroboros CLI and version support, Codex rules and skills, MCP runtime"),
       "dev-setup must keep freshness authorization and Ouroboros reporting boundaries explicit")
assert(dev_setup.include?("Aquarium does not bundle Lora, Lore, or Deslop source") &&
       dev_setup.include?("temporary detached checkout") &&
       dev_setup.include?("one regular non-symlink installation") &&
       dev_setup.include?("exact repository, roadmap, and task prompt"),
       "dev-setup must install third-party skills from exact upstream sources")
proposal_index = dev_setup.index("Ask whether to prepare an evidence-based repository operating-guidance proposal")
diff_index = dev_setup.index("display the exact root AGENTS.md and CLAUDE.md paths")
apply_index = dev_setup.index("Apply exactly this diff")
assert(proposal_index && diff_index && apply_index && proposal_index < diff_index && diff_index < apply_index,
       "repository-guidance proposal and apply approvals are not ordered")
assert(dev_setup.include?("If either changed, discard the approval") &&
       dev_setup.include?("second approval covers only the exact displayed root AGENTS.md/CLAUDE.md diff"),
       "combined instruction-file stale approval guard is missing")
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
assert(dev_setup.include?("Never read credential values in this skill, even after setup approval") &&
       dev_setup.include?("Do not open `.env*`, authentication, key, token, secret, or credential files") &&
       dev_setup.include?("For either `Show proposal` or `Diagnose only`") &&
       dev_setup.include?("Diagnosis reports coverage and conflicts without drafting or mutation") &&
       agents_reference.include?("Diagnosis uses its structure and evidence rules without drafting"),
       "dev-setup must keep credential values unread and diagnose-only guidance non-drafting")
assert(dev_setup.include?("When another copy exists, report the duplicate risk") &&
       dev_setup.include?("never create a known duplicate"),
       "dev-setup must not install a canonical paired skill beside a known alternate-root copy")
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
assert(ROOT.join("README.md").read.include?("automatically query their official GitHub Releases metadata") &&
       ROOT.join("README.md").read.include?("four public skill files from `raw.githubusercontent.com` into ephemeral storage") &&
       ROOT.join("README.md").read.include?("Unselected tools and other network operations are not covered") &&
       ROOT.join("README.ko.md").read.include?("official GitHub Releases metadata를 자동으로 조회") &&
       ROOT.join("README.ko.md").read.include?("`raw.githubusercontent.com`에서 공개 skill 파일 4개를 임시 저장소로 내려받습니다") &&
       ROOT.join("PRIVACY.md").read.include?("Bounded read-only network operations may be authorized") &&
       ROOT.join("PRIVACY.md").read.include?("sends no repository or local skill content") &&
       ROOT.join("PRIVACY.md").read.scan("selected-skill freshness comparison contacts GitHub automatically").length == 4,
       "public documentation must disclose automatic selected-skill comparison and its privacy boundary")
assert(ROOT.join("README.md").read.include?("Invoking `release-handler` authorizes read-only release discovery") &&
       ROOT.join("README.md").read.include?("existing ambient authentication for private repositories") &&
       ROOT.join("PRIVACY.md").read.include?("Explicitly invoking `release-qa` automatically queries") &&
       ROOT.join("PRIVACY.md").read.include?("Explicitly invoking `release-handler` performs the same bounded read-only release discovery") &&
       ROOT.join("PRIVACY.md").read.include?("material release-delta source and documentation surfaces") &&
       ROOT.join("PRIVACY.md").read.include?("creates no tracked or temporary resume manifest") &&
       ROOT.join("PRIVACY.md").read.include?("unavailable access leaves the QA result incomplete"),
       "public documentation must disclose release-handler and release-qa network boundaries")
assert(test_setup_script.file?, "test-setup structural inspector is missing")
assert(test_setup_script_body.include?("aquarium-test-setup-inspection.v1") &&
       test_setup_script_body.include?('"semantic_scope": "not_evaluated"') &&
       test_setup_script_body.include?("framework_waiver_required") &&
       test_setup_script_body.include?("testing_profile_mismatch") &&
       test_setup_script_body.include?("bun_legacy_lock_waiver_required") &&
       test_setup_script_body.include?("typescript_package_manager_waiver_required") &&
       test_setup_script_body.include?("source_contains") &&
       test_setup_script_body.include?("only_recursive_calls") &&
       test_setup_script_body.include?("section_content") &&
       test_setup_script_body.include?("runs_cargo_test") &&
       test_setup_script_body.include?("command_preserves_failure") &&
       test_setup_script_body.include?("command_executes_tests") &&
       test_setup_script_body.include?("global_shell_semantics") &&
       test_setup_script_body.include?("GNUMAKEFLAGS") &&
       test_setup_script_body.include?("runner_variable_is") &&
       test_setup_script_body.include?("runs_dart_test") &&
       test_setup_script_body.include?("sensitive_relative_path") &&
       test_setup_script_body.include?("safe_repository_file") &&
       test_setup_script_body.include?("make_variable_values") &&
       test_setup_script_body.include?("pytest_control_only_configuration") &&
       test_setup_script_body.include?("MAKE_ALIAS_PATTERN") &&
       test_setup_script_body.include?("repository_symlinked") &&
       test_setup_script_body.include?("lexical_path_symlinked") &&
       test_setup_script_body.include?("normalize_shell_token_joins") &&
       test_setup_script_body.include?("tomllib.loads") &&
       test_setup_script_body.include?("unsafe_root_authorities") &&
       test_setup_script_body.include?("OPAQUE_PARAMETER_DEFAULT") &&
       test_setup_script_body.include?("authority_includes_unresolved") &&
       test_setup_script_body.include?("repository / \"go.sum\"") &&
       test_setup_script_body.include?("pending-dart-test") &&
       test_setup_script_body.include?("pending-patrol") &&
       !test_setup_script_body.include?("import subprocess"),
       "test-setup inspector must remain local, structural, and non-executing")
assert(test_setup.include?("scripts/inspect_testing.py") &&
       test_setup.include?("conservative structural evidence only") &&
       test_setup.include?("Apply exactly this diff") &&
       test_setup.include?("configured but unverified"),
       "test-setup must separate structural audit, exact-diff approval, and runtime proof")
assert(test_setup.include?("Never open `.env*`, authentication, key, token, secret, credential stores, or credential-named paths") &&
       test_setup.include?("Do not emit raw authority contents or inline credential values") &&
       test_setup.include?("templates proven to contain placeholders") &&
       test_setup.include?("report a gap when values would be required"),
       "test-setup must preserve credential-path exclusion and non-emission during repository inspection")
assert(test_setup.include?("does not authorize a test that creates containers") &&
       test_setup.include?("proven non-production") &&
       test_setup.include?("never convert them into a successful skip") &&
       ROOT.join("PRIVACY.md").read.include?("Explicitly invoking `test-setup`") &&
       ROOT.join("PRIVACY.md").read.include?("obtains separate approval before execution"),
       "test-setup and public privacy guidance must preserve effectful E2E approval and production safety")
assert(docs_setup_script.file?, "docs-setup structural inspector is missing")
assert(docs_setup_script_body.include?("aquarium-docs-inspection/v2") &&
       docs_setup_script_body.include?("--literal-pathspecs") &&
       docs_setup_script_body.include?("sensitive_path") &&
       docs_setup_script_body.include?("GIT_OPTIONAL_LOCKS") &&
       docs_setup_script_body.include?("core.fsmonitor=false"),
       "docs-setup inspector must expose its v2 contract and preserve bounded Git inspection")
assert(docs_setup.include?("scripts/inspect_docs.py") &&
       docs_setup.include?("Apply exactly this diff") &&
       docs_setup.include?("never stages, commits, pushes, publishes") &&
       docs_setup.include?("does not become repository-native CI"),
       "docs-setup must separate audit, exact-diff approval, and repository-native proof")
assert(docs_setup.include?("Never open `.env*`, authentication, credential, key, secret, or token paths") &&
       docs_setup.include?("Do not read ignored runtime evidence") &&
       ROOT.join("PRIVACY.md").read.include?("Explicitly invoking `docs-setup`") &&
       ROOT.join("PRIVACY.md").read.include?("without executing project code or contacting a network"),
       "docs-setup and public privacy guidance must preserve local inspection boundaries")
assert(documentation_contract.include?("## Semantic Roles") &&
       documentation_contract.include?("## Profiles") &&
       documentation_contract.include?("## TODO Dossier Lifecycle") &&
       documentation_contract.include?("## New Roadmap Identity") &&
       documentation_contract.include?("EPIC-[0-9]{3,}") &&
       documentation_contract.include?("TASK-[0-9]{3,}") &&
       documentation_contract.include?("The canonical roadmap path is the namespace") &&
       documentation_contract.include?("scope:ID") &&
       documentation_contract.include?("for that ID kind") &&
       documentation_contract.include?("roadmap identity contract") &&
       documentation_contract.include?("Do not create `.aquarium`") &&
       docs_setup_profiles.include?("single-scope") &&
       docs_setup_profiles.include?("multi-scope") &&
       docs_setup_profiles.include?("legacy-adopt") &&
       docs_setup_operations.include?("## Runbook Contract") &&
       docs_setup_operations.include?("## Empty Operations Surface"),
       "documentation governance must define audiences, eight roles, dossier lifecycle, profiles, and roadmap IDs")
assert(docs_setup_migration.include?("status is exactly `Planned`") &&
       docs_setup_migration.include?("every child task is exactly `Planned`") &&
       docs_setup_migration.include?("id-migrations/YYYY-MM-DD.md") &&
       docs_setup_migration.include?("**Canonical roadmap:**") &&
       docs_setup_migration.include?("every new ID is a current same-kind definition") &&
       docs_setup_migration.include?("Preserved Historical Paths") &&
       docs_setup_migration.include?("## Path and Profile Migration") &&
       docs_setup_migration.include?("Never move a task across epic boundaries") &&
       docs_setup_migration.include?("Do not update only the roadmap"),
       "documentation migration must preserve history and rewrite the complete tracked reference set")
documentation_roles = documentation_role_paths.keys
assert(documentation_index.include?("`single-scope`") &&
       documentation_index.include?("`Aquarium`") &&
       documentation_roles.all? { |role| documentation_index.include?("`docs/#{role}/README.md`") } &&
       documentation_index.include?("`docs/roadmap/README.md` is the namespace") &&
       documentation_index.include?("EPIC-[0-9]{3,}") &&
       documentation_index.include?("TASK-[0-9]{3,}") &&
       documentation_index.include?("English is canonical") &&
       documentation_index.include?("Aquarium maintainers and workflow authors") &&
       documentation_index.include?("current stable package as `v0.1.11`") &&
       documentation_index.include?("open `v0.1.12` release candidate") &&
       documentation_index.include?("TODO and work dossiers") &&
       documentation_index.include?("ruby tests/validate.rb"),
       "Aquarium documentation index must define its profile, roles, roadmap identity, language, and checks")
assert(ops_index.start_with?("# Aquarium Operations\n") &&
       ops_index.include?("## Current Operational Surface") &&
       ops_index.include?("## Runbook Requirements"),
       "Aquarium operations index must expose its operational surface and runbook sections")

capability_catalog = documentation_details.fetch("capabilities")
assert(capability_catalog.include?("Aquarium exposes 24 skills") &&
       expected_skill_names.all? { |name| capability_catalog.include?("`$aquarium:#{name}`") } &&
       capability_catalog.include?("open v0.1.12 candidate") &&
       capability_catalog.include?("not shipped as v0.1.11 behavior"),
       "capability catalog must inventory all Aquarium skills and separate stable from candidate behavior")

workflow_contracts_doc = documentation_details.fetch("workflow-contracts")
tool_integrations_doc = documentation_details.fetch("tool-integrations")
supported_tool_versions = [
  "Stable `v0.2.7` through `v0.2.x`",
  "Stable `v0.1.18` through `v0.1.x`",
  "Stable `v0.1.14` through `v0.1.x`",
  "Stable `v0.2.6` through `v0.2.x`",
  "`>=0.51.1,<0.52.0`"
]
assert(supported_tool_versions.all? { |version| tool_integrations_doc.include?(version) } &&
       tool_integrations_doc.include?("Go `1.26.6+` only for installation") &&
       tool_integrations_doc.include?("No Aquarium release floor declared") &&
       tool_integrations_doc.include?("No release line; disclosed full current upstream SHA"),
       "tool integration documentation must preserve supported versions and upstream boundaries")

local_interfaces_doc = documentation_details.fetch("local-interfaces")
procedure_declarations = {
  "aquarium-task-v2" => "3",
  "aquarium-goal-v2" => "4",
  "aquarium-validation-v2" => "5",
  "aquarium-design-v2" => "1",
  "aquarium-war-room-v2" => "1"
}
assert(procedure_declarations.all? do |procedure_id, version|
         local_interfaces_doc.include?("| `#{procedure_id}` | `#{version}` |")
       end,
       "local interface documentation must preserve every managed Procedure ID and version")
documented_schema_ids = %w[
  aquarium-dev-setup-inspection.v8
  aquarium-docs-inspection/v2
  aquarium-test-setup-inspection.v1
  aquarium.dev-setup-bundle/v1
  aquarium-dev-setup-bundle-plan.v1
  aquarium-independent-review-target/v1
  aquarium-orca-provider-terminal-request/v1
  aquarium-orca-provider-terminal-result/v1
  aquarium-release-notes-inspection/v1
  aquarium-release-publication-observation/v3
  aquarium-release-publication-state/v3
  aquarium-podway-compatibility.v1
]
assert(documented_schema_ids.all? { |schema_id| local_interfaces_doc.include?("`#{schema_id}`") },
       "local interface documentation must preserve the major JSON schema identifiers")

adr_index = documentation_role_paths.fetch("architecture-decision-records").read
required_adr_sections = %w[Context Decision Consequences Rejected\ Alternatives References]
documentation_adrs.each do |path, body|
  number = path.basename.to_s[/\A(\d{4})-/, 1]
  assert(body.start_with?("# ADR-#{number}: ") &&
         body.include?("**Status:** `Accepted`") &&
         body.include?("**Recorded:** `2026-08-25`") &&
         body.include?("retrospective record of current repository authority") &&
         required_adr_sections.all? { |section| body.include?("## #{section.tr('\\', ' ')}") } &&
         adr_index.include?(path.basename.to_s),
         "ADR-#{number} must be accepted, complete, retrospective, and indexed")
end

canonical_documentation_paths = [documentation_index_path] +
                                documentation_role_paths.values +
                                documentation_detail_paths.values +
                                documentation_adrs.keys
canonical_documentation = canonical_documentation_paths.map(&:read).join("\n")
assert(!canonical_documentation.include?("/Users/") &&
       !canonical_documentation.include?("file://") &&
       !canonical_documentation.match?(/(?:api[_-]?key|access[_-]?token|client[_-]?secret)\s*[:=]\s*\S+/i),
       "canonical documentation must not contain absolute workspace paths or apparent credential values")

release_012_dossier = documentation_details.fetch("release-v0.1.12-dossier")
dev_aquarium_dossier = documentation_details.fetch("dev-aquarium-dossier")
roadmap_task_ids = canonical_roadmap.scan(/^\| TASK-[0-9]{3,} \|/).map { |row| row[/TASK-[0-9]{3,}/] }
assert(canonical_roadmap.scan(/^## EPIC-[0-9]{3,}: /).length == 3 &&
       canonical_roadmap.include?("## EPIC-001: Release Aquarium v0.1.12") &&
       canonical_roadmap.include?("## EPIC-002: Build the Aquarium Development Environment") &&
       canonical_roadmap.include?("## EPIC-003: Introduce Dolgorae") &&
       canonical_roadmap.include?("**Status:** `Planned`") &&
       roadmap_task_ids.length == 18 &&
       roadmap_task_ids.uniq.sort == (1..18).map { |number| "TASK-%03d" % number }.sort &&
       canonical_roadmap.scan(/^\| TASK-[0-9]{3,} \|.*\| Planned \|/).length == 18 &&
       canonical_roadmap.include?("TODO-RELEASE-v0-1-12.md") &&
       canonical_roadmap.include?("TODO-DEV-AQUARIUM.md") &&
       canonical_roadmap.include?("No child task identity or implementation authority is allocated") &&
       !canonical_roadmap.include?("### TASK-") &&
       !canonical_roadmap.include?("/Users/"),
       "Aquarium roadmap must remain a concise lifecycle index for EPIC-001 through EPIC-003 and unique TASK-001 through TASK-018")
assert(todo_index.include?("TODO-RELEASE-v0-1-12.md") &&
       todo_index.include?("TODO-DEV-AQUARIUM.md") &&
       todo_index.include?("Checklist state is review evidence, not roadmap lifecycle state") &&
       todo_index.include?("`TASK-016` through `TASK-018`") &&
       release_012_dossier.include?("detailed scope and acceptance source of truth for `EPIC-001`") &&
       release_012_dossier.include?("## TASK-016: Align the Podway v0.2.6 Runtime Contract") &&
       release_012_dossier.include?("## TASK-017: Reauthor the Delivery Procedures") &&
       release_012_dossier.include?("## TASK-018: Reauthor the Analysis Procedures") &&
       release_012_dossier.include?("## TASK-001: Preserve Local Procedure Customization") &&
       release_012_dossier.include?("## TASK-004: Release Aquarium v0.1.12") &&
       release_012_dossier.include?("make test-podway-compat") &&
       release_012_dossier.include?("$aquarium:release-handler") &&
       dev_aquarium_dossier.include?("detailed scope and acceptance source of truth for `EPIC-002`") &&
       dev_aquarium_dossier.scan(/^## TASK-[0-9]{3,}: /).length == 11 &&
       (5..15).all? { |number| dev_aquarium_dossier.include?("## TASK-%03d:" % number) } &&
       dev_aquarium_dossier.include?("$aquarium:dev-aquarium") &&
       dev_aquarium_dossier.include?("make aquarium-dev-describe") &&
       dev_aquarium_dossier.include?("make aquarium-dev-build") &&
       dev_aquarium_dossier.include?("There is no top-level `~/.aquarium/bin/`") &&
       dev_aquarium_dossier.include?("fails closed instead of silently falling back") &&
       dev_aquarium_dossier.include?("This epic does not introduce Dolgorae"),
       "roadmap work dossiers must own the detailed release and development-environment acceptance contracts")
assert(test_setup_contract.include?("aquarium-test-contract/v1") &&
       test_setup_contract.include?("AQTEST-001") &&
       test_setup_contract.include?("AQTEST-009") &&
       test_setup_contract.include?("Test Frameworks") &&
       test_setup_contract.include?("Gaori Mapping") &&
       test_setup_contract.include?("Approved by Master") &&
       test_setup_contract.include?("Static pytest `addopts` and `PYTEST_ADDOPTS`") &&
       test_setup_contract.include?("Make-valued shell aliases") &&
       test_setup_contract.include?("Approval timing and execution evidence belong in Git history or the owning workflow report") &&
       test_setup_contract.include?("A waiver becomes stale only when a change affects a fact supporting that waiver") &&
       test_setup_contract.include?("Adding or changing test cases inside the same waived layer does not by itself stale the waiver") &&
       test_setup_contract.include?("Stale waivers do not authorize a skip"),
       "test contract must define stable rules and bounded legacy waivers")
assert(test_setup_profiles.include?("$(MAKE) test-prepare") &&
       test_setup_profiles.include?("Do not express the four stages as prerequisites") &&
       test_setup_profiles.include?("bun run test:prepare && bun run test:unit && bun run test:int && bun run test:e2e") &&
       test_setup_profiles.include?("Ginkgo v2 with Gomega") &&
       test_setup_profiles.include?("project-pinned Vitest dependency") &&
       test_setup_profiles.include?("Bun remains the package manager and script orchestrator") &&
       test_setup_profiles.include?("`MAKEFLAGS`, `MFLAGS`, or `GNUMAKEFLAGS`") &&
       test_setup_profiles.include?("New unit, integration, and Python E2E layers use pytest") &&
       test_setup_profiles.include?("New Dart unit and integration layers use `package:test`") &&
       test_setup_profiles.include?("Gaori is an optional evidence-compression adapter") &&
       test_setup_profiles.include?("specialized miss does not fall back to `generic`") &&
       test_setup_profiles.include?("Playwright in TypeScript is the preferred E2E implementation") &&
       test_setup_profiles.include?("root Makefile remains the aggregate authority"),
       "test profiles must preserve framework, parser, orchestration, and polyglot contracts")
assert(test_setup.include?("Gaori remains optional") &&
       test_setup.include?("gaori parsers list") &&
       test_setup.include?("does not prove support maturity") &&
       ROOT.join("README.md").read.include?("Gaori integration is optional"),
       "test setup must keep canonical frameworks aligned with optional Gaori evidence")
assert(ROOT.join("PRIVACY.md").read.include?("The selected `ooo --version`") &&
       ROOT.join("PRIVACY.md").read.include?("do not contact a provider, initiate authentication, or make a network request") &&
       ROOT.join("PRIVACY.md").read.include?("without exposing credential material"),
       "privacy policy must disclose the local Ouroboros diagnosis boundary")
assert(ROOT.join("PRIVACY.md").read.include?("Cursor Team Kit Deslop installation contacts GitHub and npm") &&
       ROOT.join("PRIVACY.md").read.include?("writes the upstream `SKILL.md` and MIT LICENSE") &&
       ROOT.join("PRIVACY.md").read.include?("does not bundle Lora, Ouroboros, or Cursor Team Kit skill or documentation sources"),
       "privacy policy must disclose third-party skill installation and no-vendoring boundaries")
assert(ROOT.join("TERMS.md").read.include?("does not bundle the Lora, Ouroboros, or Cursor Team Kit skill and documentation sources") &&
       ROOT.join("TERMS.md").read.include?("users install approved upstream copies under their original license terms") &&
       !ROOT.join("TERMS.md").read.include?("bundled `deslop`"),
       "terms must preserve upstream ownership without claiming a bundled Deslop copy")
assert(ROOT.join("PRIVACY.md").read.include?("may start the installed local Orca runtime") &&
       ROOT.join("PRIVACY.md").read.include?("Dirty working-tree content is never a review target") &&
       ROOT.join("PRIVACY.md").read.include?("may stage only exact paths the user approves") &&
       ROOT.join("PRIVACY.md").read.include?("current checkout as same-user processes") &&
       ROOT.join("PRIVACY.md").read.include?("rather than an operating-system read sandbox") &&
       ROOT.join("PRIVACY.md").read.include?("without a second preparation approval") &&
       ROOT.join("PRIVACY.md").read.include?("Reviews remain static") &&
       ROOT.join("PRIVACY.md").read.include?("local Run, Task, Dispatch, terminal, lifecycle, and transcript state") &&
       !ROOT.join("PRIVACY.md").read.include?("Two bounded read-only network operations") &&
       ROOT.join("TERMS.md").read.include?("exact Git target and reviewer authorizes only the bounded static review transmission") &&
       ROOT.join("TERMS.md").read.include?("Orca, Anthropic Claude Code, OpenAI Codex, Cursor, Kimi Code, Agy"),
       "privacy policy and terms must disclose Orca review consent, source transmission, local state, and external ownership")
required_guidance_sections = [
  "## Core Behavior",
  "## Master Preferences",
  "## Aquarium Development Guide",
  "## Project Configuration",
  "### Repository Index and Authorities",
  "### Commit Messages",
  "### Project-Specific Operating Rules"
]
guidance_indexes = required_guidance_sections.map { |heading| agents_reference.index(heading) }
assert(guidance_indexes.all? && guidance_indexes == guidance_indexes.sort,
       "AGENTS operating-contract sections are missing or out of order")
assert(agents_reference.include?("Every applied AGENTS.md must contain all four top-level sections") &&
       agents_reference.include?("Keep `Commit Messages` inside `Project Configuration`") &&
       agents_reference.include?("ask the user to choose one and do not finalize or apply") &&
       agents_reference.include?("recent commit subjects only as evidence"),
       "AGENTS guidance must keep project commit-message configuration mandatory and explicit")
assert(agents_reference.include?("Repository-specific rules in `Project Configuration` override") &&
       agents_reference.include?("A CLI alone does not justify a paired-skill reference"),
       "override and conditional paired-skill precedence is missing")
assert(agents_reference.include?("$aquarium:epic-handler") &&
       agents_reference.include?("$aquarium:epic-validator"),
       "AGENTS reference guidance must distinguish epic delivery and validation")
assert(agents_reference.include?("$aquarium:test-setup") &&
       agents_reference.include?("common Make or Bun testing contract"),
       "AGENTS reference guidance must route common test setup")
assert(agents_reference.include?("substantive CLAUDE.md") &&
       agents_reference.include?("merge every non-duplicate or stricter rule into AGENTS.md") &&
       agents_reference.include?("one complete combined diff for both files") &&
       agents_reference.include?("A change to either target invalidates approval") &&
       agents_reference.include?("Do not edit nested AGENTS.md, nested CLAUDE.md"),
       "AGENTS guidance must reconcile root Claude guidance without widening file scope")
assert(agents_reference.include?("2c606141936f1eeef17fa3043a72095b4765b9c2") &&
       agents_reference.include?("Do not contact that repository or fetch its text while preparing a proposal"),
       "the core behavior attribution must be pinned and runtime-offline")
durable_solution_contract = [
  "### 3. Prefer Durable Root-Cause Solutions",
  "addresses the verified root cause",
  "correctness, performance, maintainability, and structural fit",
  "canonical `deferred-feedback` owner",
  "TODO candidate or roadmap work unit",
  "Do not defer work required for current correctness or acceptance."
]
assert(durable_solution_contract.all? { |phrase| agents_reference.include?(phrase) } &&
       durable_solution_contract.all? { |phrase| root_agents.include?(phrase) },
       "root and reusable AGENTS guidance must prefer bounded durable root-cause solutions")

root_guidance_sections = [
  "## Core Behavior",
  "## Master Preferences",
  "## Aquarium Development Guide",
  "## Project Configuration",
  "### Repository Index and Authorities",
  "### Commit Messages",
  "### Project-Specific Operating Rules",
  "### Release Policy"
]
root_guidance_indexes = root_guidance_sections.map { |heading| root_agents.index(heading) }
assert(root_guidance_indexes.all? && root_guidance_indexes == root_guidance_indexes.sort,
       "Aquarium AGENTS.md must use the reusable repository operating-contract order")
assert(!root_agents.match?(/^## Commit Messages$/) &&
       root_agents.include?("Every commit title must start with exactly one approved uppercase header") &&
       root_agents.include?("[FEAT]") && root_agents.include?("[FIX]") &&
       root_agents.include?("[DEV]") && root_agents.include?("[TEST]") &&
       root_agents.include?("[DOC]") && root_agents.include?("[CI]") &&
       root_agents.include?("[REL]") && root_agents.include?("[INT]"),
       "Aquarium commit headers must be a mandatory Project Configuration subsection")
assert(root_agents.include?("use exactly `Master`") &&
       root_agents.include?("$aquarium:dev-setup-bundle") &&
       root_agents.include?(".podway/procedures/aquarium-*-v2.yaml") &&
       root_agents.include?("`docs/README.md` owns the single-scope documentation profile") &&
       root_agents.include?("`docs/roadmap/README.md` alone owns Aquarium epic and task identity") &&
       root_agents.include?("RELEASE_TAG=v<version> ruby tests/validate.rb"),
       "Aquarium's applied guidance must preserve preferences, workflow references, and release policy")
expected_claude_delegation = <<~MARKDOWN
  # CLAUDE.md

  This repository uses `AGENTS.md` as the canonical agent instruction file.

  Claude Code agents must read and follow `AGENTS.md` first. If any guidance here conflicts with `AGENTS.md`, `AGENTS.md` wins.
MARKDOWN
assert(root_claude == expected_claude_delegation,
       "root CLAUDE.md must be the canonical AGENTS.md delegation file")

assert(tool_catalog.include?("--skill lore-commits"), "Lora commit skill is missing")
assert(tool_catalog.include?("--skill lore-query"), "Lora query skill is missing")
assert(!tool_catalog.include?("--skill lore-setup"), "Lora setup skill must not be installed")
assert(tool_catalog.include?("--global") && tool_catalog.include?("--agent codex"), "Lora scope must be global Codex")
assert(tool_catalog.include?("git -C <temporary-source-root>/lora checkout --detach FETCH_HEAD") &&
       tool_catalog.include?("npx skills add <temporary-source-root>/lora") &&
       !tool_catalog.include?("tmdgusya/lora#<tag-or-full-sha>"),
       "Lora must install from an exact detached upstream checkout")
assert(tool_catalog.include?("Before updating an existing `lore-commits` or `lore-query`") &&
       tool_catalog.include?("apply the shared backup policy before the approved `npx skills add` action") &&
       tool_catalog.include?("reject missing and extra paths") &&
       tool_catalog.include?("structural presence and frontmatter as `unverifiable`"),
       "Lora skill updates must follow the request-scoped backup policy")
assert(deslop_catalog &&
       deslop_catalog.include?("https://github.com/cursor/plugins") &&
       deslop_catalog.include?("--skill deslop") &&
       deslop_catalog.include?("<approved-full-sha>") &&
       deslop_catalog.include?("cursor-team-kit/LICENSE ~/.agents/skills/deslop/LICENSE") &&
       deslop_catalog.include?("byte-identical") &&
       deslop_catalog.include?("no duplicate or symlink installation"),
       "Deslop must install with its license from one exact Cursor upstream commit")
assert(tool_catalog.include?("stable `v0.2.6` through `v0.2.x`") &&
       tool_catalog.include?("same exact tag") &&
       tool_catalog.include?("raw.githubusercontent.com/irootkernel/podway/<tag>/skills/use-podway/"),
       "Podway CLI, daemon, and use-podway must share the supported approved release")
assert(tool_catalog.include?("shasum -a 256 -c"), "Podway checksum verification is missing")
assert(tool_catalog.include?("podway.output/v3") &&
       tool_catalog.include?("podway.daemon-status-result/v2") &&
       tool_catalog.include?("readiness_state=ready") &&
       tool_catalog.include?("readiness_stage=ready") &&
       tool_catalog.include?("none failed") &&
       tool_catalog.include?("podway.status-result/v3") &&
       tool_catalog.include?("podway.compact-status-result/v3") &&
       tool_catalog.include?("podway.observation-result/v2") &&
       tool_catalog.include?("podway.session-start-result/v3") &&
       tool_catalog.include?("podway.session-begin-result/v1") &&
       tool_catalog.include?("podway.terminal-disposition-result/v1") &&
       tool_catalog.include?("podway.session-reset-result/v1") &&
       tool_catalog.include?("podway.job-result/v4") &&
       tool_catalog.include?("podway.job-lookup-result/v4"),
       "Podway v0.2.6 JSON contracts are missing")
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
       tool_catalog.include?("migration_kinds.product_rename") &&
       tool_catalog.include?("migration_kinds.podway_v0.2.5_workaround") &&
       tool_catalog.include?("classifies every other mismatch as `diverged`") &&
       tool_catalog.include?("root-kernel-task-v2.yaml") &&
       tool_catalog.include?("root-kernel-goal-v2.yaml") &&
       tool_catalog.include?("root-kernel-validation-v2.yaml"),
       "Podway migration classification contract is missing")
assert(tool_catalog.include?("readiness_status=not_configured") &&
       tool_catalog.include?("readiness_status=ready") &&
       tool_catalog.include?("v8 inspection") &&
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
assert(ROOT.join("README.md").read.include?("provides local execution memory") &&
       !ROOT.join("README.md").read.include?("durable local execution memory") &&
       !ROOT.join("README.ko.md").read.include?("영속적인 local execution memory") &&
       ROOT.join("README.md").read.include?("selected by default for `task-handler`, `epic-handler`, `epic-validator`, `new-project`, `new-feature`, `refactor`, `war-room`, and `design-qa`") &&
       ROOT.join("README.ko.md").read.include?("`task-handler`, `epic-handler`, `epic-validator`, `new-project`, `new-feature`, `refactor`, `war-room`, `design-qa`는 기본적으로 Podway를 사용") &&
       ROOT.join("README.md").read.include?("opted out before the first managed-session mutation") &&
       ROOT.join("README.md").read.include?("standalone `use-podway` skill"),
       "public Podway guidance must explain its role and workflow boundary concisely")
assert(ROOT.join("PRIVACY.md").read.include?("use-podway") &&
       ROOT.join("PRIVACY.md").read.include?("~/.agents/skills/use-podway"),
       "privacy policy must disclose Podway skill installation")
assert(ROOT.join("README.md").read.include?("Evidence has a residence") &&
       ROOT.join("README.md").read.include?("aquarium.promoted-evidence/v1") &&
       ROOT.join("README.md").read.include?("tracked roadmaps, repository handoffs, or commit messages") &&
       ROOT.join("README.ko.md").read.include?("증거에는 보존 위치가 있습니다") &&
       ROOT.join("README.ko.md").read.include?("aquarium.promoted-evidence/v1") &&
       ROOT.join("README.ko.md").read.include?("tracked roadmap, repository handoff, commit message") &&
       ROOT.join("PRIVACY.md").read.include?("must not be copied into tracked documentation as execution logs") &&
       ROOT.join("PRIVACY.md").read.include?("Standard promotion excludes raw logs") &&
       ROOT.join("PRIVACY.md").read.include?("accepted reports") &&
       ROOT.join("PRIVACY.md").read.include?("applicable repository `AGENTS.md` Project Configuration") &&
       agents_reference.include?("Do not cite their paths or identities as durable evidence") &&
       agents_reference.include?("Aquarium evidence root: <repository-relative-path>") &&
       root_agents.include?("never tracked documentation authority") &&
       root_agents.include?("Aquarium evidence root: <repository-relative-path>"),
       "public privacy and agent guidance must preserve evidence residency and promotion boundaries")
assert(gaori_catalog, "Gaori tool catalog section is missing")
assert(gaori_catalog.include?("gaori version --json"), "Gaori JSON version probe is missing")
assert(gaori_catalog.include?("stable `v0.1.14` through `v0.1.x`") &&
       gaori_catalog.include?("same exact tag") &&
       gaori_catalog.include?("raw.githubusercontent.com/irootkernel/gaori/<tag>/skills/use-gaori/") &&
       dev_setup.include?("stable `v0.1.14` through `v0.1.x`"),
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
       gaori_catalog.include?('args = ["mcp"]') &&
       gaori_catalog.include?("tool_timeout_sec = 3601") &&
       gaori_catalog.include?("prefer one user-global registration") &&
       gaori_catalog.include?("CODEX_HOME=<absolute-git-root>/.codex codex mcp remove gaori") &&
       gaori_catalog.include?("semantic-empty-file") &&
       gaori_catalog.include?("terminal-only `await_run`") &&
       gaori_catalog.include?("at least 3601 seconds") &&
       gaori_catalog.include?("read-only `list_runs`") &&
       gaori_catalog.include?("cannot recover an invocation ID or reattach"),
       "Gaori global-first MCP setup and local cleanup guidance is incomplete")
assert(sanho_catalog, "Sanho tool catalog section is missing")
assert(sanho_catalog.include?("stable `v0.2.7` through `v0.2.x`") &&
       sanho_catalog.include?("same exact tag") &&
       sanho_catalog.include?("raw.githubusercontent.com/irootkernel/sanho/<tag>/skills/use-sanho/") &&
       dev_setup.include?("stable `v0.2.7` through `v0.2.x`"),
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
       agents_reference.include?("A CLI alone does not justify a paired-skill reference"),
       "AGENTS guidance must conditionally reference use-sanho")
assert(dev_setup.include?("CLI installation or upgrade") &&
       dev_setup.include?("user-scoped skill installation or replacement") &&
       dev_setup.include?("separate approval boundaries"),
       "dev-setup must separate Sanho CLI, skill, workspace, and repair approvals")
assert(dev_setup.include?("use-gaori") &&
       dev_setup.include?("global or project-local MCP configuration") &&
       dev_setup.include?("Never start a Gaori run or MCP test command during setup"),
       "dev-setup must separate Gaori CLI, skill, config, and MCP boundaries")
assert(agents_reference.include?("$use-gaori") &&
       agents_reference.include?("A CLI alone does not justify a paired-skill reference"),
       "AGENTS guidance must conditionally reference use-gaori")

assert(mulgae_catalog, "Mulgae tool catalog section is missing")
assert(mulgae_catalog.include?("stable `v0.1.18` through `v0.1.x`") &&
       mulgae_catalog.include?("Go `1.26.6` or newer") &&
       mulgae_catalog.include?("same exact tag") &&
       mulgae_catalog.include?("raw.githubusercontent.com/irootkernel/mulgae/<tag>/skills/use-mulgae/") &&
       mulgae_catalog.include?("~/.agents/skills/use-mulgae") &&
       dev_setup.include?("stable `v0.1.18` through `v0.1.x`"),
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
       "Mulgae v0.1.18 contracts and legacy-config guidance are incomplete")
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
assert(mulgae_catalog.include?("Codex CLI `0.149.0` or newer") &&
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
       mulgae_catalog.include?('args = ["mcp"]') &&
       mulgae_catalog.include?("required = true") &&
       mulgae_catalog.include?("startup_timeout_sec = 30") &&
       mulgae_catalog.include?("tool_timeout_sec = 7501") &&
       mulgae_catalog.include?("prefer one user-global registration") &&
       mulgae_catalog.include?("CODEX_HOME=<absolute-git-root>/.codex codex mcp remove mulgae") &&
       mulgae_catalog.include?("Delete `.codex/config.toml` only when parsed TOML has no remaining semantic content") &&
       mulgae_catalog.include?("`start_review`, `await_review`, `cancel_review`") &&
       mulgae_catalog.include?("preserve any larger existing value"),
       "Mulgae global-first MCP setup and local cleanup guidance is incomplete")
assert(dev_setup.include?("use-mulgae") &&
       dev_setup.include?("project Config v3 and ignore changes") &&
       dev_setup.include?("Codex credential-profile mapping") &&
       dev_setup.include?("start a Mulgae heartbeat, review, qualification, preflight capture, live provider request") &&
       dev_setup.include?("source transmission, or MCP server during setup"),
       "dev-setup must separate Mulgae CLI, skill, Config v3, Codex profile, and MCP boundaries")
assert(agents_reference.include?("$use-mulgae") &&
       agents_reference.include?("A CLI alone does not justify a paired-skill reference"),
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
       epic_handler.include?("change after verification or review makes affected evidence stale") &&
       epic_handler.include?("approved post-review promoted-evidence projection are the sole exceptions") &&
       epic_handler.include?("projection remains outside the review target"),
       "epic-handler must separate lifecycle evidence and invalidate stale review")
assert(epic_handler.lines.length < 120, "epic-handler must remain orchestration-focused")

assert(epic_validator.include?("one canonical roadmap path inside it") &&
       epic_validator.include?("exactly one epic ID"),
       "epic-validator must require one repository roadmap and epic")
validator_approval_index = epic_validator.index("Ask once for explicit approval")
validator_audit_index = epic_validator.index("## Audit the Epic Directly")
validator_goal_index = epic_validator.index("## Group and Complete Remediation Goals")
validator_reaudit_index = epic_validator.index("## Confirm Once and Stop on New Findings")
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
       epic_validator.include?("without adding remediation history to the roadmap") &&
       epic_validator.include?("Record resulting remediation commit IDs in Podway and the orchestration report"),
       "epic-validator must preserve lifecycle vocabulary without adding remediation history")
assert(epic_validator.include?("without starting a per-goal or follow-up review") &&
       epic_validator.include?("whole-epic Mulgae confirmation review") &&
       epic_validator.include?("coverage_status=complete") &&
       epic_validator.include?("publication_status=committed") &&
       epic_validator.include?("findings query succeeds"),
       "epic-validator must avoid nested reviews and require complete whole-epic Mulgae evidence")
assert(epic_validator.include?("next positive ordinal for the current validation goal revision") &&
       epic_validator.include?("exact committed run ID") &&
       epic_validator.include?("an unprovable ordinal stops before review") &&
       epic_validator.include?("Round one is `remediation-eligible`") &&
       epic_validator.include?("round two and every user-authorized later review are `confirmation-only`") &&
       epic_validator.include?("never selects `hardening-deferral-eligible` mode"),
       "epic-validator must durably number cold whole-epic root reviews")
assert(epic_validator.include?("Do not start a third review automatically") &&
       epic_validator.include?("Critical or High findings block validation") &&
       epic_validator.include?("One or more Medium findings stop with a recommendation") &&
       epic_validator.include?("When only Low findings remain") &&
       epic_validator.include?("wait for the user's choice") &&
       epic_validator.include?("user-authorized-micro-fix") &&
       epic_validator.include?("accepted-low") &&
       epic_validator.include?("accepted-medium-risk") &&
       epic_validator.include?("Each user-authorized correction grants one remediation and one next-ordinal confirmation review only") &&
       !epic_validator.include?("repeat affected checks and review until complete") &&
       !epic_validator.include?("regroup and repeat the goal cycle"),
       "epic-validator must enforce one automatic confirmation and severity-based user direction")
assert(epic_validator.include?("planned lifecycle or accepted-risk-only roadmap change and an approved post-review promoted-evidence projection are the sole exceptions") &&
       epic_validator.include?("projection remains outside the review target") &&
       epic_validator.include?("Treat a Mulgae review as operationally complete") &&
       epic_validator.include?("Classify that complete review as clean only when zero unresolved valid findings remain") &&
       epic_validator.include?("An incomplete review or `stop` disposition never supports completion") &&
       epic_validator.include?("never create a validation record or empty commit"),
       "epic-validator must separate review completion from clean or accepted closeout and avoid empty commits")
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
assert(task_handler.lines.length < 111, "task-handler must remain orchestration-focused")

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
assert(ROOT.join("README.md").read.include?("explicit plan handoff to another agent") &&
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
assert(new_project.include?("a PRD, one initial roadmap per delivery scope") &&
       new_project.include?("non-Git project") &&
       new_project.include?("skip Podway completely") &&
       new_project.include?("gate creation requires a later explicit"),
       "new-project must stop at PRD and roadmap and keep non-Git work Podway-free")
assert(new_project.include?("documentation-governance.md") &&
       new_project.include?("`single-scope`") &&
       new_project.include?("`multi-scope`") &&
       new_project.include?("`EPIC-NNN`") &&
       new_project.include?("per-roadmap `TASK-NNN`") &&
       new_project.include?("Do not add a repository-local Aquarium state file or documentation validator"),
       "new-project must establish the shared documentation and roadmap identity contract")
assert(new_feature.include?("exactly one feature epic") &&
       new_feature.include?("documentation-governance.md") &&
       refactor.include?("exactly one refactor epic") &&
       refactor.include?("documentation-governance.md") &&
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
       podway_contract.include?("Use `not_required` only when no final external handoff or repository result is required") &&
       podway_contract.include?("epic-handler closeout with no final repository diff") &&
       podway_contract.include?("Earlier task or remediation commits do not prevent this disposition") &&
       podway_contract.include?("leave the terminal revision undisposed") &&
       podway_contract.include?("never choose force reset or force replacement automatically") &&
       podway_contract.include?("start --replace-eligible"),
       "Podway terminal disposition and eligible replacement policy is incomplete")
assert(podway_contract.include?("## Hand Off Across Workflow Owners") &&
       podway_contract.include?("replace-after-disposition, never automatic resume") &&
       podway_contract.include?("stable non-runtime artifact reference") &&
       podway_contract.include?("successor includes replacement") &&
       podway_contract.include?("current eligible `session.start_replace` template") &&
       podway_contract.include?("never force replacement"),
       "Podway cross-owner handoff must be explicit, verified, and fenced")
assert(podway_contract.include?("[evidence-residency.md](evidence-residency.md)") &&
       podway_contract.include?("These records are local runtime and orchestration evidence") &&
       podway_contract.include?("Podway's recorded claim is not a promotion source") &&
       podway_contract.include?("tracked promoted manifest and digest"),
       "Podway must keep runtime evidence separate from promoted repository authority")
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
       epic_handler.include?("Leave the final terminal session intact"),
       "epic-handler must sequence v0.2.5 dispositions and eligible replacements")
assert(epic_validator.include?("A clean validation with no canonical change creates no repository diff or validation-record commit") &&
       epic_validator.include?("record `not_required` with the verified reason even if earlier task or remediation commits exist") &&
       epic_validator.include?("Record `handed_off` with the exact final validation-owned repository result") &&
       epic_validator.include?("Leave the final terminal session intact"),
       "epic-validator must distinguish committed canonical results from clean no-change validation")
assert(agents_reference.include?("$use-podway") &&
       agents_reference.include?("A CLI alone does not justify a paired-skill reference"),
       "AGENTS guidance must conditionally reference use-podway")
assert(agents_reference.include?("use Podway by default") &&
       agents_reference.include?("opts out before the first managed-session mutation") &&
       agents_reference.include?("diagnosis, recovery, cancellation, or discard operation") &&
       agents_reference.include?("$aquarium:new-project") &&
       agents_reference.include?("$aquarium:war-room") &&
       agents_reference.include?("$aquarium:design-qa") &&
       agents_reference.include?("workflow skills retain their stricter roadmap, ownership, and approval rules"),
       "AGENTS guidance must preserve default use and workflow-local opt-out")
assert(agents_reference.include?("$aquarium:docs-setup") &&
       root_agents.include?("$aquarium:docs-setup"),
       "repository guidance must route documentation governance through docs-setup")

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
    "manual_targets" => %w[audit remediate re-audit final-review micro-remediate],
    "evidence" => {
      "decide-gaps" => required_evidence.call("audit"),
      "decide-final-review" => required_evidence.call("final-review"),
      "await-user-direction" => [["final-review", true]],
      "assess-goal" => [["capture-baseline", true], ["final-review", true], ["await-user-direction", false],
                        ["micro-remediate", false], ["record-accepted-low", false],
                        ["record-accepted-medium-risk", false], ["record-stopped", false], ["record-incomplete", false]]
    },
    "nodes" => {
      "capture-baseline" => { "next" => "audit" },
      "audit" => { "next" => "decide-gaps" },
      "decide-gaps" => { "routes" => { "clean" => %w[final-review advance], "gaps-found" => %w[remediate advance] } },
      "remediate" => { "next" => "re-audit" },
      "re-audit" => { "next" => "final-review" },
      "final-review" => { "next" => "decide-final-review" },
      "decide-final-review" => { "routes" => { "validated" => %w[assess-goal advance], "rework-required" => %w[audit rework], "user-direction" => %w[await-user-direction advance], "incomplete" => %w[record-incomplete advance] } },
      "await-user-direction" => { "routes" => { "fix-and-review" => %w[audit rework], "accept-low" => %w[record-accepted-low advance], "micro-fix" => %w[micro-remediate advance], "accept-medium-risk" => %w[record-accepted-medium-risk advance], "stop" => %w[record-stopped advance] } },
      "micro-remediate" => { "next" => "assess-goal" },
      "record-accepted-low" => { "next" => "assess-goal" },
      "record-accepted-medium-risk" => { "next" => "assess-goal" },
      "record-stopped" => { "next" => "assess-goal" },
      "record-incomplete" => { "next" => "assess-goal" },
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
  expected_version = { "aquarium-validation-v2.yaml" => "5", "aquarium-goal-v2.yaml" => "4", "aquarium-task-v2.yaml" => "3" }.fetch(filename, "1")
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

local_procedures_directory = ROOT.join(".podway/procedures")
expected_procedure_graphs.each_key do |filename|
  source = procedures_directory.join(filename)
  local = local_procedures_directory.join(filename)
  assert(local.file? && local.binread == source.binread,
         "repository-local managed procedure must match its plugin source byte-for-byte: #{filename}")
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
task_closeout_items = review_item_index.call(task_procedure, "closeout-record")
assert(task_review_items.fetch("review-round").fetch("type") == "integer" &&
       task_review_items.fetch("review-mode").fetch("choices") == %w[remediation-eligible confirmation-only] &&
       task_review_items.fetch("review-run-id").fetch("type") == "text",
       "task procedure must record the Mulgae root review ordinal, mode, and exact run")
assert(task_procedure_text.include?("leave a confirmation-only review with valid findings undecided") &&
       task_procedure_text.include?("Select no option while a confirmation-only review retains a valid finding"),
       "task procedure must represent the confirmation-only user hold")
assert(task_procedure_text.include?("Review is incomplete, CI failed, or a remediation-eligible valid finding"),
       "task procedure must route a failing-CI review to rework even with zero findings")
assert(task_closeout_items.fetch("promoted-evidence-references").fetch("type") == "list" &&
       task_closeout_items.fetch("promoted-evidence-references").fetch("required") == false &&
       task_closeout_items.fetch("promoted-evidence-references").fetch("min_items") == 0 &&
       task_closeout_items.fetch("promoted-evidence-references").fetch("max_items") == 50 &&
       task_closeout_items.fetch("promoted-evidence-references").fetch("max_item_length") == 1200 &&
       task_closeout_items.fetch("promoted-evidence-references").fetch("max_total_length") == 1_000_000 &&
       task_closeout_items.fetch("promoted-evidence-references").fetch("unique") == true,
       "task procedure must record optional committed promoted evidence at closeout")

validation_procedure_text = procedures_directory.join("aquarium-validation-v2.yaml").read
validation_procedure = YAML.safe_load(validation_procedure_text, aliases: false)
plan_handoff_item.call(validation_procedure, "baseline-record")
validation_review_items = review_item_index.call(validation_procedure, "final-review-record")
validation_goal_options = validation_procedure.dig("node_definitions", "goal-assessment", "options").to_h do |option|
  [option.fetch("id"), option.fetch("criteria")]
end
assert(validation_review_items.fetch("review-round").fetch("type") == "integer" &&
       validation_review_items.fetch("review-mode").fetch("choices") == %w[remediation-eligible confirmation-only] &&
       validation_review_items.fetch("review-run-id").fetch("type") == "text" &&
       %w[critical-findings high-findings medium-findings low-findings valid-finding-ids].all? { |id| validation_review_items.key?(id) } &&
       validation_procedure_text.include?("Leave this decision unset until the user explicitly selects the next action") &&
       validation_procedure_text.include?("one remediation pass and one next-ordinal whole-epic confirmation review") &&
       validation_procedure_text.include?("prior review covered its resulting bytes"),
       "validation procedure must record severity, bounded follow-up, user direction, and honest micro-fix coverage")
assert(validation_goal_options.fetch("achieved").include?("reached from validated, record-accepted-low, record-accepted-medium-risk, or micro-remediate") &&
       validation_goal_options.fetch("not-achieved").include?("record-stopped or record-incomplete") &&
       validation_goal_options.fetch("not-achieved").include?("can never select achieved"),
       "validation procedure must forbid achieved closeout from incomplete or stopped dispositions")
validation_closeout_items = review_item_index.call(validation_procedure, "closeout-record")
assert(validation_procedure.fetch("version") == "5" &&
       validation_procedure.dig("node_definitions", "closeout-record", "intent").include?("explicit no-change result") &&
       validation_closeout_items.fetch("closeout-summary").fetch("prompt").include?("verified reason no repository record is required") &&
       validation_closeout_items.fetch("promoted-evidence-references").fetch("type") == "list" &&
       validation_closeout_items.fetch("promoted-evidence-references").fetch("required") == false &&
       validation_closeout_items.fetch("promoted-evidence-references").fetch("unique") == true &&
       validation_closeout_items.fetch("promoted-evidence-references").fetch("min_items") == 0 &&
       validation_closeout_items.fetch("promoted-evidence-references").fetch("max_items") == 50 &&
       validation_closeout_items.fetch("promoted-evidence-references").fetch("max_item_length") == 1200 &&
       validation_closeout_items.fetch("promoted-evidence-references").fetch("max_total_length") == 1_000_000,
       "validation procedure must support clean no-record closeout and optional promoted evidence")

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
       goal_deferral_items.fetch("hardening-deferral-finding-ids").fetch("max_items") == 200 &&
       goal_deferral_items.fetch("hardening-deferral-evidence-path").fetch("required") == true &&
       goal_deferral_items.fetch("hardening-deferral-evidence-path").fetch("max_length") == 1024 &&
       goal_deferral_items.fetch("hardening-deferral-evidence-sha256").fetch("required") == true &&
       goal_deferral_items.fetch("hardening-deferral-evidence-sha256").fetch("min_length") == 71 &&
       goal_deferral_items.fetch("hardening-deferral-evidence-sha256").fetch("max_length") == 71 &&
       goal_deferral_items.fetch("hardening-deferral-evidence-sha256").fetch("multiline") == false &&
       goal_procedure_text.include?("verified staged aquarium.promoted-evidence/v1 manifest") &&
       goal_procedure_text.include?("linked before this decision"),
       "goal procedure must retain local Mulgae identities and require durable promoted deferral evidence")
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
  independent-review orca-review release-handler release-qa
]
podway_blind_skills.each do |name|
  body = PLUGIN.join("skills/#{name}/SKILL.md").read
  assert(!body.match?(/podway/i), "leaf and utility skill must remain Podway-blind: #{name}")
end
assert(!orca_provider_contracts.match?(/podway/i),
       "orca-review provider contracts must remain Podway-blind")

assert(independent_review.include?("Return the complete shared result envelope") &&
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
assert(independent_review.include?("[review-contract.md](../../references/review-contract.md)") &&
       independent_review.include?("[orca-supervision.md](../../references/orca-supervision.md)") &&
       independent_review.include?("scripts/inspect_review_target.py"),
       "independent-review must load the shared target and backend contracts")
assert(independent_review.include?("`staged`, `commit`, `range`, `task`, `epic`, or `special request`") &&
       independent_review.include?("always ask the user to confirm staged, `HEAD`") &&
       independent_review.include?("authority identifies one unambiguous staged candidate, commit, or range"),
       "independent-review must resolve every supported target without silently broadening it")
assert(independent_review.include?("--worktree current --agent codex") &&
       independent_review.include?("one fresh reviewer") &&
       independent_review.include?("Wrong scope, modified files, missing output"),
       "independent-review must use one fresh Codex and fail closed on incomplete review evidence")
assert(independent_review.include?("authorizes no source edits, tests, builds") &&
       independent_review.include?("Do not seed the reviewer with suspected findings") &&
       independent_review.include?("Valid, Invalid, or Needs confirmation"),
       "independent-review must remain static, read-only, and independently adjudicated")

%w[staged commit range task epic].each do |target|
  assert(review_contract.include?("`#{target}`"),
         "shared review contract target is missing: #{target}")
end
assert(review_contract.include?("Dirty working-tree content is never a target") &&
       review_contract.include?("stage all displayed paths or an explicitly named subset") &&
       review_contract.include?("git add -- <paths>") &&
       review_contract.include?("Leave the approved index changes staged") &&
       review_contract.include?("For commit, range, and confirmed `HEAD` targets, exclude dirty content automatically") &&
       review_contract.include?("same-user reviewer can technically read excluded working-tree bytes"),
       "shared review contract must preserve exact dirty-state authority boundaries")
assert(review_contract.include?("always ask the user to confirm staged, `HEAD`") &&
       review_contract.include?("explicit invocation that names an exact target and reviewer authorizes transmitting") &&
       review_contract.include?("Do not require separate preparation and transmission approvals") &&
       review_contract.include?("A staged review uses the live index") &&
       review_contract.include?("do not detect drift or invalidate the result") &&
       review_contract.include?("`runtime unverified`") &&
       review_contract.include?("A lifecycle failure or wrong scope is operationally incomplete"),
       "shared review contract must bind special requests, consent, static proof, and lifecycle status")

assert(independent_review_script.file? &&
       independent_review_script_body.include?("aquarium-independent-review-target/v1") &&
       independent_review_script_body.include?("aquarium-independent-review-target-error/v1") &&
       independent_review_script_body.include?('"--staged"') &&
       independent_review_script_body.include?('"--head"') &&
       independent_review_script_body.include?('"--commit"') &&
       independent_review_script_body.include?('"--range"') &&
       independent_review_script_body.include?('"semantic_scope": "not_evaluated"'),
       "independent-review target inspector must expose one bounded JSON interface")
assert(independent_review_script_body.include?('"status"') &&
       independent_review_script_body.include?('"--porcelain=v1"') &&
       independent_review_script_body.include?('"-z"') &&
       independent_review_script_body.include?('"--ignored=matching"') &&
       independent_review_script_body.include?('"diff", "--cached", "--binary"') &&
       independent_review_script_body.include?('"diff-tree"') &&
       independent_review_script_body.include?('"--root"') &&
       independent_review_script_body.include?('"--binary"') &&
       independent_review_script_body.scan('"--no-textconv"').length == 3 &&
       independent_review_script_body.include?('"merge-base"') &&
       independent_review_script_body.include?('"staged_target_empty"') &&
       independent_review_script_body.include?('"range_invalid"'),
       "independent-review target inspector must prove status, staged, commit, and range structure without mutation")

assert(orca_review.include?("removable non-Codex provider layer") &&
       orca_review.include?("user explicitly invokes") &&
       orca_review.include?("use its `scripts/inspect_review_target.py`") &&
       orca_review.include?("current checkout, not a private snapshot"),
       "orca-review must remain an explicit provider extension of the canonical target contract")
assert(orca_review.include?("Probe only `claude`, `kimi`, `agy`, and `cursor-agent`") &&
       orca_review.include?("Claude with a Fable lead") &&
       orca_review.include?("Kimi with K3") &&
       orca_review.include?("Agy with installed defaults") &&
       orca_review.include?("Cursor Agent with Grok 4.6") &&
       !orca_review.include?("codex:gpt"),
       "orca-review must offer only the supported non-Codex providers")
assert(orca_review.include?("prefer structured ask/answer") &&
       orca_review.include?("ask one focused question in ordinary conversation") &&
       orca_review.include?("Do not require separate preparation and transmission approvals") &&
       orca_review.include?("same operating-system user"),
       "orca-review must preserve structured selection, conversational fallback, and one consent boundary")
assert(orca_review.include?("run no tests or builds") &&
       orca_review.include?("`runtime unverified`") &&
       orca_review.include?("Valid, Invalid, or Needs confirmation") &&
       orca_review.include?("Never retry automatically, switch providers") &&
       orca_review.include?("separate Orca Run, Task, Dispatch, terminal, and lifecycle status"),
       "orca-review must remain static, adjudicated, and operationally bounded")

assert(orca_provider_contracts.include?("<PROVIDER> --model fable --dangerously-skip-permissions\n") &&
       orca_provider_contracts.include?("may create Opus or Sonnet subagents when") &&
       orca_provider_contracts.include?("A small review may remain Fable-only") &&
       orca_provider_contracts.include?("<PROVIDER> --model k3 --yolo\n") &&
       orca_provider_contracts.include?("<PROVIDER> --sandbox --dangerously-skip-permissions\n") &&
       orca_provider_contracts.include?("--agent <agent> --model <model> --effort <effort>") &&
       orca_provider_contracts.include?("Do not run `agy agent`, `agy models`") &&
       orca_provider_contracts.include?("<PROVIDER> --model grok-4.6 --yolo\n") &&
       !orca_provider_contracts.include?("--permission-mode plan") &&
       !orca_provider_contracts.include?("--model k3 --plan") &&
       !orca_provider_contracts.include?("--mode plan"),
       "orca-review provider contracts must preserve exact launches and optional provider-native delegation")
assert(orca_provider_contracts.include?("provider-native auto-approval or permission-bypass argument") &&
       orca_provider_contracts.include?("coordinator-owned pre-Dispatch and post-completion repository-state comparison") &&
       orca_provider_contracts.include?("unexpected permission or authentication prompt is an operational failure") &&
       orca_provider_contracts.include?("without asking the coordinator or user to approve it") &&
       orca_review.include?("must not enter or request a provider plan mode") &&
       orca_review.include?("never create, modify, delete, or move a file") &&
       orca_review.include?("never alter the Git index or a ref") &&
       orca_review.include?("scripts/inspect_repository_state.py --repository <exact-git-root> --snapshot") &&
       orca_review.include?("scripts/inspect_repository_state.py --repository <exact-git-root> --compare") &&
       orca_review.include?("HEAD or ref drift, provider-attributed drift, or unexplained drift") &&
       orca_review.include?("without asking the coordinator or user to approve it"),
       "orca-review auto-approval mode must preserve a supervised no-mutation boundary")
assert(orca_state_helper.file? &&
       orca_state_helper_body.include?('SCHEMA_VERSION = "aquarium-orca-review-repository-state/v1"') &&
       orca_state_helper_body.include?('"for-each-ref"') &&
       orca_state_helper_body.include?('["ls-files", "--stage", "-z"]') &&
       orca_state_helper_body.include?('["diff", "--binary", "--no-ext-diff", "--no-textconv"]') &&
       orca_state_helper_body.include?('["status", "--porcelain=v2", "-z", "--untracked-files=all"]') &&
       orca_state_helper_body.include?('"drift": bool(changed)') &&
       orca_state_helper_body.include?("baseline fingerprint is invalid"),
       "orca-review repository-state helper must compare bounded Git-observable state")
assert(ROOT.join("PRIVACY.md").read.include?("native auto-approval or permission-bypass argument") &&
       ROOT.join("PRIVACY.md").read.include?("not automatically reverted") &&
       ROOT.join("TERMS.md").read.include?("provider-native auto-approval or permission-bypass arguments") &&
       ROOT.join("TERMS.md").read.include?("invalidates a clean review verdict"),
       "public policy must disclose Orca Review's auto-approval and no-mutation boundary")
assert(orca_review.include?("scripts/create_provider_terminal.py") &&
       orca_review.include?("exact Git worktree root") &&
       orca_provider_contracts.include?("non-expanding stdin") &&
       orca_provider_contracts.include?("provider-process start") &&
       orca_provider_contracts.include?("never put provider paths or arguments in a shell command") &&
       orca_supervision.include?("deterministic terminal-creation helper"),
       "orca-review must route provider argv through the deterministic terminal helper")
assert(orca_terminal_helper.file? &&
       orca_terminal_helper_body.include?("aquarium-orca-provider-terminal-request/v1") &&
       orca_terminal_helper_body.include?("shlex.join(provider_argv)") &&
       orca_terminal_helper_body.include?(%q["terminal",]) &&
       orca_terminal_helper_body.include?(%q["create",]) &&
       orca_terminal_helper_body.include?("remote_routing_forbidden") &&
       orca_terminal_helper_body.include?("repository_not_root") &&
       orca_terminal_helper_body.include?("PROVIDER_EXEC_GUARD") &&
       orca_terminal_helper_body.include?('f"{label}_identity_changed"'),
       "provider terminal helper must bind identity and avoid coordinator shell interpolation")
assert(orca_supervision.include?("current execution backend") &&
       orca_supervision.include?("original registered checkout") &&
       orca_supervision.include?("Do not create or register a temporary repository snapshot") &&
       orca_supervision.include?("--worktree current --agent codex") &&
       orca_supervision.include?("cumulative 30-minute default liveness budget") &&
       orca_supervision.include?("current recovery and FIFO rules"),
       "shared Orca supervision must bind current-worktree execution and live lifecycle authority")

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
       release_qa.include?("prepare a clean exact candidate only through the enclosing repository workflow") &&
       release_qa.include?("one new release-qa invocation with the required confirmation manifest") &&
       release_qa.include?("timing never narrows the original full-pass delta"),
       "release-qa must distinguish version timing from candidate identity and re-QA remediated candidates")
assert(release_qa.include?("`HEAD` equal to local `main`") &&
       release_qa.include?("do not use the cached upstream-tracking SHA as candidate identity") &&
       release_qa.include?("live remote `main` equals the candidate or is a verified ancestor") &&
       release_qa.include?("A locally ahead candidate remains unpublished release state") &&
       release_qa.include?("candidate is behind remote `main`") &&
       release_qa.include?("refs have diverged"),
       "release-qa must admit a locally ahead exact candidate without accepting stale or divergent main")
assert(release_qa.include?("Do not run existing automated tests") &&
       release_qa.include?("mktemp -d /tmp/release-qa.XXXXXX") &&
       release_qa.include?("resolve that directory with `pwd -P`") &&
       release_qa.include?("physical absolute path") &&
       release_qa.include?("fresh subagents"),
       "release-qa must use isolated scenarios without duplicating existing tests")
assert(release_qa.include?("already-configured ambient authentication") &&
       release_qa.include?("existing ambient authentication for private repositories") &&
       release_qa.include?("never initiate an authentication flow") &&
       release_qa.include?("networked or live product scenarios"),
       "release-qa must separate authorized release discovery from credentials and networked scenarios")
assert(release_qa.include?("Do not replace an unavailable, failed, or timed-out fresh worker") &&
       release_qa.include?("source repository read-only") &&
       release_qa.include?("It never starts a second QA pass by itself") &&
       release_qa.include?("release-readiness decisions"),
       "release-qa must fail incomplete instead of weakening isolation")
assert(release_qa.include?("A first pass is always `full`") &&
       release_qa.include?("confirmation_attempt: 1") &&
       release_qa.include?("frozen cluster and scenario matrix from the previous full pass") &&
       release_qa.include?("Design Gate or release-delta source") &&
       release_qa.include?("authoritative frozen confirmation record") &&
       release_qa.include?("exact cluster decomposition") &&
       release_qa.include?("remediation commit range ending at the current candidate") &&
       release_qa.include?("Confirmation may run exactly once"),
       "release-qa confirmation must require exact prior evidence, candidate identity, and one bounded attempt")
assert(release_qa.include?("project-derived cluster boundaries and scenario inventory") &&
       release_qa.include?("fresh workers for every retained cluster") &&
       release_qa.include?("rerun every retained scenario and every verified finding reproduction") &&
       release_qa.include?("every remediation-changed surface to map") &&
       release_qa.include?("confirmation cannot add new coverage") &&
       release_qa.include?("Existing tests and validators remain prohibited as QA scenario evidence"),
       "release-qa confirmation must preserve the complete project-derived scenario matrix")
assert(release_qa.include?("reconcile the manifest's complete frozen inventory") &&
       release_qa.include?("exact same set of cluster and scenario identifiers") &&
       release_qa.include?("missing, extra, reassigned, or altered entry") &&
       release_qa.include?("never accept a manifest reconstructed") &&
       release_qa.include?("inventory authority for any permitted confirmation pass"),
       "release-qa confirmation must reconcile exactly against the retained full-pass record")
aquarium_specific_confirmation_phrases = [
  "previous five-cluster matrix",
  "commit-hook behavior",
  "test-inspector environment",
  "dev-setup malformed output",
  "review-workflow validation graph and Delivery settlement",
  "shipped package, public documentation, and Procedure parity",
  "additional Bash syntax variants",
  "same-family parser hardening",
  "hook boundary",
  "fuzz parser inputs",
  "probe new generated-directory names"
]
assert(aquarium_specific_confirmation_phrases.none? { |phrase| release_qa.include?(phrase) },
       "release-qa confirmation must not hardcode Aquarium-specific scenario clusters")
assert(release_qa.include?("Do not invent additional inputs, variants, paths, or scenarios") &&
       release_qa.include?("Do not turn a limitation that the candidate publicly documents") &&
       release_qa.include?("stop the release without remediation, another confirmation, or another automatic full pass") &&
       release_qa.include?("additional same-family hardening or newly discovered edge case") &&
       release_qa.include?("do not run another release-qa pass"),
       "release-qa confirmation must forbid scope expansion and automatic re-review")
assert(release_qa.include?("`PASS`") && release_qa.include?("`FINDINGS`") &&
       release_qa.include?("`INCOMPLETE`") &&
       release_qa.include?("implement only the smallest safe fixes") &&
       release_qa.include?("stop and ask for explicit user confirmation") &&
       release_qa.include?("never enter an automatic review-remediation loop") &&
       release_qa.include?("update evidence documents merely to bind an intermediate candidate SHA") &&
       !release_qa.include?("remediation requires a separate user request"),
       "release-qa must remediate once and require confirmation before re-review")
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

assert(release_handler.include?("Explicit invocation authorizes read-only release discovery") &&
       release_handler.include?("Compare every commit and material changed surface") &&
       release_handler.include?("entries are byte-identical") &&
       release_handler.include?("show its exact commands and obtain separate explicit authority") &&
       release_handler.include?("selecting `full` or `light` does not itself authorize tests") &&
       release_handler.include?("leave the gate unrun and stop as incomplete") &&
       release_handler.include?("push `main`") &&
       release_handler.include?("annotated target-version tag") &&
       release_handler.include?("Show the exact new empty `Unreleased` section and request separate commit authority") &&
       release_handler.include?("Never rewrite or delete a published tag or Release"),
       "release-handler must preserve candidate, publication, and next-cycle boundaries")
assert(release_handler.include?("Preserve the full pass's authoritative frozen confirmation record") &&
       release_handler.include?("copying its complete cluster and scenario inventory and entry facts") &&
       release_handler.include?("without re-deriving, regrouping, or sampling") &&
       release_handler.include?("changed-surface mappings") &&
       release_handler.include?("reconciled exactly against it") &&
       release_handler.include?("stop as `INCOMPLETE` before invoking confirmation"),
       "release-handler must hand off the complete retained full-pass record to confirmation")
assert(release_handler.include?("Do not push a candidate before release QA") &&
       release_handler.include?("equals the clean committed local `main` candidate or is a verified ancestor") &&
       release_handler.include?("candidate SHA, live remote SHA, and `equal` or `ancestor` relationship") &&
       release_handler.include?("recompute its ancestry relationship to the release-basis candidate") &&
       release_handler.include?("single fast-forward `push_main`"),
       "release-handler must defer publication and preserve ancestor-safe release pushes")
assert(release_handler.include?("references/gate-convergence.md") &&
       release_handler.include?("freeze its authoritative public checkpoints") &&
       release_handler.include?("Never split recipe lines") &&
       release_handler.include?("Suffix completion is never release-gate `PASS`") &&
       release_handler.include?("QA-neutral direct child") &&
       release_handler.include?("direct-QA candidate SHA") &&
       release_handler.include?("release-basis candidate SHA") &&
       release_handler.include?("every candidate and release commit SHA") &&
       release_handler.include?("exact reuse-attempt fact and approval"),
       "release-handler must use bounded public-stage convergence and distinguish QA evidence from release basis")
assert(release_gate_convergence.include?("independently invocable stage declared by repository authority") &&
       release_gate_convergence.include?("Never split recipe lines") &&
       release_gate_convergence.include?("A failed final aggregate ends the authorized cycle") &&
       release_gate_convergence.include?("obtain fresh explicit authority for the new bounded cycle") &&
       release_gate_convergence.include?("A completed suffix is diagnostic evidence") &&
       release_gate_convergence.include?("complete authoritative release gate from its first command") &&
       release_gate_convergence.include?("restore only the applied release metadata") &&
       release_gate_convergence.include?("open `Unreleased` heading") &&
       release_gate_convergence.include?("one exact reviewed commit") &&
       release_gate_convergence.include?("through its direct-commit flow, not a release-handler commit handoff operation") &&
       release_gate_convergence.include?("new full release-qa pass") &&
       release_gate_convergence.include?("exactly one direct-child correction commit") &&
       release_gate_convergence.include?("tests are not removed, skipped, weakened, or relaxed") &&
       release_gate_convergence.include?("Diff size, commit title, file location alone") &&
       release_gate_convergence.include?("Never claim that release QA directly passed the direct child") &&
       release_gate_convergence.include?("any further candidate commit requires new full release QA"),
       "release gate convergence must optimize diagnosis without weakening the final gate or exact QA binding")
assert(release_handler.include?("references/publication-recovery.md") &&
       release_handler.include?("scripts/inspect_publication_state.py") &&
       release_handler.include?("--first-release") &&
       release_qa.include?("confirmed first release") &&
       release_qa.include?("--first-release"),
       "release workflows must support first releases and deterministic publication recovery")
assert(release_recovery.include?("Recovery is stateless") &&
       release_recovery.include?("direct-QA candidate SHA") &&
       release_recovery.include?("release-basis candidate SHA") &&
       release_recovery.include?("approved QA-neutral binding") &&
       release_recovery.include?("exact reuse-attempt fact") &&
       release_recovery.include?("first-and-only reuse-attempt fact") &&
       release_recovery.include?("push_main") &&
       release_recovery.include?("create_and_push_tag") &&
       release_recovery.include?("create_hosted_release") &&
       release_recovery.include?("verify_complete") &&
       release_recovery.include?("live publication-remote tag") &&
       release_recovery.include?("A local-only tag is remote `absent`") &&
       release_recovery.include?("earlier authority does not survive a new invocation"),
       "publication recovery must reconcile matching state without persisting hidden authority")
assert(workflow_contracts_doc.include?("one approved QA-neutral direct child") &&
       workflow_contracts_doc.include?("direct-QA and release-basis SHAs remain distinct"),
       "workflow contract summary must describe bounded gate convergence and the direct-child QA exception")
assert(release_publication_script.file? &&
       release_publication_script_body.include?("aquarium-release-publication-observation/v3") &&
       release_publication_script_body.include?("aquarium-release-publication-state/v3") &&
       release_publication_script_body.include?("release_basis_candidate_sha") &&
       release_publication_script_body.include?("qa_evidence_relation_to_release_basis") &&
       release_publication_script_body.include?("approved_qa_neutral_descendant") &&
       release_publication_script_body.include?("qa_evidence != release_sha") &&
       release_publication_script_body.include?("release_sha != release_basis") &&
       release_publication_script_body.include?("qa_reuse_attempt == 1") &&
       release_publication_script_body.include?("remote_main_relation_to_release_basis") &&
       release_publication_script_body.include?(%q[remote_relation in {"equal", "ancestor"}]) &&
       release_publication_script_body.include?(%q[next_action = "push_main"]) &&
       release_publication_script_body.include?(%q[next_action = "create_and_push_tag"]) &&
       release_publication_script_body.include?(%q[next_action = "create_hosted_release"]) &&
       release_publication_script_body.include?(%q[next_action = "verify_complete"]) &&
       release_publication_script_body.include?(%q[next_action = "stop"]),
       "publication-state helper must return one ordered resumable action or stop")
assert(release_handler_script.file? && release_handler_script_body.include?("aquarium-release-notes-inspection/v1") &&
       release_handler_script_body.include?(%q["semantic_scope": "not_evaluated"]) &&
       release_handler_script_body.include?("open_release_count_invalid") &&
       release_handler_script_body.include?("authority_untracked") &&
       release_handler_script_body.include?("PROJECT_CONFIGURATION_HEADING") &&
       release_handler_script_body.include?("release_heading_invalid") &&
       release_handler_script_body.include?("release_date_invalid") &&
       release_handler_script_body.include?("release_category_invalid") &&
       release_handler_script_body.include?("release_category_duplicate") &&
       release_handler_script_body.include?("release_category_empty") &&
       release_handler_script_body.include?("release_entry_outside_category") &&
       release_handler_script_body.include?("first_release_has_completed_release") &&
       release_handler_script_body.include?("expected_version_mismatch") &&
       release_handler_script_body.include?("expected_version_not_newer") &&
       release_handler_script_body.include?("previous_release_missing"),
       "release-handler must ship the structural release-notes inspector")
assert(release_notes_contract.include?("Aquarium release notes: <repository-relative-path>") &&
       release_notes_contract.include?("`entry`") &&
       release_notes_contract.include?("`intentional no-note`") &&
       release_notes_contract.include?("`not-enrolled`") &&
       release_notes_contract.include?("at most two Markdown source lines") &&
       release_notes_contract.include?("substantive entry change creates a new candidate"),
       "shared release-notes contract must define enrollment, commit decisions, and QA stability")
assert(release_qa.include?("release-handler inspector") &&
       release_qa.include?("Do not edit the changelog during QA") &&
       task_document.include?("settle exactly one release-note decision before review") &&
       task_close.include?("release-note decision") &&
       task_commit.include?("Require the release-note decision to match the final diff") &&
       task_commit.include?("A release-handler commit handoff must name") &&
       epic_handler.include?("release-note target and decision") &&
       epic_validator.include?("release-note target and decision"),
       "release-note decisions must flow from documentation through QA and commit")

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
assert(task_verify.include?("aquarium-test-contract/v1") &&
       task_verify.include?("reject stale or unapproved waivers") &&
       task_verify.include?("An unenrolled repository") &&
       new_project.include?("initial testing-foundation work unit") &&
       new_project.include?("not eligible for a legacy waiver"),
       "new-project and task-verify must integrate test enrollment without retroactive enforcement")

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
assert(task_document.include?("Never copy ignored runtime paths or identities") &&
       task_document.include?("Do not create routine `Validation remediation` or `Validation record` sections") &&
       task_handler.include?("routine validation record") &&
       task_verify.include?("local runtime evidence that must not be copied into tracked documentation") &&
       task_close.include?("never treat an ignored runtime path or run ID as durable documentation"),
       "task workflow must keep runtime and validation logs out of canonical documentation")
assert(task_handler.include?("every repository handoff is actionable for a named future consumer") &&
       task_handler.include?("clear Internal or External lifecycle") &&
       task_handler.include?("completion or runtime evidence is not duplicated as handoff prose") &&
       task_handler.include?("consumed or stale Internal entries are removed or updated") &&
       task_handler.include?("documentation validation has current evidence"),
       "task-handler must enforce the durable repository handoff postcondition")
assert(task_handler.include?("Distinguish a leaf phase summary, Podway recovery evidence, and a durable repository handoff") &&
       task_handler.include?("Only the last belongs in project documentation"),
       "task-handler must separate orchestration, Podway, and repository handoff evidence")
assert(task_handler.include?("Reject audit logs, completion summaries, evidence collections, routine validation records, and ignored runtime references"),
       "task-handler must return evidence-log documentation for rework")
{
  "task-handler" => task_handler,
  "task-verify" => task_verify,
  "task-document" => task_document,
  "task-close" => task_close,
  "task-commit" => task_commit,
  "task-review" => task_review,
  "epic-handler" => epic_handler,
  "epic-validator" => epic_validator,
  "release-handler" => release_handler,
  "release-qa" => release_qa,
  "war-room" => war_room,
  "design-qa" => design_qa,
  "new-project" => new_project,
  "new-feature" => new_feature,
  "refactor" => refactor
}.each do |name, body|
  assert(body.include?("evidence-residency.md"), "#{name} must use the shared evidence-residency contract")
end
{
  "war-room" => war_room,
  "design-qa" => design_qa,
  "new-project" => new_project,
  "new-feature" => new_feature,
  "refactor" => refactor
}.each do |name, body|
  assert(body.include?("Always read [evidence-residency.md]") &&
         body.index("evidence-residency.md") < body.index("Podway"),
         "#{name} must apply evidence residency before any Podway opt-out")
end
assert(ouroboros_contract.include?("including when Podway is opted out or unavailable") &&
       release_qa.include?("Every `/tmp` path and worker identity remains local orchestration evidence"),
       "opted-out design and release workflows must preserve runtime evidence residency")
assert(evidence_residency.include?("aquarium.promoted-evidence/v1") &&
       evidence_residency.include?("evidence/aquarium/<work-unit-id>/<purpose>/<target-content-sha256>/") &&
       evidence_residency.include?("Aquarium-Evidence: <repository-relative-manifest-path> sha256:<64-hex-manifest-digest>") &&
       evidence_residency.include?("Never promote raw logs, excerpts, reports containing provider prose") &&
       evidence_residency.include?("Mulgae may contribute only a bounded structured JSON projection") &&
       evidence_residency.include?("contains no runtime, invocation, session, provider, or model identity") &&
       evidence_residency.include?("excluded from the Mulgae review target") &&
       evidence_residency.include?("does not make that review stale") &&
       evidence_residency.include?("Never stage a modification, replacement, move, or deletion of an existing tracked package") &&
       evidence_residency.include?("Aquarium evidence root: <repository-relative-path>") &&
       evidence_residency.include?("No other evidence-path mention is a declaration") &&
       evidence_residency.include?("At most one package may exist for the same work unit, purpose, and target digest") &&
       evidence_residency.include?("`work_unit.kind` is `task` or `epic`") &&
       evidence_residency.include?("never derive either value from a runtime or session identity") &&
       evidence_residency.include?("`target.content_sha256` in the final artifact") &&
       evidence_residency.include?("owning workflow verifies the live native evidence") &&
       evidence_residency.include?("producer does not expose an authoritative target SHA-256") &&
       evidence_residency.include?("no documentation diff and no validation-record commit") &&
       evidence_residency.include?("do not attempt to promote the missing run") &&
       evidence_residency.include?("This restriction does not affect an independently approved `accepted-risk`, `external-handoff`, or `repository-required` package"),
       "shared evidence residency must define general promotion, privacy, staleness, root, no-record, and legacy behavior")
forbidden_manifest_identity_keys = %w[runtime_id run_id invocation_id session_id provider model]
assert(forbidden_manifest_identity_keys.none? { |key| evidence_residency.include?(%Q{"#{key}"}) },
       "shared evidence residency examples must not normalize runtime identities")
assert(!epic_validator.include?("Record the final audited snapshot and evidence in the roadmap") &&
       !epic_validator.include?("Add a concise roadmap remediation note") &&
       epic_validator.include?("Never add a routine `Validation remediation`, `Validation record`") &&
       epic_validator.include?("Record resulting remediation commit IDs in Podway and the orchestration report"),
       "epic-validator must not turn validation execution into roadmap history")
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
       task_close.include?("zero or more approved promoted manifest path and digest pairs plus their owning-workflow native validation results or their explicit absence") &&
       task_close.include?("Do not stage or commit independently"),
       "task-close must leave lifecycle choice to the user and commit execution to task-commit")

promotion_index = epic_handler.index("Create and stage the smallest safe structured projection")
deferral_decision_index = epic_handler.index("then select the deferral decision", promotion_index)
podway_deferral_index = epic_handler.index("record the exact run and finding IDs", deferral_decision_index)
assert(promotion_index && deferral_decision_index && podway_deferral_index &&
       promotion_index < deferral_decision_index && deferral_decision_index < podway_deferral_index,
       "epic-handler must promote and verify evidence before selecting and recording a hardening deferral")
assert(epic_validator.include?("zero or more promoted manifest path and digest pairs or their explicit absence") &&
       epic_validator.include?("named consumer that requires durable accepted-risk evidence") &&
       epic_validator.include?("this owning workflow verifies live native evidence") &&
       epic_handler.include?("zero or more promoted manifest path and digest pairs or their explicit absence"),
       "handler commit handoffs must support every approved promoted-evidence purpose")

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
assert(task_commit.include?("When a handler handoff includes one or more promoted-evidence packages") &&
       task_commit.include?("zero or more staged promoted-evidence manifest paths") &&
       task_commit.include?("Aquarium-Evidence: <repository-relative-manifest-path> sha256:<64-hex-manifest-digest>") &&
       task_commit.include?("one repeatable `Aquarium-Evidence") &&
       task_commit.include?("Never add new `Mulgae-Deferred-Run` or `Mulgae-Deferred-Finding` trailers") &&
       !task_commit.include?("Mulgae-Deferred-Run: r_") &&
       !task_commit.include?("Mulgae-Deferred-Finding: F") &&
       !task_commit.include?("When an epic-handler handoff includes a hardening deferral:") &&
       task_commit.include?("Do not copy finding descriptions, recommendations, severities, paths, reports") &&
       task_commit.include?("Reject any staged modification, replacement, move, or deletion of an existing tracked package") &&
       task_commit.include?("approved post-review promoted-evidence packages equal the staged diff") &&
       task_commit.include?("committed manifest/payload digest") &&
       epic_handler.include?("verify every member-task `Aquarium-Evidence` manifest and payload") &&
       epic_handler.include?("Load findings only for `hardening-deferral`") &&
       epic_handler.include?("Use an available exact run for legacy `Mulgae-Deferred-Run` and `Mulgae-Deferred-Finding` trailers") &&
       epic_handler.include?("When that run is gone, do not promote it") &&
       epic_handler.include?("without local runtime"),
       "all promoted evidence must use the common commit boundary with hardening-only live verification and legacy compatibility")
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
  assert(body.include?("stable `v0.2.6` through `v0.2.x`"),
         "Podway supported release line has drifted: #{name}")
end

phase_names.each do |name|
  body = PLUGIN.join("skills/#{name}/SKILL.md").read
  assert(body.include?("to the orchestrator"), "leaf skill must return its report to the orchestrator: #{name}")
end

assert(!PLUGIN.join("skills/deslop").exist?,
       "Aquarium must not bundle the third-party Deslop skill or license")

%w[LICENSE Makefile README.md README.ko.md PRIVACY.md TESTING.md TERMS.md pyproject.toml requirements.txt].each do |relative_path|
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

makefile = ROOT.join("Makefile").read
testing_document = ROOT.join("TESTING.md").read
inspect_testing_tests = ROOT.join("tests/test_inspect_testing.py").read
testing_headings = [
  "Contract",
  "Canonical Commands",
  "Stage Mapping",
  "Test Frameworks",
  "Gaori Mapping",
  "E2E Environment",
  "Language Diagnostics",
  "Legacy Waivers"
]
assert(makefile.include?(".PHONY: test test-requirements test-prepare test-unit test-int test-e2e") &&
       %w[test-prepare test-unit test-int test-e2e].all? { |target| makefile.include?("$(MAKE) #{target}") } &&
       makefile.include?("override VENV_DIR := .venv") &&
       makefile.include?("override PYTHON := $(VENV_DIR)/bin/python") &&
       makefile.include?("override RUFF := $(VENV_DIR)/bin/ruff") &&
       makefile.include?("override PYTEST_ADDOPTS :=") &&
       makefile.include?("export PYTEST_ADDOPTS") &&
       makefile.include?("test-requirements:") &&
       %w[test-prepare test-unit test-int test-e2e].all? { |target| makefile.include?("#{target}: test-requirements") } &&
       makefile.include?("pip install -r requirements.txt") &&
       makefile.include?("open(\"requirements.txt\"") &&
       makefile.include?("subprocess.run([\"$(RUFF)\", \"--version\"]") &&
       makefile.include?("export GIT_PAGER := cat") &&
       makefile.include?("export PAGER := cat") &&
       makefile.include?("export PYTEST_DISABLE_PLUGIN_AUTOLOAD := 1") &&
       makefile.include?("git --no-pager diff --check"),
       "root Makefile must expose the serial common test contract")
assert(makefile.include?("plugins/aquarium/skills/release-handler/scripts/inspect_release_notes.py") &&
       makefile.include?("plugins/aquarium/skills/release-handler/scripts/inspect_publication_state.py") &&
       makefile.include?("plugins/aquarium/skills/orca-review/scripts/create_provider_terminal.py") &&
       makefile.include?("plugins/aquarium/skills/orca-review/scripts/inspect_repository_state.py") &&
       makefile.include?("tests/unit/test_inspect_release_notes_unit.py") &&
       makefile.include?("tests/unit/test_inspect_publication_state_unit.py") &&
       makefile.include?("tests/unit/test_create_provider_terminal_unit.py") &&
       makefile.include?("tests/unit/test_inspect_orca_review_state_unit.py") &&
       makefile.include?("plugins/aquarium/skills/independent-review/scripts/inspect_review_target.py") &&
       makefile.include?("tests/unit/test_inspect_review_target_unit.py") &&
       testing_document.include?("release-notes, publication-state, provider-terminal, Orca Review repository-state, and independent-review target inspectors and helpers") &&
       testing_document.include?("release-notes, publication-state, provider-terminal, Orca Review repository-state, and independent-review target helpers' bounded structural states"),
       "release and review helpers and tests must remain in the common test contract")
assert(makefile.include?("test-podway-compat: test-requirements") &&
       makefile.include?('PODWAY_BIN="$(PODWAY_BIN)" $(PYTHON) tests/verify_podway_compatibility.py') &&
       makefile.include?("tests/unit/test_verify_podway_compatibility_unit.py") &&
       testing_document.include?("external-artifact gate") &&
       testing_document.include?("development-contract evidence only") &&
       testing_document.include?("not runtime record-value enforcement") &&
       root_agents.include?("PODWAY_BIN=<absolute-path-to-extracted-v0.2.6-podway> make test-podway-compat") &&
       root_agents.include?("cannot satisfy this distribution gate"),
       "Podway v0.2.6 compatibility must remain an exact-artifact release gate")
assert(ROOT.join("README.md").read.include?("$aquarium:orca-review") &&
       ROOT.join("README.md").read.include?("[Orca Review]") &&
       ROOT.join("README.ko.md").read.include?("$aquarium:orca-review") &&
       ROOT.join("README.ko.md").read.include?("[Orca Review]"),
       "public workflow and toolchain documentation must include Orca Review")
assert(testing_document.include?("aquarium-test-contract/v1") &&
       testing_headings.all? { |heading| testing_document.include?("## #{heading}") } &&
       testing_document.include?("AQ-WAIVER-001") &&
       testing_document.include?("Approved by Master") &&
       testing_document.include?("Routine additions or edits to test cases inside the same waived suites do not by themselves stale the waiver") &&
       !testing_document.match?(/\b20\d{2}-\d{2}-\d{2}\b/) &&
       !testing_document.include?("Last revalidated") &&
       !testing_document.include?("against functional candidate") &&
       testing_document.include?("tests/test_inspect_docs.py tests/test_inspect_testing.py") &&
       testing_document.include?("docs-setup, release-notes, publication-state, provider-terminal, Orca Review repository-state, and independent-review target inspectors and helpers") &&
       root_agents.include?("`Makefile` is the executable test authority") &&
       root_agents.include?("RELEASE_TAG=v<version> make test") &&
       ROOT.join("README.md").read.include?("make test"),
       "Aquarium must remain enrolled in its own common test contract")
assert(inspect_testing_tests.include?("import pytest") &&
       inspect_testing_tests.include?("@pytest.fixture(autouse=True)") &&
       !inspect_testing_tests.match?(/^import unittest$/) &&
       !inspect_testing_tests.match?(/class\s+\w+\(unittest\.TestCase\)/) &&
       !inspect_testing_tests.include?("self.assert"),
       "the new inspector integration suite must remain native pytest")
gaori_commands = YAML.safe_load(ROOT.join(".gaori/tester.yaml").read, aliases: false).fetch("commands")
expected_gaori_handlers = {
  "test" => ["make", "test"],
  "test-prepare" => ["make", "test-prepare"],
  "test-unit" => ["make", "test-unit"],
  "test-int" => ["make", "test-int"],
  "test-e2e" => ["make", "test-e2e"]
}
assert(gaori_commands.keys.sort == expected_gaori_handlers.keys.sort &&
       expected_gaori_handlers.all? { |name, command| gaori_commands.dig(name, "command") == command },
       "Gaori must wrap each common Make handler without duplicating its implementation")

readme = ROOT.join("README.md").read
korean_readme = ROOT.join("README.ko.md").read
readme_skill_names = %w[
  design-qa
  dev-setup-bundle
  dev-setup
  docs-setup
  epic-handler
  epic-validator
  independent-review
  new-feature
  new-project
  refactor
  release-handler
  release-qa
  task-commit
  task-handler
  test-setup
  war-room
]
assert(readme.lines.length <= 120 && korean_readme.lines.length <= 120,
       "README files must remain concise product overviews")
assert(readme.include?("plugins/aquarium/assets/hero.png"), "README hero image is missing")
assert(readme.include?("[한국어](README.ko.md)") &&
       korean_readme.include?("[English](README.md)") &&
       readme.include?("[Aquarium for Claude](https://github.com/irootkernel/aquarium-for-claude)") &&
       korean_readme.include?("[Aquarium for Claude](https://github.com/irootkernel/aquarium-for-claude)") &&
       korean_readme.include?("plugins/aquarium/assets/hero.png"),
       "README language navigation and Korean hero are incomplete")
assert(korean_readme.include?("AI Fleet") &&
       korean_readme.include?("Agentic Engineering") &&
       korean_readme.include?("Loop Engineering") &&
       korean_readme.include?("Graph Engineering") &&
       %w[설치 주요\ 워크플로 생태계가\ 연결되는\ 방식 운영\ 경계 검증].all? { |heading| korean_readme.include?("## #{heading}") } &&
       readme_skill_names.all? { |name| korean_readme.include?("$aquarium:#{name}") },
       "Korean README must retain the product identity, core sections, and main workflows")
assert(readme.include?("https://home.rootkernel.xyz"), "README homepage is missing")
assert(readme.include?("[Canonical documentation](docs/README.md)") &&
       korean_readme.include?("[Canonical documentation](docs/README.md)"),
       "README files must link to the canonical documentation index")
assert(readme.include?("mailto:cs@rootkernel.xyz"), "README support email is missing")
assert(readme.include?("codex plugin marketplace add irootkernel/aquarium --ref main"),
       "README marketplace install command is missing")
assert(readme.include?("codex plugin add aquarium@root-kernel"),
       "README plugin install command is missing")
assert(readme.include?("By [Root Kernel](https://home.rootkernel.xyz)"),
       "README Root Kernel byline is missing")
assert(readme.include?("codex plugin remove root-kernel@root-kernel-dev-skills") &&
       readme.include?("codex plugin marketplace remove root-kernel-dev-skills") &&
       readme.include?("$aquarium:dev-setup"),
       "README product-rename migration is missing")
assert(readme.include?("codex plugin remove aquarium@aquarium") &&
       readme.include?("codex plugin marketplace remove aquarium"),
       "README marketplace-rename migration is missing")
readme_skill_names.each do |name|
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
  assert(lines[frontmatter_end + 2] == "",
         "skill frontmatter must be followed by one blank line: #{path}")
  lines[(frontmatter_end + 2)..].each_with_index do |line, offset|
    assert(line.length <= 560,
           "skill body line exceeds 560 characters: #{path}:#{frontmatter_end + 3 + offset} (#{line.length})")
  end
end

assert(Dir[ROOT.join("**/.aquarium")].empty?, "central project-state file must not exist")

puts "validated #{skill_paths.length} skills, marketplace and plugin metadata, managed procedures, cross-file pins, and documentation invariants"
