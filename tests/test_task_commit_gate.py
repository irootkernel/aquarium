from __future__ import annotations

import json
import os
import shlex
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

    def configure_identity(
        self,
        repo: Path,
        *,
        name: str = "Repository User",
        email: str = "repository@example.invalid",
        scope: str = "--local",
    ) -> None:
        subprocess.run(
            ["git", "-C", repo, "config", scope, "user.name", name], check=True
        )
        subprocess.run(
            ["git", "-C", repo, "config", scope, "user.email", email], check=True
        )

    def run_hook(
        self, cwd: Path, command: str, env: dict[str, str] | None = None
    ) -> dict[str, Any] | None:
        payload = {"tool_input": {"command": command}, "cwd": str(cwd)}
        process_env = os.environ.copy()
        if env:
            process_env.update(env)
        result = subprocess.run(
            ["python3", HOOK],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=True,
            env=process_env,
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
        self.configure_identity(repo)
        result = self.run_hook(repo, "git commit -m 'work'")
        self.assert_denied(result)
        reason = result["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertNotIn("Configure the repository identity", reason)

    def test_gate_marker_allows_task_commit(self) -> None:
        repo = self.make_repo("TASK-1 | In Review\n")
        self.configure_identity(repo)
        result = self.run_hook(
            repo,
            "AQUARIUM_COMMIT_GATE=task-commit-v1 git commit -m 'work'",
        )
        self.assertIsNone(result)

    def test_gate_marker_rejects_global_only_identity(self) -> None:
        repo = self.make_repo("TASK-1 | In Review\n")
        global_config = repo / "global.gitconfig"
        global_config.write_text(
            "[user]\n\tname = Global User\n\temail = global@example.invalid\n",
            encoding="utf-8",
        )
        result = self.run_hook(
            repo,
            "AQUARIUM_COMMIT_GATE=task-commit-v1 git commit -m work",
            {"GIT_CONFIG_GLOBAL": str(global_config)},
        )
        self.assert_denied(result)
        reason = result["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("Configure the repository identity", reason)

    def test_gate_marker_rejects_command_scope_identity(self) -> None:
        repo = self.make_repo("TASK-1 | In Review\n")
        result = self.run_hook(
            repo,
            "AQUARIUM_COMMIT_GATE=task-commit-v1 git commit -m work",
            {
                "GIT_CONFIG_COUNT": "2",
                "GIT_CONFIG_KEY_0": "user.name",
                "GIT_CONFIG_VALUE_0": "Command User",
                "GIT_CONFIG_KEY_1": "user.email",
                "GIT_CONFIG_VALUE_1": "command@example.invalid",
            },
        )
        self.assert_denied(result)

    def test_gate_marker_rejects_partial_or_empty_local_identity(self) -> None:
        for key, value in (
            ("user.name", "Repository User"),
            ("user.email", "repository@example.invalid"),
            ("user.name", ""),
            ("user.email", ""),
        ):
            with self.subTest(key=key, value=value):
                repo = self.make_repo("TASK-1 | In Review\n")
                subprocess.run(
                    ["git", "-C", repo, "config", "--local", key, value],
                    check=True,
                )
                self.assert_denied(
                    self.run_hook(
                        repo,
                        "AQUARIUM_COMMIT_GATE=task-commit-v1 git commit -m work",
                    )
                )

    def test_gate_marker_allows_worktree_identity(self) -> None:
        repo = self.make_repo("TASK-1 | In Review\n")
        subprocess.run(
            ["git", "-C", repo, "config", "extensions.worktreeConfig", "true"],
            check=True,
        )
        self.configure_identity(repo, scope="--worktree")
        self.assertIsNone(
            self.run_hook(
                repo,
                "AQUARIUM_COMMIT_GATE=task-commit-v1 git commit -m work",
            )
        )

    def test_pinned_identity_ignores_environment_and_config_overrides(self) -> None:
        repo = self.make_repo("TASK-1 | In Review\n")
        expected_name = "Repository User"
        expected_email = "repository@example.invalid"
        self.configure_identity(repo, name=expected_name, email=expected_email)
        global_config = repo / "global.gitconfig"
        global_config.write_text(
            "[author]\n"
            "\tname = Wrong Config Author\n"
            "\temail = wrong-config-author@example.invalid\n"
            "[committer]\n"
            "\tname = Wrong Config Committer\n"
            "\temail = wrong-config-committer@example.invalid\n",
            encoding="utf-8",
        )
        command = " ".join(
            [
                "env",
                "-u GIT_AUTHOR_NAME",
                "-u GIT_AUTHOR_EMAIL",
                "-u GIT_COMMITTER_NAME",
                "-u GIT_COMMITTER_EMAIL",
                "AQUARIUM_COMMIT_GATE=task-commit-v1",
                "git",
                f"-c user.name={shlex.quote(expected_name)}",
                f"-c user.email={shlex.quote(expected_email)}",
                f"-c author.name={shlex.quote(expected_name)}",
                f"-c author.email={shlex.quote(expected_email)}",
                f"-c committer.name={shlex.quote(expected_name)}",
                f"-c committer.email={shlex.quote(expected_email)}",
                "commit -qm work",
            ]
        )
        self.assertIsNone(self.run_hook(repo, command))
        process_env = os.environ.copy()
        process_env.update(
            {
                "GIT_CONFIG_GLOBAL": str(global_config),
                "GIT_AUTHOR_NAME": "Wrong Author",
                "GIT_AUTHOR_EMAIL": "wrong-author@example.invalid",
                "GIT_COMMITTER_NAME": "Wrong Committer",
                "GIT_COMMITTER_EMAIL": "wrong-committer@example.invalid",
            }
        )
        subprocess.run(command, cwd=repo, shell=True, check=True, env=process_env)
        identity = (
            subprocess.run(
                ["git", "-C", repo, "show", "-s", "--format=%an%x00%ae%x00%cn%x00%ce"],
                check=True,
                stdout=subprocess.PIPE,
            )
            .stdout.rstrip(b"\n")
            .split(b"\0")
        )
        self.assertEqual(
            identity,
            [
                expected_name.encode(),
                expected_email.encode(),
                expected_name.encode(),
                expected_email.encode(),
            ],
        )

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

    def test_command_substitution_text_inside_heredoc_is_ignored(self) -> None:
        repo = self.make_repo("TASK-1 | Completed\n")
        command = "cat <<'EOF'\n$(git commit -m not-real)\nEOF\n"
        self.assertIsNone(self.run_hook(repo, command))

    def test_command_substitution_inside_expanding_heredoc_is_denied(self) -> None:
        repo = self.make_repo("TASK-1 | Completed\n")
        command = "cat <<EOF\n$(git commit -m real)\nEOF\n"
        self.assert_denied(self.run_hook(repo, command))

    def test_command_substitution_inside_backslash_quoted_heredoc_is_ignored(
        self,
    ) -> None:
        repo = self.make_repo("TASK-1 | Completed\n")
        command = "cat <<\\EOF\n$(git commit -m not-real)\nEOF\n"
        self.assertIsNone(self.run_hook(repo, command))

    def test_commit_after_mixed_quoted_heredoc_is_denied(self) -> None:
        repo = self.make_repo("TASK-1 | Completed\n")
        for marker in ('E"OF"', "'E'OF"):
            with self.subTest(marker=marker):
                command = f"cat <<{marker}\nnot a command\nEOF\ngit commit -m real\n"
                self.assert_denied(self.run_hook(repo, command))

    def test_commit_after_extended_quoted_heredoc_is_denied(self) -> None:
        repo = self.make_repo("TASK-1 | Completed\n")
        for marker, delimiter in (
            ('"E\\OF"', "E\\OF"),
            ("$'EOF'", "EOF"),
            ('$"EOF"', "EOF"),
        ):
            with self.subTest(marker=marker):
                command = (
                    f"cat <<{marker}\nnot a command\n{delimiter}\ngit commit -m real\n"
                )
                self.assert_denied(self.run_hook(repo, command))

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
        self.assert_denied(
            self.run_hook(repo, "cd definitely-missing || git commit -m work")
        )
        self.assertIsNone(self.run_hook(repo, "cd . || git commit -m work"))
        self.assertIsNone(
            self.run_hook(repo, "cd definitely-missing && echo skipped && git commit")
        )
        self.assertIsNone(self.run_hook(repo, "cd . || echo skipped || git commit"))

    def test_env_chdir_and_git_worktree_retargeting_are_resolved(self) -> None:
        repo = self.make_repo("TASK-1 | In Progress\n")
        outside = repo.parent

        self.assert_denied(self.run_hook(outside, f"env -C {repo} git commit -m work"))
        self.assert_denied(
            self.run_hook(outside, f"env -u LC_ALL -C {repo} git commit -m work")
        )
        self.assert_denied(
            self.run_hook(outside, f"env -P /usr/bin -C {repo} git commit -m work")
        )
        self.assert_denied(
            self.run_hook(outside, f"env -S 'git -C {repo} commit -m work'")
        )
        self.assert_denied(self.run_hook(outside, f"env -C{repo} git commit -m work"))
        self.assert_denied(self.run_hook(outside, f"env -iC{repo} git commit -m work"))
        self.assert_denied(
            self.run_hook(outside, f"env '-Sgit -C {repo} commit -m work'")
        )
        self.assert_denied(self.run_hook(repo, "exec git commit -m work"))
        self.assert_denied(self.run_hook(repo, "time git commit -m work"))
        for command in (
            "{ git commit -m work; }",
            "( git commit -m work )",
            "(git commit -m work)",
            "! git commit -m work",
            "if true; then git commit -m work; fi",
            "case x in x) git commit -m work;; esac",
            "case x in x)git commit -m work;;esac",
            "commit_now() { git commit -m work; }; commit_now",
            'f() { git commit -m work; }; echo "$(f)"',
            "function commit_now { git commit -m work; }; commit_now",
            "function commit_now() ( git commit -m work ); commit_now",
            "echo `git commit -m work`",
            "echo <(git commit -m work)",
            "diff <(command git commit -m $(echo work)) expected",
            r"echo `echo \`git commit -m work\``",
        ):
            with self.subTest(command=command):
                self.assert_denied(self.run_hook(repo, command))

        for command in (
            "case x in y) git commit -m work;; esac",
            "if false; then git commit -m work; fi",
            "while false; do git commit -m work; done",
            "until true; do git commit -m work; done",
            "commit_now() { git commit -m work; }",
            "function commit_now { git commit -m work; }",
            "echo '`git commit -m work`'",
            "echo '<(git commit -m work)'",
            'echo "<(git commit -m work)"',
            r"echo \`git commit -m work\`",
            r"echo \<\(git commit -m work\)",
        ):
            with self.subTest(command=command):
                self.assertIsNone(self.run_hook(repo, command))
        for command in (
            f"exec env -C {repo} git commit -m work",
            f"time env -C {repo} git commit -m work",
            f"nohup env -C {repo} git commit -m work",
            f"time command git -C {repo} commit -m work",
        ):
            with self.subTest(command=command):
                self.assert_denied(self.run_hook(outside, command))
        self.assert_denied(
            self.run_hook(
                outside,
                f"git --git-dir={repo / '.git'} --work-tree={repo} commit -m work",
            )
        )
        self.assert_denied(
            self.run_hook(
                outside,
                f"git --work-tree={repo.name} --git-dir={repo.name}/.git commit -m work",
            )
        )
        self.assert_denied(
            self.run_hook(
                outside,
                f"GIT_DIR={repo / '.git'} GIT_WORK_TREE={repo} git commit -m work",
            )
        )
        self.assert_denied(
            self.run_hook(
                outside,
                f"env GIT_DIR={repo / '.git'} GIT_WORK_TREE={repo} git commit -m work",
            )
        )
        self.assert_denied(
            self.run_hook(
                outside,
                f"env GIT_DIR={repo / '.git'} GIT_WORK_TREE={repo} env git commit",
            )
        )
        git_link = outside / "roadmap-git-link"
        git_link.symlink_to(repo / ".git")
        self.addCleanup(git_link.unlink)
        self.assert_denied(
            self.run_hook(outside, f"git --git-dir={git_link} commit -m work")
        )
        self.assert_denied(
            self.run_hook(outside, f"git -C {repo.name} --git-dir=.git commit -m work")
        )
        self.assert_denied(
            self.run_hook(outside, f"git -C {repo.name} --work-tree=. commit -m work")
        )

    def test_marker_text_outside_git_environment_does_not_bypass(self) -> None:
        repo = self.make_repo("TASK-1 | In Progress\n")
        command = "echo AQUARIUM_COMMIT_GATE=task-commit-v1; git commit -m work"
        self.assert_denied(self.run_hook(repo, command))

    def test_removed_or_overridden_gate_marker_does_not_bypass(self) -> None:
        repo = self.make_repo("TASK-1 | In Progress\n")
        for command in (
            "AQUARIUM_COMMIT_GATE=task-commit-v1 env -i git commit",
            "AQUARIUM_COMMIT_GATE=task-commit-v1 env -u AQUARIUM_COMMIT_GATE git commit",
            "AQUARIUM_COMMIT_GATE=task-commit-v1 env AQUARIUM_COMMIT_GATE=wrong git commit",
            "AQUARIUM_COMMIT_GATE=task-commit-v1 AQUARIUM_COMMIT_GATE=wrong git commit",
        ):
            with self.subTest(command=command):
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
