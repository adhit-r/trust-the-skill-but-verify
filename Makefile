PYTHON_BIN ?= python3
ARTIFACT_BUNDLE_DIR ?= tmp/artifact-release-bundle

.PHONY: verify reproduce-paper-tables artifact-release-bundle validate-artifact-release-bundle

verify:
	PYTHON_BIN="$(PYTHON_BIN)" bash scripts/verify_all.sh

reproduce-paper-tables:
	PYTHON_BIN="$(PYTHON_BIN)" bash scripts/reproduce_paper_tables.sh

artifact-release-bundle:
	"$(PYTHON_BIN)" tools/build_artifact_release_bundle.py --replace --output-dir "$(ARTIFACT_BUNDLE_DIR)"

validate-artifact-release-bundle:
	"$(PYTHON_BIN)" tools/validate_artifact_release_bundle.py --bundle-dir "$(ARTIFACT_BUNDLE_DIR)"
