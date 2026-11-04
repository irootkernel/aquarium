PYTHON := python3
export PYTHONDONTWRITEBYTECODE := 1
.PHONY: test test-prepare test-unit test-int test-e2e test-release-metadata
test:
	$(MAKE) test-prepare
	$(MAKE) test-unit
	$(MAKE) test-int
	$(MAKE) test-e2e
test-prepare:
	$(PYTHON) -B "$(AQUARIUM_RELEASE_FIXTURE_DRIVER)" gate --root "$(AQUARIUM_RELEASE_FIXTURE_ROOT)" --stage prepare
test-unit:
	$(PYTHON) -B "$(AQUARIUM_RELEASE_FIXTURE_DRIVER)" gate --root "$(AQUARIUM_RELEASE_FIXTURE_ROOT)" --stage unit
test-int:
	$(PYTHON) -B "$(AQUARIUM_RELEASE_FIXTURE_DRIVER)" gate --root "$(AQUARIUM_RELEASE_FIXTURE_ROOT)" --stage int
test-e2e:
	$(PYTHON) -B "$(AQUARIUM_RELEASE_FIXTURE_DRIVER)" gate --root "$(AQUARIUM_RELEASE_FIXTURE_ROOT)" --stage e2e
test-release-metadata:
	$(PYTHON) -B "$(AQUARIUM_RELEASE_FIXTURE_DRIVER)" gate --root "$(AQUARIUM_RELEASE_FIXTURE_ROOT)" --stage metadata
