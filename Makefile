override VENV_DIR := .venv

ifneq ($(wildcard $(VENV_DIR)/bin/python),)
override PYTHON := $(VENV_DIR)/bin/python
override RUFF := $(VENV_DIR)/bin/ruff
else
override PYTHON := python3
override RUFF := ruff
endif

export GIT_PAGER := cat
export PAGER := cat
export PYTEST_DISABLE_PLUGIN_AUTOLOAD := 1
override PYTEST_ADDOPTS :=
export PYTEST_ADDOPTS

PYTHON_FILES := \
	plugins/aquarium/hooks/task_commit_gate.py \
	plugins/aquarium/skills/dev-setup/scripts/inspect_tools.py \
	plugins/aquarium/skills/dev-setup-bundle/scripts/normalize_manifest.py \
	plugins/aquarium/skills/docs-setup/scripts/inspect_docs.py \
	plugins/aquarium/skills/independent-review/scripts/inspect_review_target.py \
	plugins/aquarium/skills/orca-review/scripts/create_provider_terminal.py \
	plugins/aquarium/skills/release-handler/scripts/inspect_publication_state.py \
	plugins/aquarium/skills/release-handler/scripts/inspect_release_notes.py \
	plugins/aquarium/skills/test-setup/scripts/inspect_testing.py \
	tests/test_inspect_docs.py \
	tests/test_inspect_tools.py \
	tests/test_inspect_testing.py \
	tests/test_normalize_manifest.py \
	tests/test_task_commit_gate.py \
	tests/unit/test_inspect_docs_unit.py \
	tests/unit/test_create_provider_terminal_unit.py \
	tests/unit/test_inspect_publication_state_unit.py \
	tests/unit/test_inspect_review_target_unit.py \
	tests/unit/test_inspect_release_notes_unit.py \
	tests/unit/test_inspect_testing_unit.py \
	tests/e2e/test_test_setup_cli.py

.PHONY: test test-requirements test-prepare test-unit test-int test-e2e

test:
	$(MAKE) test-prepare
	$(MAKE) test-unit
	$(MAKE) test-int
	$(MAKE) test-e2e

test-requirements:
	@command -v "$(PYTHON)" >/dev/null 2>&1 || { echo "error: Python is unavailable; create .venv and install requirements.txt" >&2; exit 2; }
	@command -v "$(RUFF)" >/dev/null 2>&1 || { echo "error: Ruff is unavailable; run $(PYTHON) -m pip install -r requirements.txt" >&2; exit 2; }
	@$(PYTHON) -c 'import importlib.util, subprocess, sys; from importlib.metadata import distributions; lines = [line.strip() for line in open("requirements.txt", encoding="utf-8") if line.strip() and not line.lstrip().startswith("#")]; invalid = [line for line in lines if line.count("==") != 1]; expected = {name.lower(): wanted for name, wanted in (line.split("==", 1) for line in lines if line.count("==") == 1)}; installed = {distribution.metadata["Name"].lower(): distribution.version for distribution in distributions() if distribution.metadata["Name"]}; missing = sorted(name for name in expected if name not in installed); mismatches = [f"{name}=={installed[name]} (expected {wanted})" for name, wanted in expected.items() if name in installed and installed[name] != wanted]; missing_modules = [name for name, module in (("pytest", "pytest"), ("PyYAML", "yaml")) if importlib.util.find_spec(module) is None]; ruff = subprocess.run(["$(RUFF)", "--version"], capture_output=True, text=True, check=False); expected_ruff = "ruff " + expected.get("ruff", ""); observed_ruff = ruff.stdout.strip() or ruff.stderr.strip() or "exit " + str(ruff.returncode); errors = ([f"Python {sys.version.split()[0]} is unsupported; expected >=3.11"] if sys.version_info < (3, 11) else []) + (["non-exact requirements: " + ", ".join(invalid)] if invalid else []) + (["missing distributions: " + ", ".join(missing)] if missing else []) + (["missing modules: " + ", ".join(missing_modules)] if missing_modules else []) + (["version mismatch: " + ", ".join(mismatches)] if mismatches else []) + ([f"Ruff executable reports {observed_ruff} (expected {expected_ruff})"] if ruff.returncode != 0 or ruff.stdout.strip() != expected_ruff else []); sys.exit("; ".join(errors) if errors else 0)' || { echo "error: test dependencies are unavailable or incompatible; run $(PYTHON) -m pip install -r requirements.txt" >&2; exit 2; }

test-prepare: test-requirements
	$(RUFF) format $(PYTHON_FILES)
	$(RUFF) check $(PYTHON_FILES)
	$(PYTHON) -m json.tool plugins/aquarium/.codex-plugin/plugin.json >/dev/null
	ruby -c tests/validate.rb
	ruby tests/validate.rb
	git --no-pager diff --check

test-unit: test-requirements
	$(PYTHON) -m pytest tests/unit

test-int: test-requirements
	$(PYTHON) -m pytest tests/test_inspect_docs.py tests/test_inspect_testing.py
	$(PYTHON) -m unittest tests/test_inspect_tools.py tests/test_task_commit_gate.py tests/test_normalize_manifest.py

test-e2e: test-requirements
	$(PYTHON) -m pytest tests/e2e
