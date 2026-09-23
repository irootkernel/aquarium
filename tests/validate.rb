# frozen_string_literal: true

require "json"
require "open3"
require "pathname"
require "yaml"

ROOT = Pathname.new(__dir__).parent.expand_path
PLUGIN = ROOT.join("plugins/aquarium")

def assert(condition, message)
  raise message unless condition
end

def local_path(path)
  path = path.cleanpath
  assert(path.to_s.start_with?("#{ROOT}/"), "path escapes repository: #{path}")
  current = path
  until current == ROOT
    assert(!current.symlink?, "symlink is not a package input: #{current}")
    current = current.parent
  end
  assert(path.exist?, "missing local path: #{path}")
  path
end

def read_file(path)
  assert(local_path(path).file?, "expected a regular file: #{path}")
  path.read
end

def nonempty_string(value)
  value.is_a?(String) && !value.strip.empty?
end

# Keep this validator structural. Master separately verifies skill behavior.
manifest = JSON.parse(read_file(PLUGIN.join(".codex-plugin/plugin.json")))
assert(manifest.fetch("name") == "aquarium", "plugin name must be aquarium")
assert(manifest.fetch("version") == "0.1.17", "plugin version must be 0.1.17")
release_tag = ENV.fetch("RELEASE_TAG", "")
assert(release_tag.empty? || release_tag == "v#{manifest.fetch('version')}",
       "release tag must match plugin version v#{manifest.fetch('version')}")
assert(nonempty_string(manifest.fetch("description")), "plugin description is missing")
assert(local_path(PLUGIN.join(manifest.fetch("skills"))) == PLUGIN.join("skills"),
       "plugin skills path must resolve to its skill directory")

mcp = JSON.parse(read_file(PLUGIN.join(manifest.fetch("mcpServers"))))
mcp.fetch("mcp_servers").each do |name, server|
  command = server.fetch("command")
  assert(command.start_with?("./"), "bundled MCP command must be plugin-relative: #{name}")
  executable = local_path(PLUGIN.join(command))
  assert(executable.to_s.start_with?("#{PLUGIN}/"), "MCP command escapes plugin: #{name}")
  assert(executable.file? && executable.executable?, "MCP command is not executable: #{name}")
  assert(server.fetch("args").is_a?(Array), "MCP arguments must be an array: #{name}")
end

marketplace = JSON.parse(read_file(ROOT.join(".agents/plugins/marketplace.json")))
entries = marketplace.fetch("plugins")
assert(entries.is_a?(Array) && entries.length == 1, "marketplace must publish one plugin")
entry = entries.first
assert(entry.fetch("name") == manifest.fetch("name"), "marketplace plugin name mismatch")
assert(entry.dig("source", "source") == "local", "marketplace plugin source must be local")
assert(local_path(ROOT.join(entry.fetch("source").fetch("path"))) == PLUGIN,
       "marketplace source must resolve to the plugin directory")

skill_directories = Dir[PLUGIN.join("skills/*")].sort.map { |path| Pathname.new(path) }
assert(!skill_directories.empty?, "plugin has no skills")
skill_directories.each do |directory|
  path = directory.join("SKILL.md")
  frontmatter = read_file(path).match(/\A---\r?\n(.*?)\r?\n---(?:\r?\n|\z)/m)
  assert(frontmatter, "missing skill frontmatter: #{path}")
  metadata = YAML.safe_load(frontmatter[1], aliases: false)
  assert(metadata.is_a?(Hash), "skill metadata must be a mapping: #{path}")
  assert(metadata.fetch("name") == directory.basename.to_s, "skill name/path mismatch: #{path}")
  assert(nonempty_string(metadata.fetch("description")), "skill description is missing: #{path}")

  ui_path = directory.join("agents/openai.yaml")
  ui = YAML.safe_load(read_file(ui_path), aliases: false)
  assert(nonempty_string(ui.fetch("interface").fetch("default_prompt")),
         "default prompt is missing: #{ui_path}")
  assert([true, false].include?(ui.fetch("policy").fetch("allow_implicit_invocation")),
         "implicit invocation policy must be boolean: #{ui_path}")
  if directory.basename.to_s == "mulgae-review"
    assert(ui.fetch("policy").fetch("allow_implicit_invocation") == false,
           "standalone Mulgae review must require explicit invocation: #{ui_path}")
  end
