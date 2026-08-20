from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins/aquarium/skills/dev-setup/scripts/inspect_tools.py"
MULGAE_MCP_FIXTURES = ROOT / "tests/fixtures/codex-mcp-get-mulgae.json"

sys.path.insert(0, str(SCRIPT.parent))

import inspect_tools


class InspectToolsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary_directory.name)
        self.repository = self.base / "repository"
        self.bin_directory = self.base / "bin"
        self.home = self.base / "home"
        self.codex_home = self.base / "codex"
        self.repository.mkdir()
        self.bin_directory.mkdir()
        self.home.mkdir()
        self.codex_home.mkdir()
        self.environment = os.environ.copy()
        self.environment.update(
            {
                "HOME": str(self.home),
                "CODEX_HOME": str(self.codex_home),
                "PATH": f"{self.bin_directory}:/usr/bin:/bin",
            }
        )
        self.git("init", "--quiet")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "Test User")
        (self.repository / "tracked.txt").write_text("initial\n", encoding="utf-8")
        self.git("add", "tracked.txt")
        self.git("commit", "--quiet", "-m", "Initial")

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def git(
        self, *arguments: str, check: bool = True
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *arguments],
            cwd=self.repository,
            env=self.environment,
            check=check,
            capture_output=True,
            text=True,
        )

    def run_script(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *arguments],
            env=self.environment,
            check=False,
            capture_output=True,
            text=True,
        )

    def inspect(
        self,
        repository: Path | None = None,
        timeout_seconds: float = 3.0,
        include_podway: bool = False,
        include_ouroboros: bool = False,
        require_mulgae_mcp: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        arguments = [
            "--repository",
            str(repository or self.repository),
            "--timeout-seconds",
            str(timeout_seconds),
        ]
        if include_podway:
            arguments.append("--include-podway")
        if include_ouroboros:
            arguments.append("--include-ouroboros")
        if require_mulgae_mcp:
            arguments.append("--require-mulgae-mcp")
        return self.run_script(*arguments)

    def mulgae_mcp_fixture(self, name: str) -> dict[str, object]:
        fixtures = json.loads(MULGAE_MCP_FIXTURES.read_text(encoding="utf-8"))
        replacements = {
            "<mulgae>": str(self.bin_directory / "mulgae"),
            "<repository>": str(self.repository),
            "<wrong-repository>": str(self.base / "wrong-repository"),
            "<wrong-command>": str(self.bin_directory / "wrong-mulgae"),
        }

        def replace(value: object) -> object:
            if isinstance(value, str):
                return replacements.get(value, value)
            if isinstance(value, list):
                return [replace(item) for item in value]
            if isinstance(value, dict):
                return {key: replace(item) for key, item in value.items()}
            return value

        result = replace(fixtures[name])
        self.assertIsInstance(result, dict)
        return result

    def install_fake_tools(
        self,
        malformed_sanho: bool = False,
        sanho_version: str = "v0.2.7",
        sanho_doctor_warnings: int = 0,
        mulgae_version: str = "v0.1.16",
        mulgae_output_schema: str = "mulgae-command-result.v4",
        mulgae_doctor_schema: str = "mulgae-doctor-result.v2",
        mulgae_doctor_case: str = "ready",
        mulgae_mcp_mode: str | None = None,
        go_version: str = "go1.26.6",
        gaori_version: str = "0.1.13",
        gaori_config_ok: bool = True,
        malformed_gaori_config: bool = False,
        slow_gaori_config: bool = False,
        gaori_mcp_mode: str | None = None,
        slow_gaori: bool = False,
        failing_mulgae_providers: bool = False,
        podway_version: str = "v0.2.5",
        podway_daemon_version: str = "0.2.5",
        podway_daemon_reachable: bool = True,
        podway_doctor_ok: bool = True,
        podway_active_session: bool = False,
        podway_prepared_session: bool = False,
        podway_procedure_ok: bool = True,
        podway_output_schema: str = "podway.output/v3",
        podway_status_result_schema: str = "podway.status-result/v3",
        podway_legacy_state: bool = False,
        ouroboros_version: str | None = None,
        ouroboros_version_ok: bool = True,
        ouroboros_codex_doctor_ok: bool = True,
        ouroboros_mcp_doctor_ok: bool = True,
        ouroboros_mcp_doctor_malformed: bool = False,
        ouroboros_mcp_mode: str | None = None,
    ) -> None:
        mulgae_mcp_fixture_names = {
            "configured": "required_true",
            "required-true": "required_true",
            "not-required": "required_false",
            "required-false": "required_false",
            "required-absent": "required_absent",
            "wrong-repo": "wrong_args",
            "wrong-args": "wrong_args",
            "wrong-cwd": "wrong_cwd",
            "disabled": "disabled",
            "non-stdio": "non_stdio",
            "missing-command": "wrong_command",
            "wrong-command": "wrong_command",
            "insufficient-timeout": "startup_timeout",
            "startup-timeout": "startup_timeout",
            "tool-timeout": "tool_timeout",
            "invalid-required": "invalid_required",
        }
        mulgae_mcp_result = (
            self.mulgae_mcp_fixture(mulgae_mcp_fixture_names[mulgae_mcp_mode])
            if mulgae_mcp_mode not in {None, "missing"}
            else None
        )
        source = textwrap.dedent(
            f"""\
            #!{sys.executable}
            import json
            import pathlib
            import subprocess
            import sys
            import time

            name = pathlib.Path(sys.argv[0]).name
            arguments = sys.argv[1:]
            if name == "go":
                if arguments == ["env", "-json", "GOVERSION", "GOOS", "GOARCH"]:
                    print(json.dumps({{"GOVERSION": {go_version!r}, "GOOS": "darwin", "GOARCH": "arm64"}}))
                    raise SystemExit(0)
                raise SystemExit(2)
            if name == "sanho":
                if arguments == ["version", "--json"]:
                    print("not-json" if {malformed_sanho!r} else json.dumps({{"name": "sanho", "version": {sanho_version!r}}}))
                    raise SystemExit(0)
                if arguments == ["status", "--json"]:
                    print(json.dumps({{
                        "project": "secret-project",
                        "workspace_id": "secret:/private/workspace",
                        "canonical": {{"publication_url": "git@example.invalid:private/docs.git"}},
                        "relation": {{"known": True, "behind": 1, "ahead": 0}},
                        "publication": {{"known": True, "pending": False}},
                        "sync_preview": {{"known": True, "clean": False, "conflicts": ["secret.md"]}},
                        "working_copy": {{"known": True, "docs_clean": True}},
                        "local_readiness": {{
                            "sync": {{"ready": True, "blocked_by": []}},
                            "pull": {{"ready": False, "blocked_by": ["local_docs_changed"]}},
                        }},
                        "sync_in_progress": False,
                    }}))
                    raise SystemExit(0)
                if arguments == ["doctor", "--json"]:
                    print(json.dumps({{
                        "workspace": "/private/workspace",
                        "checks": [{{"name": "hooks", "severity": "warning" if {sanho_doctor_warnings!r} else "ok", "detail": "secret detail /private/workspace"}}],
                        "warnings": {sanho_doctor_warnings!r},
                    }}))
                    raise SystemExit(0)
                print(json.dumps({{"state": "ready"}}))
                raise SystemExit(0)
            if name == "mulgae":
                if arguments == ["version", "--json"]:
                    print(json.dumps({{"name": "mulgae", "version": {mulgae_version!r}}}))
                    raise SystemExit(0)
                project_config = pathlib.Path.cwd() / ".mulgae/config.yaml"
                local_config = pathlib.Path.cwd() / ".mulgae/local.yaml"
                project_present = project_config.is_file()
                local_present = local_config.is_file()
                project_v3 = project_present and "version: 3" in project_config.read_text(encoding="utf-8")
                local_v3 = local_present and "version: 3" in local_config.read_text(encoding="utf-8")
                local_secure = local_present and local_config.stat().st_mode & 0o777 == 0o600
                local_tracked = local_present and subprocess.run(
                    ["git", "ls-files", "--error-unmatch", ".mulgae/local.yaml"],
                    check=False, capture_output=True, text=True,
                ).returncode == 0
                config_ready = project_v3 and local_v3 and local_secure and not local_tracked
                if arguments == ["doctor", "--output", "json"]:
                    doctor_case = "binary_missing" if {failing_mulgae_providers!r} else {mulgae_doctor_case!r}
                    diagnostic = lambda status, *reasons: {{"status": status, "reason_codes": list(reasons)}}
                    compatible = lambda status, eligibility, compatibility, reason, version="": {{
                        "status": status,
                        "observed_version": version,
                        "eligibility": eligibility,
                        "compatibility": compatibility,
                        "minimum_version": "0.15.2",
                        "verified_latest": "0.16.1",
                        "reason_code": reason,
                    }}
                    not_applicable_cli = compatible("not_applicable", "not_evaluated", "not_observed", "")
                    not_observed_row = lambda family: {{
                        "family": family, "configured": False, "referenced_by_roles": [],
                        "state": "not_observed", "reason": "config_not_ready",
                        "binary_available": diagnostic("not_applicable"),
                        "cli_compatible": not_applicable_cli,
                    }}
                    invalid_identity = doctor_case in {{"identity_invalid", "role_invalid"}} and project_present and local_present
                    schema_invalid = project_present and local_present and not (project_v3 and local_v3)
                    local_invalid = project_v3 and local_v3 and not config_ready
                    if not project_present:
                        config_reason = "config_missing"
                        config_status = "missing"
                        config_v3 = diagnostic("failed", config_reason)
                        local_configuration = diagnostic("not_applicable")
                        provider_identity = diagnostic("not_applicable")
                    elif not local_present:
                        config_reason = "local_config_missing"
                        config_status = "missing"
                        config_v3 = diagnostic("unverifiable", config_reason)
                        local_configuration = diagnostic("failed", config_reason)
                        provider_identity = diagnostic("unverifiable", config_reason)
                    elif invalid_identity:
                        config_reason = "config_provider_identity_invalid" if doctor_case == "identity_invalid" else "config_role_mapping_invalid"
                        config_status = "invalid"
                        config_v3 = diagnostic("failed", config_reason)
                        local_configuration = diagnostic("verified")
                        provider_identity = diagnostic("failed", config_reason)
                    elif schema_invalid:
                        config_reason = "config_yaml_invalid"
                        config_status = "invalid"
                        config_v3 = diagnostic("failed", config_reason)
                        local_configuration = diagnostic("verified")
                        provider_identity = diagnostic("unverifiable", config_reason)
                    elif local_invalid:
                        config_reason = "config_locality_unsafe"
                        config_status = "unsafe"
                        config_v3 = diagnostic("unverifiable", "config_not_observed_due_to_locality")
                        local_configuration = diagnostic("failed", config_reason)
                        provider_identity = diagnostic("not_applicable")
                    else:
                        config_reason = ""
                        config_status = "ready"
                        config_v3 = diagnostic("verified")
                        local_configuration = diagnostic("verified")
                        provider_identity = diagnostic("verified")

                    provider_issue = doctor_case if config_ready and not invalid_identity else ""
                    binary = diagnostic("verified")
                    cli = compatible("verified", "eligible", "verified", "provider_cli_version_supported", "0.16.1")
                    provider_state = "eligible"
                    provider_reason = "provider_cli_version_supported"
                    if provider_issue in {{"binary_missing", "binary_nonexecutable"}}:
                        provider_reason = "provider_executable_missing" if provider_issue == "binary_missing" else "provider_executable_not_executable"
                        binary = diagnostic("failed", provider_reason)
                        cli = not_applicable_cli
                        provider_state = "unavailable"
                    elif provider_issue in {{"cli_below", "cli_malformed", "cli_failure", "cli_timeout"}}:
                        details = {{
                            "cli_below": ("failed", "ineligible", "below_minimum", "provider_cli_version_below_minimum", "0.1.0"),
                            "cli_malformed": ("failed", "ineligible", "malformed", "provider_cli_version_malformed", ""),
                            "cli_failure": ("unverifiable", "not_evaluated", "not_observed", "provider_cli_version_command_failed", ""),
                            "cli_timeout": ("unverifiable", "not_evaluated", "not_observed", "provider_cli_version_timeout", ""),
                        }}[provider_issue]
                        cli = compatible(*details)
                        provider_state = "unavailable"
                        provider_reason = details[3]
                    elif provider_issue == "newer":
                        cli = compatible("verified", "eligible", "newer_than_verified", "provider_cli_version_newer_than_verified", "9.9.9")
                        provider_reason = "provider_cli_version_newer_than_verified"

                    config_observed = config_ready and not invalid_identity
                    if config_observed:
                        inventory = [
                            {{"family": "kimi", "configured": False, "referenced_by_roles": [], "state": "not_configured", "reason": "not_configured", "binary_available": diagnostic("not_applicable"), "cli_compatible": not_applicable_cli}},
                            {{"family": "zcode", "configured": True, "referenced_by_roles": ["logic"], "state": provider_state, "reason": provider_reason, "binary_available": binary, "cli_compatible": cli, "executable": "/private/zcode"}},
                            {{"family": "agy", "configured": False, "referenced_by_roles": [], "state": "not_configured", "reason": "not_configured", "binary_available": diagnostic("not_applicable"), "cli_compatible": not_applicable_cli}},
                            {{"family": "codex", "configured": False, "referenced_by_roles": [], "state": "not_configured", "reason": "not_configured", "binary_available": diagnostic("not_applicable"), "cli_compatible": not_applicable_cli, "credential_home": "/private/codex-home"}},
                        ]
                    else:
                        inventory = [not_observed_row(family) for family in ["kimi", "zcode", "agy", "codex"]]
                    ready = config_observed and provider_state == "eligible"
                    readiness_reason = "" if ready else "provider_offline_readiness_failed" if config_observed else config_reason
                    readiness_state = "ready" if ready else "unsafe" if config_status == "unsafe" else "unverified"
                    readiness_exit = 0 if ready else 8 if readiness_state == "unsafe" else 4
                    readiness = {{"state": readiness_state, "exit_code": readiness_exit, "reason_codes": [] if ready else [readiness_reason]}}
                    print(json.dumps({{
                        "schema_version": {mulgae_output_schema!r},
                        "request": {{"project_root": "/private/repository", "request_id": "secret-request"}},
                        "reasons": [] if ready else [{{"code": "readiness_unverified", "message": "secret detail /private/home"}}],
                        "result": {{
                            "kind": "diagnosed",
                            "readiness": readiness_state,
                            "doctor": {{
                                "schema_version": {mulgae_doctor_schema!r},
                                "config": {{
                                    "status": config_status,
                                    "uri": ".mulgae/config.yaml",
                                    "locality": "verified" if config_status in {{"ready", "missing", "invalid"}} and project_present else "rejected" if config_status == "unsafe" else "not_observed",
                                    "native_home_identity": "verified" if config_ready else "",
                                    "provenance_state": "accepted" if config_ready else "",
                                    "reason_codes": [] if config_status == "ready" else [config_reason],
                                    "sha256": "secret-digest",
                                }},
                                "config_v3": config_v3,
                                "local_configuration": local_configuration,
                                "provider_identity": provider_identity,
                                "configured_provider_ids": ["zcode"] if config_observed else [],
                                "provider_inventory": inventory,
                                "assignment": {{"state": "ready" if ready else "unavailable" if config_observed else "not_observed", "resilience": "ready" if ready else "unavailable" if config_observed else "not_observed"}},
                                "readiness": readiness,
                                "configured_readiness": readiness,
                                "role_route_readiness": readiness,
                                "platform_evidence": [{{"cell": "darwin-arm64", "native": True}}],
                                "diagnostics": [{{"message": "secret detail /private/home"}}],
                                "provider_stdout": "secret complete stdout",
                                "provider_stderr": "secret complete stderr",
                            }},
                        }},
                    }}))
                    raise SystemExit(readiness_exit)
                raise SystemExit(2)
            if name == "gaori":
                if arguments == ["version", "--json"]:
                    if {slow_gaori!r}:
                        time.sleep(4)
                    print(json.dumps({{"name": "gaori", "version": {gaori_version!r}}}))
                    raise SystemExit(0)
                if arguments == ["--json", "config", "check"]:
                    if {slow_gaori_config!r}:
                        time.sleep(4)
                    print("not-json" if {malformed_gaori_config!r} else json.dumps({{"schema_version": 2, "commands": ["unit"], "rules": {{"active": 0}}}}))
                    raise SystemExit(0 if {gaori_config_ok!r} else 2)
                raise SystemExit(2)
            if name == "ooo":
                if arguments == ["--version"]:
                    print("Ouroboros version " + {ouroboros_version!r})
                    raise SystemExit(0 if {ouroboros_version_ok!r} else 1)
                if arguments == ["codex", "doctor"]:
                    print("Codex integration OK" if {ouroboros_codex_doctor_ok!r} else "Codex integration degraded")
                    raise SystemExit(0 if {ouroboros_codex_doctor_ok!r} else 1)
                if arguments == ["mcp", "doctor", "--json"]:
                    print("not-json" if {ouroboros_mcp_doctor_malformed!r} else json.dumps([{{"name": "runtime", "status": "pass" if {ouroboros_mcp_doctor_ok!r} else "fail"}}]))
                    raise SystemExit(0 if {ouroboros_mcp_doctor_ok!r} else 1)
                raise SystemExit(2)
            if name == "codex":
                if arguments == ["--version"]:
                    print("codex-cli 0.147.0")
                    raise SystemExit(0)
                if len(arguments) != 4 or arguments[:2] != ["mcp", "get"] or arguments[3] != "--json":
                    raise SystemExit(2)
                server = arguments[2]
                mode = (
                    {mulgae_mcp_mode!r}
                    if server == "mulgae"
                    else {gaori_mcp_mode!r}
                    if server == "gaori"
                    else {ouroboros_mcp_mode!r}
                )
                if mode == "missing":
                    print(f"Error: No MCP server named '{{server}}' found.", file=sys.stderr)
                    raise SystemExit(1)
                if mode == "timeout":
                    time.sleep(4)
                if mode == "probe-failure":
                    print("secret registration failure", file=sys.stderr)
                    raise SystemExit(2)
                repository = {str(self.repository)!r} if mode != "wrong-repo" else "/tmp/wrong-repo"
                if server == "mulgae":
                    print(json.dumps({mulgae_mcp_result!r}))
                    raise SystemExit(0)
                if server == "ouroboros":
                    if mode == "malformed":
                        print("not-json")
                        raise SystemExit(0)
                    result = {{"name": "ouroboros", "transport": {{"type": "stdio", "command": "ooo", "args": ["mcp", "serve"]}}}}
                    if mode != "enabled-absent":
                        result["enabled"] = "yes" if mode == "enabled-invalid" else mode != "disabled"
                    print(json.dumps(result))
                    raise SystemExit(0)
                print(json.dumps({{
                    "name": "gaori",
                    "enabled": mode != "disabled",
                    "transport": {{
                        "type": "http" if mode == "non-stdio" else "stdio",
                        "command": "/tmp/missing-gaori" if mode == "missing-command" else {str(self.bin_directory / "gaori")!r},
                        "args": ["--repo", repository, "mcp"],
                        "env": {{"SECRET_TOKEN": "must-not-leak"}},
                        "env_vars": [],
                        "cwd": None,
                    }},
                    "tool_timeout_sec": 60,
                }}))
                raise SystemExit(0)
            if name == "podway":
                if arguments == ["version", "--json"]:
                    print(json.dumps({{"name": "podway", "version": {podway_version!r}}}))
                    raise SystemExit(0)
                if arguments == ["daemon", "status", "--json"]:
                    print(json.dumps({{"schema": {podway_output_schema!r}, "command": "daemon.status", "result": {{"schema": "podway.daemon-status-result/v1", "installed": True, "loaded": True, "reachable": {podway_daemon_reachable!r}, "status": "running", "daemon_version": {podway_daemon_version!r}, "target": "aarch64-apple-darwin", "contract_manifest_schema": "podway.contract-manifest/v1", "contract_manifest_digest": "sha256:test"}}}}))
                    raise SystemExit(0 if {podway_daemon_reachable!r} else 1)
                if arguments == ["doctor", "--json"]:
                    if {podway_legacy_state!r}:
                        print(json.dumps(dict(schema="podway.error/v1", command="workspace.doctor", code="LEGACY_PROCEDURE_STATE_UNSUPPORTED")))
                        raise SystemExit(5)
                    print(json.dumps(dict(schema={podway_output_schema!r}, command="workspace.doctor", result=dict(healthy={podway_doctor_ok!r}))))
                    raise SystemExit(0 if {podway_doctor_ok!r} else 1)
                if arguments == ["--json", "status"]:
                    if {podway_legacy_state!r}:
                        print(json.dumps(dict(schema="podway.error/v1", command="session.status", code="LEGACY_PROCEDURE_STATE_UNSUPPORTED")))
                        raise SystemExit(5)
                    if {podway_active_session!r}:
                        status = dict(
                            schema={podway_status_result_schema!r},
                            procedure=dict(schema="podway.procedure/v2", id="aquarium-task-v2", version="1", digest="sha256:procedure"),
                            session=dict(id="00000000-0000-4000-8000-000000000001", lifecycle="prepared" if {podway_prepared_session!r} else "running", revision=0 if {podway_prepared_session!r} else 7),
                            current=None if {podway_prepared_session!r} else dict(node=dict(graph_node_id="verify")),
                            item_values=[] if {podway_prepared_session!r} else [dict(value="sensitive evidence")],
                        )
                        if not {podway_prepared_session!r}:
                            status.update(goal_revision=2, goal=dict(statement="sensitive goal text"))
                        print(json.dumps(dict(schema={podway_output_schema!r}, command="session.status", result=status)))
                        raise SystemExit(0)
                    print(json.dumps({{"schema": "podway.error/v1", "command": "session.status", "code": "SESSION_NOT_FOUND", "retryable": False, "exit_code": 1, "details": {{}}}}))
                    raise SystemExit(1)
                if arguments[:4] == ["--json", "procedure", "check", "--warnings-as-errors"]:
                    print(json.dumps({{"schema": {podway_output_schema!r}, "command": "procedure.check", "result": {{"schema": "podway.procedure-diagnostics-result/v1", "valid": {podway_procedure_ok!r}, "digest": "sha256:procedure"}}}}))
                    raise SystemExit(0 if {podway_procedure_ok!r} else 1)
                raise SystemExit(2)
            raise SystemExit(2)
            """
        )
        names = ["go", "sanho", "mulgae", "gaori", "podway"]
        if ouroboros_version is not None:
            names.append("ooo")
        if (
            gaori_mcp_mode is not None
            or mulgae_mcp_mode is not None
            or ouroboros_mcp_mode is not None
        ):
            names.append("codex")
        for name in names:
            executable = self.bin_directory / name
            executable.write_text(source, encoding="utf-8")
            executable.chmod(0o755)

    def install_lora_skill(self, name: str) -> None:
        skill_directory = self.codex_home / "skills" / name
        skill_directory.mkdir(parents=True)
        skill_directory.joinpath("SKILL.md").write_text(
            f"---\nname: {name}\ndescription: Test skill.\n---\n", encoding="utf-8"
        )

    def install_agent_skill(
        self,
        skill_name: str,
        root: Path | None = None,
        complete: bool = True,
        frontmatter_name: str | None = None,
    ) -> None:
        skill_directory = (root or self.codex_home / "skills") / skill_name
        skill_directory.joinpath("references").mkdir(parents=True)
        skill_directory.joinpath("SKILL.md").write_text(
            f"---\nname: {frontmatter_name or skill_name}\ndescription: Test skill.\n---\n",
            encoding="utf-8",
        )
        references = ("lifecycle", "authoring", "recovery") if complete else ("lifecycle",)
        for reference in references:
            skill_directory.joinpath("references", f"{reference}.md").write_text(
                f"# {reference}\n", encoding="utf-8"
            )

    def install_sanho_skill(
        self, root: Path | None = None, complete: bool = True, name: str = "use-sanho"
    ) -> None:
        self.install_agent_skill(
            "use-sanho", root=root, complete=complete, frontmatter_name=name
        )

    def install_gaori_skill(
        self, root: Path | None = None, complete: bool = True, name: str = "use-gaori"
    ) -> None:
        self.install_agent_skill(
            "use-gaori", root=root, complete=complete, frontmatter_name=name
        )

    def install_mulgae_skill(
        self, root: Path | None = None, complete: bool = True, name: str = "use-mulgae"
    ) -> None:
        self.install_agent_skill(
            "use-mulgae", root=root, complete=complete, frontmatter_name=name
        )

    def install_podway_skill(
        self, root: Path | None = None, complete: bool = True, name: str = "use-podway"
    ) -> None:
        self.install_agent_skill(
            "use-podway", root=root, complete=complete, frontmatter_name=name
        )

    def install_mulgae_config(
        self, local_mode: int = 0o600, track_local: bool = False
    ) -> None:
        self.repository.joinpath(".mulgae").mkdir(exist_ok=True)
        self.repository.joinpath(".mulgae/config.yaml").write_text(
            'version: 3\nexecution:\n  workspace_access: "none"\n', encoding="utf-8"
        )
        self.repository.joinpath(".mulgae/local.yaml").write_text(
            "version: 3\n", encoding="utf-8"
        )
        self.repository.joinpath(".mulgae/local.yaml").chmod(local_mode)
        self.repository.joinpath(".gitignore").write_text(
            "/.mulgae/*\n!/.mulgae/config.yaml\n", encoding="utf-8"
        )
        if track_local:
            self.git("add", "-f", ".mulgae/local.yaml")

    def install_managed_podway_procedures(self, tracked: bool = True) -> None:
        source = ROOT / "plugins/aquarium/assets/podway/procedures"
        target = self.repository / ".podway/procedures"
        target.mkdir(parents=True, exist_ok=True)
        self.repository.joinpath(".podway/config.yaml").write_text(
            "schema: podway.workspace/v1\n", encoding="utf-8"
        )
        self.repository.joinpath(".podway/.gitignore").write_text(
            "runtime/\n", encoding="utf-8"
        )
        for procedure in source.glob("*.yaml"):
            shutil.copyfile(procedure, target / procedure.name)
        if tracked:
            self.git(
                "add",
                ".podway/config.yaml",
                ".podway/.gitignore",
                ".podway/procedures",
            )

    def test_missing_tools_are_a_successful_inventory_and_do_not_mutate_repository(
        self,
    ) -> None:
        before = self.git("status", "--porcelain=v1").stdout
        completed = self.inspect()
        after = self.git("status", "--porcelain=v1").stdout
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stderr, "")
        self.assertEqual(before, after)
        payload = json.loads(completed.stdout)
        self.assertEqual(
            payload["schema_version"], "aquarium-dev-setup-inspection.v5"
        )
        self.assertEqual(
            payload["repository"]["worktree"],
            {"conflicted": 0, "staged": 0, "unstaged": 0, "untracked": 0},
        )
        self.assertEqual(payload["tools"]["sanho"]["status"], "missing")
        self.assertEqual(payload["tools"]["sanho"]["agent_skill"]["status"], "missing")
        self.assertEqual(payload["tools"]["mulgae"]["status"], "missing")
        self.assertEqual(payload["tools"]["mulgae"]["agent_skill"]["status"], "missing")
        self.assertEqual(payload["tools"]["mulgae"]["mcp_registration"]["status"], "unavailable")
        self.assertEqual(payload["tools"]["gaori"]["agent_skill"]["status"], "missing")
        self.assertEqual(payload["tools"]["gaori"]["mcp_registration"]["status"], "unavailable")
        self.assertEqual(payload["tools"]["lora"]["status"], "missing")
        self.assertNotIn("podway", payload["tools"])

    def test_configured_tools_are_normalized_without_config_contents(self) -> None:
        self.install_fake_tools()
        self.repository.joinpath(".sanho.json").write_text(
            "secret-value\n", encoding="utf-8"
        )
        self.repository.joinpath(".sanho_base.json").write_text(
            "{}\n", encoding="utf-8"
        )
        self.repository.joinpath(".mulgae").mkdir()
        self.repository.joinpath(".mulgae/config.yaml").write_text(
            'version: 3\nexecution:\n  workspace_access: "none"\ncredential: hidden\n', encoding="utf-8"
        )
        self.repository.joinpath(".mulgae/local.yaml").write_text(
            "version: 3\nnative_home: /private/home\n", encoding="utf-8"
        )
        self.repository.joinpath(".mulgae/local.yaml").chmod(0o600)
        self.repository.joinpath(".gaori").mkdir()
        self.repository.joinpath(".gaori/tester.yaml").write_text(
            "schema_version: 2\n", encoding="utf-8"
        )
        self.repository.joinpath(".gaori/tester/rules").mkdir(parents=True)
        self.repository.joinpath(".gaori/tester/rules/generic-v1.yaml").write_text(
            "id: generic-v1\n", encoding="utf-8"
        )
        self.repository.joinpath(".gitignore").write_text(
            ".sanho.json\n.sanho_base.json\n/.mulgae/*\n!/.mulgae/config.yaml\n"
            ".gaori/*\n!.gaori/tester.yaml\n!.gaori/tester/\n"
            ".gaori/tester/*\n!.gaori/tester/rules/\n"
            ".gaori/tester/rules/*\n!.gaori/tester/rules/*.yaml\n",
            encoding="utf-8",
        )
        for name in ("lore-commits", "lore-query", "lore-setup"):
            self.install_lora_skill(name)
        completed = self.inspect()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertNotIn("secret-value", completed.stdout)
        self.assertNotIn("credential: hidden", completed.stdout)
        tools = json.loads(completed.stdout)["tools"]
        self.assertEqual(tools["sanho"]["version"], "v0.2.7")
        self.assertTrue(tools["sanho"]["version_supported"])
        self.assertEqual(tools["sanho"]["status"], "configured")
        self.assertEqual(tools["sanho"]["agent_skill"]["status"], "missing")
        self.assertNotIn("secret-project", completed.stdout)
        self.assertNotIn("git@example.invalid", completed.stdout)
        self.assertNotIn("secret detail", completed.stdout)
        self.assertNotIn("secret complete stdout", completed.stdout)
        self.assertNotIn("secret complete stderr", completed.stdout)
        self.assertNotIn("/private/codex-home", completed.stdout)
        self.assertNotIn("/private/personal", completed.stdout)
        self.assertNotIn("/private/work", completed.stdout)
        self.assertEqual(
            tools["sanho"]["probes"]["status"]["result"]["sync_preview"]["conflict_count"],
            1,
        )
        self.assertEqual(tools["mulgae"]["version"], "v0.1.16")
        self.assertTrue(tools["mulgae"]["version_supported"])
        expected_mulgae_status = (
            "configured"
            if platform.system() == "Darwin" and platform.machine() in {"arm64", "aarch64"}
            else "degraded"
        )
        self.assertEqual(tools["mulgae"]["status"], expected_mulgae_status)
        self.assertEqual(tools["mulgae"]["agent_skill"]["status"], "missing")
        self.assertEqual(tools["mulgae"]["mcp_registration"]["status"], "unavailable")
        mulgae_configuration = {
            entry["path"]: entry for entry in tools["mulgae"]["configuration"]
        }
        self.assertFalse(mulgae_configuration[".mulgae/config.yaml"]["ignored"])
        self.assertTrue(mulgae_configuration[".mulgae/local.yaml"]["ignored"])
        self.assertTrue(mulgae_configuration[".mulgae/local.yaml"]["mode_0600"])
        self.assertTrue(mulgae_configuration[".mulgae/runtime/"]["ignored"])
        self.assertEqual(set(tools["mulgae"]["probes"]), {"version", "doctor"})
        self.assertEqual(
            tools["mulgae"]["health"]["configured_readiness"]["state"], "ready"
        )
        self.assertEqual(
            tools["mulgae"]["health"]["config_v3"]["status"], "verified"
        )
        zcode = tools["mulgae"]["provider_inventory"][1]
        self.assertEqual(zcode["binary_available"]["status"], "verified")
        self.assertEqual(zcode["cli_compatible"]["eligibility"], "eligible")
        self.assertEqual(tools["gaori"]["version"], "0.1.13")
        self.assertTrue(tools["gaori"]["version_supported"])
        self.assertEqual(tools["gaori"]["status"], "configured")
        self.assertEqual(tools["gaori"]["agent_skill"]["status"], "missing")
        self.assertEqual(tools["gaori"]["mcp_registration"]["status"], "unavailable")
        self.assertTrue(tools["gaori"]["probes"]["config_check"]["ok"])
        gaori_configuration = {
            entry["path"]: entry for entry in tools["gaori"]["configuration"]
        }
        self.assertFalse(gaori_configuration[".gaori/tester.yaml"]["ignored"])
        self.assertFalse(gaori_configuration[".gaori/tester/rules/"]["ignored"])
        self.assertTrue(gaori_configuration[".gaori/toolchain.yaml"]["ignored"])
        self.assertEqual(tools["lora"]["status"], "configured")
        self.assertTrue(tools["lora"]["lore_setup_present"])
    def test_matching_managed_procedures_are_ready_only_on_supported_platform(
        self,
    ) -> None:
        self.install_fake_tools()
        self.install_managed_podway_procedures()
        completed = self.inspect(include_podway=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        podway = json.loads(completed.stdout)["tools"]["podway"]
        platform_supported = platform.system() == "Darwin" and platform.machine() in {
            "arm64",
            "aarch64",
        }
        self.assertTrue(all(item["matches_source"] for item in podway["managed_procedures"]))
        self.assertEqual(
            podway["readiness_status"],
            "ready" if platform_supported else "degraded",
        )
        self.assertEqual(
            podway["status"], "configured" if platform_supported else "degraded"
        )

    def test_session_not_found_is_ready_in_an_initialized_workspace(self) -> None:
        self.install_fake_tools()
        self.install_managed_podway_procedures()
        with (
            mock.patch.dict(os.environ, self.environment),
            mock.patch("inspect_tools.platform.system", return_value="Darwin"),
            mock.patch("inspect_tools.platform.machine", return_value="arm64"),
        ):
            podway = inspect_tools.inspect_podway(self.repository.resolve(), 3.0)
        self.assertEqual(
            podway["probes"]["session_status"],
            {
                "attempted": True,
                "ok": False,
                "exit_code": 1,
                "timed_out": False,
                "error_code": "SESSION_NOT_FOUND",
                "output_schema": "podway.error/v1",
            },
        )
        self.assertEqual(podway["readiness_status"], "ready")
        self.assertEqual(podway["status"], "configured")

    def test_managed_procedure_checks_report_validity_and_digest(self) -> None:
        self.install_fake_tools()
        self.install_managed_podway_procedures()
        completed = self.inspect(include_podway=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        managed = json.loads(completed.stdout)["tools"]["podway"]["managed_procedures"]
        self.assertEqual(
            [entry["path"] for entry in managed],
            [
                ".podway/procedures/aquarium-task-v2.yaml",
                ".podway/procedures/aquarium-goal-v2.yaml",
                ".podway/procedures/aquarium-validation-v2.yaml",
                ".podway/procedures/aquarium-design-v2.yaml",
                ".podway/procedures/aquarium-war-room-v2.yaml",
            ],
        )
        for entry in managed:
            with self.subTest(path=entry["path"]):
                self.assertEqual(
                    entry["check"],
                    {
                        "attempted": True,
                        "ok": True,
                        "exit_code": 0,
                        "timed_out": False,
                        "output_schema": "podway.output/v3",
                        "result_schema": "podway.procedure-diagnostics-result/v1",
                        "valid": True,
                        "digest": "sha256:procedure",
                    },
                )

    def test_partial_or_drifted_managed_procedures_are_degraded(self) -> None:
        self.install_fake_tools()
        self.install_managed_podway_procedures()
        managed = self.repository / ".podway/procedures"
        managed.joinpath("aquarium-task-v2.yaml").write_text(
            "schema: drifted\n", encoding="utf-8"
        )
        managed.joinpath("aquarium-goal-v2.yaml").unlink()
        completed = self.inspect(include_podway=True)
        podway = json.loads(completed.stdout)["tools"]["podway"]
        self.assertEqual(podway["readiness_status"], "degraded")
        self.assertEqual(podway["status"], "degraded")

    def test_renamed_managed_procedures_require_explicit_migration(self) -> None:
        self.install_fake_tools()
        self.install_managed_podway_procedures()
        legacy = self.repository / ".podway/procedures/root-kernel-task-v2.yaml"
        legacy.write_text("schema: podway.procedure/v2\n", encoding="utf-8")
        completed = self.inspect(include_podway=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        podway = json.loads(completed.stdout)["tools"]["podway"]
        self.assertTrue(podway["migration_required"])
        self.assertEqual(podway["readiness_status"], "degraded")
        self.assertEqual(podway["status"], "degraded")
        self.assertEqual(
            [
                entry["path"]
                for entry in podway["legacy_managed_procedures"]
                if entry["present"]
            ],
            [".podway/procedures/root-kernel-task-v2.yaml"],
        )

    def test_managed_procedures_without_initialized_workspace_are_degraded(self) -> None:
        self.install_fake_tools()
        source = ROOT / "plugins/aquarium/assets/podway/procedures"
        target = self.repository / ".podway/procedures"
        target.mkdir(parents=True)
        for procedure in source.glob("*.yaml"):
            shutil.copyfile(procedure, target / procedure.name)
        completed = self.inspect(include_podway=True)
        podway = json.loads(completed.stdout)["tools"]["podway"]
        self.assertEqual(podway["readiness_status"], "degraded")
        self.assertEqual(podway["status"], "degraded")

    def test_unsupported_or_mixed_podway_versions_are_degraded(self) -> None:
        self.install_fake_tools(
            podway_version="v0.3.0", podway_daemon_version="0.2.7"
        )
        self.install_managed_podway_procedures()
        completed = self.inspect(include_podway=True)
        podway = json.loads(completed.stdout)["tools"]["podway"]
        self.assertFalse(podway["version_supported"])
        self.assertFalse(podway["versions_match"])
        self.assertEqual(podway["readiness_status"], "degraded")

    def test_podway_v025_is_the_minimum_supported_release(self) -> None:
        for version, supported in (
            ("v0.2.0", False),
            ("v0.2.2", False),
            ("v0.2.3", False),
            ("v0.2.4", False),
            ("v0.2.5", True),
            ("v0.2.5-rc.1", False),
            ("0.2.99", True),
            ("v0.3.0", False),
        ):
            with self.subTest(version=version):
                for executable in self.bin_directory.iterdir():
                    executable.unlink()
                self.install_fake_tools(
                    podway_version=version,
                    podway_daemon_version=version.removeprefix("v"),
                )
                with (
                    mock.patch.dict(os.environ, self.environment),
                    mock.patch("inspect_tools.platform.system", return_value="Darwin"),
                    mock.patch("inspect_tools.platform.machine", return_value="arm64"),
                ):
                    podway = inspect_tools.inspect_podway(
                        self.repository.resolve(), 3.0
                    )
                self.assertEqual(podway["version_supported"], supported)
                self.assertEqual(
                    podway["status"], "installed" if supported else "degraded"
                )

    def test_podway_requires_v3_envelopes_and_v3_session_results(self) -> None:
        cases = (
            {"podway_output_schema": "podway.output/v2"},
            {
                "podway_active_session": True,
                "podway_status_result_schema": "podway.status-result/v2",
            },
        )
        for options in cases:
            with self.subTest(options=options):
                for executable in self.bin_directory.iterdir():
                    executable.unlink()
                self.install_fake_tools(**options)
                self.install_managed_podway_procedures()
                with (
                    mock.patch.dict(os.environ, self.environment),
                    mock.patch("inspect_tools.platform.system", return_value="Darwin"),
                    mock.patch("inspect_tools.platform.machine", return_value="arm64"),
                ):
                    podway = inspect_tools.inspect_podway(
                        self.repository.resolve(), 3.0
                    )
                self.assertEqual(podway["readiness_status"], "degraded")
                self.assertEqual(podway["status"], "degraded")

    def test_legacy_procedure_state_is_reported_without_recovery_mutation(self) -> None:
        self.install_fake_tools(podway_legacy_state=True)
        self.install_managed_podway_procedures()
        with (
            mock.patch.dict(os.environ, self.environment),
            mock.patch("inspect_tools.platform.system", return_value="Darwin"),
            mock.patch("inspect_tools.platform.machine", return_value="arm64"),
        ):
            podway = inspect_tools.inspect_podway(self.repository.resolve(), 3.0)
        self.assertTrue(podway["legacy_state_detected"])
        self.assertEqual(
            podway["probes"]["doctor"]["error_code"],
            "LEGACY_PROCEDURE_STATE_UNSUPPORTED",
        )
        self.assertEqual(podway["readiness_status"], "degraded")

    def test_podway_skill_is_independent_from_cli_and_readiness(self) -> None:
        self.install_fake_tools()
        self.install_managed_podway_procedures()
        self.install_podway_skill(root=self.home / ".agents/skills")
        with (
            mock.patch.dict(os.environ, self.environment),
            mock.patch("inspect_tools.platform.system", return_value="Darwin"),
            mock.patch("inspect_tools.platform.machine", return_value="arm64"),
        ):
            podway = inspect_tools.inspect_podway(self.repository.resolve(), 3.0)
        self.assertEqual(podway["status"], "configured")
        self.assertEqual(podway["agent_skill"]["status"], "configured")
        installation = podway["agent_skill"]["installations"][0]
        self.assertTrue(installation["frontmatter_valid"])
        self.assertTrue(all(item["present"] for item in installation["files"]))

    def test_partial_invalid_or_duplicate_podway_skills_are_degraded(self) -> None:
        for case in ("partial", "invalid", "duplicate"):
            with self.subTest(case=case):
                for root in (self.codex_home / "skills", self.home / ".agents/skills"):
                    shutil.rmtree(root / "use-podway", ignore_errors=True)
                if case == "partial":
                    self.install_podway_skill(complete=False)
                elif case == "invalid":
                    self.install_podway_skill(name="wrong-name")
                else:
                    self.install_podway_skill()
                    self.install_podway_skill(root=self.home / ".agents/skills")
                podway = json.loads(
                    self.inspect(include_podway=True).stdout
                )["tools"]["podway"]
                self.assertEqual(podway["agent_skill"]["status"], "degraded")
                self.assertEqual(podway["readiness_status"], "not_configured")
                self.assertEqual(podway["agent_skill"]["duplicate"], case == "duplicate")

    def test_unhealthy_daemon_doctor_or_procedure_is_degraded(self) -> None:
        cases = (
            {"podway_daemon_reachable": False},
            {"podway_doctor_ok": False},
            {"podway_procedure_ok": False},
        )
        for options in cases:
            with self.subTest(options=options):
                for executable in self.bin_directory.iterdir():
                    executable.unlink()
                self.install_fake_tools(**options)
                self.install_managed_podway_procedures()
                completed = self.inspect(include_podway=True)
                podway = json.loads(completed.stdout)["tools"]["podway"]
                self.assertEqual(podway["readiness_status"], "degraded")
                self.assertEqual(podway["status"], "degraded")

    def test_active_session_inventory_exposes_identity_without_evidence(self) -> None:
        self.install_fake_tools(podway_active_session=True)
        self.install_managed_podway_procedures()
        completed = self.inspect(include_podway=True)
        podway = json.loads(completed.stdout)["tools"]["podway"]
        session = podway["probes"]["session_status"]["result"]
        self.assertEqual(session["procedure"]["id"], "aquarium-task-v2")
        self.assertEqual(session["current_graph_node_id"], "verify")
        self.assertEqual(session["goal_revision"], 2)
        self.assertNotIn("sensitive goal text", completed.stdout)
        self.assertNotIn("sensitive evidence", completed.stdout)

    def test_prepared_session_inventory_has_no_cursor_or_goal(self) -> None:
        self.install_fake_tools(
            podway_active_session=True,
            podway_prepared_session=True,
        )
        self.install_managed_podway_procedures()
        with (
            mock.patch.dict(os.environ, self.environment),
            mock.patch("inspect_tools.platform.system", return_value="Darwin"),
            mock.patch("inspect_tools.platform.machine", return_value="arm64"),
        ):
            podway = inspect_tools.inspect_podway(self.repository.resolve(), 3.0)
        session = podway["probes"]["session_status"]["result"]
        self.assertEqual(
            session["session"],
            {
                "id": "00000000-0000-4000-8000-000000000001",
                "lifecycle": "prepared",
                "revision": 0,
            },
        )
        self.assertIsNone(session["current_graph_node_id"])
        self.assertIsNone(session["goal_revision"])
        self.assertEqual(podway["readiness_status"], "ready")

    def test_malformed_json_and_timeout_degrade_only_the_affected_probes(self) -> None:
        self.install_fake_tools(
            malformed_sanho=True, slow_gaori=True, failing_mulgae_providers=True
        )
        completed = self.inspect(timeout_seconds=3.5)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        tools = json.loads(completed.stdout)["tools"]
        self.assertEqual(
            tools["sanho"]["probes"]["version"]["error_code"], "invalid_json"
        )
        self.assertIsNone(tools["sanho"]["version"])
        self.assertEqual(tools["sanho"]["status"], "degraded")
        self.assertTrue(tools["gaori"]["probes"]["version"]["timed_out"])
        self.assertIsNone(tools["gaori"]["version"])
        self.assertEqual(tools["gaori"]["status"], "degraded")
        self.assertEqual(tools["mulgae"]["version"], "v0.1.16")
        self.assertFalse(tools["mulgae"]["probes"]["doctor"]["ok"])
        self.assertEqual(tools["mulgae"]["probes"]["doctor"]["exit_code"], 4)
        self.assertEqual(
            tools["mulgae"]["health"]["config_v3"]["reason_codes"],
            ["config_missing"],
        )

    def test_sanho_version_support_and_doctor_warnings_are_explicit(self) -> None:
        cases = (
            ("v0.2.5", False, "degraded"),
            ("v0.2.6", False, "degraded"),
            ("v0.2.7", True, "configured"),
            ("v0.2.7-rc.1", False, "degraded"),
            ("v0.2.99", True, "configured"),
            ("v0.3.0", False, "degraded"),
        )
        self.repository.joinpath(".sanho.json").write_text("{}\n", encoding="utf-8")
        for version, supported, status in cases:
            with self.subTest(version=version):
                for executable in self.bin_directory.iterdir():
                    executable.unlink()
                self.install_fake_tools(sanho_version=version)
                sanho = json.loads(self.inspect().stdout)["tools"]["sanho"]
                self.assertEqual(sanho["version_supported"], supported)
                self.assertEqual(sanho["status"], status)

        for executable in self.bin_directory.iterdir():
            executable.unlink()
        self.install_fake_tools(sanho_doctor_warnings=1)
        sanho = json.loads(self.inspect().stdout)["tools"]["sanho"]
        self.assertEqual(sanho["probes"]["doctor"]["result"]["warnings"], 1)
        self.assertEqual(sanho["status"], "degraded")

    def test_sanho_skill_is_reported_independently_from_cli_health(self) -> None:
        self.install_fake_tools()
        self.repository.joinpath(".sanho.json").write_text("{}\n", encoding="utf-8")
        self.install_sanho_skill()
        sanho = json.loads(self.inspect().stdout)["tools"]["sanho"]
        self.assertEqual(sanho["status"], "configured")
        self.assertEqual(sanho["agent_skill"]["status"], "configured")
        installation = sanho["agent_skill"]["installations"][0]
        self.assertTrue(installation["frontmatter_valid"])
        self.assertTrue(all(item["present"] for item in installation["files"]))
        self.assertTrue(all(item["sha256"] for item in installation["files"]))

    def test_partial_invalid_or_duplicate_sanho_skills_are_degraded(self) -> None:
        cases = ("partial", "invalid", "duplicate")
        for case in cases:
            with self.subTest(case=case):
                for root in (self.codex_home / "skills", self.home / ".agents/skills"):
                    shutil.rmtree(root / "use-sanho", ignore_errors=True)
                if case == "partial":
                    self.install_sanho_skill(complete=False)
                elif case == "invalid":
                    self.install_sanho_skill(name="wrong-name")
                else:
                    self.install_sanho_skill()
                    self.install_sanho_skill(root=self.home / ".agents/skills")
                skill = json.loads(self.inspect().stdout)["tools"]["sanho"]["agent_skill"]
                self.assertEqual(skill["status"], "degraded")
                self.assertEqual(skill["duplicate"], case == "duplicate")

    def test_mulgae_version_and_installation_prerequisites_are_explicit(self) -> None:
        cases = (
            ("v0.1.14", False, "degraded"),
            ("v0.1.15", False, "degraded"),
            ("v0.1.16", True, "installed"),
            ("v0.1.16-rc.1", False, "degraded"),
            ("0.1.99", True, "installed"),
            ("v0.2.0", False, "degraded"),
        )
        for version, supported, status in cases:
            with self.subTest(version=version):
                for executable in self.bin_directory.iterdir():
                    executable.unlink()
                self.install_fake_tools(mulgae_version=version)
                with (
                    mock.patch.dict(os.environ, self.environment),
                    mock.patch("inspect_tools.platform.system", return_value="Darwin"),
                    mock.patch("inspect_tools.platform.machine", return_value="arm64"),
                ):
                    mulgae = inspect_tools.inspect_mulgae(self.repository.resolve(), 3.0)
                self.assertEqual(mulgae["version_supported"], supported)
                self.assertEqual(mulgae["status"], status)

        for version, supported in (("go1.26.5", False), ("go1.26.6", True), ("go1.27.0", True)):
            with self.subTest(go_version=version):
                for executable in self.bin_directory.iterdir():
                    executable.unlink()
                self.install_fake_tools(go_version=version)
                mulgae = json.loads(self.inspect().stdout)["tools"]["mulgae"]
                go = mulgae["installation_prerequisites"]["go"]
                self.assertEqual(go["version"], version)
                self.assertEqual(go["supported"], supported)

    def test_mulgae_config_v3_pair_and_private_policy_are_verified(self) -> None:
        self.install_fake_tools()
        self.install_mulgae_config()
        with (
            mock.patch.dict(os.environ, self.environment),
            mock.patch("inspect_tools.platform.system", return_value="Darwin"),
            mock.patch("inspect_tools.platform.machine", return_value="arm64"),
        ):
            mulgae = inspect_tools.inspect_mulgae(self.repository.resolve(), 3.0)
        self.assertEqual(mulgae["status"], "configured")
        configuration = {entry["path"]: entry for entry in mulgae["configuration"]}
        self.assertFalse(configuration[".mulgae/config.yaml"]["ignored"])
        self.assertTrue(configuration[".mulgae/local.yaml"]["ignored"])
        self.assertFalse(configuration[".mulgae/local.yaml"]["tracked"])
        self.assertTrue(configuration[".mulgae/local.yaml"]["mode_0600"])
        self.assertTrue(configuration[".mulgae/runtime/"]["ignored"])

        self.repository.joinpath(".mulgae/local.yaml").chmod(0o644)
        with (
            mock.patch.dict(os.environ, self.environment),
            mock.patch("inspect_tools.platform.system", return_value="Darwin"),
            mock.patch("inspect_tools.platform.machine", return_value="arm64"),
        ):
            insecure = inspect_tools.inspect_mulgae(self.repository.resolve(), 3.0)
        self.assertEqual(insecure["status"], "degraded")

        self.repository.joinpath(".mulgae/local.yaml").chmod(0o600)
        self.git("add", "-f", ".mulgae/local.yaml")
        with (
            mock.patch.dict(os.environ, self.environment),
            mock.patch("inspect_tools.platform.system", return_value="Darwin"),
            mock.patch("inspect_tools.platform.machine", return_value="arm64"),
        ):
            tracked = inspect_tools.inspect_mulgae(self.repository.resolve(), 3.0)
        self.assertEqual(tracked["status"], "degraded")

    def test_mulgae_doctor_v2_dimensions_are_independent_and_observable(
        self,
    ) -> None:
        self.install_fake_tools()
        self.install_mulgae_config()
        with (
            mock.patch.dict(os.environ, self.environment),
            mock.patch("inspect_tools.platform.system", return_value="Darwin"),
            mock.patch("inspect_tools.platform.machine", return_value="arm64"),
        ):
            mulgae = inspect_tools.inspect_mulgae(self.repository.resolve(), 3.0)
        self.assertEqual(mulgae["status"], "configured")
        health = mulgae["health"]
        self.assertEqual(health["mulgae_cli_compatibility"], "compatible")
        self.assertEqual(health["doctor_contract"], "supported")
        for name in ("config_v3", "local_configuration", "provider_identity"):
            self.assertEqual(health[name], {"status": "verified", "reason_codes": []})
        self.assertEqual(health["configured_readiness"]["state"], "ready")
        self.assertEqual(health["role_route_readiness"]["state"], "ready")
        self.assertNotIn("provider_static_admission", health)
        self.assertNotIn("live_review", health)
        self.assertNotIn("review_qualified", health)

    def test_mulgae_setup_inspection_uses_only_non_runtime_probes(self) -> None:
        self.install_fake_tools()
        self.install_mulgae_config()
        commands: list[list[str]] = []
        run_command = inspect_tools.run_command

        def record_command(
            arguments: list[str], cwd: Path, timeout_seconds: float
        ) -> dict[str, object]:
            commands.append(arguments)
            return run_command(arguments, cwd, timeout_seconds)

        with (
            mock.patch.dict(os.environ, self.environment),
            mock.patch("inspect_tools.platform.system", return_value="Darwin"),
            mock.patch("inspect_tools.platform.machine", return_value="arm64"),
            mock.patch("inspect_tools.run_command", side_effect=record_command),
        ):
            inspect_tools.inspect_mulgae(self.repository.resolve(), 3.0)

        mulgae_arguments = {
            tuple(arguments[1:])
            for arguments in commands
            if Path(arguments[0]).name == "mulgae"
        }
        self.assertEqual(
            mulgae_arguments,
            {
                ("version", "--json"),
                ("doctor", "--output", "json"),
            },
        )

    def test_mulgae_shared_only_config_reports_local_bootstrap_gap(self) -> None:
        self.install_fake_tools()
        self.repository.joinpath(".mulgae").mkdir()
        self.repository.joinpath(".mulgae/config.yaml").write_text(
            'version: 3\nexecution:\n  workspace_access: "none"\n', encoding="utf-8"
        )
        self.repository.joinpath(".gitignore").write_text(
            "/.mulgae/*\n!/.mulgae/config.yaml\n", encoding="utf-8"
        )
        mulgae = json.loads(self.inspect().stdout)["tools"]["mulgae"]
        self.assertEqual(mulgae["status"], "degraded")
        self.assertEqual(mulgae["health"]["config_v3"]["status"], "unverifiable")
        self.assertEqual(
            mulgae["health"]["local_configuration"],
            {"status": "failed", "reason_codes": ["local_config_missing"]},
        )
        config = mulgae["probes"]["doctor"]["result"]["doctor"]["config"]
        self.assertEqual(config["reason_codes"], ["local_config_missing"])

    def test_mulgae_config_v2_pair_is_rejected(self) -> None:
        self.install_fake_tools()
        self.repository.joinpath(".mulgae").mkdir()
        self.repository.joinpath(".mulgae/config.yaml").write_text(
            "version: 2\n", encoding="utf-8"
        )
        self.repository.joinpath(".mulgae/local.yaml").write_text(
            "version: 2\n", encoding="utf-8"
        )
        self.repository.joinpath(".mulgae/local.yaml").chmod(0o600)
        self.repository.joinpath(".gitignore").write_text(
            "/.mulgae/*\n!/.mulgae/config.yaml\n", encoding="utf-8"
        )
        mulgae = json.loads(self.inspect().stdout)["tools"]["mulgae"]
        self.assertEqual(mulgae["status"], "degraded")
        config = mulgae["probes"]["doctor"]["result"]["doctor"]["config"]
        self.assertEqual(config["reason_codes"], ["config_yaml_invalid"])

    def test_mulgae_legacy_command_envelope_is_unsupported_not_fabricated(self) -> None:
        self.install_fake_tools(mulgae_output_schema="mulgae-command-result.v3")
        self.install_mulgae_config()
        mulgae = json.loads(self.inspect().stdout)["tools"]["mulgae"]
        self.assertEqual(mulgae["status"], "degraded")
        probe = mulgae["probes"]["doctor"]
        self.assertTrue(probe["ok"])
        self.assertEqual(probe["error_code"], "unsupported_output_schema")
        self.assertEqual(mulgae["health"]["doctor_contract"], "unsupported")
        self.assertEqual(mulgae["health"]["config_v3"]["status"], "unverifiable")

    def test_mulgae_skill_is_independent_from_cli_and_mcp_health(self) -> None:
        self.install_mulgae_skill(root=self.home / ".agents/skills")
        mulgae = json.loads(self.inspect().stdout)["tools"]["mulgae"]
        self.assertEqual(mulgae["status"], "missing")
        self.assertEqual(mulgae["agent_skill"]["status"], "configured")
        self.assertEqual(mulgae["mcp_registration"]["status"], "unavailable")
        installation = mulgae["agent_skill"]["installations"][0]
        self.assertTrue(installation["frontmatter_valid"])
        self.assertIn("/.agents/skills/use-mulgae", installation["path"])
        self.assertTrue(all(item["present"] for item in installation["files"]))
        self.assertTrue(all(item["sha256"] for item in installation["files"]))

    def test_partial_invalid_or_duplicate_mulgae_skills_are_degraded(self) -> None:
        for case in ("partial", "invalid", "duplicate"):
            with self.subTest(case=case):
                for root in (self.codex_home / "skills", self.home / ".agents/skills"):
                    shutil.rmtree(root / "use-mulgae", ignore_errors=True)
                if case == "partial":
                    self.install_mulgae_skill(complete=False)
                elif case == "invalid":
                    self.install_mulgae_skill(name="wrong-name")
                else:
                    self.install_mulgae_skill()
                    self.install_mulgae_skill(root=self.home / ".agents/skills")
                skill = json.loads(self.inspect().stdout)["tools"]["mulgae"]["agent_skill"]
                self.assertEqual(skill["status"], "degraded")
                self.assertEqual(skill["duplicate"], case == "duplicate")

    def test_mulgae_mcp_registration_is_scoped_and_sanitized(self) -> None:
        self.repository.joinpath(".codex").mkdir()
        self.repository.joinpath(".codex/config.toml").write_text(
            "[mcp_servers.mulgae]\n", encoding="utf-8"
        )
        self.install_fake_tools(mulgae_mcp_mode="configured")
        completed = self.inspect()
        self.assertNotIn("must-not-leak", completed.stdout)
        registration = json.loads(completed.stdout)["tools"]["mulgae"]["mcp_registration"]
        self.assertEqual(registration["status"], "configured")
        self.assertTrue(registration["enabled"])
        self.assertTrue(registration["stdio"])
        self.assertTrue(registration["repository_bound"])
        self.assertTrue(registration["cwd_bound"])
        self.assertTrue(registration["required"])
        self.assertEqual(registration["required_verification"], "verified")
        self.assertEqual(registration["required_output_capability"], "reported")
        self.assertIsNone(registration["compatibility_reason"])
        self.assertEqual(registration["codex_version"], "0.147.0")
        self.assertTrue(registration["binary_matches_selected"])
        self.assertEqual(registration["startup_timeout_sec"], 30)
        self.assertEqual(registration["tool_timeout_sec"], 54000)

    def test_mulgae_mcp_registration_mismatch_is_degraded(self) -> None:
        self.repository.joinpath(".codex").mkdir()
        self.repository.joinpath(".codex/config.toml").write_text(
            "[mcp_servers.mulgae]\n", encoding="utf-8"
        )
        modes = (
            "wrong-args",
            "wrong-cwd",
            "disabled",
            "required-false",
            "non-stdio",
            "wrong-command",
            "startup-timeout",
            "tool-timeout",
        )
        for mode in modes:
            with self.subTest(mode=mode):
                for executable in self.bin_directory.iterdir():
                    executable.unlink()
                self.install_fake_tools(mulgae_mcp_mode=mode)
                registration = json.loads(
                    self.inspect(timeout_seconds=10.0).stdout
                )["tools"]["mulgae"]["mcp_registration"]
                self.assertEqual(registration["status"], "degraded")
                self.assertEqual(registration["reason"], "registration_mismatch")

    def test_mulgae_mcp_absent_required_is_compatible_but_unverifiable(self) -> None:
        self.repository.joinpath(".codex").mkdir()
        self.repository.joinpath(".codex/config.toml").write_text(
            "[mcp_servers.mulgae]\nrequired = true\n", encoding="utf-8"
        )
        self.install_fake_tools(mulgae_mcp_mode="required-absent")
        registration = json.loads(self.inspect().stdout)["tools"]["mulgae"][
            "mcp_registration"
        ]
        self.assertEqual(registration["status"], "configured")
        self.assertIsNone(registration["required"])
        self.assertEqual(registration["required_verification"], "unverifiable")
        self.assertEqual(
            registration["required_output_capability"], "not_reported"
        )
        self.assertEqual(
            registration["compatibility_reason"], "required_unverifiable"
        )
        self.assertNotIn("reason", registration)

    def test_mulgae_mcp_invalid_required_type_fails_closed(self) -> None:
        self.repository.joinpath(".codex").mkdir()
        self.repository.joinpath(".codex/config.toml").write_text(
            "[mcp_servers.mulgae]\n", encoding="utf-8"
        )
        self.install_fake_tools(mulgae_mcp_mode="invalid-required")
        registration = json.loads(self.inspect().stdout)["tools"]["mulgae"][
            "mcp_registration"
        ]
        self.assertEqual(registration["status"], "degraded")
        self.assertEqual(registration["reason"], "invalid_registration_result")
        self.assertEqual(registration["required_output_capability"], "invalid")

    def test_mulgae_mcp_absence_is_not_cli_degradation(self) -> None:
        self.install_fake_tools(mulgae_mcp_mode="missing")
        mulgae = json.loads(self.inspect().stdout)["tools"]["mulgae"]
        self.assertEqual(mulgae["mcp_registration"]["status"], "missing")
        if platform.system() == "Darwin" and platform.machine() in {"arm64", "aarch64"}:
            self.assertEqual(mulgae["status"], "installed")

    def test_mulgae_mcp_is_status_gating_only_when_selected(self) -> None:
        self.install_fake_tools(mulgae_mcp_mode="missing")
        self.install_mulgae_config()
        with (
            mock.patch.dict(os.environ, self.environment),
            mock.patch("inspect_tools.platform.system", return_value="Darwin"),
            mock.patch("inspect_tools.platform.machine", return_value="arm64"),
        ):
            optional = inspect_tools.inspect_mulgae(
                self.repository.resolve(), 3.0, require_mcp=False
            )
            required = inspect_tools.inspect_mulgae(
                self.repository.resolve(), 3.0, require_mcp=True
            )
        self.assertEqual(optional["status"], "configured")
        self.assertFalse(optional["mcp_required_for_status"])
        self.assertEqual(required["status"], "degraded")
        self.assertTrue(required["mcp_required_for_status"])

    def test_gaori_version_support_and_config_check_are_explicit(self) -> None:
        cases = (
            ("0.1.11", False, "degraded"),
            ("0.1.12", False, "degraded"),
            ("0.1.13", True, "configured"),
            ("v0.1.13-rc.1", False, "degraded"),
            ("v0.1.99", True, "configured"),
            ("0.2.0", False, "degraded"),
        )
        self.repository.joinpath(".gaori").mkdir()
        self.repository.joinpath(".gaori/tester.yaml").write_text(
            "version: 2\n", encoding="utf-8"
        )
        for version, supported, status in cases:
            with self.subTest(version=version):
                for executable in self.bin_directory.iterdir():
                    executable.unlink()
                self.install_fake_tools(gaori_version=version)
                gaori = json.loads(self.inspect().stdout)["tools"]["gaori"]
                self.assertEqual(gaori["version_supported"], supported)
                self.assertEqual(gaori["status"], status)
                self.assertTrue(gaori["probes"]["config_check"]["attempted"])

        for executable in self.bin_directory.iterdir():
            executable.unlink()
        self.install_fake_tools(gaori_config_ok=False)
        gaori = json.loads(self.inspect().stdout)["tools"]["gaori"]
        self.assertFalse(gaori["probes"]["config_check"]["ok"])
        self.assertEqual(gaori["status"], "degraded")

        for executable in self.bin_directory.iterdir():
            executable.unlink()
        self.install_fake_tools(malformed_gaori_config=True)
        gaori = json.loads(self.inspect().stdout)["tools"]["gaori"]
        self.assertEqual(gaori["probes"]["config_check"]["error_code"], "invalid_json")
        self.assertEqual(gaori["status"], "degraded")

        for executable in self.bin_directory.iterdir():
            executable.unlink()
        self.install_fake_tools(slow_gaori_config=True)
        gaori = json.loads(self.inspect(timeout_seconds=0.5).stdout)["tools"]["gaori"]
        self.assertTrue(gaori["probes"]["config_check"]["timed_out"])
        self.assertEqual(gaori["status"], "degraded")

    def test_gaori_skill_is_independent_from_cli_and_mcp_health(self) -> None:
        self.install_gaori_skill()
        gaori = json.loads(self.inspect().stdout)["tools"]["gaori"]
        self.assertEqual(gaori["status"], "missing")
        self.assertEqual(gaori["agent_skill"]["status"], "configured")
        self.assertEqual(gaori["mcp_registration"]["status"], "unavailable")
        installation = gaori["agent_skill"]["installations"][0]
        self.assertTrue(installation["frontmatter_valid"])
        self.assertTrue(all(item["present"] for item in installation["files"]))
        self.assertTrue(all(item["sha256"] for item in installation["files"]))

    def test_partial_invalid_or_duplicate_gaori_skills_are_degraded(self) -> None:
        for case in ("partial", "invalid", "duplicate"):
            with self.subTest(case=case):
                for root in (self.codex_home / "skills", self.home / ".agents/skills"):
                    shutil.rmtree(root / "use-gaori", ignore_errors=True)
                if case == "partial":
                    self.install_gaori_skill(complete=False)
                elif case == "invalid":
                    self.install_gaori_skill(name="wrong-name")
                else:
                    self.install_gaori_skill()
                    self.install_gaori_skill(root=self.home / ".agents/skills")
                skill = json.loads(self.inspect().stdout)["tools"]["gaori"][
                    "agent_skill"
                ]
                self.assertEqual(skill["status"], "degraded")
                self.assertEqual(skill["duplicate"], case == "duplicate")

    def test_gaori_mcp_registration_is_scoped_and_sanitized(self) -> None:
        self.repository.joinpath(".codex").mkdir()
        self.repository.joinpath(".codex/config.toml").write_text(
            "[mcp_servers.gaori]\n", encoding="utf-8"
        )
        self.install_fake_tools(gaori_mcp_mode="configured")
        completed = self.inspect()
        self.assertNotIn("must-not-leak", completed.stdout)
        registration = json.loads(completed.stdout)["tools"]["gaori"][
            "mcp_registration"
        ]
        self.assertEqual(registration["status"], "configured")
        self.assertTrue(registration["enabled"])
        self.assertTrue(registration["stdio"])
        self.assertTrue(registration["repository_bound"])
        self.assertTrue(registration["command_resolvable"])
        self.assertTrue(registration["binary_matches_selected"])
        self.assertEqual(registration["tool_timeout_sec"], 60)

    def test_gaori_mcp_registration_mismatch_is_degraded(self) -> None:
        self.repository.joinpath(".codex").mkdir()
        self.repository.joinpath(".codex/config.toml").write_text(
            "[mcp_servers.gaori]\n", encoding="utf-8"
        )
        for mode in ("wrong-repo", "disabled", "non-stdio", "missing-command"):
            with self.subTest(mode=mode):
                for executable in self.bin_directory.iterdir():
                    executable.unlink()
                self.install_fake_tools(gaori_mcp_mode=mode)
                registration = json.loads(self.inspect().stdout)["tools"]["gaori"][
                    "mcp_registration"
                ]
                self.assertEqual(registration["status"], "degraded")
                self.assertEqual(registration["reason"], "registration_mismatch")

    def test_gaori_mcp_absence_is_not_cli_degradation(self) -> None:
        self.install_fake_tools(gaori_mcp_mode="missing")
        gaori = json.loads(self.inspect().stdout)["tools"]["gaori"]
        self.assertEqual(gaori["status"], "installed")
        self.assertEqual(gaori["mcp_registration"]["status"], "missing")

    def test_worktree_counts_staged_unstaged_and_untracked_files(self) -> None:
        self.repository.joinpath("tracked.txt").write_text("staged\n", encoding="utf-8")
        self.git("add", "tracked.txt")
        self.repository.joinpath("tracked.txt").write_text(
            "unstaged\n", encoding="utf-8"
        )
        self.repository.joinpath("untracked.txt").write_text("new\n", encoding="utf-8")
        completed = self.inspect()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        counts = json.loads(completed.stdout)["repository"]["worktree"]
        self.assertEqual(
            counts, {"conflicted": 0, "staged": 1, "unstaged": 1, "untracked": 1}
        )

    def test_renamed_files_are_counted_once_as_staged(self) -> None:
        self.git("mv", "tracked.txt", "renamed.txt")
        completed = self.inspect()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        counts = json.loads(completed.stdout)["repository"]["worktree"]
        self.assertEqual(
            counts, {"conflicted": 0, "staged": 1, "unstaged": 0, "untracked": 0}
        )

    def test_repository_reports_root_branch_and_upstream_state(self) -> None:
        default_branch = self.git("branch", "--show-current").stdout.strip()
        completed = self.inspect()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        repository = json.loads(completed.stdout)["repository"]
        self.assertEqual(repository["root"], str(self.repository.resolve()))
        self.assertEqual(repository["branch"], default_branch)
        self.assertIsNone(repository["upstream"])
        self.git("branch", "other")
        self.git("branch", "--set-upstream-to=other", default_branch)
        tracking = json.loads(self.inspect().stdout)["repository"]
        self.assertEqual(tracking["branch"], default_branch)
        self.assertEqual(tracking["upstream"], "other")
        self.git("checkout", "--quiet", "--detach")
        head = self.git("rev-parse", "--short", "HEAD").stdout.strip()
        detached = json.loads(self.inspect().stdout)["repository"]
        self.assertEqual(detached["branch"], head)
        self.assertIsNone(detached["upstream"])

    def test_invalid_lora_frontmatter_is_degraded(self) -> None:
        self.install_lora_skill("lore-commits")
        invalid_directory = self.codex_home / "skills" / "lore-query"
        invalid_directory.mkdir(parents=True)
        invalid_directory.joinpath("SKILL.md").write_text(
            "---\nname: wrong-name\ndescription: Test skill.\n---\n", encoding="utf-8"
        )
        completed = self.inspect()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        lora = json.loads(completed.stdout)["tools"]["lora"]
        self.assertEqual(lora["status"], "degraded")
        self.assertFalse(lora["installed"])
        self.assertFalse(lora["skills"]["lore-query"]["frontmatter_valid"])

    def test_conflicted_files_are_counted_separately(self) -> None:
        default_branch = self.git("branch", "--show-current").stdout.strip()
        self.git("checkout", "--quiet", "-b", "other")
        self.repository.joinpath("tracked.txt").write_text("other\n", encoding="utf-8")
        self.git("commit", "--quiet", "-am", "Other")
        self.git("checkout", "--quiet", default_branch)
        self.repository.joinpath("tracked.txt").write_text(
            "default\n", encoding="utf-8"
        )
        self.git("commit", "--quiet", "-am", "Default")
        self.git("merge", "other", check=False)
        completed = self.inspect()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        counts = json.loads(completed.stdout)["repository"]["worktree"]
        self.assertEqual(counts["conflicted"], 1)
        self.assertEqual(counts["staged"], 0)
        self.assertEqual(counts["unstaged"], 0)

    def test_invalid_and_non_git_paths_return_structured_errors(self) -> None:
        invalid = self.inspect(self.base / "missing")
        self.assertEqual(invalid.returncode, 2)
        self.assertEqual(
            json.loads(invalid.stdout)["error"]["code"], "invalid_repository_path"
        )
        non_git = self.base / "not-git"
        non_git.mkdir()
        outside = self.inspect(non_git)
        self.assertEqual(outside.returncode, 2)
        self.assertEqual(
            json.loads(outside.stdout)["error"]["code"], "not_a_git_repository"
        )

    def test_missing_repository_argument_returns_a_json_error_envelope(self) -> None:
        completed = self.run_script()
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(completed.stderr, "")
        payload = json.loads(completed.stdout)
        self.assertEqual(
            payload["schema_version"], "aquarium-dev-setup-inspection.v5"
        )
        self.assertEqual(payload["error"]["code"], "invalid_arguments")
        self.assertIn("--repository", payload["error"]["message"])

    def test_non_positive_timeout_is_rejected_before_inspection(self) -> None:
        completed = self.inspect(timeout_seconds=0)
        self.assertEqual(completed.returncode, 2)
        error = json.loads(completed.stdout)["error"]
        self.assertEqual(error["code"], "invalid_arguments")
        self.assertIn("greater than zero", error["message"])

    def test_execution_failures_are_reported_without_json_parsing(self) -> None:
        with mock.patch(
            "inspect_tools.subprocess.run", side_effect=OSError("boom")
        ) as patched_run:
            raw_probe = inspect_tools.run_command(["anything"], self.repository, 1.0)
        self.assertEqual(patched_run.call_count, 1)
        self.assertTrue(raw_probe["attempted"])
        self.assertFalse(raw_probe["ok"])
        self.assertIsNone(raw_probe["exit_code"])
        self.assertFalse(raw_probe["timed_out"])
        self.assertEqual(raw_probe["error_code"], "execution_failed")
        self.assertEqual(raw_probe["error_type"], "OSError")
        probe = inspect_tools.parse_json_probe(raw_probe)
        self.assertEqual(probe["error_code"], "execution_failed")
        self.assertNotIn("result", probe)

    def test_mulgae_doctor_v2_provider_outcomes_gate_offline_readiness(self) -> None:
        self.install_mulgae_config()
        cases = (
            ("ready", "configured", "verified", "eligible", "verified"),
            (
                "newer",
                "configured",
                "verified",
                "eligible",
                "newer_than_verified",
            ),
            ("binary_missing", "degraded", "failed", "not_evaluated", "not_observed"),
            (
                "binary_nonexecutable",
                "degraded",
                "failed",
                "not_evaluated",
                "not_observed",
            ),
            ("cli_below", "degraded", "verified", "ineligible", "below_minimum"),
            ("cli_malformed", "degraded", "verified", "ineligible", "malformed"),
            (
                "cli_failure",
                "degraded",
                "verified",
                "not_evaluated",
                "not_observed",
            ),
            (
                "cli_timeout",
                "degraded",
                "verified",
                "not_evaluated",
                "not_observed",
            ),
        )
        for case, status, binary, eligibility, compatibility in cases:
            with self.subTest(case=case):
                for executable in self.bin_directory.iterdir():
                    executable.unlink()
                self.install_fake_tools(mulgae_doctor_case=case)
                with (
                    mock.patch.dict(os.environ, self.environment),
                    mock.patch("inspect_tools.platform.system", return_value="Darwin"),
                    mock.patch("inspect_tools.platform.machine", return_value="arm64"),
                ):
                    mulgae = inspect_tools.inspect_mulgae(
                        self.repository.resolve(), 3.0
                    )
                self.assertEqual(mulgae["status"], status)
                zcode = mulgae["provider_inventory"][1]
                self.assertEqual(zcode["binary_available"]["status"], binary)
                self.assertEqual(zcode["cli_compatible"]["eligibility"], eligibility)
                self.assertEqual(
                    zcode["cli_compatible"]["compatibility"], compatibility
                )

    def test_mulgae_doctor_v2_rejects_invalid_identity_and_role_mapping(self) -> None:
        self.install_mulgae_config()
        for case, reason in (
            ("identity_invalid", "config_provider_identity_invalid"),
            ("role_invalid", "config_role_mapping_invalid"),
        ):
            with self.subTest(case=case):
                for executable in self.bin_directory.iterdir():
                    executable.unlink()
                self.install_fake_tools(mulgae_doctor_case=case)
                with (
                    mock.patch.dict(os.environ, self.environment),
                    mock.patch("inspect_tools.platform.system", return_value="Darwin"),
                    mock.patch("inspect_tools.platform.machine", return_value="arm64"),
                ):
                    mulgae = inspect_tools.inspect_mulgae(
                        self.repository.resolve(), 3.0
                    )
                self.assertEqual(mulgae["status"], "degraded")
                self.assertEqual(
                    mulgae["health"]["provider_identity"],
                    {"status": "failed", "reason_codes": [reason]},
                )

    def test_mulgae_legacy_doctor_fields_are_unsupported_not_failed(self) -> None:
        self.install_fake_tools(mulgae_doctor_schema="mulgae-doctor-result.v1")
        self.install_mulgae_config()
        mulgae = json.loads(self.inspect().stdout)["tools"]["mulgae"]
        self.assertEqual(mulgae["status"], "degraded")
        self.assertEqual(mulgae["health"]["doctor_contract"], "unsupported")
        self.assertEqual(
            mulgae["health"]["config_v3"],
            {
                "status": "unverifiable",
                "reason_codes": ["doctor_v2_unsupported"],
            },
        )
        self.assertNotIn("provider_static_admission", mulgae["health"])
        self.assertNotIn("live_review", mulgae["health"])

    def test_mulgae_doctor_v2_missing_required_dimensions_is_invalid(self) -> None:
        normalized = inspect_tools.normalize_mulgae_doctor(
            {
                "attempted": True,
                "ok": True,
                "exit_code": 0,
                "timed_out": False,
                "result": {
                    "schema_version": "mulgae-command-result.v4",
                    "result": {
                        "kind": "diagnosed",
                        "doctor": {"schema_version": "mulgae-doctor-result.v2"},
                    },
                },
            }
        )
        self.assertEqual(normalized["doctor_capability"], "invalid")
        self.assertNotIn("doctor", normalized["result"])

    def test_default_inspection_does_not_call_podway_inspector(self) -> None:
        with mock.patch("inspect_tools.inspect_podway") as podway_inspector:
            payload = inspect_tools.inspect(str(self.repository), 3.0)
        podway_inspector.assert_not_called()
        self.assertNotIn("podway", payload["tools"])

    def test_default_inspection_does_not_call_ouroboros_inspector(self) -> None:
        with mock.patch("inspect_tools.inspect_ouroboros") as ouroboros_inspector:
            payload = inspect_tools.inspect(str(self.repository), 3.0)
        ouroboros_inspector.assert_not_called()
        self.assertNotIn("ouroboros", payload["tools"])

    def test_ouroboros_supports_only_the_selected_minor_line(self) -> None:
        expected = {
            "0.51.0": False,
            "0.51.1": True,
            "v0.51.9": True,
            "0.50.9": False,
            "0.52.0": False,
        }
        for version, supported in expected.items():
            with self.subTest(version=version):
                self.assertEqual(
                    inspect_tools.supported_ouroboros_version(version), supported
                )

    def test_ouroboros_version_parser_removes_terminal_formatting(self) -> None:
        output = "\x1b[1mOuroboros\x1b[0m version \x1b[1m0.51\x1b[0m.\x1b[1m1\x1b[0m\n"
        self.assertEqual(
            inspect_tools.ouroboros_version_from_output(output), "0.51.1"
        )

    def test_ouroboros_version_parser_reports_unsupported_major(self) -> None:
        output = "runtime 9.9.9\nOuroboros version 1.0.0\n"
        version = inspect_tools.ouroboros_version_from_output(output)
        self.assertEqual(version, "1.0.0")
        self.assertFalse(inspect_tools.supported_ouroboros_version(version))

    def test_installed_ouroboros_reports_configured_components(self) -> None:
        self.install_fake_tools(
            ouroboros_version="0.51.1", ouroboros_mcp_mode="configured"
        )
        completed = self.inspect(include_ouroboros=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        ouroboros = json.loads(completed.stdout)["tools"]["ouroboros"]
        self.assertEqual(ouroboros["version"], "0.51.1")
        self.assertTrue(ouroboros["version_supported"])
        self.assertEqual(ouroboros["codex_integration"]["status"], "configured")
        self.assertEqual(ouroboros["mcp_runtime"]["status"], "configured")
        self.assertEqual(ouroboros["mcp_registration"]["status"], "configured")
        self.assertEqual(ouroboros["status"], "configured")
        self.assertNotIn("name", ouroboros)

    def test_installed_ouroboros_keeps_component_failures_independent(self) -> None:
        cases = (
            ("codex", False, True, "degraded", "configured"),
            ("mcp", True, False, "configured", "degraded"),
        )
        for name, codex_ok, mcp_ok, codex_status, mcp_status in cases:
            with self.subTest(component=name):
                self.install_fake_tools(
                    ouroboros_version="0.51.1",
                    ouroboros_codex_doctor_ok=codex_ok,
                    ouroboros_mcp_doctor_ok=mcp_ok,
                    ouroboros_mcp_mode="configured",
                )
                completed = self.inspect(include_ouroboros=True)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                ouroboros = json.loads(completed.stdout)["tools"]["ouroboros"]
                self.assertEqual(
                    ouroboros["codex_integration"]["status"], codex_status
                )
                self.assertEqual(ouroboros["mcp_runtime"]["status"], mcp_status)
                self.assertEqual(
                    ouroboros["mcp_registration"]["status"], "configured"
                )
                self.assertEqual(ouroboros["status"], "degraded")

    def test_ouroboros_version_failures_and_unsupported_versions_degrade(self) -> None:
        for version, version_ok in (("0.52.0", True), ("0.51.1", False)):
            with self.subTest(version=version, version_ok=version_ok):
                self.install_fake_tools(
                    ouroboros_version=version,
                    ouroboros_version_ok=version_ok,
                    ouroboros_mcp_mode="configured",
                )
                completed = self.inspect(include_ouroboros=True)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                ouroboros = json.loads(completed.stdout)["tools"]["ouroboros"]
                self.assertFalse(ouroboros["version_supported"])
                self.assertEqual(ouroboros["probes"]["version"]["ok"], version_ok)
                self.assertEqual(ouroboros["status"], "degraded")

    def test_ouroboros_malformed_mcp_doctor_json_degrades_runtime(self) -> None:
        self.install_fake_tools(
            ouroboros_version="0.51.1",
            ouroboros_mcp_doctor_malformed=True,
            ouroboros_mcp_mode="configured",
        )
        completed = self.inspect(include_ouroboros=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        ouroboros = json.loads(completed.stdout)["tools"]["ouroboros"]
        self.assertEqual(ouroboros["mcp_runtime"]["status"], "degraded")
        self.assertEqual(
            ouroboros["mcp_runtime"]["probe"]["error_code"], "invalid_json"
        )
        self.assertEqual(ouroboros["status"], "degraded")

    def test_ouroboros_registration_requires_explicit_enabled_true(self) -> None:
        expected_reasons = {
            "disabled": "registration_disabled",
            "enabled-absent": "registration_enabled_missing",
            "enabled-invalid": "registration_enabled_invalid",
            "malformed": "registration_invalid_json",
        }
        for mode, reason in expected_reasons.items():
            with self.subTest(mode=mode):
                self.install_fake_tools(
                    ouroboros_version="0.51.1", ouroboros_mcp_mode=mode
                )
                completed = self.inspect(include_ouroboros=True)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                ouroboros = json.loads(completed.stdout)["tools"]["ouroboros"]
                self.assertEqual(
                    ouroboros["mcp_registration"]["status"], "degraded"
                )
                self.assertEqual(
                    ouroboros["mcp_registration"]["probe"]["reason"], reason
                )
                self.assertEqual(ouroboros["status"], "degraded")

    def test_ouroboros_registration_missing_is_distinct_from_probe_failure(self) -> None:
        for mode, status, reason in (
            ("missing", "missing", "registration_not_found"),
            ("probe-failure", "degraded", "registration_probe_failed"),
            ("timeout", "degraded", "registration_probe_timed_out"),
        ):
            with self.subTest(mode=mode):
                self.install_fake_tools(
                    ouroboros_version="0.51.1", ouroboros_mcp_mode=mode
                )
                completed = self.inspect(
                    include_ouroboros=True,
                    timeout_seconds=0.05 if mode == "timeout" else 3.0,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertNotIn("secret registration failure", completed.stdout)
                registration = json.loads(completed.stdout)["tools"]["ouroboros"][
                    "mcp_registration"
                ]
                self.assertEqual(registration["status"], status)
                self.assertEqual(registration["probe"]["reason"], reason)

    def test_missing_ouroboros_still_inspects_codex_registration(self) -> None:
        self.install_fake_tools(ouroboros_mcp_mode="configured")
        completed = self.inspect(include_ouroboros=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        ouroboros = json.loads(completed.stdout)["tools"]["ouroboros"]
        self.assertFalse(ouroboros["installed"])
        self.assertEqual(ouroboros["status"], "missing")
        self.assertEqual(ouroboros["mcp_registration"]["status"], "configured")
        self.assertEqual(
            ouroboros["probes"]["version"]["reason"], "executable_missing"
        )

    def test_installed_ouroboros_reports_registration_unverifiable_without_codex(
        self,
    ) -> None:
        self.install_fake_tools(ouroboros_version="0.51.1")
        completed = self.inspect(include_ouroboros=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        ouroboros = json.loads(completed.stdout)["tools"]["ouroboros"]
        self.assertEqual(ouroboros["mcp_registration"]["status"], "unverifiable")
        self.assertEqual(
            ouroboros["mcp_registration"]["probe"]["reason"],
            "codex_executable_missing",
        )
        self.assertEqual(ouroboros["status"], "degraded")

    def test_explicit_ouroboros_inspection_reports_independent_components(self) -> None:
        completed = self.inspect(include_ouroboros=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        ouroboros = json.loads(completed.stdout)["tools"]["ouroboros"]
        self.assertEqual(ouroboros["supported_range"], ">=0.51.1,<0.52.0")
        self.assertEqual(ouroboros["status"], "missing")
        self.assertEqual(ouroboros["codex_integration"]["status"], "missing")
        self.assertEqual(ouroboros["mcp_runtime"]["status"], "missing")
        self.assertEqual(ouroboros["mcp_registration"]["status"], "unverifiable")
        self.assertEqual(
            ouroboros["probes"]["version"]["reason"], "executable_missing"
        )

    def test_supported_platform_readiness_is_verified_on_any_host(self) -> None:
        self.install_fake_tools()
        self.install_managed_podway_procedures()
        with (
            mock.patch.dict(os.environ, self.environment),
            mock.patch("inspect_tools.platform.system", return_value="Darwin"),
            mock.patch("inspect_tools.platform.machine", return_value="arm64"),
        ):
            podway = inspect_tools.inspect_podway(self.repository.resolve(), 3.0)
        self.assertEqual(
            podway["platform"],
            {"system": "Darwin", "machine": "arm64", "supported": True},
        )
        self.assertTrue(podway["version_supported"])
        self.assertTrue(podway["versions_match"])
        self.assertEqual(podway["readiness_status"], "ready")
        self.assertEqual(podway["status"], "configured")

    def test_untracked_managed_procedures_have_degraded_readiness(self) -> None:
        self.install_fake_tools()
        self.install_managed_podway_procedures(tracked=False)
        with (
            mock.patch.dict(os.environ, self.environment),
            mock.patch("inspect_tools.platform.system", return_value="Darwin"),
            mock.patch("inspect_tools.platform.machine", return_value="arm64"),
        ):
            podway = inspect_tools.inspect_podway(self.repository.resolve(), 3.0)
        for entry in podway["managed_procedures"]:
            self.assertTrue(entry["present"])
            self.assertTrue(entry["matches_source"])
            self.assertFalse(entry["tracked"])
        self.assertEqual(podway["readiness_status"], "degraded")
        self.assertEqual(podway["status"], "degraded")


if __name__ == "__main__":
    unittest.main()
