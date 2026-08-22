"""Inspect the structural Aquarium test contract without executing project code."""

from __future__ import annotations

import argparse
import ast
import configparser
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

import tomllib

SCHEMA_VERSION = "aquarium-test-setup-inspection.v1"
ERROR_SCHEMA_VERSION = "aquarium-test-setup-inspection-error.v1"
CONTRACT_MARKER = "aquarium-test-contract/v1"
TESTING_HEADINGS = (
    "Contract",
    "Canonical Commands",
    "Stage Mapping",
    "Test Frameworks",
    "Gaori Mapping",
    "E2E Environment",
    "Language Diagnostics",
    "Legacy Waivers",
)
MAKE_TARGETS = ("test", "test-prepare", "test-unit", "test-int", "test-e2e")
MAKE_STAGES = MAKE_TARGETS[1:]
BUN_SCRIPTS = ("test", "test:prepare", "test:unit", "test:int", "test:e2e")
BUN_STAGES = BUN_SCRIPTS[1:]
EXPECTED_BUN_AGGREGATE = " && ".join(f"bun run {name}" for name in BUN_STAGES)
TARGET_PATTERN = re.compile(r"^([^\s:#=][^:=]*?):(?![=])(.*)$")
RECURSIVE_MAKE_PATTERN = re.compile(
    r"^\s*[@+]*\s*(?:\$\(MAKE\)|\$\{MAKE\})(?:\s+--no-print-directory)?\s+"
    r"(test(?:-[A-Za-z0-9_-]+)?)\s*$"
)
PINNED_BUN_PATTERN = re.compile(r"^bun@\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
GO_GINKGO_MODULE = "github.com/onsi/ginkgo/v2"
GO_GOMEGA_MODULE = "github.com/onsi/gomega"
PYTEST_COMMAND_PATTERN = re.compile(
    r"^\s*[@+]*\s*(?:(?P<runner>\$\([^)]+\)|\$\{[^}]+\}|(?:\S*/)?python(?:\d+(?:\.\d+)*)?)\s+-m\s+)?pytest(?=\s|$)"
)
UNITTEST_COMMAND_PATTERN = re.compile(
    r"^\s*[@+]*\s*(?:(?P<runner>\$\([^)]+\)|\$\{[^}]+\}|(?:\S*/)?python(?:\d+(?:\.\d+)*)?)\s+-m\s+)?unittest(?=\s|$)"
)
LEGACY_PYTHON_COMMAND_PATTERN = re.compile(
    r"^\s*[@+]*\s*(?:(?P<runner>\$\([^)]+\)|\$\{[^}]+\}|(?:\S*/)?python(?:\d+(?:\.\d+)*)?)\s+-m\s+)?(?:\S*/)?(?:nose|nose2|nosetests)(?=\s|$)"
)
SENSITIVE_PATH_COMPONENT = re.compile(
    r"(?i)(?:^|[._-])(?:auth(?:entication)?|credentials?|keys?|secrets?|tokens?)(?:[._-]|$)"
)
INFORMATION_ONLY_ARGUMENT = re.compile(
    r"(?:^|[\s\"'\[,;&|()])(?:--help|-h|--version|-V|--collect-only|--collectonly|--co|--fixtures(?:-per-test)?|--funcargs|--markers|--cache-show(?:=\S+)?|--setup-plan|--setup-only|--list|--list-tests|--no-run|--dry-run(?:=true)?|--dryRun(?:=true)?)(?:[\s\"'\],};&|()]|$)"
)
INFORMATION_ONLY_SUBCOMMAND = re.compile(
    r"^\s*[@+]*\s*ginkgo\s+(?:build|help|labels|outline|version)(?:\s|$)"
)
MAKE_ALIAS_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_])[A-Za-z_][A-Za-z0-9_]*\s*=\s*[^\s;&|]*make"
)
OPAQUE_PARAMETER_DEFAULT = re.compile(r"\$\{[^}]*:-[^}]*\}")
OPAQUE_SHELL_EXPANSION = re.compile(r"`[^`]*`|\$")


class InspectionError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise InspectionError("invalid_arguments", "invalid command-line arguments")


def strict_json_loads(content: str) -> Any:
    def object_from_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    def reject_constant(_value: str) -> None:
        raise ValueError("invalid JSON constant")

    def finite_float(value: str) -> float:
        parsed = float(value)
        if not math.isfinite(parsed):
            raise ValueError("non-finite JSON number")
        return parsed

    return json.loads(
        content,
        object_pairs_hook=object_from_pairs,
        parse_constant=reject_constant,
        parse_float=finite_float,
    )


def finding(code: str, severity: str, message: str) -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def sensitive_relative_path(path: Path, repository: Path) -> bool:
    try:
        parts = path.relative_to(repository).parts
    except ValueError:
        return True
    return any(
        part.lower().startswith(".env") or SENSITIVE_PATH_COMPONENT.search(part)
        for part in parts
    )


def detect_languages(repository: Path, package: dict[str, Any] | None) -> list[str]:
    languages: set[str] = set()
    if safe_repository_file(repository / "go.mod", repository):
        languages.add("go")
    if safe_repository_file(repository / "Cargo.toml", repository):
        languages.add("rust")
    if any(
        safe_repository_file(repository / name, repository)
        for name in ("pyproject.toml", "setup.py", "setup.cfg")
    ) or any(
        not sensitive_relative_path(path, repository)
        and safe_repository_file(path, repository)
        for path in repository.glob("requirements*.txt")
    ):
        languages.add("python")
    if safe_repository_file(repository / "pubspec.yaml", repository):
        languages.add("dart")

    executable_authority = read_optional_text(repository / "Makefile", repository)
    if package:
        scripts = package.get("scripts")
        if isinstance(scripts, dict):
            executable_authority += "\n" + "\n".join(
                value for value in scripts.values() if isinstance(value, str)
            )
    if re.search(
        r"(?:^|[\s;&|])(?:(?:\S*/)?python(?:\d+(?:\.\d+)*)?\s+-m\s+)?"
        r"(?:pytest|unittest|(?:\S*/)?nose(?:2)?|(?:\S*/)?nosetests)(?:\s|$)",
        executable_authority,
    ):
        languages.add("python")

    typescript_manifest = any(
        safe_repository_file(path, repository)
        for path in repository.glob("tsconfig*.json")
    )
    if package:
        dependencies: dict[str, Any] = {}
        for key in ("dependencies", "devDependencies", "peerDependencies"):
            value = package.get(key)
            if isinstance(value, dict):
                dependencies.update(value)
        typescript_manifest = typescript_manifest or "typescript" in dependencies
    if typescript_manifest:
        languages.add("typescript")
    return sorted(languages)


