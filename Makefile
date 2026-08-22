VENV_DIR ?= .venv

ifneq ($(wildcard $(VENV_DIR)/bin/python),)
PYTHON ?= $(VENV_DIR)/bin/python
RUFF ?= $(VENV_DIR)/bin/ruff
else
PYTHON ?= python3
RUFF ?= ruff
endif

export GIT_PAGER := cat
export PAGER := cat
export PYTEST_DISABLE_PLUGIN_AUTOLOAD := 1

PYTHON_FILES := \
	plugins/aquarium/hooks/task_commit_gate.py \
	plugins/aquarium/skills/dev-setup/scripts/inspect_tools.py \
	plugins/aquarium/skills/dev-setup-bundle/scripts/normalize_manifest.py \
	plugins/aquarium/skills/test-setup/scripts/inspect_testing.py \
	tests/test_inspect_tools.py \
	tests/test_inspect_testing.py \
	tests/test_normalize_manifest.py \
	tests/test_task_commit_gate.py \
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
	@$(PYTHON) -c 'import importlib.util, sys; from importlib.metadata import version; expected = {"pytest": ("pytest", "9.1.1"), "PyYAML": ("yaml", "6.0.3"), "ruff": ("ruff", "0.16.2")}; missing = [name for name, (module, _) in expected.items() if importlib.util.find_spec(module) is None]; actual = {name: version(name) for name in expected if name not in missing}; mismatches = [f"{name}=={actual[name]} (expected {wanted})" for name, (_, wanted) in expected.items() if name in actual and actual[name] != wanted]; errors = ([f"Python {sys.version.split()[0]} is unsupported; expected >=3.10"] if sys.version_info < (3, 10) else []) + (["missing: " + ", ".join(missing)] if missing else []) + (["version mismatch: " + ", ".join(mismatches)] if mismatches else []); sys.exit("; ".join(errors) if errors else 0)' || { echo "error: test dependencies are unavailable or incompatible; run $(PYTHON) -m pip install -r requirements.txt" >&2; exit 2; }

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
	$(PYTHON) -m unittest tests/test_inspect_tools.py tests/test_inspect_testing.py tests/test_task_commit_gate.py tests/test_normalize_manifest.py

test-e2e: test-requirements
	$(PYTHON) -m pytest tests/e2e
