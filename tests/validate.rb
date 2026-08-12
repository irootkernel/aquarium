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
  epic-handler
  epic-validator
  independent-review
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
       "plugin skill set does not match the expected skills")

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
epic_handler = PLUGIN.join("skills/epic-handler/SKILL.md").read
epic_validator = PLUGIN.join("skills/epic-validator/SKILL.md").read
task_handler = PLUGIN.join("skills/task-handler/SKILL.md").read
independent_review = PLUGIN.join("skills/independent-review/SKILL.md").read
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
lookup_approval_index = dev_setup.index("obtain explicit ask/answer approval for that network operation")
version_resolution_index = dev_setup.index("resolve the exact stable version and source provenance")
action_approval_index = dev_setup.index("Obtain separate explicit ask/answer approval for the displayed action")
assert(lookup_approval_index && version_resolution_index && action_approval_index &&
       lookup_approval_index < version_resolution_index && version_resolution_index < action_approval_index &&
       dev_setup.include?("A lookup approval authorizes no installation or other mutation"),
       "dev-setup must approve release metadata lookup before resolution and approve setup separately")
assert(agents_reference.include?("Repository-specific rules below override"), "override precedence is missing")
assert(agents_reference.include?("$root-kernel:epic-handler") &&
       agents_reference.include?("$root-kernel:epic-validator"),
       "AGENTS reference guidance must distinguish epic delivery and validation")

assert(tool_catalog.include?("--skill lore-commits"), "Lora commit skill is missing")
assert(tool_catalog.include?("--skill lore-query"), "Lora query skill is missing")
assert(!tool_catalog.include?("--skill lore-setup"), "Lora setup skill must not be installed")
assert(tool_catalog.include?("--global") && tool_catalog.include?("--agent codex"), "Lora scope must be global Codex")
assert(tool_catalog.include?("Status: planned"), "Podway must remain planned")
assert(tool_catalog.include?("https://github.com/irootkernel/podway"), "Podway source URL is missing")
assert(tool_catalog.include?("gaori version --json"), "Gaori JSON version probe is missing")

epic_handler_ui = YAML.safe_load(PLUGIN.join("skills/epic-handler/agents/openai.yaml").read, aliases: false)
assert(epic_handler_ui.dig("policy", "allow_implicit_invocation") == false,
       "epic-handler must disable implicit invocation")
assert(epic_handler.include?("one canonical roadmap path inside that repository") &&
       epic_handler.include?("exactly one epic ID"),
       "epic-handler must require one repository roadmap and epic")
approval_index = epic_handler.index("Ask once for explicit approval")
task_goal_index = epic_handler.index("For each non-terminal task in order")
epic_goal_index = epic_handler.index("one final epic closeout goal")
assert(approval_index && task_goal_index && epic_goal_index && approval_index < task_goal_index && task_goal_index < epic_goal_index,
       "epic-handler must approve once, serialize task goals, then create the closeout goal")
assert(epic_handler.include?("Do not invoke `$root-kernel:task-handler` or its phase skills") &&
       epic_handler.include?("sequence of goal-centered task executions") &&
       epic_handler.include?("do not manufacture phase artifacts"),
       "epic-handler must remain independent and goal-centered")
assert(epic_handler.include?("Run Mulgae at least once on the latest complete task target") &&
       epic_handler.include?("audit again from scratch"),
       "epic-handler must require task and convergent epic Mulgae review")
assert(epic_handler.include?("It does not authorize amend, push, PR or release changes"),
       "epic-handler must preserve publication boundaries")
assert(epic_handler.include?("reference `$lore-commits` and follow it when available") &&
       epic_handler.include?("git log -5 --format=fuller") &&
       epic_handler.include?("subject, body, and trailer structure") &&
       epic_handler.include?("If fewer than five commits exist"),
       "epic-handler must prefer Lore without making it a hard dependency")