def selected_profile(languages: list[str]) -> str:
    if languages == ["typescript"]:
        return "typescript-bun"
    if "typescript" in languages and len(languages) > 1:
        return "polyglot-make"
    return "make"


def safe_repository_file(path: Path, repository: Path) -> bool:
    try:
        relative = path.relative_to(repository)
    except ValueError:
        return False
    current = repository
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            return False
    return current.is_file()


def nonempty_repository_file(path: Path, repository: Path) -> bool:
    if not safe_repository_file(path, repository):
        return False
    try:
        return path.stat().st_size > 0
    except OSError:
        return False


def unsafe_root_authorities(repository: Path) -> list[str]:
    candidates = [
        repository / name
        for name in (
            "go.mod",
            "Cargo.toml",
            "pyproject.toml",
            "setup.py",
            "setup.cfg",
            "pytest.ini",
            "tox.ini",
            "pubspec.yaml",
            "package.json",
            "bun.lock",
            "bun.lockb",
            "package-lock.json",
            "npm-shrinkwrap.json",
            "pnpm-lock.yaml",
            "yarn.lock",
            "TESTING.md",
            "Makefile",
        )
    ]
    candidates.extend(repository.glob("requirements*.txt"))
    candidates.extend(repository.glob("tsconfig*.json"))
    return sorted(
        str(path.relative_to(repository))
        for path in candidates
        if (path.exists() or path.is_symlink())
        and not safe_repository_file(path, repository)
    )


def lexical_path_symlinked(path: Path) -> bool:
    lexical = path if path.is_absolute() else Path.cwd() / path
    current = Path(lexical.anchor)
    for part in lexical.parts[1:]:
        if part == "..":
            current = current.parent
            continue
        if part == ".":
            continue
        current = current / part
        if current.is_symlink():
            return True
    return False


def normalize_shell_token_joins(command: str) -> str:
    return re.sub(r"(?<=[A-Za-z0-9_-])[\"'\\]+(?=[A-Za-z0-9_-])", "", command)


def read_optional_text(path: Path, repository: Path) -> str:
    try:
        return (
            path.read_text(encoding="utf-8")
            if safe_repository_file(path, repository)
            else ""
        )
    except (OSError, UnicodeError):
        return ""


def package_dependencies(package: dict[str, Any] | None) -> set[str]:
    dependencies: set[str] = set()
    if package is None:
        return dependencies
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        value = package.get(key)
        if isinstance(value, dict):
            dependencies.update(name for name in value if isinstance(name, str))
    return dependencies


def framework_entry(
    language: str,
    canonical: list[str],
    detected: list[str],
    status: str,
    parser: str,
    parser_support: str = "supported",
) -> dict[str, Any]:
    return {
        "language": language,
        "canonical": canonical,
        "detected": detected,
        "status": status,
        "waiver_required": status == "waiver_required",
        "unit_int_parser": parser,
        "parser_support": parser_support,
    }


def stage_commands(
    repository: Path, package: dict[str, Any] | None
) -> dict[str, list[str]]:
    commands: dict[str, list[str]] = {
        "test-unit": [],
        "test-int": [],
        "test-e2e": [],
    }
    make_content = read_optional_text(repository / "Makefile", repository)
    if make_content:
        targets, _, _ = parse_makefile(make_content)
        for stage in commands:
            definitions = targets.get(stage, [])
            if len(definitions) == 1:
                commands[stage] = definitions[0]["recipe"]

    scripts_value = package.get("scripts") if package else None
    scripts = scripts_value if isinstance(scripts_value, dict) else {}
    for stage, script_name in (
        ("test-unit", "test:unit"),
        ("test-int", "test:int"),
        ("test-e2e", "test:e2e"),
    ):
        if commands[stage]:
            continue
        script = scripts.get(script_name)
        if isinstance(script, str) and script.strip():
            commands[stage] = [script]
    return commands


def command_preserves_failure(command: str) -> bool:
    stripped = command.lstrip()
    prefix = re.match(r"^[@+-]*", stripped)
    if prefix and "-" in prefix.group(0):
        return False
    backgrounded = re.search(r"(?<!&)&(?!&)", command)
    return (
        "|" not in command
        and ";" not in command
        and "<" not in command
        and ">" not in command
        and backgrounded is None
        and not OPAQUE_PARAMETER_DEFAULT.search(command)
    )


def command_executes_tests(command: str) -> bool:
    normalized = normalize_shell_token_joins(command)
    without_runner = re.sub(
        r"^\s*[@+]*\s*\$[({][A-Za-z_][A-Za-z0-9_]*[)}]\s+",
        "",
        normalized,
        count=1,
    )
    return (
        not INFORMATION_ONLY_ARGUMENT.search(normalized)
        and not INFORMATION_ONLY_SUBCOMMAND.search(normalized)
        and not OPAQUE_SHELL_EXPANSION.search(without_runner)
    )


def make_variable_values(repository: Path) -> dict[str, set[str]]:
    definitions: dict[str, list[str]] = {}
    content = read_optional_text(repository / "Makefile", repository)
    for line in content.splitlines():
        if line.startswith("\t"):
            continue
        match = re.match(
            r"^(?:(?:override|export)\s+)*([A-Za-z_][A-Za-z0-9_]*)\s*(?:\?=|\+=|:=|=)\s*(.*?)\s*$",
            line,
        )
        if match:
            definitions.setdefault(match.group(1), []).append(match.group(2))

    def resolve(value: str, seen: frozenset[str]) -> set[str]:
        reference = re.search(r"\$\(([^)]+)\)|\$\{([^}]+)\}", value)
        if not reference:
            return {value}
        name = reference.group(1) or reference.group(2)
        if name in seen or name not in definitions:
            return {value}
        resolved: set[str] = set()
        for replacement in definitions[name]:
            expanded = (
                value[: reference.start()] + replacement + value[reference.end() :]
            )
            resolved.update(resolve(expanded, seen | {name}))
        return resolved

    return {
        name: {
            expanded
            for value in values
            for expanded in resolve(value, frozenset({name}))
        }
        for name, values in definitions.items()
    }


