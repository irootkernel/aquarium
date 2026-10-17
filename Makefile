override VENV_DIR := .venv

ifneq ($(wildcard $(VENV_DIR)/bin/python),)
override PYTHON := $(VENV_DIR)/bin/python
else
override PYTHON := python3
endif

ifneq ($(wildcard $(VENV_DIR)/bin/ruff),)
override RUFF := $(VENV_DIR)/bin/ruff
else
override RUFF := ruff
endif

export GIT_PAGER := cat
export PAGER := cat
export PYTEST_DISABLE_PLUGIN_AUTOLOAD := 1
override PYTEST_ADDOPTS :=
export PYTEST_ADDOPTS

PYTHON_FILES := \
	plugins/aquarium/shared/adaptive_promotion.py \
	plugins/aquarium/shared/promote_adaptive_procedure.py \
	tests/vm/adaptive_cases.py \
	tests/vm/fixtures/adaptive/diagnosis/sampler.py \
	tests/unit/test_adaptive_promotion_unit.py \
	tests/unit/test_adaptive_recovery_matrix_unit.py \
	tests/unit/test_vm_adaptive_cases_unit.py \
	plugins/aquarium/shared/adaptive_diagnosis.py \
	plugins/aquarium/shared/adaptive_supersede.py \
	tests/unit/test_adaptive_diagnosis_unit.py \
	tests/unit/test_adaptive_supersede_unit.py \
	plugins/aquarium/shared/adaptive_entrypoint.py \
	plugins/aquarium/shared/adaptive_design.py \
	tests/unit/test_adaptive_design_unit.py \
	plugins/aquarium/shared/adaptive_execution.py \
	plugins/aquarium/shared/adaptive_finalization.py \
	tests/unit/test_adaptive_execution_unit.py \
	plugins/aquarium/shared/adaptive_predicates.py \
	plugins/aquarium/shared/adaptive_qualification.py \
	plugins/aquarium/shared/adaptive_suitability.py \
	plugins/aquarium/shared/qualify_adaptive_procedure.py \
	tests/unit/test_adaptive_qualification_unit.py \
	tests/unit/test_adaptive_suitability_unit.py \
	plugins/aquarium/shared/adaptive_composition.py \
	tests/unit/test_adaptive_composition_unit.py \
	plugins/aquarium/shared/adaptive_preparation.py \
	plugins/aquarium/shared/prepare_adaptive_procedure.py \
	tests/unit/test_adaptive_preparation_unit.py \
	plugins/aquarium/shared/adaptive_bundles.py \
	plugins/aquarium/shared/adaptive_admission.py \
	plugins/aquarium/shared/manage_adaptive_procedure.py \
	tests/unit/test_adaptive_bundles_unit.py \
	plugins/aquarium/shared/adaptive_definitions.py \
	tests/unit/test_adaptive_definitions_unit.py \
	tests/vm/run_acceptance.py \
	tests/vm/native_observation.py \
	tests/unit/test_vm_acceptance_unit.py \
	tests/vm/fixtures/greeting/greet.py \
	tests/vm/fixtures/greeting/tests/unit/test_greet.py \
	tests/vm/fixtures/greeting/tests/integration/test_cli.py \
	tests/vm/fixtures/greeting/tests/e2e/test_greeting_cli.py \
	tests/unit/test_promoted_evidence_schema_unit.py \
	tests/unit/test_source_identity_digest_unit.py \
	plugins/aquarium/skills/task-commit/scripts/source_identity_digest.py \
	tests/check_test_requirements.py \
	tests/unit/test_check_test_requirements_unit.py \
	tests/unit/test_setup_package_contracts.py \
	plugins/aquarium/skills/dev-setup-global/scripts/inspect_skill_inventory.py \
	tests/unit/test_aquarium_dev_tool_unit.py \
	tests/unit/test_aquarium_status_install_unit.py \
	tests/unit/test_aquarium_status_unit.py \
	plugins/aquarium/tools/aquarium-dev/mcp_server.py \
	plugins/aquarium/tools/aquarium-dev/install.py \
	plugins/aquarium/tools/aquarium-dev/runtime_entry.py \
	plugins/aquarium/tools/aquarium-status/aquarium_status.py \
	plugins/aquarium/tools/aquarium-status/language_inventory.py \
	plugins/aquarium/tools/aquarium-status/install.py \
	plugins/aquarium/tools/aquarium-status/runtime_entry.py \
	plugins/aquarium/tools/aquarium-status/status_contract.py \
	plugins/aquarium/tools/aquarium-status/status_report.py \
	plugins/aquarium/tools/aquarium-status/status_store.py \
	plugins/aquarium/hooks/task_commit_gate.py \
	plugins/aquarium/skills/dev-setup/scripts/inspect_tools.py \
	plugins/aquarium/skills/dev-setup-global/scripts/inspect_global_tools.py \
	plugins/aquarium/skills/dev-setup-global/scripts/inspect_ouroboros.py \
	plugins/aquarium/tools/aquarium-dev/dev_contract.py \
	plugins/aquarium/tools/aquarium-dev/aquarium_dev.py \
	plugins/aquarium/tools/aquarium-dev/aquarium_dev_launcher.py \
	plugins/aquarium/tools/aquarium-dev/build_aquarium_artifact.py \
	plugins/aquarium/tools/aquarium-dev/dev_manager.py \
	plugins/aquarium/skills/dev-setup-bundle/scripts/normalize_manifest.py \
	plugins/aquarium/skills/docs-setup/scripts/inspect_docs.py \
	plugins/aquarium/skills/independent-review/scripts/inspect_review_target.py \
	plugins/aquarium/skills/goal-judge/scripts/prepare_assignment.py \
	plugins/aquarium/skills/goal-judge/scripts/ordinary_assignment.py \
	tests/unit/test_ordinary_assignment_unit.py \
	plugins/aquarium/skills/goal-judge/scripts/map_native_delivery.py \
	plugins/aquarium/skills/goal-judge/scripts/render_dispatch.py \
	plugins/aquarium/skills/goal-judge/scripts/bind_prepared_delivery.py \
	plugins/aquarium/skills/goal-judge/scripts/bind_claude_delivery.py \
	plugins/aquarium/skills/goal-judge/scripts/read_codex_thread.py \
	plugins/aquarium/skills/release-handler/scripts/inspect_publication_state.py \
	plugins/aquarium/skills/release-handler/scripts/inspect_release_notes.py \
	plugins/aquarium/skills/release-qa/scripts/manage_release_qa.py \
	plugins/aquarium/skills/test-setup/scripts/inspect_testing.py \
	tests/test_inspect_docs.py \
	tests/test_inspect_global_tools.py \
	tests/test_inspect_tools.py \
	tests/test_inspect_testing.py \
	tests/test_aquarium_status_integration.py \
	tests/test_normalize_manifest.py \
	tests/test_task_commit_gate.py \
	tests/podway_runtime_qualification.py \
	tests/verify_podway_compatibility.py \
	tests/unit/test_inspect_docs_unit.py \
	tests/unit/test_aquarium_dev_contract_unit.py \
	tests/unit/test_aquarium_dev_enrollment_unit.py \
	tests/unit/test_aquarium_dev_publication_unit.py \
	tests/unit/test_aquarium_dev_resolution_unit.py \
	tests/unit/test_aquarium_dev_runtime_unit.py \
	tests/unit/test_aquarium_dev_service_unit.py \
	tests/unit/test_aquarium_dev_feasibility_unit.py \
	tests/unit/test_inspect_publication_state_unit.py \
	tests/unit/test_inspect_review_target_unit.py \
	tests/unit/test_prepare_assignment_unit.py \
	tests/unit/test_map_native_delivery_unit.py \
	tests/unit/test_render_dispatch_unit.py \
	tests/unit/test_bind_prepared_delivery_unit.py \
	tests/unit/test_bind_claude_delivery_unit.py \
	tests/unit/test_read_codex_thread_unit.py \
	tests/unit/test_inspect_release_notes_unit.py \
	tests/unit/test_manage_release_qa_unit.py \
	tests/unit/test_procedure_alignment_contracts.py \
	tests/unit/test_inspect_testing_unit.py \
	tests/unit/test_verify_podway_compatibility_unit.py \
	tests/e2e/test_test_setup_cli.py \
	tests/e2e/test_aquarium_status_cli.py \
	tests/e2e/test_release_qa_confirmation_cli.py