assert(epic_handler.include?("Do not create or read `.root-kernel-dev-skills`"),
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

epic_validator_ui = YAML.safe_load(PLUGIN.join("skills/epic-validator/agents/openai.yaml").read, aliases: false)
assert(epic_validator_ui.dig("policy", "allow_implicit_invocation") == false,
       "epic-validator must disable implicit invocation")
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
assert(epic_validator.include?("Do not invoke `$root-kernel:task-handler`, `$root-kernel:epic-handler`") &&
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
assert(epic_validator.include?("run Mulgae on the latest complete remediation target") &&
       epic_validator.include?("whole-epic Mulgae review") &&
       epic_validator.include?("coverage_status=complete") &&
       epic_validator.include?("publication_status=committed") &&
       epic_validator.include?("findings query succeeds"),
       "epic-validator must require complete per-goal and final Mulgae evidence")
assert(epic_validator.include?("status or validation-record-only roadmap change is the sole exception") &&
       epic_validator.include?("never duplicate an equivalent record or create an empty commit"),
       "epic-validator must invalidate stale evidence and avoid empty closeout commits")
assert(epic_validator.include?("reference `$lore-commits` and follow it when available") &&
       epic_validator.include?("git log -5 --format=fuller") &&
       epic_validator.include?("If fewer than five commits exist"),
       "epic-validator must prefer Lore with a repository-history fallback")
assert(epic_validator.include?("Commit is not upstream publication") &&
       epic_validator.include?("Do not create or read `.root-kernel-dev-skills`") &&
       epic_validator.include?("compare the commit with that snapshot byte-for-byte"),
       "epic-validator must preserve publication and shadow-state boundaries")
assert(epic_validator.lines.length < 120, "epic-validator must remain orchestration-focused")

assert(task_handler.include?("$root-kernel:dev-setup"), "task-handler must route missing setup")
assert(!task_handler.include?("$root-kernel:epic-handler"),
       "task-handler must remain independent from epic-handler")
assert(task_handler.include?("Strengthen execution of one roadmap task goal"),
       "task-handler must be goal-centered and procedure-strengthening")
assert(epic_handler.include?("requests without one canonical roadmap epic identity") &&
       task_handler.include?("requests without one canonical roadmap task identity") &&
       !epic_handler.include?("free-form") && !task_handler.include?("free-form"),
       "handlers must express applicability through canonical roadmap identities")
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

independent_review_ui = YAML.safe_load(PLUGIN.join("skills/independent-review/agents/openai.yaml").read, aliases: false)
assert(independent_review_ui.dig("policy", "allow_implicit_invocation") == false,
       "independent-review must disable implicit invocation")
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

approval_start_index = task_close.index("Re-read the roadmap vocabulary")
ask_index = task_close.index("request_user_input", approval_start_index)
tests_confirmation_index = task_close.index("Evidence accepted", ask_index)
docs_confirmation_index = task_close.index("Docs approved", ask_index)
implementation_confirmation_index = task_close.index("Approve and commit", ask_index)
non_commit_confirmation_index = task_close.index("Approve and close without commit", ask_index)
terminal_status_index = task_close.index("Treat `Completed`, `Blocked`, and `Deferred` as terminal")
staged_status_index = task_close.index("re-read the staged roadmap entry", terminal_status_index)
non_commit_transition_index = task_close.index("do not stage or commit anything", terminal_status_index)
commit_authority_index = task_close.index("authorizes one commit", staged_status_index)
assert(approval_start_index && ask_index && tests_confirmation_index && docs_confirmation_index &&
       implementation_confirmation_index && non_commit_confirmation_index && terminal_status_index &&
       staged_status_index && non_commit_transition_index && commit_authority_index &&
       approval_start_index < ask_index && ask_index < tests_confirmation_index &&
       tests_confirmation_index < docs_confirmation_index && docs_confirmation_index < implementation_confirmation_index &&
       implementation_confirmation_index < terminal_status_index && terminal_status_index < staged_status_index &&
       terminal_status_index < non_commit_transition_index && staged_status_index < commit_authority_index,
       "task-close terminal-state commit and non-commit gates are missing or misordered")
assert(task_close.include?("do not stage or commit anything") &&
       task_close.include?("This path is unavailable when repository authority requires a commit for completion"),
       "task-close must support a safe non-commit closeout path")
assert(task_close.include?("including who ran each check") && !task_close.include?("personally run"),
       "task-close must accept evidence with explicit agent or user provenance")
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
assert(readme.include?("`epic-handler`") && readme.include?("$root-kernel:epic-handler"),
       "README epic-handler entry is missing")
assert(readme.include?("`epic-validator`") && readme.include?("$root-kernel:epic-validator"),
       "README epic-validator entry is missing")
assert(readme.include?("`independent-review`") && readme.include?("$root-kernel:independent-review"),
       "README independent-review entry is missing")
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