def pytest_control_only_configuration(
    repository: Path, make_variables: dict[str, set[str]]
) -> bool:
    if any(
        INFORMATION_ONLY_ARGUMENT.search(normalize_shell_token_joins(value))
        or OPAQUE_SHELL_EXPANSION.search(value)
        for value in make_variables.get("PYTEST_ADDOPTS", set())
    ):
        return True
    pyproject_content = read_optional_text(repository / "pyproject.toml", repository)
    if pyproject_content:
        try:
            pyproject = tomllib.loads(pyproject_content)
            addopts = (
                pyproject.get("tool", {})
                .get("pytest", {})
                .get("ini_options", {})
                .get("addopts")
            )
            values = addopts if isinstance(addopts, list) else [addopts]
            if any(
                isinstance(value, str)
                and INFORMATION_ONLY_ARGUMENT.search(normalize_shell_token_joins(value))
                for value in values
            ):
                return True
        except (tomllib.TOMLDecodeError, AttributeError):
            pass
    for name, sections in (
        ("pytest.ini", ("pytest",)),
        ("setup.cfg", ("tool:pytest", "pytest")),
        ("tox.ini", ("pytest", "tool:pytest")),
    ):
        content = read_optional_text(repository / name, repository)
        parser = configparser.ConfigParser(interpolation=None)
        try:
            parser.read_string(content)
        except configparser.Error:
            continue
        if any(
            parser.has_option(section, "addopts")
            and INFORMATION_ONLY_ARGUMENT.search(
                normalize_shell_token_joins(parser.get(section, "addopts"))
            )
            for section in sections
        ):
            return True
    return False


def invalid_python_config_authorities(repository: Path) -> set[str]:
    invalid: set[str] = set()
    for name in ("pytest.ini", "setup.cfg", "tox.ini"):
        content = read_optional_text(repository / name, repository)
        if not content:
            continue
        parser = configparser.ConfigParser(interpolation=None)
        try:
            parser.read_string(content)
        except configparser.Error:
            invalid.add(name)
    setup_content = read_optional_text(repository / "setup.py", repository)
    if setup_content:
        try:
            ast.parse(setup_content, filename="setup.py")
        except SyntaxError:
            invalid.add("setup.py")
    for path in sorted(repository.glob("requirements*.txt")):
        content = read_optional_text(path, repository)
        pytest_lines = [
            line.split("#", 1)[0].strip()
            for line in content.splitlines()
            if re.match(
                r"^pytest(?:\[|\s*(?:===|==|~=|!=|<=|>=|<|>|@))",
                line.split("#", 1)[0].strip(),
                re.IGNORECASE,
            )
        ]
        if any(
            re.fullmatch(
                r"pytest(?:\[[0-9A-Za-z_.-]+(?:,[0-9A-Za-z_.-]+)*\])?"
                r"==[0-9A-Za-z][0-9A-Za-z.+-]*",
                line,
                re.IGNORECASE,
            )
            is None
            for line in pytest_lines
        ):
            invalid.add(path.name)
    return invalid


def pytest_requirement(value: str) -> bool:
    return (
        re.match(
            r"^pytest(?:\[[0-9A-Za-z_.-]+(?:,[0-9A-Za-z_.-]+)*\])?"
            r"(?:\s*(?:===|==|~=|!=|<=|>=|<|>|@)\s*|$)",
            value.strip(),
            re.IGNORECASE,
        )
        is not None
    )


def requirement_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    if isinstance(value, dict):
        return [str(name) for name in value]
    return []


def pyproject_declares_pytest(pyproject: dict[str, Any]) -> bool:
    candidates: list[str] = []
    project = pyproject.get("project")
    if isinstance(project, dict):
        candidates.extend(requirement_values(project.get("dependencies")))
        optional = project.get("optional-dependencies")
        if isinstance(optional, dict):
            for requirements in optional.values():
                candidates.extend(requirement_values(requirements))

    tool = pyproject.get("tool")
    poetry = tool.get("poetry") if isinstance(tool, dict) else None
    if isinstance(poetry, dict):
        candidates.extend(requirement_values(poetry.get("dependencies")))
        candidates.extend(requirement_values(poetry.get("dev-dependencies")))
        groups = poetry.get("group")
        if isinstance(groups, dict):
            for group in groups.values():
                if isinstance(group, dict):
                    candidates.extend(requirement_values(group.get("dependencies")))
    return any(pytest_requirement(value) for value in candidates)


def python_authority_declares_pytest(path: Path, repository: Path) -> bool:
    content = read_optional_text(path, repository)
    if path.name.startswith("requirements") and path.suffix == ".txt":
        return any(
            pytest_requirement(line.split("#", 1)[0]) for line in content.splitlines()
        )
    if path.name == "setup.py":
        try:
            tree = ast.parse(content, filename="setup.py")
        except SyntaxError:
            return False
        candidates: list[str] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            for keyword in node.keywords:
                if keyword.arg not in {
                    "install_requires",
                    "tests_require",
                    "extras_require",
                }:
                    continue
                candidates.extend(
                    child.value
                    for child in ast.walk(keyword.value)
                    if isinstance(child, ast.Constant) and isinstance(child.value, str)
                )
        return any(pytest_requirement(value) for value in candidates)
    parser = configparser.ConfigParser(interpolation=None)
    try:
        parser.read_string(content)
    except configparser.Error:
        return False
    candidates = []
    for section in parser.sections():
        for option, value in parser.items(section):
            if option in {"install_requires", "tests_require"} or section.startswith(
                "options.extras_require"
            ):
                candidates.extend(value.splitlines())
    return any(pytest_requirement(value) for value in candidates)


