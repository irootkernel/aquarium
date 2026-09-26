# frozen_string_literal: true

require "pathname"

module LocalReferences
  def self.local_path(path, root)
    raise "path escapes root: #{path}" unless path == root || path.to_s.start_with?("#{root}/")

    current = root
    raise "symlink is not a package input: #{current}" if current.symlink?
    path.to_s.delete_prefix(root.to_s).split("/").each do |part|
      next if part.empty? || part == "."

      raise "expected a directory: #{current}" unless current.directory?

      current = part == ".." ? current.parent : current.join(part)
      unless current == root || current.to_s.start_with?("#{root}/")
        raise "path escapes root: #{path}"
      end
      raise "symlink is not a package input: #{current}" if current.symlink?
    end
    raise "missing local path: #{current}" unless current.exist?

    current
  end

  def self.check(path, root)
    source = local_path(path, root)
    raise "expected a regular file: #{source}" unless source.file?

    in_fence = false
    source.each_line do |line|
      in_fence = !in_fence if line.lstrip.start_with?("```", "~~~")
      next if in_fence

      line.scan(/\]\(([^)]+)\)/).each do |(target)|
        target = target.strip.sub(/\s+"[^"]*"\z/, "").delete_prefix("<").delete_suffix(">")
        next if target.match?(/\A(?:[a-z][a-z0-9+.-]*:|#)/i)

        relative = target.split("#", 2).first
        next if relative.nil? || relative.empty?

        local_path(source.dirname.join(relative), root)
      end
    end
  end
end

if $PROGRAM_NAME == __FILE__
  root = Pathname.new(ARGV.fetch(0)).expand_path
  Dir[root.join("**/*.md")].sort.each { |path| LocalReferences.check(Pathname.new(path), root) }
end