.PHONY: test test-requirements test-prepare test-unit test-int test-e2e test-podway-compat test-vm
.PHONY: aquarium-dev-describe aquarium-dev-build

aquarium-dev-describe:
	@$(PYTHON) plugins/aquarium/tools/aquarium-dev/build_aquarium_artifact.py describe

aquarium-dev-build:
	@$(PYTHON) plugins/aquarium/tools/aquarium-dev/build_aquarium_artifact.py build

test:
	$(MAKE) test-prepare
	$(MAKE) test-unit
	$(MAKE) test-int
	$(MAKE) test-e2e

test-requirements:
	@command -v ruby >/dev/null 2>&1 || { echo "error: Ruby is unavailable; install Ruby 3.3+ (macOS: brew install ruby)" >&2; exit 2; }
	@command -v "$(PYTHON)" >/dev/null 2>&1 || { echo "error: Python is unavailable; create .venv and install requirements.txt" >&2; exit 2; }
	@command -v "$(RUFF)" >/dev/null 2>&1 || { echo "error: Ruff is unavailable; run $(PYTHON) -m pip install -r requirements.txt" >&2; exit 2; }
	@$(PYTHON) tests/check_test_requirements.py "$(RUFF)" || { echo "error: test dependencies are unavailable or below minimum; run $(PYTHON) -m pip install -r requirements.txt" >&2; exit 2; }

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
	$(PYTHON) -m pytest tests/test_aquarium_status_integration.py tests/test_inspect_docs.py tests/test_inspect_global_tools.py tests/test_inspect_testing.py
	$(PYTHON) -m unittest tests/test_inspect_tools.py tests/test_task_commit_gate.py tests/test_normalize_manifest.py

test-e2e: test-requirements
	$(PYTHON) -m pytest tests/e2e

test-podway-compat: test-requirements
	PODWAY_BIN="$(PODWAY_BIN)" $(PYTHON) tests/verify_podway_compatibility.py

test-vm:
	$(PYTHON) -B tests/vm/run_acceptance.py run