def command_matches_python_runner(
    command: str, pattern: re.Pattern[str], variables: dict[str, set[str]]
) -> bool:
    match = pattern.search(command)
    if (
        not match
        or not command_preserves_failure(command)
        or not command_executes_tests(command)
    ):
        return False
    runner = match.group("runner")
    if not runner or not runner.startswith("$"):
        return True
    name = runner[2:-1]
    values = variables.get(name, set())
    return bool(values) and all(
        re.fullmatch(r"(?:\S*/)?python(?:\d+(?:\.\d+)*)?", value) for value in values
    )


def runner_variable_is(
    command: str,
    variable_name: str,
    executable: str,
    variables: dict[str, set[str]],
) -> bool:
    if not re.search(rf"\$\({variable_name}\)|\$\{{{variable_name}\}}", command):
        return True
    values = variables.get(variable_name, set())
    return bool(values) and all(
        re.fullmatch(rf"(?:\S*/)?{re.escape(executable)}", value) for value in values
    )


def python_stage_parser(
    commands: list[str], variables: dict[str, set[str]]
) -> str | None:
    has_pytest = any(
        command_matches_python_runner(command, PYTEST_COMMAND_PATTERN, variables)
        for command in commands
    )
    has_unittest = any(
        command_matches_python_runner(command, UNITTEST_COMMAND_PATTERN, variables)
        for command in commands
    )
    has_legacy = any(
        command_matches_python_runner(command, LEGACY_PYTHON_COMMAND_PATTERN, variables)
        for command in commands
    )
    if has_pytest and not has_unittest and not has_legacy:
        return "pytest"
    if has_unittest or has_legacy:
        return "generic"
    return None


def source_contains(repository: Path, suffix: str, patterns: tuple[str, ...]) -> bool:
    ignored = {".git", ".venv", "node_modules", "vendor"}
    for path in repository.rglob(f"*{suffix}"):
        if any(part in ignored for part in path.parts):
            continue
        if sensitive_relative_path(path, repository):
            continue
        try:
            if (
                not safe_repository_file(path, repository)
                or path.stat().st_size > 1_000_000
            ):
                continue
        except OSError:
            continue
        content = read_optional_text(path, repository)
        if any(re.search(pattern, content) for pattern in patterns):
            return True
    return False


