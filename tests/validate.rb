# frozen_string_literal: true

require "json"
require "pathname"
require "yaml"

ROOT = Pathname.new(__dir__).parent
PLUGIN = ROOT.join("plugins/root-kernel")

def assert(condition, message)
  raise message unless condition
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
  deslop
  dev-setup
  task-close
  task-document
  task-handler
  task-implement
  task-plan
  task-refine
  task-review
  task-verify
]
assert(skill_paths.map { |path| path.dirname.basename.to_s } == expected_skill_names,
       "plugin skill set does not match the orchestrated task workflow")

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
  assert(prompt.include?("$root-kernel:#{metadata.fetch('name')}"), "default prompt lacks skill name: #{ui_path}")
  assert(prompt.length <= 128, "default prompt exceeds 128 characters: #{ui_path}")
end

manifest = JSON.parse(PLUGIN.join(".codex-plugin/plugin.json").read)
assert(manifest.fetch("license") == "MIT", "plugin license must be MIT")
assert((%w[deslop lora lore orchestration] - manifest.fetch("keywords")).empty?, "plugin discovery keywords are missing")
assert(manifest.fetch("homepage") == "https://home.rootkernel.xyz", "plugin homepage is incorrect")
assert(manifest.dig("author", "url") == manifest.fetch("homepage"), "author URL must match the homepage")
assert(manifest.dig("author", "email") == "cs@rootkernel.xyz", "support email is incorrect")
prompts = manifest.fetch("interface").fetch("defaultPrompt")
assert(prompts.is_a?(Array) && prompts.length == 2, "plugin defaultPrompt must contain two prompts")
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
  asset_path = PLUGIN.join(relative_path.delete_prefix("./"))
  bytes = asset_path.binread(24)
  assert(bytes.start_with?("\x89PNG\r\n\x1a\n".b), "plugin #{key} must be a PNG")
  width, height = bytes.byteslice(16, 8).unpack("NN")
  assert([width, height] == [expected_width, expected_height], "plugin #{key} dimensions are incorrect")
end
assert(PLUGIN.join("assets/logo-black.png").file?, "dark-theme README logo is missing")

dev_setup = PLUGIN.join("skills/dev-setup/SKILL.md").read
dev_setup_script = PLUGIN.join("skills/dev-setup/scripts/inspect_tools.py")
agents_reference = PLUGIN.join("skills/dev-setup/references/agents-guidance.md").read
tool_catalog = PLUGIN.join("skills/dev-setup/references/tool-catalog.md").read
task_handler = PLUGIN.join("skills/task-handler/SKILL.md").read
task_plan = PLUGIN.join("skills/task-plan/SKILL.md").read
task_implement = PLUGIN.join("skills/task-implement/SKILL.md").read
task_verify = PLUGIN.join("skills/task-verify/SKILL.md").read
task_refine = PLUGIN.join("skills/task-refine/SKILL.md").read
task_document = PLUGIN.join("skills/task-document/SKILL.md").read
task_review = PLUGIN.join("skills/task-review/SKILL.md").read
task_close = PLUGIN.join("skills/task-close/SKILL.md").read

assert(dev_setup.include?("request_user_input"), "dev-setup must prefer Codex ask/answer")
assert(dev_setup.include?("planned Podway integration"), "dev-setup description must trigger for Podway availability")
assert(dev_setup.include?("scripts/inspect_tools.py"), "dev-setup must use deterministic local inspection")
assert(dev_setup_script.file?, "dev-setup inspection script is missing")
proposal_index = dev_setup.index("Ask whether to prepare")
diff_index = dev_setup.index("Display the exact target path")
apply_index = dev_setup.index("Apply exactly this diff")
assert(proposal_index && diff_index && apply_index && proposal_index < diff_index && diff_index < apply_index,
       "AGENTS proposal and apply approvals are not ordered")
assert(dev_setup.include?("If it changed, discard the approval"), "stale AGENTS approval guard is missing")
assert(agents_reference.include?("Repository-specific rules below override"), "override precedence is missing")

assert(tool_catalog.include?("--skill lore-commits"), "Lora commit skill is missing")
assert(tool_catalog.include?("--skill lore-query"), "Lora query skill is missing")
assert(!tool_catalog.include?("--skill lore-setup"), "Lora setup skill must not be installed")
assert(tool_catalog.include?("--global") && tool_catalog.include?("--agent codex"), "Lora scope must be global Codex")
assert(tool_catalog.include?("Status: planned"), "Podway must remain planned")
assert(tool_catalog.include?("https://github.com/irootkernel/podway"), "Podway source URL is missing")
assert(tool_catalog.include?("gaori version --json"), "Gaori JSON version probe is missing")

assert(task_handler.include?("$root-kernel:dev-setup"), "task-handler must route missing setup")
phase_names = %w[task-plan task-implement task-verify task-refine task-document task-review task-close]
phase_section_index = task_handler.index("Resolve every phase skill")
phase_indexes = phase_names.map { |name| task_handler.index("$root-kernel:#{name}", phase_section_index) }
assert(phase_indexes.all? && phase_indexes.each_cons(2).all? { |left, right| left < right },
       "task-handler phase skills are missing or misordered")
assert(task_handler.include?("A leaf skill's report is a handoff summary, not proof by itself"),
       "task-handler must verify leaf postconditions independently")
assert(task_handler.include?("Resume at the earliest phase whose postcondition is not currently proven"),
       "task-handler must reconstruct safe resume state")
assert(task_handler.include?("Do not create or read `.root-kernel-dev-skills`"),
       "task-handler must not create shadow orchestration state")
assert(task_handler.lines.length < 100, "task-handler must remain orchestration-focused")

