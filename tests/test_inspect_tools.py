from __future__ import annotations

import hashlib
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
# macOS may delay first execution of freshly written fixture binaries while
# performing local trust checks. Timeout-specific tests pass shorter values.
NORMAL_PROBE_TIMEOUT_SECONDS = 30.0

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
        timeout_seconds: float = NORMAL_PROBE_TIMEOUT_SECONDS,
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
        mulgae_version: str = "v0.1.18",
        mulgae_output_schema: str = "mulgae-command-result.v5",
        mulgae_doctor_schema: str = "mulgae-doctor-result.v2",
        mulgae_doctor_case: str = "ready",
        mulgae_mcp_mode: str | None = None,
        mulgae_mcp_global: bool = False,
        go_version: str = "go1.26.6",
        gaori_version: str = "0.1.14",
        gaori_config_ok: bool = True,
        malformed_gaori_config: bool = False,
        slow_gaori_config: bool = False,
        gaori_mcp_mode: str | None = None,
        gaori_mcp_global: bool = False,
        mcp_neutral_failure: bool = False,
        mcp_neutral_mixed_missing: bool = False,
        slow_gaori: bool = False,
        failing_mulgae_providers: bool = False,
        podway_version: str = "v0.2.7",
        podway_daemon_version: str = "0.2.7",
        podway_daemon_reachable: bool = True,
        podway_daemon_status_schema: str = "podway.daemon-status-result/v2",
        podway_readiness_state: str = "ready",
        podway_readiness_stage: str | None = "ready",
        podway_worktree_recovery: tuple[int, int, int] | None = (1, 1, 0),
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
            "higher-timeout": "higher_timeout",
            "invalid-required": "invalid_required",
        }
        mulgae_mcp_result = (
            self.mulgae_mcp_fixture(mulgae_mcp_fixture_names[mulgae_mcp_mode])
            if mulgae_mcp_mode not in {None, "missing", "silent-failure"}
            else None
        )
        source = textwrap.dedent(
            f"""\
            #!{sys.executable}
            import json
            import os
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
                        "minimum_version": "0.16.3",
                        "verified_latest": "0.16.3",
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
                    cli = compatible("verified", "eligible", "verified", "provider_cli_version_supported", "0.16.3")
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
                    print("codex-cli 0.149.0")
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
                global_registration = (
                    {mulgae_mcp_global!r}
                    if server == "mulgae"
                    else {gaori_mcp_global!r}
                    if server == "gaori"
                    else True
                )
                repository_path = pathlib.Path({str(self.repository)!r}).resolve()
                local_codex_home = repository_path / ".codex"
                active_codex_home = pathlib.Path(os.environ.get("CODEX_HOME", "")).resolve()
                isolated_local = active_codex_home == local_codex_home
                effective_lookup = pathlib.Path.cwd().resolve() == repository_path and not isolated_local
                local_config = local_codex_home / "config.toml"
                local_registration = local_config.is_file() and f"[mcp_servers.{{server}}]" in local_config.read_text(encoding="utf-8")
                use_global_registration = not isolated_local and not (effective_lookup and local_registration)
                if server in {{"mulgae", "gaori"}}:
                    if {mcp_neutral_mixed_missing!r}:
                        print("neutral configuration failed", file=sys.stderr)
                        print(f"Error: No MCP server named '{{server}}' found.", file=sys.stderr)
                        raise SystemExit(1)
                    if {mcp_neutral_failure!r}:
                        print("neutral configuration failed", file=sys.stderr)
                        raise SystemExit(1)
                    if isolated_local and not local_registration:
                        print(f"Error: No MCP server named '{{server}}' found.", file=sys.stderr)
                        raise SystemExit(1)
                    if use_global_registration and not global_registration:
                        print(f"Error: No MCP server named '{{server}}' found.", file=sys.stderr)
                        raise SystemExit(1)
                if mode == "missing":
                    print(f"Error: No MCP server named '{{server}}' found.", file=sys.stderr)
                    raise SystemExit(1)
                if mode == "silent-failure":
                    raise SystemExit(1)
                if mode == "timeout":
                    time.sleep(4)
                if mode == "probe-failure":
                    print("secret registration failure", file=sys.stderr)
                    raise SystemExit(2)
                repository = {str(self.repository)!r} if mode != "wrong-repo" else "/tmp/wrong-repo"
                if server == "mulgae":
                    result = {mulgae_mcp_result!r}
                    if use_global_registration:
                        result["transport"]["args"] = ["mcp"]
                        result["transport"]["cwd"] = None
                    print(json.dumps(result))
                    raise SystemExit(0)
                if server == "ouroboros":
                    if mode == "malformed":
                        print("not-json")
                        raise SystemExit(0)
                    if isinstance(mode, str) and mode.startswith("isolated"):
                        args = ["--isolated", "--python", ">=3.12", "--from", "ouroboros-ai[mcp]", "ouroboros", "mcp", "serve"]
                        env = {{"OUROBOROS_AGENT_RUNTIME": "codex", "OUROBOROS_LLM_BACKEND": "codex"}}
                        if mode == "isolated-pinned":
                            args[4] = "ouroboros-ai[mcp]==0.51.15"
                        elif mode == "isolated-suffix":
                            args.extend(["--runtime", "codex", "--llm-backend", "codex"])
                            env = {{}}
                        elif mode == "isolated-legacy-selector":
                            env["OUROBOROS_RUNTIME"] = "codex"
                        elif mode == "isolated-missing-flag":
                            args.pop(0)
                        elif mode == "isolated-wrong-python":
                            args[2] = ">=3.11"
                        elif mode == "isolated-wrong-package":
                            args[4] = "ouroboros-ai"
                        elif mode == "isolated-unsupported-pin":
                            args[4] = "ouroboros-ai[mcp]==0.52.0"
                        elif mode == "isolated-old-pin":
                            args[4] = "ouroboros-ai[mcp]==0.51.0"
                        elif mode == "isolated-extra-arg":
                            args.append("--unexpected")
                        elif mode == "isolated-missing-env":
                            env = {{}}
                        elif mode == "isolated-conflicting-env":
                            env["OUROBOROS_LLM_BACKEND"] = "claude"
                        elif mode == "isolated-nested-env":
                            env["_OUROBOROS_NESTED"] = "1"
                        elif mode == "isolated-extra-env":
                            env["UV_INDEX_URL"] = "https://example.invalid/simple"
                        result = {{
                            "name": "ouroboros",
                            "enabled": True,
                            "transport": {{
                                "type": "http" if mode == "isolated-non-stdio" else "stdio",
                                "command": "missing-uvx" if mode == "isolated-wrong-command" else "ooo" if mode == "isolated-imposter-command" else "uvx",
                                "args": args,
                                "env": env,
                            }},
                        }}
                    else:
                        result = {{
                            "name": "wrong-name" if mode == "wrong-name" else "ouroboros",
                            "transport": {{
                                "type": "http" if mode == "non-stdio" else "stdio",
                                "command": "wrong-ooo" if mode == "wrong-command" else "ooo",
                                "args": ["serve"] if mode == "wrong-args" else ["mcp", "serve"],
                            }},
                        }}
                    if mode != "enabled-absent":
                        result["enabled"] = "yes" if mode == "enabled-invalid" else mode != "disabled"
                    print(json.dumps(result))
                    raise SystemExit(0)
                result = {{
                    "name": "gaori",
                    "enabled": mode != "disabled",
                    "transport": {{
                        "type": "http" if mode == "non-stdio" else "stdio",
                        "command": "/tmp/missing-gaori" if mode == "missing-command" else {str(self.bin_directory / "wrong-gaori")!r} if mode == "wrong-command" else {str(self.bin_directory / "gaori")!r},
                        "args": (["--unexpected"] if mode == "extra-arg" else []) + ["--repo", repository, "mcp"],
                        "env": {{"SECRET_TOKEN": "must-not-leak"}},
                        "env_vars": [],
                        "cwd": None,
                    }},
                }}
                if use_global_registration:
                    result["transport"]["args"] = ["mcp"]
                if mode != "timeout-absent":
                    result["tool_timeout_sec"] = (
                        "3601"
                        if mode == "timeout-invalid"
                        else 3600
                        if mode == "tool-timeout"
                        else 3602
                        if mode == "higher-timeout"
                        else 3601
                    )
                print(json.dumps(result))
                raise SystemExit(0)
            if name == "podway":
                if arguments == ["version", "--json"]:
                    print(json.dumps({{"name": "podway", "version": {podway_version!r}}}))
                    raise SystemExit(0)
                if len(arguments) == 5 and arguments[:4] == ["--json", "daemon", "wait-ready", "--timeout"] and arguments[4] == "120s":
                    daemon_status = {{"schema": {podway_daemon_status_schema!r}, "installed": True, "loaded": True, "reachable": {podway_daemon_reachable!r}, "status": "running", "daemon_version": {podway_daemon_version!r}, "target": "aarch64-apple-darwin", "contract_manifest_schema": "podway.contract-manifest/v1", "contract_manifest_digest": "sha256:test"}}
                    if {podway_daemon_status_schema!r} == "podway.daemon-status-result/v2":
                        recovery = {podway_worktree_recovery!r}
                        daemon_status.update(readiness_state={podway_readiness_state!r}, readiness_stage={podway_readiness_stage!r}, readiness_elapsed_ms=5, worktree_recovery=None if recovery is None else dict(zip(("total", "completed", "failed"), recovery)))
                    print(json.dumps({{"schema": {podway_output_schema!r}, "command": "daemon.wait-ready", "result": daemon_status}}))
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
                if len(arguments) == 4 and arguments[:3] == ["--json", "procedure", "preview"]:
                    procedure_id = next(
                        (line.split(":", 1)[1].strip() for line in pathlib.Path(arguments[3]).read_text(encoding="utf-8").splitlines() if line.startswith("id:")),
                        "",
                    )
                    print(json.dumps({{"schema": {podway_output_schema!r}, "command": "procedure.preview", "result": {{"schema": "podway.procedure-preview-result/v1", "admissible": {podway_procedure_ok!r}, "procedure_id": procedure_id}}}}))
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
        if gaori_mcp_mode == "wrong-command":
            names.append("wrong-gaori")
        if ouroboros_mcp_mode == "wrong-command":
            names.append("wrong-ooo")
        if isinstance(ouroboros_mcp_mode, str) and ouroboros_mcp_mode.startswith(
            "isolated"
        ):
            names.append("uvx")
        for name in names:
            executable = self.bin_directory / name
            executable.write_text(source, encoding="utf-8")
            executable.chmod(0o755)

    def install_lora_skill(self, name: str, root: Path | None = None) -> Path:
        skill_directory = (root or self.codex_home / "skills") / name
        skill_directory.mkdir(parents=True)
        skill_directory.joinpath("SKILL.md").write_text(
            f"---\nname: {name}\ndescription: Test skill.\n---\n", encoding="utf-8"
        )
        return skill_directory

    def write_project_mcp_config(
        self, name: str, *, startup: int = 30, timeout: int | None = None
    ) -> None:
        self.repository.joinpath(".codex").mkdir(exist_ok=True)
        if name == "mulgae":
            args = ["mcp", "--project-root", str(self.repository)]
            cwd = f"cwd = {json.dumps(str(self.repository))}\n"
            tool_timeout = timeout or 7501
        else:
            args = ["--repo", str(self.repository), "mcp"]
            cwd = ""
            tool_timeout = timeout or 3601
        self.repository.joinpath(".codex/config.toml").write_text(
            f"[mcp_servers.{name}]\n"
            f"command = {json.dumps(str(self.bin_directory / name))}\n"
            f"args = {json.dumps(args)}\n"
            f"{cwd}"
            "enabled = true\n"
            + ("required = true\n" if name == "mulgae" else "")
            + (f"startup_timeout_sec = {startup}\n" if name == "mulgae" else "")
            + f"tool_timeout_sec = {tool_timeout}\n",
            encoding="utf-8",
        )

    def install_deslop_skill(
        self,
        root: Path | None = None,
        name: str = "deslop",
        include_license: bool = True,
    ) -> Path:
        skill_directory = (root or self.codex_home / "skills") / "deslop"
        skill_directory.mkdir(parents=True)
        skill_directory.joinpath("SKILL.md").write_text(
            f"---\nname: {name}\ndescription: Test skill.\n---\n", encoding="utf-8"
        )
        if include_license:
            skill_directory.joinpath("LICENSE").write_text(
                "MIT License\n", encoding="utf-8"
            )
        return skill_directory

    def install_humanizer_skill(
        self,
        root: Path | None = None,
        *,
        name: str = "humanizer",
        version: str = "2.11.1",
        include_license: bool = True,
    ) -> Path:
        skill_directory = (root or self.home / ".agents/skills") / "humanizer"
        skill_directory.mkdir(parents=True)
        skill_directory.joinpath("SKILL.md").write_text(
            "---\n"
            f"name: {name}\n"
            "description: Test skill.\n"
            "metadata:\n"
            f'  version: "{version}"\n'
            "---\n",
            encoding="utf-8",
        )
        if include_license:
            skill_directory.joinpath("LICENSE").write_text(
                "MIT License\n", encoding="utf-8"
            )
        return skill_directory

    def install_im_not_ai_skill(
        self,
        root: Path | None = None,
        *,
        name: str = "humanize-korean",
        include_license: bool = True,
    ) -> Path:
        skill_directory = (root or self.codex_home / "skills") / "humanize-korean"
        skill_directory.mkdir(parents=True)
        for relative_path in inspect_tools.HUMANIZE_KOREAN_SKILL_FILES:
            path = skill_directory / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            if relative_path == "SKILL.md":
                path.write_text(
                    f"---\nname: {name}\ndescription: Test skill.\n---\n",
                    encoding="utf-8",
                )
            elif relative_path == "LICENSE":
                if include_license:
                    path.write_text("MIT License\n", encoding="utf-8")
            else:
                path.write_text(f"# {path.name}\n", encoding="utf-8")
        return skill_directory

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
        references = (
            ("lifecycle", "authoring", "recovery") if complete else ("lifecycle",)
        )
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
        skill_root = (root or self.codex_home / "skills") / "use-podway"
        skill_root.joinpath("references").mkdir(parents=True, exist_ok=True)
        skill_root.joinpath("SKILL.md").write_text(
            f"---\nname: {name}\ndescription: test\n---\n", encoding="utf-8"
        )
        if complete:
            for reference in ("lifecycle.md", "goal.md", "recovery.md"):
                skill_root.joinpath("references", reference).write_text(
                    f"# {reference}\n", encoding="utf-8"
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

    def install_podway_v025_workarounds(self) -> None:
        self.install_managed_podway_procedures(tracked=False)
        procedures = self.repository / ".podway/procedures"
        goal = procedures / "aquarium-goal-v2.yaml"
        goal.write_text(
            goal.read_text(encoding="utf-8").replace(
                "        max_total_length: 1000000\n", "", 1
            ),
            encoding="utf-8",
        )
        for name in ("aquarium-task-v2.yaml", "aquarium-validation-v2.yaml"):
            procedure = procedures / name
            procedure.write_text(
                procedure.read_text(encoding="utf-8").replace(
                    "        max_item_length: 1200\n"
                    "        max_total_length: 1000000\n",
                    "        max_item_length: 1000\n",
                    1,
                ),
                encoding="utf-8",
            )
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
        self.assertEqual(payload["schema_version"], "aquarium-dev-setup-inspection.v12")
        self.assertEqual(
            payload["repository"]["worktree"],
            {"conflicted": 0, "staged": 0, "unstaged": 0, "untracked": 0},
        )
        self.assertEqual(payload["tools"]["sanho"]["status"], "missing")
        self.assertEqual(payload["tools"]["dolgorae"]["status"], "missing")
        self.assertEqual(payload["tools"]["sanho"]["agent_skill"]["status"], "missing")
        self.assertEqual(payload["tools"]["mulgae"]["status"], "missing")
        self.assertEqual(payload["tools"]["mulgae"]["agent_skill"]["status"], "missing")
        self.assertEqual(
            payload["tools"]["mulgae"]["mcp_registration"]["status"], "unavailable"
        )
        self.assertEqual(payload["tools"]["gaori"]["agent_skill"]["status"], "missing")
        self.assertEqual(
            payload["tools"]["gaori"]["mcp_registration"]["status"], "unavailable"
        )
        self.assertEqual(payload["tools"]["lora"]["status"], "missing")
        self.assertEqual(payload["tools"]["deslop"]["status"], "missing")
        self.assertEqual(payload["tools"]["humanizer"]["status"], "missing")
        self.assertEqual(payload["tools"]["im-not-ai"]["status"], "missing")
        self.assertNotIn("podway", payload["tools"])

    def test_dolgorae_requires_exact_official_machine_binary(self) -> None:
        executable = self.bin_directory / "dolgorae"
        executable.write_text(
            """#!/bin/sh
printf '%s\\n' '{"schema_version":1,"ok":true,"command":"version","invocation_id":"019d0000-0000-7000-8000-000000000000","data":{"text":"dolgorae 0.1.0"}}'
""",
            encoding="utf-8",
        )
        executable.chmod(0o700)
        digest = hashlib.sha256(executable.read_bytes()).hexdigest()
        with (
            mock.patch.dict(os.environ, self.environment, clear=True),
            mock.patch.object(inspect_tools, "DOLGORAE_EXECUTABLE_SHA256", digest),
            mock.patch.object(inspect_tools.platform, "system", return_value="Darwin"),
            mock.patch.object(inspect_tools.platform, "machine", return_value="arm64"),
        ):
            tool = inspect_tools.inspect_dolgorae(
                self.repository, NORMAL_PROBE_TIMEOUT_SECONDS
            )

        self.assertEqual(tool["status"], "installed")
        self.assertEqual(tool["version"], "0.1.0")
        self.assertTrue(tool["version_supported"])
        self.assertTrue(tool["official_executable"])
        self.assertEqual(tool["executable_sha256"], digest)

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
            'version: 3\nexecution:\n  workspace_access: "none"\ncredential: hidden\n',
            encoding="utf-8",
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
        self.install_deslop_skill()
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
            tools["sanho"]["probes"]["status"]["result"]["sync_preview"][
                "conflict_count"
            ],
            1,
        )
        self.assertEqual(tools["mulgae"]["version"], "v0.1.18")
        self.assertTrue(tools["mulgae"]["version_supported"])
        expected_mulgae_status = (
            "configured"
            if platform.system() == "Darwin"
            and platform.machine() in {"arm64", "aarch64"}
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
        self.assertEqual(tools["mulgae"]["health"]["config_v3"]["status"], "verified")
        zcode = tools["mulgae"]["provider_inventory"][1]
        self.assertEqual(zcode["binary_available"]["status"], "verified")
        self.assertEqual(zcode["cli_compatible"]["eligibility"], "eligible")
        self.assertEqual(tools["gaori"]["version"], "0.1.14")
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
        self.assertEqual(tools["lora"]["status"], "unverifiable")
        self.assertFalse(tools["lora"]["complete_tree_verified"])
        self.assertTrue(tools["lora"]["lore_setup_present"])
        self.assertFalse(tools["lora"]["skills"]["lore-commits"]["duplicate"])
        self.assertFalse(tools["lora"]["skills"]["lore-query"]["symlinked"])
        self.assertEqual(tools["deslop"]["status"], "unverifiable")
        self.assertTrue(tools["deslop"]["installed"])
        self.assertFalse(tools["deslop"]["complete_tree_verified"])
        self.assertEqual(tools["deslop"]["verification_scope"], "structure_only")

    def test_deslop_installation_with_extra_file_is_degraded(self) -> None:
        skill_directory = self.install_deslop_skill()
        skill_directory.joinpath("EXTRA.txt").write_text(
            "unexpected\n", encoding="utf-8"
        )

        deslop = json.loads(self.inspect().stdout)["tools"]["deslop"]

        self.assertEqual(deslop["status"], "degraded")
        self.assertFalse(deslop["installed"])
        self.assertEqual(
            deslop["agent_skill"]["installations"][0]["unexpected_entries"],
            ["EXTRA.txt"],
        )

    def test_deslop_invalid_frontmatter_is_degraded(self) -> None:
        self.install_deslop_skill(name="wrong-name")
        deslop = json.loads(self.inspect().stdout)["tools"]["deslop"]
        self.assertEqual(deslop["status"], "degraded")
        self.assertFalse(deslop["installed"])
        self.assertFalse(deslop["agent_skill"]["installations"][0]["frontmatter_valid"])

    def test_deslop_incomplete_installation_is_degraded(self) -> None:
        (self.codex_home / "skills/deslop").mkdir(parents=True)
        deslop = json.loads(self.inspect().stdout)["tools"]["deslop"]
        self.assertEqual(deslop["status"], "degraded")
        self.assertFalse(deslop["installed"])
        self.assertFalse(
            deslop["agent_skill"]["installations"][0]["skill_file_present"]
        )

    def test_deslop_installation_without_license_is_degraded(self) -> None:
        self.install_deslop_skill(include_license=False)
        deslop = json.loads(self.inspect().stdout)["tools"]["deslop"]
        self.assertEqual(deslop["status"], "degraded")
        self.assertFalse(deslop["installed"])
        self.assertFalse(
            deslop["agent_skill"]["installations"][0]["license_file_present"]
        )

    def test_deslop_duplicate_installations_are_degraded(self) -> None:
        self.install_deslop_skill()
        self.install_deslop_skill(root=self.home / ".agents/skills")
        deslop = json.loads(self.inspect().stdout)["tools"]["deslop"]
        self.assertEqual(deslop["status"], "degraded")
        self.assertFalse(deslop["installed"])
        self.assertTrue(deslop["agent_skill"]["duplicate"])
        self.assertEqual(len(deslop["agent_skill"]["installations"]), 2)

    def test_deslop_symlink_installation_is_degraded(self) -> None:
        source = self.install_deslop_skill(root=self.base / "source-skills")
        target_root = self.codex_home / "skills"
        target_root.mkdir(parents=True, exist_ok=True)
        target_root.joinpath("deslop").symlink_to(source, target_is_directory=True)
        deslop = json.loads(self.inspect().stdout)["tools"]["deslop"]
        self.assertEqual(deslop["status"], "degraded")
        self.assertFalse(deslop["installed"])
        self.assertTrue(deslop["agent_skill"]["installations"][0]["symlinked"])

    def test_writing_skill_installations_are_structurally_unverifiable(self) -> None:
        self.install_humanizer_skill()
        self.install_im_not_ai_skill()

        tools = json.loads(self.inspect().stdout)["tools"]

        humanizer = tools["humanizer"]
        self.assertTrue(humanizer["installed"])
        self.assertEqual(humanizer["status"], "unverifiable")
        self.assertEqual(humanizer["version"], "2.11.1")
        self.assertTrue(humanizer["version_supported"])
        self.assertEqual(humanizer["supported_release"], "v2.11.1")
        self.assertEqual(
            humanizer["expected_target"],
            str(self.home / ".agents/skills/humanizer"),
        )
        self.assertEqual(
            humanizer["agent_skill"]["installations"][0]["unexpected_entries"],
            [],
        )

        im_not_ai = tools["im-not-ai"]
        self.assertTrue(im_not_ai["installed"])
        self.assertEqual(im_not_ai["status"], "unverifiable")
        self.assertIsNone(im_not_ai["version"])
        self.assertIsNone(im_not_ai["version_supported"])
        self.assertEqual(im_not_ai["supported_release"], "v2.3.2")
        self.assertEqual(
            im_not_ai["expected_target"],
            str(self.codex_home / "skills/humanize-korean"),
        )
        self.assertEqual(
            im_not_ai["agent_skill"]["installations"][0]["unexpected_entries"],
            [],
        )

    def test_writing_skill_extra_missing_and_symlinked_files_are_degraded(self) -> None:
        humanizer = self.install_humanizer_skill()
        humanizer.joinpath("README.md").write_text("extra\n", encoding="utf-8")
        self.install_im_not_ai_skill(include_license=False)

        tools = json.loads(self.inspect().stdout)["tools"]

        self.assertEqual(tools["humanizer"]["status"], "degraded")
        self.assertFalse(tools["humanizer"]["installed"])
        self.assertEqual(
            tools["humanizer"]["agent_skill"]["installations"][0]["unexpected_entries"],
            ["README.md"],
        )
        self.assertEqual(tools["im-not-ai"]["status"], "degraded")
        self.assertFalse(tools["im-not-ai"]["installed"])

        shutil.rmtree(self.codex_home / "skills/humanize-korean")
        source = self.install_im_not_ai_skill(root=self.base / "source-skills")
        (self.codex_home / "skills").mkdir(parents=True, exist_ok=True)
        (self.codex_home / "skills/humanize-korean").symlink_to(
            source, target_is_directory=True
        )
        im_not_ai = json.loads(self.inspect().stdout)["tools"]["im-not-ai"]
        self.assertEqual(im_not_ai["status"], "degraded")
        self.assertTrue(im_not_ai["agent_skill"]["installations"][0]["symlinked"])

    def test_writing_skill_duplicates_and_invalid_frontmatter_are_degraded(
        self,
    ) -> None:
        self.install_humanizer_skill(name="wrong-name")
        self.install_humanizer_skill(root=self.codex_home / "skills")

        humanizer = json.loads(self.inspect().stdout)["tools"]["humanizer"]

        self.assertEqual(humanizer["status"], "degraded")
        self.assertFalse(humanizer["installed"])
        self.assertTrue(humanizer["agent_skill"]["duplicate"])
        self.assertTrue(
            any(
                not installation["frontmatter_valid"]
                for installation in humanizer["agent_skill"]["installations"]
            )
        )

    def test_writing_skills_in_noncanonical_roots_are_degraded(self) -> None:
        self.install_humanizer_skill(root=self.codex_home / "skills")
        self.install_im_not_ai_skill(root=self.home / ".agents/skills")

        tools = json.loads(self.inspect().stdout)["tools"]

        self.assertEqual(tools["humanizer"]["status"], "degraded")
        self.assertFalse(tools["humanizer"]["installed"])
        self.assertEqual(tools["im-not-ai"]["status"], "degraded")
        self.assertFalse(tools["im-not-ai"]["installed"])

    def test_humanizer_requires_the_pinned_supported_release(self) -> None:
        self.install_humanizer_skill(version="2.10.0")

        humanizer = json.loads(self.inspect().stdout)["tools"]["humanizer"]

        self.assertFalse(humanizer["installed"])
        self.assertFalse(humanizer["version_supported"])
        self.assertEqual(humanizer["status"], "degraded")

    def test_writing_skill_version_reader_rejects_a_special_skill_file(self) -> None:
        skill_directory = self.home / ".agents/skills/humanizer"
        skill_directory.mkdir(parents=True)
        skill_directory.joinpath("SKILL.md").mkdir()
        skill_directory.joinpath("LICENSE").write_text(
            "MIT License\n", encoding="utf-8"
        )

        with mock.patch(
            "inspect_tools.frontmatter_version",
            side_effect=AssertionError("unsafe version read"),
        ) as version_reader:
            humanizer = json.loads(self.inspect().stdout)["tools"]["humanizer"]

        version_reader.assert_not_called()
        self.assertFalse(humanizer["installed"])
        self.assertEqual(humanizer["status"], "degraded")

    def test_im_not_ai_target_follows_effective_codex_home(self) -> None:
        self.install_im_not_ai_skill()

        im_not_ai = json.loads(self.inspect().stdout)["tools"]["im-not-ai"]

        self.assertEqual(
            im_not_ai["expected_target"],
            str(self.codex_home / "skills/humanize-korean"),
        )
        self.assertTrue(im_not_ai["installed"])

    def test_im_not_ai_target_anchors_relative_codex_home_to_cwd(self) -> None:
        relative_home = Path("relative-codex")
        expected_home = self.base / relative_home
        self.install_im_not_ai_skill(root=expected_home / "skills")
        self.environment["CODEX_HOME"] = str(relative_home)

        with (
            mock.patch.dict(os.environ, self.environment, clear=True),
            mock.patch.object(inspect_tools.Path, "cwd", return_value=self.base),
        ):
            im_not_ai = inspect_tools.inspect_im_not_ai()

        self.assertEqual(
            im_not_ai["expected_target"],
            str(expected_home / "skills/humanize-korean"),
        )
        self.assertTrue(im_not_ai["installed"])
        self.assertEqual(im_not_ai["status"], "unverifiable")

    def test_symlinked_writing_skill_root_is_not_walked(self) -> None:
        external_home = self.base / "external-codex"
        self.install_im_not_ai_skill(root=external_home / "skills")
        symlink_home = self.base / "codex-link"
        symlink_home.symlink_to(external_home, target_is_directory=True)
        self.environment["CODEX_HOME"] = str(symlink_home)

        im_not_ai = json.loads(self.inspect().stdout)["tools"]["im-not-ai"]

        installation = im_not_ai["agent_skill"]["installations"][0]
        self.assertTrue(installation["symlinked"])
        self.assertEqual(installation["unexpected_entries"], ["<unsafe-or-unreadable>"])

    def test_symlinked_codex_home_is_not_traversed_for_skills(self) -> None:
        external_home = self.base / "external-codex"
        self.install_gaori_skill(root=external_home / "skills")
        symlink_home = self.base / "codex-link"
        symlink_home.symlink_to(external_home, target_is_directory=True)
        self.environment["CODEX_HOME"] = str(symlink_home)

        skill = json.loads(self.inspect().stdout)["tools"]["gaori"]["agent_skill"]

        self.assertEqual(skill["status"], "degraded")
        installation = skill["installations"][0]
        self.assertTrue(installation["symlinked"])
        self.assertFalse(installation["frontmatter_valid"])
        self.assertTrue(all(item["sha256"] is None for item in installation["files"]))

    def test_deep_symlinked_codex_home_ancestor_is_not_traversed(self) -> None:
        external_home = self.base / "external-codex"
        self.install_gaori_skill(root=external_home / "nested/skills")
        linked_parent = self.base / "linked-parent"
        linked_parent.symlink_to(external_home, target_is_directory=True)
        self.environment["CODEX_HOME"] = str(linked_parent / "nested")

        skill = json.loads(self.inspect().stdout)["tools"]["gaori"]["agent_skill"]

        self.assertEqual(skill["status"], "degraded")
        installation = skill["installations"][0]
        self.assertTrue(installation["symlinked"])
        self.assertTrue(all(item["sha256"] is None for item in installation["files"]))

    def test_codex_home_symlink_before_dotdot_is_not_normalized_away(self) -> None:
        external = self.base / "external-codex"
        (external / "child").mkdir(parents=True)
        self.install_gaori_skill(root=external / "skills")
        self.install_gaori_skill(root=self.base / "skills")
        jump = self.base / "jump"
        jump.symlink_to(external / "child", target_is_directory=True)
        self.environment["CODEX_HOME"] = str(jump / "..")

        skill = json.loads(self.inspect().stdout)["tools"]["gaori"]["agent_skill"]

        self.assertEqual(skill["status"], "degraded")
        self.assertTrue(skill["installations"][0]["symlinked"])
        self.assertTrue(
            all(item["sha256"] is None for item in skill["installations"][0]["files"])
        )

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
        self.assertTrue(
            all(item["matches_source"] for item in podway["managed_procedures"])
        )
        self.assertTrue(
            all(
                item["source_state"] == "canonical"
                for item in podway["managed_procedures"]
            )
        )
        self.assertEqual(
            podway["migration_kinds"],
            {"product_rename": False},
        )
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
            podway = inspect_tools.inspect_podway(
                self.repository.resolve(), NORMAL_PROBE_TIMEOUT_SECONDS
            )
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

    def test_managed_procedure_checks_report_validity_without_payload(self) -> None:
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
                    },
                )
                self.assertEqual(
                    entry["preview"],
                    {
                        "attempted": True,
                        "ok": True,
                        "exit_code": 0,
                        "timed_out": False,
                        "output_schema": "podway.output/v3",
                        "result_schema": "podway.procedure-preview-result/v1",
                        "admissible": True,
                        "procedure_id": Path(entry["path"]).stem,
                    },
                )

    def test_symlinked_managed_procedure_is_never_hashed_or_checked(self) -> None:
        self.install_fake_tools()
        self.install_managed_podway_procedures(tracked=False)
        target = self.repository / ".podway/procedures/aquarium-task-v2.yaml"
        external = self.base / "external-procedure.yaml"
        external.write_bytes(
            (
                ROOT / "plugins/aquarium/assets/podway/procedures/aquarium-task-v2.yaml"
            ).read_bytes()
        )
        target.unlink()
        target.symlink_to(external)

        podway = json.loads(self.inspect(include_podway=True).stdout)["tools"]["podway"]
        entry = next(
            item
            for item in podway["managed_procedures"]
            if item["path"].endswith("aquarium-task-v2.yaml")
        )

        self.assertEqual(podway["readiness_status"], "degraded")
        self.assertTrue(entry["symlinked"])
        self.assertFalse(entry["present"])
        self.assertEqual(entry["source_state"], "unsafe")
        self.assertIsNone(entry["installed_sha256"])
        self.assertNotIn("check", entry)

    def test_partial_or_invalid_managed_procedures_are_degraded(self) -> None:
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
        states = {entry["path"]: entry for entry in podway["managed_procedures"]}
        self.assertEqual(
            states[".podway/procedures/aquarium-task-v2.yaml"]["source_state"],
            "invalid",
        )
        self.assertIn("check", states[".podway/procedures/aquarium-task-v2.yaml"])
        self.assertEqual(
            states[".podway/procedures/aquarium-goal-v2.yaml"]["source_state"],
            "missing",
        )
        self.assertFalse(podway["migration_required"])

    def test_valid_same_id_customization_is_ready_and_not_overwritten(self) -> None:
        self.install_fake_tools()
        self.install_managed_podway_procedures()
        target = self.repository / ".podway/procedures/aquarium-task-v2.yaml"
        customized = target.read_text(encoding="utf-8").replace(
            "Record the approved plan and its authority boundary.",
            "Record the locally customized plan and its authority boundary.",
            1,
        )
        target.write_text(customized, encoding="utf-8")
        before = target.read_bytes()

        with (
            mock.patch.dict(os.environ, self.environment),
            mock.patch("inspect_tools.platform.system", return_value="Darwin"),
            mock.patch("inspect_tools.platform.machine", return_value="arm64"),
        ):
            podway = inspect_tools.inspect_podway(
                self.repository.resolve(), NORMAL_PROBE_TIMEOUT_SECONDS
            )

        entry = next(
            item
            for item in podway["managed_procedures"]
            if item["path"].endswith("aquarium-task-v2.yaml")
        )
        self.assertEqual(entry["source_state"], "valid_customization")
        self.assertEqual(entry["update_explanation"], "local_customization")
        self.assertFalse(entry["matches_source"])
        self.assertEqual(entry["preview"]["procedure_id"], "aquarium-task-v2")
        self.assertEqual(podway["readiness_status"], "ready")
        self.assertEqual(podway["status"], "configured")
        self.assertEqual(target.read_bytes(), before)
        self.assertFalse(
            (self.repository / ".podway/procedure-ownership.json").exists()
        )

    def test_valid_wrong_id_content_is_invalid(self) -> None:
        self.install_fake_tools()
        self.install_managed_podway_procedures()
        target = self.repository / ".podway/procedures/aquarium-task-v2.yaml"
        target.write_text(
            target.read_text(encoding="utf-8").replace(
                "id: aquarium-task-v2", "id: custom-task-v2", 1
            ),
            encoding="utf-8",
        )

        podway = json.loads(self.inspect(include_podway=True).stdout)["tools"]["podway"]
        entry = next(
            item
            for item in podway["managed_procedures"]
            if item["path"].endswith("aquarium-task-v2.yaml")
        )
        self.assertEqual(entry["source_state"], "invalid")
        self.assertEqual(entry["preview"]["procedure_id"], "custom-task-v2")
        self.assertEqual(podway["readiness_status"], "degraded")

    def test_prior_canonical_identities_are_bounded_update_explanations(self) -> None:
        self.assertEqual(
            inspect_tools.PODWAY_PRIOR_CANONICAL_SHA256,
            {
                "aquarium-task-v2.yaml": {
                    "c666f17cf41e8a9403f610f89b0b7397352d8ac6e2e5e05e1c268fc0e6ece3d9",
                    "0ae730df9ca5854ff61b02679e3ac58aa4508ee35c5a09ba76c35e7d0ef3d45d",
                    "b703da6c798801a396d144be1c9c71e0fdb05c95e9e293386bf83c0d238ef927",
                },
                "aquarium-goal-v2.yaml": {
                    "90411e16758cb79a01294e008d9a091a52b341fc1e9bb968ce9521fed2910ec3",
                    "8ca12a8ba36e9dd035bc70c903b8a5a0a9e4fd6db00cf75e2448f66082ab6ac6",
                },
                "aquarium-validation-v2.yaml": {
                    "45192a644087b811eb34952576798ae4f3e85ebdf87c77fc8dc097d3c8bb2f50"
                },
                "aquarium-design-v2.yaml": {
                    "4ec653b2b4d740d77bcd4826f40288d9fadd7d696a3939c197b9789dbba824b6"
                },
                "aquarium-war-room-v2.yaml": {
                    "ca9f2363107b315e829ba9f0357d35cbc242d07fbbf5a4702868bbb781dee1cb"
                },
            },
        )

    def test_exact_podway_v025_workarounds_are_migration_eligible(self) -> None:
        self.install_fake_tools(podway_version="v0.2.5", podway_daemon_version="0.2.5")
        self.install_podway_v025_workarounds()

        podway = json.loads(self.inspect(include_podway=True).stdout)["tools"]["podway"]

        states = {
            Path(entry["path"]).name: entry for entry in podway["managed_procedures"]
        }
        for name in (
            "aquarium-task-v2.yaml",
            "aquarium-goal-v2.yaml",
            "aquarium-validation-v2.yaml",
        ):
            self.assertEqual(states[name]["source_state"], "valid_customization")
            self.assertEqual(
                states[name]["update_explanation"], "podway_v0.2.5_workaround"
            )
            self.assertFalse(states[name]["matches_source"])
            self.assertIn("check", states[name])
        for name in ("aquarium-design-v2.yaml", "aquarium-war-room-v2.yaml"):
            self.assertEqual(states[name]["source_state"], "canonical")
        self.assertEqual(
            podway["migration_kinds"],
            {"product_rename": False},
        )
        self.assertFalse(podway["migration_required"])
        self.assertEqual(podway["readiness_status"], "degraded")

    def test_renamed_managed_procedures_require_explicit_migration(self) -> None:
        self.install_fake_tools()
        self.install_managed_podway_procedures()
        legacy = self.repository / ".podway/procedures/root-kernel-task-v2.yaml"
        legacy.write_text("schema: podway.procedure/v2\n", encoding="utf-8")
        completed = self.inspect(include_podway=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        podway = json.loads(completed.stdout)["tools"]["podway"]
        self.assertTrue(podway["migration_required"])
        self.assertEqual(
            podway["migration_kinds"],
            {"product_rename": True},
        )
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

    def test_managed_procedures_without_initialized_workspace_are_degraded(
        self,
    ) -> None:
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
        self.install_fake_tools(podway_version="v0.3.0", podway_daemon_version="0.2.7")
        self.install_managed_podway_procedures()
        completed = self.inspect(include_podway=True)
        podway = json.loads(completed.stdout)["tools"]["podway"]
        self.assertFalse(podway["version_supported"])
        self.assertFalse(podway["versions_match"])
        self.assertEqual(podway["readiness_status"], "degraded")

    def test_podway_v027_is_the_minimum_supported_release(self) -> None:
        for version, supported in (
            ("v0.2.0", False),
            ("v0.2.2", False),
            ("v0.2.3", False),
            ("v0.2.4", False),
            ("v0.2.5", False),
            ("v0.2.6", False),
            ("v0.2.7", True),
            ("v0.2.7-rc.1", False),
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
                        self.repository.resolve(), NORMAL_PROBE_TIMEOUT_SECONDS
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
                        self.repository.resolve(), NORMAL_PROBE_TIMEOUT_SECONDS
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
            podway = inspect_tools.inspect_podway(
                self.repository.resolve(), NORMAL_PROBE_TIMEOUT_SECONDS
            )
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
            podway = inspect_tools.inspect_podway(
                self.repository.resolve(), NORMAL_PROBE_TIMEOUT_SECONDS
            )
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
                podway = json.loads(self.inspect(include_podway=True).stdout)["tools"][
                    "podway"
                ]
                self.assertEqual(podway["agent_skill"]["status"], "degraded")
                self.assertEqual(podway["readiness_status"], "not_configured")
                self.assertEqual(
                    podway["agent_skill"]["duplicate"], case == "duplicate"
                )

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

    def test_daemon_wait_ready_requires_completed_ready_recovery(self) -> None:
        cases = (
            ({}, "ready", True, None),
            (
                {
                    "podway_readiness_state": "recovering",
                    "podway_readiness_stage": "workspaces",
                    "podway_worktree_recovery": (2, 1, 0),
                },
                "degraded",
                True,
                None,
            ),
            (
                {"podway_worktree_recovery": (1, 1, 1)},
                "ready",
                True,
                None,
            ),
            (
                {"podway_worktree_recovery": None},
                "degraded",
                False,
                "invalid_daemon_readiness",
            ),
        )
        for options, readiness, probe_ok, error_code in cases:
            with self.subTest(options=options):
                for executable in self.bin_directory.iterdir():
                    executable.unlink()
                self.install_fake_tools(
                    podway_daemon_status_schema="podway.daemon-status-result/v2",
                    **options,
                )
                self.install_managed_podway_procedures()
                with (
                    mock.patch.dict(os.environ, self.environment),
                    mock.patch("inspect_tools.platform.system", return_value="Darwin"),
                    mock.patch("inspect_tools.platform.machine", return_value="arm64"),
                ):
                    podway = inspect_tools.inspect_podway(
                        self.repository.resolve(), NORMAL_PROBE_TIMEOUT_SECONDS
                    )
                daemon = podway["probes"]["daemon_status"]
                self.assertEqual(podway["readiness_status"], readiness)
                self.assertEqual(daemon["ok"], probe_ok)
                self.assertEqual(daemon.get("error_code"), error_code)

    def test_daemon_wait_ready_rejects_legacy_status_result(self) -> None:
        self.install_fake_tools(
            podway_daemon_status_schema="podway.daemon-status-result/v1"
        )
        self.install_managed_podway_procedures()
        with (
            mock.patch.dict(os.environ, self.environment),
            mock.patch("inspect_tools.platform.system", return_value="Darwin"),
            mock.patch("inspect_tools.platform.machine", return_value="arm64"),
        ):
            podway = inspect_tools.inspect_podway(
                self.repository.resolve(), NORMAL_PROBE_TIMEOUT_SECONDS
            )

        daemon = podway["probes"]["daemon_status"]
        self.assertFalse(daemon["ok"])
        self.assertEqual(daemon["error_code"], "unexpected_result_schema")
        self.assertEqual(podway["readiness_status"], "degraded")

    def test_active_session_inventory_exposes_state_without_identity(self) -> None:
        self.install_fake_tools(podway_active_session=True)
        self.install_managed_podway_procedures()
        with (
            mock.patch.dict(os.environ, self.environment),
            mock.patch("inspect_tools.platform.system", return_value="Darwin"),
            mock.patch("inspect_tools.platform.machine", return_value="arm64"),
        ):
            podway = inspect_tools.inspect_podway(
                self.repository.resolve(), NORMAL_PROBE_TIMEOUT_SECONDS
            )
        session = podway["probes"]["session_status"]["result"]
        self.assertTrue(session["procedure_present"])
        self.assertTrue(session["procedure_schema_valid"])
        self.assertTrue(session["current_graph_node_present"])
        self.assertEqual(session["session_lifecycle"], "running")
        self.assertEqual(session["goal_revision"], 2)
        self.assertEqual(podway["readiness_status"], "ready")
        self.assertNotIn("sensitive goal text", json.dumps(podway))
        self.assertNotIn("sensitive evidence", json.dumps(podway))

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
            podway = inspect_tools.inspect_podway(
                self.repository.resolve(), NORMAL_PROBE_TIMEOUT_SECONDS
            )
        session = podway["probes"]["session_status"]["result"]
        self.assertTrue(session["session_present"])
        self.assertEqual(session["session_lifecycle"], "prepared")
        self.assertEqual(session["session_revision"], 0)
        self.assertFalse(session["current_graph_node_present"])
        self.assertIsNone(session["goal_revision"])
        self.assertEqual(podway["readiness_status"], "ready")

    def test_malformed_json_and_timeout_degrade_only_the_affected_probes(self) -> None:
        self.install_mulgae_config()
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
        self.assertEqual(tools["mulgae"]["version"], "v0.1.18")
        self.assertFalse(tools["mulgae"]["probes"]["doctor"]["ok"])
        self.assertEqual(tools["mulgae"]["probes"]["doctor"]["exit_code"], 4)
        self.assertEqual(
            tools["mulgae"]["health"]["config_v3"]["reason_codes"],
            [],
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
                skill = json.loads(self.inspect().stdout)["tools"]["sanho"][
                    "agent_skill"
                ]
                self.assertEqual(skill["status"], "degraded")
                self.assertEqual(skill["duplicate"], case == "duplicate")

    def test_mulgae_version_and_installation_prerequisites_are_explicit(self) -> None:
        cases = (
            ("v0.1.14", False, "degraded"),
            ("v0.1.15", False, "degraded"),
            ("v0.1.16", False, "degraded"),
            ("v0.1.17", False, "degraded"),
            ("v0.1.18", True, "installed"),
            ("v0.1.018", False, "degraded"),
            ("v0.1.0018", False, "degraded"),
            ("v0.1.18-rc.1", False, "degraded"),
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
                    mulgae = inspect_tools.inspect_mulgae(
                        self.repository.resolve(), NORMAL_PROBE_TIMEOUT_SECONDS
                    )
                self.assertEqual(mulgae["version_supported"], supported)
                self.assertEqual(mulgae["status"], status)

        for version, observed_version, supported in (
            ("go1.26.5", "go1.26.5", False),
            ("go1.26.6", "go1.26.6", True),
            ("go1.26.06", None, False),
            ("go01.26.6", None, False),
            ("go1.27.0", "go1.27.0", True),
        ):
            with self.subTest(go_version=version):
                for executable in self.bin_directory.iterdir():
                    executable.unlink()
                self.install_fake_tools(go_version=version)
                mulgae = json.loads(self.inspect().stdout)["tools"]["mulgae"]
                go = mulgae["installation_prerequisites"]["go"]
                self.assertEqual(go["version"], observed_version)
                self.assertEqual(go["supported"], supported)

    def test_mulgae_config_v3_pair_and_private_policy_are_verified(self) -> None:
        self.install_fake_tools()
        self.install_mulgae_config()
        with (
            mock.patch.dict(os.environ, self.environment),
            mock.patch("inspect_tools.platform.system", return_value="Darwin"),
            mock.patch("inspect_tools.platform.machine", return_value="arm64"),
        ):
            mulgae = inspect_tools.inspect_mulgae(
                self.repository.resolve(), NORMAL_PROBE_TIMEOUT_SECONDS
            )
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
            insecure = inspect_tools.inspect_mulgae(
                self.repository.resolve(), NORMAL_PROBE_TIMEOUT_SECONDS
            )
        self.assertEqual(insecure["status"], "degraded")

        self.repository.joinpath(".mulgae/local.yaml").chmod(0o600)
        self.git("add", "-f", ".mulgae/local.yaml")
        with (
            mock.patch.dict(os.environ, self.environment),
            mock.patch("inspect_tools.platform.system", return_value="Darwin"),
            mock.patch("inspect_tools.platform.machine", return_value="arm64"),
        ):
            tracked = inspect_tools.inspect_mulgae(
                self.repository.resolve(), NORMAL_PROBE_TIMEOUT_SECONDS
            )
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
            mulgae = inspect_tools.inspect_mulgae(
                self.repository.resolve(), NORMAL_PROBE_TIMEOUT_SECONDS
            )
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
            inspect_tools.inspect_mulgae(
                self.repository.resolve(), NORMAL_PROBE_TIMEOUT_SECONDS
            )

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
        self.assertEqual(mulgae["probes"]["doctor"]["reason"], "configuration_missing")
        self.assertEqual(mulgae["health"]["doctor_contract"], "not_observed")

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
        self.install_fake_tools(mulgae_output_schema="mulgae-command-result.v4")
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
                skill = json.loads(self.inspect().stdout)["tools"]["mulgae"][
                    "agent_skill"
                ]
                self.assertEqual(skill["status"], "degraded")
                self.assertEqual(skill["duplicate"], case == "duplicate")

    def test_mulgae_mcp_registration_is_scoped_and_sanitized(self) -> None:
        self.write_project_mcp_config("mulgae")
        self.install_fake_tools(mulgae_mcp_mode="configured")
        completed = self.inspect()
        self.assertNotIn("must-not-leak", completed.stdout)
        registration = json.loads(completed.stdout)["tools"]["mulgae"][
            "mcp_registration"
        ]
        self.assertEqual(registration["status"], "configured")
        self.assertEqual(registration["preferred_scope"], "global")
        self.assertEqual(registration["effective_scope"], "local")
        self.assertTrue(registration["local_confirmation_required"])
        self.assertEqual(
            registration["recommendation"],
            "confirm_local_intent_or_migrate_to_global",
        )
        local = registration["local"]
        self.assertEqual(registration["global"]["status"], "missing")
        self.assertTrue(local["enabled"])
        self.assertTrue(local["stdio"])
        self.assertTrue(local["repository_bound"])
        self.assertTrue(local["arguments_match"])
        self.assertTrue(local["cwd_bound"])
        self.assertTrue(local["required"])
        self.assertEqual(local["required_verification"], "verified")
        self.assertEqual(local["required_output_capability"], "reported")
        self.assertIsNone(local["compatibility_reason"])
        self.assertEqual(registration["codex_version"], "0.149.0")
        self.assertTrue(local["binary_matches_selected"])
        self.assertEqual(local["startup_timeout_sec"], 30)
        self.assertEqual(local["tool_timeout_sec"], 7501)

    def test_mulgae_mcp_registration_accepts_larger_timeouts(self) -> None:
        self.write_project_mcp_config("mulgae", startup=31, timeout=7502)
        self.install_fake_tools(mulgae_mcp_mode="higher-timeout")
        registration = json.loads(self.inspect().stdout)["tools"]["mulgae"][
            "mcp_registration"
        ]
        self.assertEqual(registration["status"], "configured")
        self.assertEqual(registration["local"]["startup_timeout_sec"], 31)
        self.assertEqual(registration["local"]["tool_timeout_sec"], 7502)

    def test_global_mcp_registration_is_preferred_without_local_entry(self) -> None:
        self.repository.joinpath(".codex").mkdir()
        self.repository.joinpath(".codex/config.toml").write_text(
            '[mcp_servers.other]\ncommand = "other"\nargs = []\n',
            encoding="utf-8",
        )
        self.install_fake_tools(
            mulgae_mcp_mode="configured",
            mulgae_mcp_global=True,
            gaori_mcp_mode="configured",
            gaori_mcp_global=True,
        )

        tools = json.loads(self.inspect().stdout)["tools"]
        for name in ("mulgae", "gaori"):
            registration = tools[name]["mcp_registration"]
            self.assertEqual(registration["status"], "configured")
            self.assertEqual(registration["preferred_scope"], "global")
            self.assertEqual(registration["effective_scope"], "global")
            self.assertEqual(registration["global"]["status"], "configured")
            self.assertEqual(registration["local"]["status"], "missing")
            self.assertFalse(registration["local_confirmation_required"])
            self.assertEqual(registration["recommendation"], "none")

    def test_local_mcp_overrides_global_and_requires_confirmation(self) -> None:
        for name in ("mulgae", "gaori"):
            with self.subTest(name=name):
                shutil.rmtree(self.repository / ".codex", ignore_errors=True)
                for executable in self.bin_directory.iterdir():
                    executable.unlink()
                self.write_project_mcp_config(name)
                self.install_fake_tools(
                    mulgae_mcp_mode="configured" if name == "mulgae" else None,
                    mulgae_mcp_global=name == "mulgae",
                    gaori_mcp_mode="configured" if name == "gaori" else None,
                    gaori_mcp_global=name == "gaori",
                )

                registration = json.loads(self.inspect().stdout)["tools"][name][
                    "mcp_registration"
                ]

                self.assertEqual(registration["status"], "configured")
                self.assertEqual(registration["effective_scope"], "local")
                self.assertEqual(registration["global"]["status"], "configured")
                self.assertEqual(registration["local"]["status"], "configured")
                self.assertTrue(registration["local_confirmation_required"])
                self.assertEqual(
                    registration["recommendation"],
                    "confirm_or_remove_local_registration",
                )

    def test_invalid_global_mcp_registration_is_degraded(self) -> None:
        self.install_fake_tools(
            mulgae_mcp_mode="disabled",
            mulgae_mcp_global=True,
            gaori_mcp_mode="disabled",
            gaori_mcp_global=True,
        )

        tools = json.loads(self.inspect().stdout)["tools"]

        for name in ("mulgae", "gaori"):
            with self.subTest(name=name):
                registration = tools[name]["mcp_registration"]
                self.assertEqual(registration["status"], "degraded")
                self.assertEqual(registration["effective_scope"], "global")
                self.assertEqual(registration["global"]["status"], "degraded")
                self.assertEqual(
                    registration["recommendation"], "repair_global_registration"
                )

    def test_global_mcp_probe_failure_is_not_treated_as_local_proof(self) -> None:
        self.write_project_mcp_config("mulgae")
        self.install_fake_tools(mulgae_mcp_mode="configured", mcp_neutral_failure=True)

        registration = json.loads(self.inspect().stdout)["tools"]["mulgae"][
            "mcp_registration"
        ]

        self.assertEqual(registration["status"], "degraded")
        self.assertEqual(registration["global"]["status"], "degraded")

    def test_repository_resolution_ignores_ambient_git_redirection(self) -> None:
        other = self.base / "other-repository"
        other.mkdir()
        subprocess.run(
            ["git", "init", "--quiet"],
            cwd=other,
            env=self.environment,
            check=True,
        )
        self.environment["GIT_DIR"] = str(other / ".git")
        self.environment["GIT_WORK_TREE"] = str(other)

        completed = self.inspect()
        result = json.loads(completed.stdout)

        self.assertEqual(completed.returncode, 0)
        self.assertEqual(Path(result["repository"]["root"]), self.repository.resolve())

    def test_mulgae_mcp_arbitrary_exit_one_is_degraded(self) -> None:
        self.write_project_mcp_config("mulgae")
        self.install_fake_tools(mulgae_mcp_mode="silent-failure")

        registration = json.loads(self.inspect().stdout)["tools"]["mulgae"][
            "mcp_registration"
        ]

        self.assertEqual(registration["status"], "degraded")
        self.assertEqual(registration["reason"], "registration_probe_failed")

    def test_named_mcp_absence_requires_clean_stdout_and_paired_quotes(self) -> None:
        base = {
            "exit_code": 1,
            "timed_out": False,
            "stdout": "",
            "stderr": "Error: No MCP server named 'mulgae' found.\n",
        }

        self.assertTrue(inspect_tools.named_mcp_server_missing(base, "mulgae"))
        self.assertFalse(
            inspect_tools.named_mcp_server_missing(
                {**base, "stdout": '{"unexpected":true}\n'}, "mulgae"
            )
        )
        self.assertFalse(
            inspect_tools.named_mcp_server_missing(
                {**base, "stderr": "Error: No MCP server named 'mulgae\" found.\n"},
                "mulgae",
            )
        )

    def test_ouroboros_absence_requires_exact_named_server_diagnostic(self) -> None:
        base = {
            "attempted": True,
            "ok": False,
            "exit_code": 1,
            "timed_out": False,
            "stdout": "",
            "stderr": "Error: No MCP server named 'ouroboros' found.\n",
        }

        self.assertEqual(
            inspect_tools.classify_ouroboros_registration(base, None)["status"],
            "missing",
        )
        for raw in (
            {**base, "stdout": '{"unexpected":true}\n'},
            {**base, "exit_code": 2},
            {**base, "stderr": "No MCP server named ouroboros found\n"},
        ):
            with self.subTest(raw=raw):
                self.assertEqual(
                    inspect_tools.classify_ouroboros_registration(raw, None)["status"],
                    "degraded",
                )

    def test_normalized_probe_drops_untrusted_json_fields(self) -> None:
        raw = {
            "attempted": True,
            "ok": True,
            "exit_code": 0,
            "timed_out": False,
            "result": {
                "version": "0.2.7",
                "credential": "AQUARIUM_QA_SYNTHETIC_SECRET",
            },
        }

        normalized = inspect_tools.normalized_probe(raw)

        self.assertNotIn("result", normalized)
        self.assertNotIn("credential", json.dumps(normalized))

    def test_json_probe_rejects_nonfinite_constants(self) -> None:
        for constant in ("NaN", "Infinity", "-Infinity", "1e309"):
            with self.subTest(constant=constant):
                probe = inspect_tools.parse_json_probe(
                    {
                        "attempted": True,
                        "ok": True,
                        "exit_code": 0,
                        "timed_out": False,
                        "stdout": f'{{"value":{constant}}}',
                    }
                )

                self.assertFalse(probe["ok"])
                self.assertEqual(probe["error_code"], "invalid_json")

        duplicate = inspect_tools.parse_json_probe(
            {
                "attempted": True,
                "ok": True,
                "exit_code": 0,
                "timed_out": False,
                "stdout": '{"version":"0.2.6","version":"0.2.7"}',
            }
        )

        self.assertFalse(duplicate["ok"])
        self.assertEqual(duplicate["error_code"], "invalid_json")

    def test_sanho_normalizers_emit_only_typed_aggregate_evidence(self) -> None:
        secret = "QA21_SYNTHETIC_SECRET"
        status = inspect_tools.normalize_sanho_status(
            {
                "attempted": True,
                "ok": True,
                "exit_code": 0,
                "timed_out": False,
                "result": {
                    "relation": {"known": True, "behind": secret, "ahead": 0},
                    "local_readiness": {
                        "sync": {"ready": False, "blocked_by": [secret]},
                        "pull": {"ready": False, "blocked_by": [secret]},
                    },
                },
            }
        )
        doctor = inspect_tools.normalize_sanho_doctor(
            {
                "attempted": True,
                "ok": True,
                "exit_code": 0,
                "timed_out": False,
                "result": {
                    "warnings": 0,
                    "checks": [{"name": secret, "severity": secret}],
                },
            }
        )

        self.assertFalse(status["contract_valid"])
        self.assertFalse(doctor["contract_valid"])
        self.assertNotIn(secret, json.dumps({"status": status, "doctor": doctor}))

    def test_untrusted_mulgae_and_podway_fields_are_not_reflected(self) -> None:
        secret = "QA21_SYNTHETIC_SECRET"
        mulgae = inspect_tools.normalize_mulgae_doctor(
            {
                "attempted": True,
                "ok": True,
                "exit_code": 0,
                "timed_out": False,
                "result": {
                    "schema_version": "mulgae-command-result.v5",
                    "result": {
                        "kind": secret,
                        "readiness": secret,
                        "doctor": {
                            "schema_version": "mulgae-doctor-result.v2",
                            "config": {"status": secret, "uri": secret},
                        },
                    },
                },
            }
        )
        podway, _ = inspect_tools.normalize_podway_envelope(
            {
                "attempted": True,
                "ok": False,
                "exit_code": 1,
                "timed_out": False,
                "result": {"schema": "podway.error/v1", "code": secret},
            },
            "session.status",
        )

        self.assertNotIn(secret, json.dumps({"mulgae": mulgae, "podway": podway}))
        self.assertEqual(podway["error_code"], "unrecognized_podway_error")

    def test_global_mcp_probe_rejects_mixed_named_missing_diagnostic(self) -> None:
        self.write_project_mcp_config("mulgae")
        self.install_fake_tools(
            mulgae_mcp_mode="configured", mcp_neutral_mixed_missing=True
        )

        registration = json.loads(self.inspect().stdout)["tools"]["mulgae"][
            "mcp_registration"
        ]

        self.assertEqual(registration["status"], "degraded")
        self.assertEqual(registration["global"]["status"], "degraded")

    def test_symlinked_mulgae_and_codex_configuration_skip_owning_probes(self) -> None:
        external = self.base / "external-config"
        external.mkdir()
        external.joinpath("config.yaml").write_text("version: 3\n", encoding="utf-8")
        external.joinpath("local.yaml").write_text("providers: {}\n", encoding="utf-8")
        external.joinpath("config.toml").write_text(
            "[mcp_servers.mulgae]\n", encoding="utf-8"
        )
        self.repository.joinpath(".mulgae").mkdir()
        self.repository.joinpath(".mulgae/config.yaml").symlink_to(
            external / "config.yaml"
        )
        self.repository.joinpath(".mulgae/local.yaml").symlink_to(
            external / "local.yaml"
        )
        self.repository.joinpath(".codex").mkdir()
        self.repository.joinpath(".codex/config.toml").symlink_to(
            external / "config.toml"
        )
        self.install_fake_tools(mulgae_mcp_mode="configured")

        mulgae = json.loads(self.inspect().stdout)["tools"]["mulgae"]

        self.assertEqual(mulgae["status"], "degraded")
        self.assertEqual(
            mulgae["probes"]["doctor"]["reason"], "configuration_symlinked"
        )
        self.assertIsNone(mulgae["configuration"][1]["mode"])
        self.assertEqual(
            mulgae["mcp_registration"]["reason"],
            "project_configuration_symlinked",
        )

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
                    self.inspect(timeout_seconds=NORMAL_PROBE_TIMEOUT_SECONDS).stdout
                )["tools"]["mulgae"]["mcp_registration"]
                self.assertEqual(registration["status"], "degraded")
                self.assertEqual(
                    registration["local"]["reason"], "registration_mismatch"
                )

    def test_mulgae_mcp_absent_required_is_compatible_but_unverifiable(self) -> None:
        self.write_project_mcp_config("mulgae")
        self.install_fake_tools(mulgae_mcp_mode="required-absent")
        registration = json.loads(self.inspect().stdout)["tools"]["mulgae"][
            "mcp_registration"
        ]
        self.assertEqual(registration["status"], "configured")
        local = registration["local"]
        self.assertIsNone(local["required"])
        self.assertEqual(local["required_verification"], "unverifiable")
        self.assertEqual(local["required_output_capability"], "not_reported")
        self.assertEqual(local["compatibility_reason"], "required_unverifiable")
        self.assertNotIn("reason", local)

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
        self.assertEqual(registration["local"]["required_output_capability"], "invalid")

    def test_mulgae_mcp_absence_is_not_cli_degradation(self) -> None:
        self.install_fake_tools(mulgae_mcp_mode="missing")
        mulgae = json.loads(self.inspect().stdout)["tools"]["mulgae"]
        self.assertEqual(mulgae["mcp_registration"]["status"], "missing")
        self.assertEqual(mulgae["mcp_registration"]["reason"], "registration_not_found")
        self.assertEqual(mulgae["mcp_registration"]["codex_version"], "0.149.0")
        self.assertEqual(
            mulgae["mcp_registration"]["recommendation"],
            "install_global_registration",
        )
        self.assertEqual(mulgae["probes"]["doctor"]["reason"], "configuration_missing")
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
                self.repository.resolve(),
                NORMAL_PROBE_TIMEOUT_SECONDS,
                require_mcp=False,
            )
            required = inspect_tools.inspect_mulgae(
                self.repository.resolve(),
                NORMAL_PROBE_TIMEOUT_SECONDS,
                require_mcp=True,
            )
        self.assertEqual(optional["status"], "configured")
        self.assertFalse(optional["mcp_required_for_status"])
        self.assertEqual(required["status"], "degraded")
        self.assertTrue(required["mcp_required_for_status"])

    def test_gaori_version_support_and_config_check_are_explicit(self) -> None:
        cases = (
            ("0.1.11", False, "degraded"),
            ("0.1.12", False, "degraded"),
            ("0.1.13", False, "degraded"),
            ("0.1.14", True, "configured"),
            ("v0.1.14-rc.1", False, "degraded"),
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

    def test_symlinked_gaori_configuration_is_not_probed(self) -> None:
        self.repository.joinpath(".gaori").mkdir()
        external = self.base / "credentials.yaml"
        external.write_text("credential-marker: secret\n", encoding="utf-8")
        self.repository.joinpath(".gaori/tester.yaml").symlink_to(external)
        self.install_fake_tools()

        completed = self.inspect()
        gaori = json.loads(completed.stdout)["tools"]["gaori"]
        configuration = gaori["configuration"][0]

        self.assertFalse(configuration["present"])
        self.assertTrue(configuration["symlinked"])
        self.assertFalse(gaori["probes"]["config_check"]["attempted"])
        self.assertNotIn("credential-marker", completed.stdout)

    def test_symlinked_gaori_rules_are_not_probed(self) -> None:
        self.repository.joinpath(".gaori/tester").mkdir(parents=True)
        self.repository.joinpath(".gaori/tester.yaml").write_text(
            "version: 2\n", encoding="utf-8"
        )
        external = self.base / "external-rules"
        external.mkdir()
        external.joinpath("example.yaml").write_text(
            "credential-marker: secret\n", encoding="utf-8"
        )
        self.repository.joinpath(".gaori/tester/rules").symlink_to(
            external, target_is_directory=True
        )
        self.install_fake_tools()

        completed = self.inspect()
        gaori = json.loads(completed.stdout)["tools"]["gaori"]

        self.assertFalse(gaori["probes"]["config_check"]["attempted"])
        self.assertEqual(
            gaori["probes"]["config_check"]["reason"], "configuration_symlinked"
        )
        self.assertNotIn("credential-marker", completed.stdout)

    def test_symlinked_gaori_rule_file_is_not_probed(self) -> None:
        rules = self.repository / ".gaori/tester/rules"
        rules.mkdir(parents=True)
        self.repository.joinpath(".gaori/tester.yaml").write_text(
            "version: 2\n", encoding="utf-8"
        )
        external = self.base / "external-rule.yaml"
        external.write_text("credential-marker: secret\n", encoding="utf-8")
        rules.joinpath("external.yaml").symlink_to(external)
        self.install_fake_tools()

        completed = self.inspect()
        gaori = json.loads(completed.stdout)["tools"]["gaori"]

        self.assertTrue(gaori["configuration"][1]["tree_symlinked"])
        self.assertFalse(gaori["probes"]["config_check"]["attempted"])
        self.assertNotIn("credential-marker", completed.stdout)

    def test_symlinked_gaori_toolchain_is_not_probed(self) -> None:
        self.repository.joinpath(".gaori").mkdir()
        self.repository.joinpath(".gaori/tester.yaml").write_text(
            "version: 2\n", encoding="utf-8"
        )
        external = self.base / "external-toolchain.yaml"
        external.write_text("credential-marker: secret\n", encoding="utf-8")
        self.repository.joinpath(".gaori/toolchain.yaml").symlink_to(external)
        self.install_fake_tools()

        completed = self.inspect()
        gaori = json.loads(completed.stdout)["tools"]["gaori"]

        self.assertFalse(gaori["probes"]["config_check"]["attempted"])
        self.assertNotIn("credential-marker", completed.stdout)

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
        self.write_project_mcp_config("gaori")
        self.install_fake_tools(gaori_mcp_mode="configured")
        completed = self.inspect()
        self.assertNotIn("must-not-leak", completed.stdout)
        registration = json.loads(completed.stdout)["tools"]["gaori"][
            "mcp_registration"
        ]
        self.assertEqual(registration["status"], "configured")
        self.assertEqual(registration["preferred_scope"], "global")
        self.assertEqual(registration["effective_scope"], "local")
        local = registration["local"]
        self.assertTrue(local["enabled"])
        self.assertTrue(local["stdio"])
        self.assertTrue(local["repository_bound"])
        self.assertTrue(local["command_resolvable"])
        self.assertTrue(local["binary_matches_selected"])
        self.assertEqual(local["tool_timeout_sec"], 3601)

    def test_gaori_mcp_registration_accepts_larger_timeout(self) -> None:
        self.write_project_mcp_config("gaori", timeout=3602)
        self.install_fake_tools(gaori_mcp_mode="higher-timeout")
        registration = json.loads(self.inspect().stdout)["tools"]["gaori"][
            "mcp_registration"
        ]
        self.assertEqual(registration["status"], "configured")
        self.assertEqual(registration["local"]["tool_timeout_sec"], 3602)

    def test_gaori_mcp_registration_mismatch_is_degraded(self) -> None:
        self.repository.joinpath(".codex").mkdir()
        self.repository.joinpath(".codex/config.toml").write_text(
            "[mcp_servers.gaori]\n", encoding="utf-8"
        )
        for mode in (
            "wrong-repo",
            "disabled",
            "non-stdio",
            "missing-command",
            "wrong-command",
            "tool-timeout",
            "timeout-absent",
            "timeout-invalid",
            "extra-arg",
        ):
            with self.subTest(mode=mode):
                for executable in self.bin_directory.iterdir():
                    executable.unlink()
                self.install_fake_tools(gaori_mcp_mode=mode)
                registration = json.loads(self.inspect().stdout)["tools"]["gaori"][
                    "mcp_registration"
                ]
                self.assertEqual(registration["status"], "degraded")
                local = registration["local"]
                self.assertEqual(local["reason"], "registration_mismatch")
                if mode == "wrong-command":
                    self.assertTrue(local["command_resolvable"])
                    self.assertFalse(local["binary_matches_selected"])
                if mode == "extra-arg":
                    self.assertFalse(local["arguments_match"])

    def test_symlinked_paired_skill_is_degraded(self) -> None:
        source = self.base / "source-skill"
        self.install_gaori_skill(root=source)
        target_root = self.codex_home / "skills"
        target_root.mkdir(parents=True, exist_ok=True)
        target_root.joinpath("use-gaori").symlink_to(
            source / "use-gaori", target_is_directory=True
        )

        skill = json.loads(self.inspect().stdout)["tools"]["gaori"]["agent_skill"]

        self.assertEqual(skill["status"], "degraded")
        self.assertTrue(skill["installations"][0]["symlinked"])

    def test_symlinked_paired_skill_ancestor_is_not_read(self) -> None:
        self.install_gaori_skill()
        skill_directory = self.codex_home / "skills/use-gaori"
        shutil.rmtree(skill_directory / "references")
        external = self.base / "sensitive"
        external.mkdir()
        for name in ("lifecycle", "authoring", "recovery"):
            external.joinpath(f"{name}.md").write_text(
                "credential-value-must-not-be-read\n", encoding="utf-8"
            )
        skill_directory.joinpath("references").symlink_to(
            external, target_is_directory=True
        )

        completed = self.inspect()
        skill = json.loads(completed.stdout)["tools"]["gaori"]["agent_skill"]

        self.assertNotIn("credential-value-must-not-be-read", completed.stdout)
        self.assertEqual(skill["status"], "degraded")
        references = [
            entry
            for entry in skill["installations"][0]["files"]
            if entry["path"].startswith("references/")
        ]
        self.assertTrue(all(entry["symlinked"] for entry in references))
        self.assertTrue(all(entry["sha256"] is None for entry in references))

    def test_gaori_mcp_absence_is_not_cli_degradation(self) -> None:
        self.install_fake_tools(gaori_mcp_mode="missing")
        gaori = json.loads(self.inspect().stdout)["tools"]["gaori"]
        self.assertEqual(gaori["status"], "installed")
        self.assertEqual(gaori["mcp_registration"]["status"], "missing")
        self.assertEqual(gaori["mcp_registration"]["reason"], "registration_not_found")
        self.assertEqual(
            gaori["mcp_registration"]["recommendation"],
            "install_global_registration",
        )

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

    def test_incomplete_lora_installation_is_degraded(self) -> None:
        self.install_lora_skill("lore-commits")
        (self.codex_home / "skills/lore-query").mkdir(parents=True)
        lora = json.loads(self.inspect().stdout)["tools"]["lora"]
        self.assertEqual(lora["status"], "degraded")
        self.assertFalse(lora["installed"])
        self.assertFalse(
            lora["skills"]["lore-query"]["installations"][0]["skill_file_present"]
        )

    def test_duplicate_lora_installation_is_degraded(self) -> None:
        for name in ("lore-commits", "lore-query"):
            self.install_lora_skill(name)
        self.install_lora_skill("lore-query", root=self.home / ".agents/skills")
        lora = json.loads(self.inspect().stdout)["tools"]["lora"]
        self.assertEqual(lora["status"], "degraded")
        self.assertFalse(lora["installed"])
        self.assertTrue(lora["skills"]["lore-query"]["duplicate"])
        self.assertEqual(len(lora["skills"]["lore-query"]["installations"]), 2)

    def test_symlinked_lora_installation_is_degraded(self) -> None:
        self.install_lora_skill("lore-commits")
        source = self.install_lora_skill("lore-query", root=self.base / "source-skills")
        target_root = self.codex_home / "skills"
        target_root.mkdir(parents=True, exist_ok=True)
        target_root.joinpath("lore-query").symlink_to(source, target_is_directory=True)
        lora = json.loads(self.inspect().stdout)["tools"]["lora"]
        self.assertEqual(lora["status"], "degraded")
        self.assertFalse(lora["installed"])
        self.assertTrue(lora["skills"]["lore-query"]["symlinked"])

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
        self.assertEqual(payload["schema_version"], "aquarium-dev-setup-inspection.v12")
        self.assertEqual(payload["error"]["code"], "invalid_arguments")
        self.assertEqual(payload["error"]["message"], "invalid command-line arguments")

    def test_unknown_argument_value_is_not_reflected(self) -> None:
        secret = "QA20_SYNTHETIC_SECRET"

        completed = self.run_script(
            "--repository", str(self.repository), f"--api-token={secret}"
        )

        self.assertEqual(completed.returncode, 2)
        self.assertNotIn(secret, completed.stdout)

    def test_untrusted_version_and_go_fields_are_omitted(self) -> None:
        secret = "QA20_SYNTHETIC_SECRET"
        self.install_fake_tools(
            sanho_version=secret,
            mulgae_version=secret,
            gaori_version=secret,
            go_version=secret,
        )

        completed = self.inspect()

        self.assertEqual(completed.returncode, 0)
        self.assertNotIn(secret, completed.stdout)

    def test_non_positive_timeout_is_rejected_before_inspection(self) -> None:
        for timeout_seconds in (0, float("nan"), float("inf"), 1e308):
            with self.subTest(timeout_seconds=timeout_seconds):
                completed = self.inspect(timeout_seconds=timeout_seconds)
                self.assertEqual(completed.returncode, 2)
                error = json.loads(completed.stdout)["error"]
                self.assertEqual(error["code"], "invalid_arguments")
                self.assertIn("greater than zero and at most", error["message"])

    def test_oversized_mcp_timeout_is_not_a_supported_number(self) -> None:
        self.assertFalse(inspect_tools.finite_number(10**400))

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

    def test_invalid_utf8_probe_output_is_replaced_and_classified(self) -> None:
        raw_probe = inspect_tools.run_command(
            [
                sys.executable,
                "-c",
                "import os; os.write(1, b'\\xff')",
            ],
            self.repository,
            1.0,
        )

        self.assertTrue(raw_probe["ok"])
        self.assertEqual(raw_probe["stdout"], "\ufffd")
        probe = inspect_tools.parse_json_probe(raw_probe)
        self.assertFalse(probe["ok"])
        self.assertEqual(probe["error_code"], "invalid_json")

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
                        self.repository.resolve(), NORMAL_PROBE_TIMEOUT_SECONDS
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
                        self.repository.resolve(), NORMAL_PROBE_TIMEOUT_SECONDS
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
                    "schema_version": "mulgae-command-result.v5",
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
            payload = inspect_tools.inspect(
                str(self.repository), NORMAL_PROBE_TIMEOUT_SECONDS
            )
        podway_inspector.assert_not_called()
        self.assertNotIn("podway", payload["tools"])

    def test_default_inspection_does_not_call_ouroboros_inspector(self) -> None:
        with mock.patch("inspect_tools.inspect_ouroboros") as ouroboros_inspector:
            payload = inspect_tools.inspect(
                str(self.repository), NORMAL_PROBE_TIMEOUT_SECONDS
            )
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
        self.assertEqual(inspect_tools.ouroboros_version_from_output(output), "0.51.1")

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

    def test_ouroboros_accepts_canonical_isolated_launchers(self) -> None:
        for mode in (
            "isolated",
            "isolated-pinned",
            "isolated-suffix",
            "isolated-legacy-selector",
        ):
            with self.subTest(mode=mode):
                self.install_fake_tools(
                    ouroboros_version="0.51.15",
                    ouroboros_mcp_doctor_ok=False,
                    ouroboros_mcp_mode=mode,
                )
                completed = self.inspect(include_ouroboros=True)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                ouroboros = json.loads(completed.stdout)["tools"]["ouroboros"]
                self.assertEqual(ouroboros["mcp_registration"]["status"], "configured")
                self.assertEqual(ouroboros["mcp_runtime"]["status"], "configured")
                self.assertEqual(
                    ouroboros["mcp_runtime"]["probe"]["reason"],
                    "isolated_launcher_configured",
                )
                self.assertEqual(ouroboros["status"], "configured")

    def test_ouroboros_accepts_isolated_launcher_without_base_cli(self) -> None:
        self.install_fake_tools(ouroboros_mcp_mode="isolated")
        completed = self.inspect(include_ouroboros=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        ouroboros = json.loads(completed.stdout)["tools"]["ouroboros"]
        self.assertFalse(ouroboros["installed"])
        self.assertEqual(ouroboros["status"], "missing")
        self.assertEqual(ouroboros["mcp_registration"]["status"], "configured")
        self.assertEqual(ouroboros["mcp_runtime"]["status"], "configured")
        self.assertEqual(
            ouroboros["mcp_runtime"]["probe"]["reason"],
            "isolated_launcher_configured",
        )

    def test_ouroboros_rejects_noncanonical_isolated_launchers(self) -> None:
        modes = (
            "isolated-missing-flag",
            "isolated-wrong-command",
            "isolated-imposter-command",
            "isolated-wrong-python",
            "isolated-wrong-package",
            "isolated-unsupported-pin",
            "isolated-old-pin",
            "isolated-extra-arg",
            "isolated-missing-env",
            "isolated-conflicting-env",
            "isolated-nested-env",
            "isolated-extra-env",
            "isolated-non-stdio",
        )
        for mode in modes:
            with self.subTest(mode=mode):
                self.install_fake_tools(
                    ouroboros_version="0.51.15", ouroboros_mcp_mode=mode
                )
                completed = self.inspect(include_ouroboros=True)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                ouroboros = json.loads(completed.stdout)["tools"]["ouroboros"]
                self.assertEqual(ouroboros["mcp_registration"]["status"], "degraded")
                self.assertEqual(
                    ouroboros["mcp_registration"]["probe"]["reason"],
                    "registration_mismatch",
                )
                self.assertEqual(ouroboros["status"], "degraded")

    def test_ouroboros_skips_base_runtime_probe_for_launcher_mismatch(self) -> None:
        self.install_fake_tools(
            ouroboros_version="0.51.15",
            ouroboros_mcp_doctor_malformed=True,
            ouroboros_mcp_mode="isolated-wrong-package",
        )
        completed = self.inspect(include_ouroboros=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        ouroboros = json.loads(completed.stdout)["tools"]["ouroboros"]
        self.assertEqual(ouroboros["mcp_registration"]["status"], "degraded")
        self.assertEqual(ouroboros["mcp_runtime"]["status"], "unverifiable")
        self.assertFalse(ouroboros["mcp_runtime"]["probe"]["attempted"])
        self.assertEqual(
            ouroboros["mcp_runtime"]["probe"]["reason"],
            "registration_not_supported_launcher",
        )

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
                self.assertEqual(ouroboros["codex_integration"]["status"], codex_status)
                self.assertEqual(ouroboros["mcp_runtime"]["status"], mcp_status)
                self.assertEqual(ouroboros["mcp_registration"]["status"], "configured")
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
                self.assertEqual(ouroboros["mcp_registration"]["status"], "degraded")
                self.assertEqual(
                    ouroboros["mcp_registration"]["probe"]["reason"], reason
                )
                self.assertEqual(ouroboros["status"], "degraded")

    def test_ouroboros_registration_requires_exact_stdio_command(self) -> None:
        for mode in ("wrong-name", "non-stdio", "wrong-command", "wrong-args"):
            with self.subTest(mode=mode):
                self.install_fake_tools(
                    ouroboros_version="0.51.1", ouroboros_mcp_mode=mode
                )
                completed = self.inspect(include_ouroboros=True)
                registration = json.loads(completed.stdout)["tools"]["ouroboros"][
                    "mcp_registration"
                ]
                self.assertEqual(registration["status"], "degraded")
                self.assertEqual(
                    registration["probe"]["reason"], "registration_mismatch"
                )

    def test_ouroboros_registration_missing_is_distinct_from_probe_failure(
        self,
    ) -> None:
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
                    timeout_seconds=(
                        0.05 if mode == "timeout" else NORMAL_PROBE_TIMEOUT_SECONDS
                    ),
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertNotIn("secret registration failure", completed.stdout)
                ouroboros = json.loads(completed.stdout)["tools"]["ouroboros"]
                registration = ouroboros["mcp_registration"]
                self.assertEqual(registration["status"], status)
                self.assertEqual(registration["probe"]["reason"], reason)
                self.assertEqual(ouroboros["mcp_runtime"]["status"], "unverifiable")
                self.assertEqual(ouroboros["mcp_runtime"]["probe"]["reason"], reason)

    def test_missing_ouroboros_still_inspects_codex_registration(self) -> None:
        self.install_fake_tools(ouroboros_mcp_mode="configured")
        completed = self.inspect(include_ouroboros=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        ouroboros = json.loads(completed.stdout)["tools"]["ouroboros"]
        self.assertFalse(ouroboros["installed"])
        self.assertEqual(ouroboros["status"], "missing")
        self.assertEqual(ouroboros["mcp_registration"]["status"], "degraded")
        self.assertEqual(ouroboros["mcp_runtime"]["status"], "unverifiable")
        self.assertEqual(
            ouroboros["mcp_runtime"]["probe"]["reason"],
            "registration_not_supported_launcher",
        )
        self.assertEqual(ouroboros["probes"]["version"]["reason"], "executable_missing")

    def test_missing_ouroboros_keeps_invalid_isolated_runtime_unverifiable(
        self,
    ) -> None:
        for mode in (
            "isolated-unsupported-pin",
            "isolated-nested-env",
            "isolated-extra-arg",
        ):
            with self.subTest(mode=mode):
                self.install_fake_tools(ouroboros_mcp_mode=mode)
                completed = self.inspect(include_ouroboros=True)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                ouroboros = json.loads(completed.stdout)["tools"]["ouroboros"]
                self.assertFalse(ouroboros["installed"])
                self.assertEqual(ouroboros["mcp_registration"]["status"], "degraded")
                self.assertEqual(ouroboros["mcp_runtime"]["status"], "unverifiable")
                self.assertEqual(
                    ouroboros["mcp_runtime"]["probe"]["reason"],
                    "registration_not_supported_launcher",
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
        self.assertEqual(ouroboros["mcp_runtime"]["status"], "unverifiable")
        self.assertEqual(
            ouroboros["mcp_runtime"]["probe"]["reason"],
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
        self.assertEqual(ouroboros["probes"]["version"]["reason"], "executable_missing")

    def test_supported_platform_readiness_is_verified_on_any_host(self) -> None:
        self.install_fake_tools()
        self.install_managed_podway_procedures()
        with (
            mock.patch.dict(os.environ, self.environment),
            mock.patch("inspect_tools.platform.system", return_value="Darwin"),
            mock.patch("inspect_tools.platform.machine", return_value="arm64"),
        ):
            podway = inspect_tools.inspect_podway(
                self.repository.resolve(), NORMAL_PROBE_TIMEOUT_SECONDS
            )
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
            podway = inspect_tools.inspect_podway(
                self.repository.resolve(), NORMAL_PROBE_TIMEOUT_SECONDS
            )
        for entry in podway["managed_procedures"]:
            self.assertTrue(entry["present"])
            self.assertTrue(entry["matches_source"])
            self.assertFalse(entry["tracked"])
        self.assertEqual(podway["readiness_status"], "degraded")
        self.assertEqual(podway["status"], "degraded")


if __name__ == "__main__":
    unittest.main()
