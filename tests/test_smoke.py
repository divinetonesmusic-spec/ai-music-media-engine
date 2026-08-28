"""Foundation smoke test — proves the package is importable and versioned."""

import market_intelligence


def test_package_exposes_semver_version():
    version = market_intelligence.__version__
    parts = version.split(".")
    assert len(parts) == 3, f"expected semver, got {version!r}"
    assert all(p.isdigit() for p in parts), f"expected numeric semver, got {version!r}"


def test_schema_version_constant_matches_spec():
    # docs/TECHNICAL-SPEC-V1.md front matter: schema_version "1.0.0"
    assert market_intelligence.SCHEMA_VERSION == "1.0.0"