phase_names.each do |name|
  ui = YAML.safe_load(PLUGIN.join("skills/#{name}/agents/openai.yaml").read, aliases: false)
  assert(ui.dig("policy", "allow_implicit_invocation") == false,
         "task phase skill must disable implicit invocation: #{name}")
end

assert(task_plan.include?("decision-complete plan"), "task-plan must own decision-complete planning")
assert(task_plan.include?("Do not create a goal"), "task-plan must remain mutation-free")
assert(task_implement.include?("smallest maintainable change"), "task-implement must bound implementation")
assert(task_implement.include?("Do not stage"), "task-implement must leave staging to later phases")
assert(task_verify.include?("requirement-to-test matrix"), "task-verify must map requirements to evidence")
assert(task_verify.include?("do not rerun the same check merely to duplicate it"),
       "task-verify must avoid duplicating current user-run tests")

deslop_index = task_refine.index("Load and follow the bundled `$root-kernel:deslop`")
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
assert(task_review.include?("Select exactly one target that contains the complete task diff"),
       "task-review must isolate one complete Mulgae target")
assert(task_review.include?("Treat every finding as an advisory hypothesis"),
       "task-review must verify Mulgae findings")

commit_status_index = task_close.index("When the user asks to commit")
ask_index = task_close.index("request_user_input", commit_status_index)
tests_confirmation_index = task_close.index("Tests passed", ask_index)
docs_confirmation_index = task_close.index("Docs approved", ask_index)
implementation_confirmation_index = task_close.index("Approve and commit", ask_index)
terminal_status_index = task_close.index("Treat `Completed`, `Blocked`, and `Deferred` as terminal")
staged_status_index = task_close.index("Re-read the staged roadmap entry", terminal_status_index)
commit_authority_index = task_close.index("authorizes one commit", staged_status_index)
assert(commit_status_index && ask_index && tests_confirmation_index && docs_confirmation_index &&
       implementation_confirmation_index && terminal_status_index && staged_status_index && commit_authority_index &&
       commit_status_index < ask_index && ask_index < tests_confirmation_index &&
       tests_confirmation_index < docs_confirmation_index && docs_confirmation_index < implementation_confirmation_index &&
       implementation_confirmation_index < terminal_status_index && terminal_status_index < staged_status_index &&
       staged_status_index < commit_authority_index, "task-close terminal-state commit gate is missing or misordered")
assert(task_close.include?("Any other task-owned code, test, documentation, or roadmap change after the answers invalidates all three confirmations"),
       "task-close must invalidate stale confirmations")
assert(task_close.include?("The exact proposed status-only edit is part of approval and does not invalidate it"),
       "task-close must keep the approved status transition actionable")
assert(task_close.include?("Do not rerun user-confirmed tests or documentation checks solely"),
       "task-close must avoid redundant closeout verification")
assert(task_close.include?("Never infer approval from silence"),
       "task-close must require explicit approval")
assert(task_close.include?("If structured ask/answer is unavailable"),
       "task-close must define an ask/answer fallback")
assert(task_close.include?("$lore-commits"), "task-close must honor Lore guidance")

assert(PLUGIN.join("skills/deslop/LICENSE").read.include?("Copyright (c) 2026 Cursor"),
       "deslop MIT attribution is missing")
deslop_ui = YAML.safe_load(PLUGIN.join("skills/deslop/agents/openai.yaml").read, aliases: false)
assert(deslop_ui.dig("policy", "allow_implicit_invocation") == true, "deslop implicit invocation must be explicit")

%w[LICENSE README.md PRIVACY.md TERMS.md .github/workflows/validate.yml].each do |relative_path|
  assert(ROOT.join(relative_path).file?, "distribution file is missing: #{relative_path}")
end

workflow = ROOT.join(".github/workflows/validate.yml").read
assert(workflow.include?("ruby/setup-ruby@v1"), "CI must configure Ruby explicitly")
assert(workflow.include?("actions/setup-python@v5"), "CI must configure Python explicitly")
assert(workflow.include?("python -m unittest tests/test_inspect_tools.py"), "CI must run inspection tests")
assert(workflow.include?("ruby tests/validate.rb"), "CI must run repository validation")

readme = ROOT.join("README.md").read
assert(readme.include?("plugins/root-kernel/assets/logo-white.png"), "README light-theme logo is missing")
assert(readme.include?("plugins/root-kernel/assets/logo-black.png"), "README dark-theme logo is missing")
assert(readme.include?("https://home.rootkernel.xyz"), "README homepage is missing")
assert(readme.include?("mailto:cs@rootkernel.xyz"), "README support email is missing")
assert(readme.include?("codex plugin marketplace add irootkernel/root-kernel-dev-skills --ref main"),
       "README marketplace install command is missing")
assert(readme.include?("codex plugin add root-kernel@root-kernel-dev-skills"),
       "README plugin install command is missing")
phase_names.each do |name|
  assert(readme.include?("`#{name}`"), "README phase skill is missing: #{name}")
end
%w[
  https://github.com/irootkernel/sanho
  https://github.com/irootkernel/mulgae
  https://github.com/irootkernel/gaori
  https://github.com/tmdgusya/lora
  https://github.com/irootkernel/podway
].each do |url|
  assert(readme.include?(url), "README tool URL is missing: #{url}")
end

document_paths = Dir[ROOT.join("**/*.md")].map { |path| Pathname.new(path) }
document_paths.concat([ROOT.join("LICENSE"), PLUGIN.join("skills/deslop/LICENSE")])
document_paths.uniq.each { |path| assert_no_hard_wrap(path) }

assert(Dir[ROOT.join("**/.root-kernel-dev-skills")].empty?, "central project-state file must not exist")

puts "validated #{skill_paths.length} skills and plugin invariants"