end

# Parse package data without inspecting Python source or duplicating workflow prose.
Dir[PLUGIN.join("**/*.{json,yaml,yml}")].sort.each do |filename|
  path = Pathname.new(filename)
  content = read_file(path)
  path.extname == ".json" ? JSON.parse(content) : YAML.safe_load(content, aliases: false)
end

hooks = JSON.parse(read_file(PLUGIN.join("hooks/hooks.json")))
hooks.fetch("hooks").fetch("PreToolUse").each do |hook_group|
  Regexp.new(hook_group.fetch("matcher"))
  hook_group.fetch("hooks").each do |hook|
    assert(hook.fetch("type") == "command", "expected a command hook")
    assert(nonempty_string(hook.fetch("command")), "hook command is missing")
    hook.fetch("command").scan(/\$\{PLUGIN_ROOT\}\/([^"\s]+)/).each do |(relative)|
      assert(local_path(PLUGIN.join(relative)).file?, "hook script is missing: #{relative}")
    end
  end
end

procedures = Dir[PLUGIN.join("assets/podway/procedures/*.yaml")].sort
assert(!procedures.empty?, "plugin has no procedures")
procedures.each do |filename|
  path = Pathname.new(filename)
  procedure = YAML.safe_load(read_file(path), aliases: false)
  assert(procedure.fetch("schema") == "podway.procedure/v2", "unsupported procedure schema: #{path}")
  assert(procedure.fetch("id") == path.basename(".yaml").to_s, "procedure ID/path mismatch: #{path}")
  nodes = procedure.fetch("graph").fetch("nodes")
  ids = nodes.map { |node| node.fetch("id") }
  assert(!ids.empty? && ids.uniq == ids, "missing or duplicate procedure nodes: #{path}")
  targets = [procedure.fetch("graph").fetch("entry")]
  targets.concat(procedure.fetch("manual_rework").fetch("allowed_targets"))
  nodes.each do |node|
    definition = procedure.fetch("node_definitions")[node.fetch("use")]
    assert(definition,
           "unknown node definition: #{path}:#{node.fetch('id')}")
    if definition.fetch("type") == "action"
      instructions = definition["instructions"]
      assert(instructions.is_a?(Array) && !instructions.empty? &&
             instructions.all? { |instruction| nonempty_string(instruction) },
             "action instructions are missing: #{path}:#{node.fetch('id')}")
    end
    targets << node["next"] if node.key?("next")
    targets.concat(node.fetch("routes", {}).values.map { |route| route.fetch("to") })
    targets.concat(node.fetch("evidence_from", []).map { |evidence| evidence.fetch("node") })
  end
  assert((targets - ids).empty?, "unresolved procedure node reference: #{path}")
  local = ROOT.join(".podway/procedures", path.basename)
  assert(read_file(local) == read_file(path), "installed procedure differs from package source: #{local}")
end

hero = local_path(PLUGIN.join("assets/hero.png"))
bytes = hero.binread(24)
assert(bytes.start_with?("\x89PNG\r\n\x1a\n".b), "hero asset must be PNG")
assert(bytes.byteslice(16, 8)&.unpack("NN") == [2172, 724], "hero asset dimensions are incorrect")

# Check tracked documentation present in the working tree, including staged additions.
# Untracked notes and ignored runtime evidence are not documentation authorities.
output, status = Open3.capture2("git", "-C", ROOT.to_s, "ls-files", "--cached",
                               "-z", "--", "*.md")
assert(status.success?, "cannot list source documentation")
output.split("\0").each do |relative|
  path = ROOT.join(relative)
  next unless path.exist? || path.symlink?
  in_fence = false
  read_file(path).each_line do |line|
    in_fence = !in_fence if line.lstrip.start_with?("```", "~~~")
    next if in_fence

    line.scan(/\]\(([^)]+)\)/).each do |(target)|
      target = target.strip.sub(/\s+"[^"]*"\z/, "").delete_prefix("<").delete_suffix(">")
      next if target.match?(/\A(?:[a-z][a-z0-9+.-]*:|#)/i)

      relative_target = target.split("#", 2).first
      next if relative_target.nil? || relative_target.empty?

      local_path(path.dirname.join(relative_target))
    end
  end
end

puts "validated #{skill_directories.length} skill packages, metadata, local references, and procedure structure; skill behavior is not evaluated"
