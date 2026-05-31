PYTHON_BIN ?= python3
ARTIFACT_BUNDLE_DIR ?= tmp/artifact-release-bundle
ARTIFACT_PACKAGING_PROFILE ?= local_machine
VENUE_METADATA_DIR ?= tmp/venue-package-metadata

.PHONY: verify reproduce-paper-tables artifact-release-bundle validate-artifact-release-bundle venue-package-metadata validate-venue-package-metadata validate-selected-venue-policy

verify:
	PYTHON_BIN="$(PYTHON_BIN)" bash scripts/verify_all.sh

reproduce-paper-tables:
	PYTHON_BIN="$(PYTHON_BIN)" bash scripts/reproduce_paper_tables.sh

artifact-release-bundle:
	"$(PYTHON_BIN)" tools/build_artifact_release_bundle.py --replace --packaging-profile "$(ARTIFACT_PACKAGING_PROFILE)" --output-dir "$(ARTIFACT_BUNDLE_DIR)"

validate-artifact-release-bundle:
	"$(PYTHON_BIN)" tools/validate_artifact_release_bundle.py --packaging-profile "$(ARTIFACT_PACKAGING_PROFILE)" --bundle-dir "$(ARTIFACT_BUNDLE_DIR)"

venue-package-metadata:
	"$(PYTHON_BIN)" tools/build_venue_package_metadata.py --replace --output-dir "$(VENUE_METADATA_DIR)"

validate-venue-package-metadata:
	"$(PYTHON_BIN)" tools/validate_venue_package_metadata.py --bundle-dir "$(VENUE_METADATA_DIR)"

validate-selected-venue-policy:
	"$(PYTHON_BIN)" tools/validate_selected_venue_policy.py --venue-metadata-dir "$(VENUE_METADATA_DIR)"
