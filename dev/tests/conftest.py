"""Shared pytest configuration and fixtures for the AIF test suite."""

import sys
from pathlib import Path
import pytest

# ── Path setup ──────────────────────────────────────────────────────────────
# Allow ``import check_aif_format``, ``import sync_dictionaries``, etc.
# without installing the dev scripts as a package.

REPO_ROOT = Path(__file__).parent.parent.parent
DEV_DIR = REPO_ROOT / "dev"

if str(DEV_DIR) not in sys.path:
    sys.path.insert(0, str(DEV_DIR))

# ── Convenience constants ────────────────────────────────────────────────────

FIXTURES_DIR = Path(__file__).parent / "fixtures"
EXAMPLES_DIR = REPO_ROOT / "examples"
PLACEHOLDER = "__AIF_VERSION__"

VALID_ENUM_METHOD = {"volumetric", "gravimetric", "chromatographic", "simulation", "other"}
VALID_ENUM_ISOTHERM_TYPE = {"absolute", "excess", "net"}

# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def json_path(repo_root) -> Path:
    return repo_root / "aif_dictionary.json"


@pytest.fixture(scope="session")
def dic_path(repo_root) -> Path:
    return repo_root / "aif_dictionary.dic"


@pytest.fixture(scope="session")
def yaml_path(repo_root) -> Path:
    return repo_root / "aif_dictionary.yaml"


@pytest.fixture(scope="session")
def example_aif_path(repo_root) -> Path:
    return repo_root / "example.aif"


@pytest.fixture
def tmp_aif(tmp_path):
    """Return a helper that writes an AIF snippet to a tmp file and returns its Path."""

    def _write(content: str, name: str = "test.aif") -> Path:
        p = tmp_path / name
        p.write_text(content, encoding="utf-8")
        return p

    return _write
