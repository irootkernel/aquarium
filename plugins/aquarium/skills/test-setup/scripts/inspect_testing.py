"""Inspect the structural Aquarium test contract without executing project code."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "aquarium-test-setup-inspection.v1"
ERROR_SCHEMA_VERSION = "aquarium-test-setup-inspection-error.v1"
CONTRACT_MARKER = "aquarium-test-contract/v1"
MAKE_TARGETS = ("test", "test-prepare", "test-unit", "test-int", "test-e2e")
MAKE_STAGES = MAKE_TARGETS[1:]
BUN_SCRIPTS = ("test", "test:prepare", "test:unit", "test:int", "test:e2e")
BUN_STAGES = BUN_SCRIPTS[1:]
EXPECTED_BUN_AGGREGATE = " && ".join(f"bun run {name}" for name in BUN_STAGES)
TARGET_PATTERN = re.compile(r"^([^\s:#=][^:=]*?):(?![=])(.*)$")
RECURSIVE_MAKE_PATTERN = re.compile(
    r"(?:\$\(MAKE\)|\$\{MAKE\})(?:\s+--no-print-directory)?\s+"
    r"(test(?:-[A-Za-z0-9_-]+)?)\b"
)
PINNED_BUN_PATTERN = re.compile(r"^bun@\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
GO_GINKGO_MODULE = "github.com/onsi/ginkgo/v2"
GO_GOMEGA_MODULE = "github.com/onsi/gomega"


class InspectionError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise InspectionError("invalid_arguments", message)


def finding(code: str, severity: str, message: str) -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def detect_languages(repository: Path, package: dict[str, Any] | None) -> list[str]:
    languages: set[str] = set()
    if (repository / "go.mod").is_file():
        languages.add("go")
    if (repository / "Cargo.toml").is_file():
        languages.add("rust")
    if any(
        (repository / name).is_file()
        for name in ("pyproject.toml", "setup.py", "setup.cfg")
    ):
        languages.add("python")
    if (repository / "pubspec.yaml").is_file():
        languages.add("dart")

    typescript_manifest = any(repository.glob("tsconfig*.json"))
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


def read_optional_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8") if path.is_file() else ""
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


def inspect_frameworks(
    repository: Path, languages: list[str], package: dict[str, Any] | None
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    entries: list[dict[str, Any]] = []
    findings: list[dict[str, str]] = []

    if "go" in languages:
        go_mod = read_optional_text(repository / "go.mod")
        detected = [
            name for name in (GO_GINKGO_MODULE, GO_GOMEGA_MODULE) if name in go_mod
        ]
        status = "canonical" if len(detected) == 2 else "waiver_required"
        entries.append(
            framework_entry("go", ["ginkgo-v2", "gomega"], detected, status, "ginkgo")
        )

    if "python" in languages:
        authority_paths = [
            repository / "pyproject.toml",
            repository / "setup.cfg",
            repository / "setup.py",
            *sorted(repository.glob("requirements*.txt")),
        ]
        has_pytest = any(
            re.search(r"\bpytest\b", read_optional_text(path))
            for path in authority_paths
        )
        entries.append(
            framework_entry(
                "python",
                ["pytest"],
                ["pytest"] if has_pytest else [],
                "canonical" if has_pytest else "waiver_required",
                "pytest",
            )
        )

    if "typescript" in languages:
        scripts_value = package.get("scripts") if package else None
        scripts = scripts_value if isinstance(scripts_value, dict) else {}
        unit_int_commands = "\n".join(
            value
            for key in ("test:unit", "test:int")
            if isinstance((value := scripts.get(key)), str)
        )
        dependencies = package_dependencies(package)
        detected: list[str] = []
        if re.search(r"(?:^|\s)bun\s+test(?:\s|$)", unit_int_commands):
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
        status = "canonical" if detected == ["vitest"] else "waiver_required"
        entries.append(
            framework_entry(
                "typescript", ["vitest"], sorted(set(detected)), status, "vitest"
            )
        )

    if "rust" in languages:
        entries.append(
            framework_entry(
                "rust", ["cargo-test"], ["cargo-test"], "canonical", "cargo-test"
            )
        )

    if "dart" in languages:
        pubspec = read_optional_text(repository / "pubspec.yaml")
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
            status = "canonical" if "flutter_test" in detected else "waiver_required"
            entry = framework_entry(
                "flutter",
                ["flutter_test", "patrol-e2e"],
                detected,
                status,
                "flutter-test",
            )
            entry["e2e_parser"] = "generic"
            entry["e2e_parser_support"] = "pending-patrol"
            entries.append(entry)
        else:
            has_test = bool(re.search(r"(?m)^\s*test:\s*", pubspec))
            entries.append(
                framework_entry(
                    "dart",
                    ["package:test"],
                    ["package:test"] if has_test else [],
                    "canonical" if has_test else "waiver_required",
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
    gaori = {
        "config_path": str(repository / ".gaori/tester.yaml"),
        "config_present": (repository / ".gaori/tester.yaml").is_file(),
        "parser_availability": "not_evaluated",
        "stage_parser_defaults": {
            "test": "generic",
            "test-prepare": "generic",
            "test-unit": unit_int_parser,
            "test-int": unit_int_parser,
            "test-e2e": "inspect_e2e_runner",
        },
    }
    return {"entries": entries, "gaori": gaori}, findings


def read_package(repository: Path) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    path = repository / "package.json"
    result: dict[str, Any] = {
        "path": str(path),
        "present": path.is_file(),
        "valid": False,
    }
    if not path.is_file():
        return None, result
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
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


def bun_adapter_matches(recipe: list[str], script: str) -> bool:
    if len(recipe) != 1:
        return False
    pattern = re.compile(
        rf"^[+@-]*\s*(?:bun|\$\(BUN\)|\$\{{BUN\}})\s+run\s+{re.escape(script)}\s*$"
    )
    return bool(pattern.fullmatch(recipe[0]))


def inspect_makefile(
    repository: Path, profile: str
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    path = repository / "Makefile"
    result: dict[str, Any] = {"path": str(path), "present": path.is_file()}
    findings: list[dict[str, str]] = []
    if not path.is_file():
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
    result["includes"] = includes
    result["targets"] = {}
    missing = []
    duplicates = []
    for name in MAKE_TARGETS:
        definitions = targets.get(name, [])
        result["targets"][name] = {
            "present": bool(definitions),
            "phony": name in phony,
            "definitions": definitions,
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
        if profile == "typescript-bun":
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
                    definition["recipe"], script
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
                for match in RECURSIVE_MAKE_PATTERN.finditer(command)
            ]
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
            elif recursive_calls == list(MAKE_STAGES):
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
        if required:
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
            "command": value if present else None,
        }
        if not present:
            missing.append(name)
    result["scripts"] = script_status
    aggregate = scripts.get("test") if isinstance(scripts.get("test"), str) else ""
    normalized = " ".join(aggregate.split())
    result["aggregate_serial"] = normalized == EXPECTED_BUN_AGGREGATE
    result["make_cycles"] = sorted(
        name
        for name, value in scripts.items()
        if isinstance(value, str)
        and re.search(r"(?:^|[;&|]\s*)make\s+test(?:\s|$|:|-)", value)
    )
    package_manager = package.get("packageManager")
    result["package_manager"] = package_manager
    result["bun_version_pinned"] = isinstance(package_manager, str) and bool(
        PINNED_BUN_PATTERN.fullmatch(package_manager)
    )
    engines = package.get("engines")
    result["bun_engine"] = engines.get("bun") if isinstance(engines, dict) else None
    result["lockfile"] = {
        "bun.lock": (repository / "bun.lock").is_file(),
        "bun.lockb": (repository / "bun.lockb").is_file(),
    }

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
        if result["make_cycles"]:
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
    return result, findings


def inspect_testing_document(
    repository: Path,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    path = repository / "TESTING.md"
    result = {
        "path": str(path),
        "present": path.is_file(),
        "contract_registered": False,
    }
    findings: list[dict[str, str]] = []
    if not path.is_file():
        findings.append(
            finding("testing_document_missing", "error", "Root TESTING.md is missing.")
        )
        return result, findings
    try:
        result["contract_registered"] = CONTRACT_MARKER in path.read_text(
            encoding="utf-8"
        )
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
    document_result, document_findings = inspect_testing_document(repository)
    findings = make_findings + bun_findings + framework_findings + document_findings
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
        repository = Path(options.repository).expanduser().resolve()
        if not repository.is_dir():
            raise InspectionError(
                "repository_not_found", "repository must be an existing directory"
            )
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
