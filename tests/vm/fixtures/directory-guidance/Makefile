PYTHON ?= python3
export PYTHONDONTWRITEBYTECODE := 1
export PYTHONPATH := src

.PHONY: test
test:
	$(PYTHON) -B -m unittest discover -s tests -v
