ifneq ($(wildcard .venv/bin/python),)
override PYTHON := .venv/bin/python
else
override PYTHON := python3
endif

export GIT_PAGER := cat
export PAGER := cat
export PYTEST_DISABLE_PLUGIN_AUTOLOAD := 1
export PYTHONDONTWRITEBYTECODE := 1
override PYTEST_ADDOPTS :=
export PYTEST_ADDOPTS

.PHONY: test test-prepare test-unit test-int test-e2e

test:
	$(MAKE) test-prepare
	$(MAKE) test-unit
	$(MAKE) test-int
	$(MAKE) test-e2e

test-prepare:
	$(PYTHON) -m ruff format greet.py tests
	$(PYTHON) -m ruff check --no-cache greet.py tests
	$(PYTHON) -B -c 'import ast, pathlib; ast.parse(pathlib.Path("greet.py").read_text())'

test-unit:
	$(PYTHON) -m pytest tests/unit

test-int:
	$(PYTHON) -m pytest tests/integration

test-e2e:
	$(PYTHON) -m pytest tests/e2e
