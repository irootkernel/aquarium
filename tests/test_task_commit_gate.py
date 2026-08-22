from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "plugins/aquarium/hooks/task_commit_gate.py"


class TaskCommitGateTests(unittest.TestCase):
    def make_repo(self, roadmap: str | None = None) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        repo = Path(temporary.name)
        subprocess.run(["git", "init", "-q", repo], check=True)
        (repo / "app.txt").write_text("content\n", encoding="utf-8")
        subprocess.run(["git", "-C", repo, "add", "app.txt"], check=True)
        if roadmap is not None:
            path = repo / "docs/product-roadmap.md"
            path.parent.mkdir()
            path.write_text(roadmap, encoding="utf-8")
            subprocess.run(
                ["git", "-C", repo, "add", "docs/product-roadmap.md"],
                check=True,
            )
        return repo

    def run_hook(self, cwd: Path, command: str) -> dict[str, Any] | None:
        payload = {"tool_input": {"command": command}, "cwd": str(cwd)}
        result = subprocess.run(
            ["python3", HOOK],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual(result.stderr, "")
        return json.loads(result.stdout) if result.stdout else None

    def assert_denied(self, result: dict[str, Any] | None) -> None:
        self.assertIsNotNone(result)
        output = result["hookSpecificOutput"]
        self.assertEqual(output["permissionDecision"], "deny")
        self.assertIn("$aquarium:task-commit", output["permissionDecisionReason"])

    def test_direct_commit_in_roadmap_repository_is_denied(self) -> None:
        repo = self.make_repo("TASK-1 | In Progress\n")
        self.assert_denied(self.run_hook(repo, "git commit -m 'work'"))

    def test_gate_marker_allows_task_commit(self) -> None:
        repo = self.make_repo("TASK-1 | In Review\n")
        result = self.run_hook(
            repo,
            "AQUARIUM_COMMIT_GATE=task-commit-v1 git commit -m 'work'",
        )
        self.assertIsNone(result)

    def test_repository_without_roadmap_is_untouched(self) -> None:
        repo = self.make_repo()
        self.assertIsNone(self.run_hook(repo, "git commit -m 'work'"))

    def test_roadmap_without_lifecycle_vocabulary_is_untouched(self) -> None:
        repo = self.make_repo("Ideas for later\n")
        self.assertIsNone(self.run_hook(repo, "git commit -m 'work'"))

    def test_lowercase_prose_is_not_lifecycle_evidence(self) -> None:
        repo = self.make_repo(
            "Milestones completed in 2024; blocked upstream work is discussed.\n"
        )
        self.assertIsNone(self.run_hook(repo, "git commit -m work"))

    def test_quoted_git_text_is_not_treated_as_a_commit(self) -> None:
        repo = self.make_repo("TASK-1 | Completed\n")
        self.assertIsNone(self.run_hook(repo, "echo 'git commit -m work'"))

    def test_multiline_commit_message_is_denied(self) -> None:
        repo = self.make_repo("TASK-1 | In Progress\n")
        self.assert_denied(self.run_hook(repo, 'git commit -m "subject\nbody"'))

    def test_quoted_heredoc_marker_in_multiline_message_is_not_masked(self) -> None:
        repo = self.make_repo("TASK-1 | In Progress\n")
        command = 'git commit -m "subject\n<<EOF\nbody\nEOF\nclosing"'
        self.assert_denied(self.run_hook(repo, command))

    def test_line_continued_commit_is_denied(self) -> None:
        repo = self.make_repo("TASK-1 | In Review\n")
        self.assert_denied(self.run_hook(repo, "git \\\ncommit -m work"))

    def test_commit_after_command_newline_is_denied(self) -> None:
        repo = self.make_repo("TASK-1 | Deferred\n")
        self.assert_denied(self.run_hook(repo, "echo ready\ngit commit -m work"))

    def test_commit_with_heredoc_message_is_denied(self) -> None:
        repo = self.make_repo("TASK-1 | Completed\n")
        command = "git commit -F - <<'EOF'\nsubject\nbody\nEOF\n"
        self.assert_denied(self.run_hook(repo, command))

    def test_git_commit_text_inside_heredoc_is_ignored(self) -> None:
        repo = self.make_repo("TASK-1 | Completed\n")
        command = "cat <<'EOF'\ngit commit -m not-real\nEOF\n"
        self.assertIsNone(self.run_hook(repo, command))

    def test_commit_after_heredoc_is_denied(self) -> None:
        repo = self.make_repo("TASK-1 | Completed\n")
        command = "cat <<'EOF'\nnot a command\nEOF\ngit commit -m real\n"
        self.assert_denied(self.run_hook(repo, command))

    def test_commit_prefix_before_lexical_error_is_denied(self) -> None:
        repo = self.make_repo("TASK-1 | Completed\n")
        self.assert_denied(self.run_hook(repo, 'git commit -m "unfinished'))

    def test_git_dash_c_and_cd_are_resolved(self) -> None:
        repo = self.make_repo("TASK-1 | Deferred\n")
        parent = repo.parent
        self.assert_denied(self.run_hook(parent, f"git -C {repo.name} commit -m work"))
        self.assert_denied(
            self.run_hook(parent, f"cd {repo.name} && git commit -m work")
        )

    def test_env_chdir_and_git_worktree_retargeting_are_resolved(self) -> None:
        repo = self.make_repo("TASK-1 | In Progress\n")
        outside = repo.parent

        self.assert_denied(self.run_hook(outside, f"env -C {repo} git commit -m work"))
        self.assert_denied(
            self.run_hook(
                outside,
                f"git --git-dir={repo / '.git'} --work-tree={repo} commit -m work",
            )
        )

    def test_marker_text_outside_git_environment_does_not_bypass(self) -> None:
        repo = self.make_repo("TASK-1 | In Progress\n")
        command = "echo AQUARIUM_COMMIT_GATE=task-commit-v1; git commit -m work"
        self.assert_denied(self.run_hook(repo, command))

    def test_tracked_roadmap_symlink_is_not_followed(self) -> None:
        repo = self.make_repo()
        external = tempfile.TemporaryDirectory()
        self.addCleanup(external.cleanup)
        target = Path(external.name) / "external-roadmap.md"
        target.write_text("TASK-1 | In Review\n", encoding="utf-8")
        symlink = repo / "roadmap.md"
        symlink.symlink_to(target)
        subprocess.run(["git", "-C", repo, "add", "roadmap.md"], check=True)
        self.assertIsNone(self.run_hook(repo, "git commit -m work"))


if __name__ == "__main__":
    unittest.main()