def inspect_frameworks(
    repository: Path, languages: list[str], package: dict[str, Any] | None
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    entries: list[dict[str, Any]] = []
    findings: list[dict[str, str]] = []
    commands = stage_commands(repository, package)
    make_variables = make_variable_values(repository)

    if "go" in languages:
        go_mod = read_optional_text(repository / "go.mod", repository)
        go_sum = read_optional_text(repository / "go.sum", repository)
        go_commands = "\n".join(
            command
            for stage in ("test-unit", "test-int")
            for command in commands[stage]
        )
        has_ginkgo_command = all(
            commands[stage]
            and any(
                command_preserves_failure(command)
                and command_executes_tests(command)
                and re.search(r"^\s*[@+]*\s*ginkgo(?:\s|$)", command)
                for command in commands[stage]
            )
            for stage in ("test-unit", "test-int")
        )
        has_ginkgo_sources = all(
            source_contains(repository, "_test.go", (re.escape(name),))
            for name in (GO_GINKGO_MODULE, GO_GOMEGA_MODULE)
        )
        detected = [
            name
            for name in (GO_GINKGO_MODULE, GO_GOMEGA_MODULE)
            if name in go_mod
            or name in go_sum
            or name in go_commands
            or has_ginkgo_sources
        ]
        dependencies_pinned = all(
            name in go_mod and name in go_sum
            for name in (GO_GINKGO_MODULE, GO_GOMEGA_MODULE)
        )
        status = (
            "canonical"
            if dependencies_pinned and has_ginkgo_command and has_ginkgo_sources
            else "waiver_required"
        )
        entries.append(
            framework_entry(
                "go",
                ["ginkgo-v2", "gomega"],
                detected,
                status,
                "ginkgo" if status == "canonical" else "generic",
            )
        )

    if "python" in languages:
        invalid_configs = invalid_python_config_authorities(repository)
        for name in sorted(invalid_configs):
            findings.append(
                finding(
                    "python_config_invalid",
                    "error",
                    f"{name} is invalid and cannot prove pytest configuration.",
                )
            )
        pyproject_path = repository / "pyproject.toml"
        pyproject_content = read_optional_text(pyproject_path, repository)
        pyproject_valid = True
        pyproject: dict[str, Any] = {}
        if pyproject_content:
            try:
                pyproject = tomllib.loads(pyproject_content)
            except tomllib.TOMLDecodeError:
                pyproject_valid = False
                findings.append(
                    finding(
                        "pyproject_invalid",
                        "error",
                        "pyproject.toml is invalid and cannot prove pytest configuration.",
                    )
                )
        authority_paths = [
            repository / "setup.cfg",
            repository / "setup.py",
            *sorted(repository.glob("requirements*.txt")),
        ]
        has_pytest_declaration = (
            pyproject_valid and pyproject_declares_pytest(pyproject)
        ) or any(
            python_authority_declares_pytest(path, repository)
            for path in authority_paths
            if path.name not in invalid_configs
            and not sensitive_relative_path(path, repository)
        )
        stage_parsers = {
            stage: python_stage_parser(commands[stage], make_variables)
            for stage in ("test-unit", "test-int")
        }
        if pytest_control_only_configuration(repository, make_variables):
            stage_parsers = {stage: None for stage in stage_parsers}
        has_pytest_command = "pytest" in stage_parsers.values()
        has_unittest_command = any(
            command_matches_python_runner(
                command, UNITTEST_COMMAND_PATTERN, make_variables
            )
            for stage in ("test-unit", "test-int", "test-e2e")
            for command in commands[stage]
        )
        has_legacy_runner = any(
            command_matches_python_runner(
                command, LEGACY_PYTHON_COMMAND_PATTERN, make_variables
            )
            for stage in ("test-unit", "test-int", "test-e2e")
            for command in commands[stage]
        )
        has_unittest = has_unittest_command or source_contains(
            repository,
            ".py",
            (r"(?m)^\s*(?:from\s+unittest\s+import|import\s+unittest\b)",),
        )
        detected = [
            name
            for name, present in (
                ("pytest", has_pytest_declaration or has_pytest_command),
                ("unittest", has_unittest),
                ("legacy-python-runner", has_legacy_runner),
            )
            if present
        ]
        status = (
            "canonical"
            if pyproject_valid
            and not invalid_configs
            and has_pytest_declaration
            and all(parser == "pytest" for parser in stage_parsers.values())
            and not has_unittest
            and not has_legacy_runner
            else "waiver_required"
        )
        entries.append(
            framework_entry(
                "python",
                ["pytest"],
                detected,
                status,
                "pytest" if status == "canonical" else "generic",
            )
        )

    if "typescript" in languages:
        scripts_value = package.get("scripts") if package else None
        scripts = scripts_value if isinstance(scripts_value, dict) else {}
        unit_int_scripts = [scripts.get(key) for key in ("test:unit", "test:int")]
        unit_int_commands = "\n".join(
            value for value in unit_int_scripts if isinstance(value, str)
        )
        dependencies = package_dependencies(package)
        detected: list[str] = []
        if any(
            isinstance(command, str)
            and command_preserves_failure(command)
            and command_executes_tests(command)
            and re.search(r"^\s*bun\s+test(?:\s|$)", command)
            for command in unit_int_scripts
        ):
            detected.append("bun-test")
        for dependency, label in (
            ("vitest", "vitest"),
            ("jest", "jest"),
            ("node:test", "node-test"),
        ):
            if dependency in dependencies or re.search(
                rf"(?:^|\s){re.escape(dependency)}(?:\s|$)", unit_int_commands
            ):
                detected.append(label)
        runs_vitest = all(
            isinstance(command, str)
            and command_preserves_failure(command)
            and command_executes_tests(command)
            and bool(re.search(r"^\s*(?:bun\s+run\s+)?vitest(?:\s|$)", command))
            for command in unit_int_scripts
        )
        status = (
            "canonical"
            if detected == ["vitest"] and "vitest" in dependencies and runs_vitest
            else "waiver_required"
        )
        entries.append(
            framework_entry(
                "typescript",
                ["vitest"],
                sorted(set(detected)),
                status,
                "vitest" if status == "canonical" else "generic",
            )
        )

    if "rust" in languages:
        runs_cargo_test = all(
            commands[stage]
            and any(
                re.search(
                    r"^\s*[@+]*\s*(?:cargo|\$\(CARGO\)|\$\{CARGO\})(?:\s+\+\S+)?\s+test(?:\s|$)",
                    command,
                )
                and command_preserves_failure(command)
                and command_executes_tests(command)
                and runner_variable_is(command, "CARGO", "cargo", make_variables)
                for command in commands[stage]
            )
            for stage in ("test-unit", "test-int")
        )
        status = "canonical" if runs_cargo_test else "waiver_required"
        entries.append(
            framework_entry(
                "rust",
                ["cargo-test"],
                ["cargo-test"] if runs_cargo_test else [],
                status,
                "cargo-test" if status == "canonical" else "generic",
            )
        )

    if "dart" in languages:
        pubspec = read_optional_text(repository / "pubspec.yaml", repository)
        is_flutter = (
            bool(re.search(r"(?m)^\s*flutter:\s*$", pubspec))
            or "sdk: flutter" in pubspec
        )
        if is_flutter:
            detected = [
                name
                for name in ("flutter_test", "patrol")
                if re.search(rf"(?m)^\s*{name}:\s*", pubspec)
            ]
            runs_flutter_test = all(
                commands[stage]
                and any(
                    command_preserves_failure(command)
                    and command_executes_tests(command)
                    and re.search(r"^\s*[@+]*\s*flutter\s+test(?:\s|$)", command)
                    for command in commands[stage]
                )
                for stage in ("test-unit", "test-int")
            )
            status = (
                "canonical"
                if "flutter_test" in detected and runs_flutter_test
                else "waiver_required"
            )
            entry = framework_entry(
                "flutter",
                ["flutter_test", "patrol-e2e"],
                detected,
                status,
                "flutter-test" if status == "canonical" else "generic",
            )
            entry["e2e_parser"] = "generic"
            entry["e2e_parser_support"] = "pending-patrol"
            entries.append(entry)
        else:
            has_test = bool(re.search(r"(?m)^\s*test:\s*", pubspec))
            runs_dart_test = all(
                commands[stage]
                and any(
                    command_preserves_failure(command)
                    and command_executes_tests(command)
                    and re.search(r"^\s*[@+]*\s*dart\s+test(?:\s|$)", command)
                    for command in commands[stage]
                )
                for stage in ("test-unit", "test-int")
            )
            status = "canonical" if has_test and runs_dart_test else "waiver_required"
            entries.append(
                framework_entry(
                    "dart",
                    ["package:test"],
                    ["package:test"] if has_test else [],
                    status,
                    "generic",
                    "pending-dart-test",
                )
            )

    for entry in entries:
        if entry["status"] == "waiver_required":
            findings.append(
                finding(
                    "framework_waiver_required",
                    "unverifiable",
                    f"{entry['language']} does not expose only its canonical unit/integration framework; inspect actual tests and an approved AQTEST-009 waiver.",
                )
            )

    specialized = [entry["unit_int_parser"] for entry in entries]
    unit_int_parser = specialized[0] if len(specialized) == 1 else "generic"
    stage_parser_defaults = {
        "test": "generic",
        "test-prepare": "generic",
        "test-unit": unit_int_parser,
        "test-int": unit_int_parser,
        "test-e2e": "inspect_e2e_runner",
    }
    if len(entries) == 1 and entries[0]["language"] == "python":
        for stage in ("test-unit", "test-int"):
            detected_parser = python_stage_parser(commands[stage], make_variables)
            if detected_parser is not None:
                stage_parser_defaults[stage] = detected_parser
    gaori = {
        "config_path": str(repository / ".gaori/tester.yaml"),
        "config_present": safe_repository_file(
            repository / ".gaori/tester.yaml", repository
        ),
        "parser_availability": "not_evaluated",
        "stage_parser_defaults": stage_parser_defaults,
    }
    return {"entries": entries, "gaori": gaori}, findings


def read_package(repository: Path) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    path = repository / "package.json"
    result: dict[str, Any] = {
        "path": str(path),
        "present": safe_repository_file(path, repository),
        "valid": False,
    }
    if not result["present"]:
        return None, result
    try:
        value = strict_json_loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        result["error"] = type(error).__name__
        return None, result
    if not isinstance(value, dict):
        result["error"] = "root_not_object"
        return None, result
    result["valid"] = True
    return value, result


def parse_makefile(
    content: str,
) -> tuple[dict[str, list[dict[str, Any]]], set[str], list[str]]:
    lines = content.splitlines()
    targets: dict[str, list[dict[str, Any]]] = {}
    phony: set[str] = set()
    includes: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not line.startswith("\t") and re.match(r"^-?include\s+", stripped):
            includes.append(stripped)
        if not line.startswith("\t") and stripped.startswith(".PHONY:"):
            declaration = stripped
            while declaration.endswith("\\") and index + 1 < len(lines):
                index += 1
                declaration = declaration[:-1] + " " + lines[index].strip()
            phony.update(declaration.split(":", 1)[1].split())
            index += 1
            continue
        if line.startswith("\t") or not stripped or stripped.startswith("#"):
            index += 1
            continue
        match = TARGET_PATTERN.match(line)
        if not match:
            index += 1
            continue
        names = [name for name in match.group(1).split() if "%" not in name]
        prerequisites = match.group(2).split(";", 1)[0].strip()
        recipe: list[str] = []
        cursor = index + 1
        if ";" in match.group(2):
            inline = match.group(2).split(";", 1)[1].strip()
            if inline:
                recipe.append(inline)
        while cursor < len(lines):
            candidate = lines[cursor]
            if candidate.startswith("\t"):
                command = candidate[1:].strip()
                if command and not command.startswith("#"):
                    recipe.append(command)
                cursor += 1
                continue
            if not candidate.strip() or candidate.lstrip().startswith("#"):
                cursor += 1
                continue
            break
        for name in names:
            targets.setdefault(name, []).append(
                {
                    "line": index + 1,
                    "prerequisites": prerequisites.split() if prerequisites else [],
                    "recipe": recipe,
                }
            )
        index = cursor
    return targets, phony, includes


def bun_adapter_matches(
    recipe: list[str], script: str, variables: dict[str, set[str]]
) -> bool:
    if len(recipe) != 1:
        return False
    pattern = re.compile(
        rf"^[+@]*\s*(?:bun|\$\(BUN\)|\$\{{BUN\}})\s+run\s+{re.escape(script)}\s*$"
    )
    return (
        command_preserves_failure(recipe[0])
        and command_executes_tests(recipe[0])
        and bool(pattern.fullmatch(recipe[0]))
        and runner_variable_is(recipe[0], "BUN", "bun", variables)
    )


def inspect_makefile(
    repository: Path, profile: str
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    path = repository / "Makefile"
    result: dict[str, Any] = {
        "path": str(path),
        "present": safe_repository_file(path, repository),
    }
    findings: list[dict[str, str]] = []
    if not result["present"]:
        findings.append(
            finding("makefile_missing", "error", "Root Makefile is missing.")
        )
        return result, findings
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        result["read_error"] = type(error).__name__
        findings.append(
            finding("makefile_unreadable", "error", "Root Makefile is unreadable.")
        )
        return result, findings

    targets, phony, includes = parse_makefile(content)
    make_variables = make_variable_values(repository)
    pytest_addopts_bare_export = bool(
        re.search(
            r"(?m)^\s*(?:(?:export|unexport|undefine)\s+)+PYTEST_ADDOPTS\s*$", content
        )
    ) and make_variables.get("PYTEST_ADDOPTS") != {""}
    result["include_count"] = len(includes)
    result["global_shell_semantics"] = bool(
        re.search(r"(?m)^\s*\.(?:ONESHELL|IGNORE)\s*:", content)
        or re.search(r"(?m)^\s*\.RECIPEPREFIX\s*[:?+]?=", content)
        or re.search(
            r"(?m)^[^#\t\n][^:\n]*:\s*(?:(?:override|export)\s+)*[A-Za-z_][A-Za-z0-9_]*\s*[:?+]?=",
            content,
        )
        or re.search(r"\$\((?:eval|call|foreach|if)\b", content)
        or re.search(
            r"(?m)^\s*(?:(?:override|export)\s+)*(?:BUN|CARGO|PYTHON|RUFF)\s*\?=",
            content,
        )
        or re.search(r"(?m)^\s*(?:ifeq|ifneq|ifdef|ifndef|else|endif)\b", content)
        or re.search(
            r"(?m)^\s*(?:override\s+)?define\s+(?:SHELL|\.SHELLFLAGS|MAKE|MAKEFLAGS|MFLAGS|GNUMAKEFLAGS)\b",
            content,
        )
        or re.search(
            r"(?m)^\s*(?:(?:export|unexport|undefine)\s+)+(?:SHELL|\.SHELLFLAGS|MAKE|MAKEFLAGS|MFLAGS|GNUMAKEFLAGS)\s*$",
            content,
        )
        or pytest_addopts_bare_export
        or "\\\n" in content
        or re.search(
            r"(?m)^\s*(?:override\s+)?(?:export\s+)?(?:SHELL|\.SHELLFLAGS|MAKE|MAKEFLAGS|MFLAGS|GNUMAKEFLAGS)\s*[:?+]?=",
            content,
        )
    )
    result["authority_includes_unresolved"] = bool(includes)
    result["targets"] = {}
    missing = []
    duplicates = []
    for name in MAKE_TARGETS:
        definitions = targets.get(name, [])
        public_definitions = [
            {
                "line": definition["line"],
                "prerequisite_count": len(definition["prerequisites"]),
                "recipe_command_count": len(definition["recipe"]),
            }
            for definition in definitions
        ]
        result["targets"][name] = {
            "present": bool(definitions),
            "phony": name in phony,
            "definitions": public_definitions,
        }
        if not definitions:
            missing.append(name)
        elif len(definitions) > 1:
            duplicates.append(name)
        if name not in phony:
            findings.append(
                finding(
                    "make_target_not_phony", "error", f"{name} is not declared phony."
                )
            )

    if missing:
        severity = "unverifiable" if includes else "error"
        findings.append(
            finding(
                "make_targets_missing",
                severity,
                f"Missing literal targets: {', '.join(missing)}.",
            )
        )
    if duplicates:
        findings.append(
            finding(
                "make_targets_ambiguous",
                "unverifiable",
                f"Multiple definitions: {', '.join(duplicates)}.",
            )
        )

    if not missing and not duplicates:
        if result["global_shell_semantics"] or result["authority_includes_unresolved"]:
            result["aggregate_mode"] = "unverifiable"
            findings.append(
                finding(
                    "make_authority_unverifiable",
                    "unverifiable",
                    "Included or custom global Make semantics prevent fail-fast proof.",
                )
            )
        elif profile == "typescript-bun":
            adapter_map = {
                "test": "test",
                "test-prepare": "test:prepare",
                "test-unit": "test:unit",
                "test-int": "test:int",
                "test-e2e": "test:e2e",
            }
            adapter_ok = True
            for target, script in adapter_map.items():
                definition = targets[target][0]
                matches = not definition["prerequisites"] and bun_adapter_matches(
                    definition["recipe"], script, make_variables
                )
                result["targets"][target]["bun_adapter"] = matches
                adapter_ok = adapter_ok and matches
            result["aggregate_mode"] = (
                "bun_adapter" if adapter_ok else "invalid_bun_adapter"
            )
            if not adapter_ok:
                findings.append(
                    finding(
                        "bun_make_adapter_invalid",
                        "error",
                        "Make targets must delegate one-way to their matching Bun scripts.",
                    )
                )
        else:
            aggregate = targets["test"][0]
            recursive_calls = [
                match.group(1)
                for command in aggregate["recipe"]
                for match in [RECURSIVE_MAKE_PATTERN.match(command)]
                if match is not None
            ]
            only_recursive_calls = len(aggregate["recipe"]) == len(recursive_calls)
            result["aggregate_recursive_calls"] = recursive_calls
            if aggregate["prerequisites"]:
                result["aggregate_mode"] = "prerequisites"
                findings.append(
                    finding(
                        "make_aggregate_parallel_unsafe",
                        "error",
                        "test uses prerequisites, which do not preserve stage order under make -j.",
                    )
                )
            elif only_recursive_calls and recursive_calls == list(MAKE_STAGES):
                result["aggregate_mode"] = "recursive_recipe"
            else:
                result["aggregate_mode"] = "unverifiable"
                findings.append(
                    finding(
                        "make_aggregate_order_unverifiable",
                        "unverifiable",
                        "The literal recursive stage order is not the four-stage contract.",
                    )
                )
    return result, findings


def inspect_bun(
    repository: Path,
    package: dict[str, Any] | None,
    package_result: dict[str, Any],
    required: bool,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    result = dict(package_result)
    findings: list[dict[str, str]] = []
    if not package_result["present"]:
        if required:
            findings.append(
                finding(
                    "package_json_missing",
                    "error",
                    "TypeScript root lacks package.json.",
                )
            )
        return result, findings
    if package is None:
        findings.append(
            finding("package_json_invalid", "error", "package.json is invalid.")
        )
        return result, findings

    scripts_value = package.get("scripts")
    scripts = scripts_value if isinstance(scripts_value, dict) else {}
    script_status: dict[str, dict[str, Any]] = {}
    missing = []
    for name in BUN_SCRIPTS:
        value = scripts.get(name)
        present = isinstance(value, str) and bool(value.strip())
        script_status[name] = {
            "present": present,
            "command_redacted": present,
        }
        if not present:
            missing.append(name)
    result["scripts"] = script_status
    aggregate = scripts.get("test") if isinstance(scripts.get("test"), str) else ""
    normalized = " ".join(aggregate.split())
    result["aggregate_serial"] = normalized == EXPECTED_BUN_AGGREGATE

    def calls_make(value: str) -> bool:
        normalized_shell_words = normalize_shell_token_joins(value)
        return bool(
            re.search(
                r"(?:^|[\s;&|()\"'])(?:(?:\S*/)?make|\$\(MAKE\)|\$\{MAKE\})(?:\s|[\"']|$)",
                normalized_shell_words,
            )
            or MAKE_ALIAS_PATTERN.search(normalized_shell_words)
            or OPAQUE_PARAMETER_DEFAULT.search(normalized_shell_words)
            or OPAQUE_SHELL_EXPANSION.search(normalized_shell_words)
        )

    make_cycles = sorted(
        name
        for name, value in scripts.items()
        if isinstance(value, str) and calls_make(value)
    )
    result["make_cycles"] = [name for name in make_cycles if name in BUN_SCRIPTS]
    result["make_cycle_count"] = len(make_cycles)
    package_manager = package.get("packageManager")
    result["package_manager_present"] = isinstance(package_manager, str)
    result["bun_version_pinned"] = isinstance(package_manager, str) and bool(
        PINNED_BUN_PATTERN.fullmatch(package_manager)
    )
    engines = package.get("engines")
    result["bun_engine_present"] = bool(
        isinstance(engines, dict) and isinstance(engines.get("bun"), str)
    )
    result["lockfile"] = {
        "bun.lock": nonempty_repository_file(repository / "bun.lock", repository),
        "bun.lockb": nonempty_repository_file(repository / "bun.lockb", repository),
    }
    result["legacy_package_manager_files"] = [
        name
        for name in (
            "package-lock.json",
            "npm-shrinkwrap.json",
            "pnpm-lock.yaml",
            "yarn.lock",
        )
        if safe_repository_file(repository / name, repository)
    ]

    if required:
        if missing:
            findings.append(
                finding(
                    "bun_scripts_missing",
                    "error",
                    f"Missing Bun scripts: {', '.join(missing)}.",
                )
            )
        if not result["aggregate_serial"]:
            findings.append(
                finding(
                    "bun_aggregate_invalid",
                    "error",
                    "test must call the four Bun stage scripts once with serial && operators.",
                )
            )
        if make_cycles:
            findings.append(
                finding(
                    "bun_make_cycle",
                    "error",
                    "Bun test scripts call Make and create a reverse edge.",
                )
            )
        if not result["bun_version_pinned"]:
            findings.append(
                finding(
                    "bun_version_unpinned",
                    "error",
                    "packageManager must pin an exact Bun version.",
                )
            )
        if not result["lockfile"]["bun.lock"]:
            findings.append(
                finding(
                    "bun_lock_missing", "error", "Tracked-format bun.lock is missing."
                )
            )
        if result["lockfile"]["bun.lockb"]:
            findings.append(
                finding(
                    "bun_legacy_lock_waiver_required",
                    "unverifiable",
                    "bun.lockb requires an approved AQTEST-008 legacy waiver.",
                )
            )
        if result["legacy_package_manager_files"]:
            findings.append(
                finding(
                    "typescript_package_manager_waiver_required",
                    "unverifiable",
                    "Legacy package-manager files require an approved AQTEST-008 waiver: "
                    + ", ".join(result["legacy_package_manager_files"])
                    + ".",
                )
            )
    return result, findings


def inspect_testing_document(
    repository: Path,
    expected_profile: str,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    path = repository / "TESTING.md"
    result = {
        "path": str(path),
        "present": safe_repository_file(path, repository),
        "contract_registered": False,
        "profile": None,
        "sections": {heading: False for heading in TESTING_HEADINGS},
    }
    findings: list[dict[str, str]] = []
    if not result["present"]:
        findings.append(
            finding("testing_document_missing", "error", "Root TESTING.md is missing.")
        )
        return result, findings
    try:
        content = path.read_text(encoding="utf-8")
        section_content: dict[str, str] = {}
        result["sections"] = {}
        for heading in TESTING_HEADINGS:
            section = re.search(
                rf"(?ms)^##\s+{re.escape(heading)}\s*$\n(.*?)(?=^##\s+|\Z)",
                content,
            )
            body = section.group(1).strip() if section else ""
            section_content[heading] = body
            result["sections"][heading] = bool(body)
        contract_content = section_content["Contract"]
        result["contract_registered"] = bool(
            re.search(
                rf"(?im)^\s*(?:[-*]\s*)?Contract:\s*`?{re.escape(CONTRACT_MARKER)}`?\s*$",
                contract_content,
            )
            or re.search(
                rf"(?i)\bis enrolled in\s+`{re.escape(CONTRACT_MARKER)}`",
                contract_content,
            )
        )
        explicit_profile = re.search(
            r"(?im)^\s*(?:[-*]\s*)?Profile:\s*`?(make|typescript-bun|polyglot-make)`?\s*$",
            contract_content,
        )
        prose_profile = re.search(
            r"(?i)`(make|typescript-bun|polyglot-make)`\s+profile\b",
            contract_content,
        )
        profile_match = explicit_profile or prose_profile
        if profile_match:
            result["profile"] = profile_match.group(1)
    except (OSError, UnicodeError):
        findings.append(
            finding(
                "testing_document_unreadable", "error", "Root TESTING.md is unreadable."
            )
        )
        return result, findings
    if not result["contract_registered"]:
        findings.append(
            finding(
                "testing_contract_unregistered",
                "error",
                f"TESTING.md lacks {CONTRACT_MARKER}.",
            )
        )
    if result["profile"] is None:
        findings.append(
            finding(
                "testing_profile_missing",
                "error",
                "TESTING.md does not declare a supported selected profile.",
            )
        )
    elif result["profile"] != expected_profile:
        findings.append(
            finding(
                "testing_profile_mismatch",
                "error",
                f"TESTING.md declares {result['profile']} but executable authorities select {expected_profile}.",
            )
        )
    missing_sections = [
        heading for heading, present in result["sections"].items() if not present
    ]
    if missing_sections:
        findings.append(
            finding(
                "testing_sections_missing",
                "error",
                f"TESTING.md lacks required non-empty sections: {', '.join(missing_sections)}.",
            )
        )
    return result, findings


def inspect_repository(repository: Path) -> dict[str, Any]:
    package, package_result = read_package(repository)
    languages = detect_languages(repository, package)
    profile = selected_profile(languages)
    make_result, make_findings = inspect_makefile(repository, profile)
    bun_result, bun_findings = inspect_bun(
        repository, package, package_result, required=profile == "typescript-bun"
    )
    framework_result, framework_findings = inspect_frameworks(
        repository, languages, package
    )
    document_result, document_findings = inspect_testing_document(repository, profile)
    findings = make_findings + bun_findings + framework_findings + document_findings
    unsafe_authorities = unsafe_root_authorities(repository)
    if unsafe_authorities:
        findings.append(
            finding(
                "root_authority_symlinked",
                "error",
                "Root test authorities must be regular non-symlink files: "
                + ", ".join(unsafe_authorities),
            )
        )
    if any(item["severity"] == "error" for item in findings):
        status = "nonconforming"
    elif any(item["severity"] == "unverifiable" for item in findings):
        status = "unverifiable"
    else:
        status = "conforming"
    return {
        "schema_version": SCHEMA_VERSION,
        "repository": str(repository),
        "detected_languages": languages,
        "selected_profile": profile,
        "structural_status": status,
        "make": make_result,
        "bun": bun_result,
        "frameworks": framework_result,
        "testing_document": document_result,
        "findings": findings,
        "semantic_scope": "not_evaluated",
        "waiver_equivalence": "not_evaluated",
    }


def parse_arguments(arguments: list[str]) -> argparse.Namespace:
    parser = JsonArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    return parser.parse_args(arguments)


def main(arguments: list[str] | None = None) -> int:
    try:
        options = parse_arguments(arguments if arguments is not None else sys.argv[1:])
        requested_repository = Path(options.repository).expanduser()
        if lexical_path_symlinked(requested_repository):
            raise InspectionError(
                "repository_symlinked",
                "repository and its lexical ancestors must not be symlinks",
            )
        if not requested_repository.is_dir():
            raise InspectionError(
                "repository_not_found", "repository must be an existing directory"
            )
        repository = requested_repository.resolve()
        payload = inspect_repository(repository)
    except InspectionError as error:
        payload = {
            "schema_version": ERROR_SCHEMA_VERSION,
            "error": {"code": error.code, "message": str(error)},
        }
        print(json.dumps(payload, sort_keys=True))
        return 2
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
