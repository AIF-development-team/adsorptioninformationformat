"""Tests for AIF file structural rules using purpose-built fixture files.

Validates that the helper rules used in test_example_files.py correctly
detect problems in deliberately malformed AIF fixtures, and that valid
fixtures pass without errors. Uses the fixture files from dev/tests/fixtures/.
"""

import re
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"
PLACEHOLDER = "__AIF_VERSION__"

VALID_METHOD = {"volumetric", "gravimetric", "chromatographic", "simulation", "other"}
VALID_ISOTHERM_TYPE = {"absolute", "excess", "net"}


# ── Parse helpers (same logic as test_example_files.py) ─────────────────────


def _parse_loops(text: str):
    loops = []
    blocks = re.split(r"\bloop_\b", text, flags=re.IGNORECASE)
    for block in blocks[1:]:
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        headers: list[str] = []
        data_lines: list[str] = []
        in_headers = True
        for ln in lines:
            if ln.startswith("#"):
                continue
            if in_headers and ln.startswith("_"):
                headers.append(ln)
            else:
                in_headers = False
                if ln.startswith(("loop_", "data_", "save_")):
                    break
                data_lines.append(ln)
        data_rows = [dl.split() for dl in data_lines]
        loops.append((headers, data_rows))
    return loops


def _has_version(text: str) -> bool:
    return bool(re.search(r"_audit_aif_version", text))


def _version_value(text: str) -> str | None:
    m = re.search(r"_audit_aif_version\s+[\"']?([^\"'\s]+)[\"']?", text)
    return m.group(1) if m else None


def _method_value(text: str) -> str | None:
    m = re.search(r"_exptl_method\s+[\"']?(\w+)[\"']?", text)
    return m.group(1).strip("\"'") if m else None


def _loop_columns_consistent(text: str) -> tuple[bool, str]:
    for idx, (headers, rows) in enumerate(_parse_loops(text), start=1):
        n = len(headers)
        for ridx, row in enumerate(rows, start=1):
            if len(row) != n:
                return False, (
                    f"loop #{idx} row {ridx}: {len(row)} tokens, {n} headers"
                )
    return True, ""


# ── Valid fixtures ────────────────────────────────────────────────────────────


class TestValidMinimalAif:
    @pytest.fixture(scope="class")
    def text(self):
        return (FIXTURES_DIR / "valid_minimal.aif").read_text(encoding="utf-8")

    def test_has_version(self, text):
        assert _has_version(text)

    def test_version_is_placeholder(self, text):
        assert _version_value(text) == PLACEHOLDER

    def test_loop_columns_consistent(self, text):
        ok, msg = _loop_columns_consistent(text)
        assert ok, msg

    def test_has_adsorp_data(self, text):
        assert re.search(r"_adsorp_pressure", text)


class TestValidWithDesorption:
    @pytest.fixture(scope="class")
    def text(self):
        return (FIXTURES_DIR / "valid_with_desorption.aif").read_text(encoding="utf-8")

    def test_has_both_loops(self, text):
        loops = _parse_loops(text)
        assert len(loops) == 2, "Expected exactly 2 loop_ blocks (adsorp + desorp)"

    def test_adsorp_loop_has_four_columns(self, text):
        headers, rows = _parse_loops(text)[0]
        assert len(headers) == 4

    def test_desorp_loop_has_four_columns(self, text):
        headers, rows = _parse_loops(text)[1]
        assert len(headers) == 4

    def test_exptl_method_valid(self, text):
        val = _method_value(text)
        if val is not None:
            assert val in VALID_METHOD

    def test_exptl_isotherm_type_valid(self, text):
        m = re.search(r"_exptl_isotherm_type\s+[\"']?(\w+)[\"']?", text)
        if m:
            assert m.group(1).strip("\"'") in VALID_ISOTHERM_TYPE

    def test_loop_columns_consistent(self, text):
        ok, msg = _loop_columns_consistent(text)
        assert ok, msg


# ── Invalid fixtures ──────────────────────────────────────────────────────────


class TestInvalidNoVersion:
    @pytest.fixture(scope="class")
    def text(self):
        return (FIXTURES_DIR / "invalid_no_version.aif").read_text(encoding="utf-8")

    def test_version_is_absent(self, text):
        assert not _has_version(text), "Fixture should have no _audit_aif_version"

    def test_version_value_is_none(self, text):
        assert _version_value(text) is None


class TestInvalidBadEnumMethod:
    @pytest.fixture(scope="class")
    def text(self):
        return (FIXTURES_DIR / "invalid_bad_enum_method.aif").read_text(encoding="utf-8")

    def test_method_is_invalid_enum(self, text):
        val = _method_value(text)
        assert val is not None, "Fixture must contain _exptl_method"
        assert val not in VALID_METHOD, (
            f"Fixture should use an invalid enum value, got '{val}'"
        )


class TestInvalidLoopColMismatch:
    @pytest.fixture(scope="class")
    def text(self):
        return (FIXTURES_DIR / "invalid_loop_col_mismatch.aif").read_text(encoding="utf-8")

    def test_loop_column_mismatch_is_detected(self, text):
        ok, msg = _loop_columns_consistent(text)
        assert not ok, "Fixture should have mismatched loop columns but none detected"


# ── Edge cases ────────────────────────────────────────────────────────────────


class TestEdgeCases:
    def test_empty_file_has_no_version(self, tmp_path):
        p = tmp_path / "empty.aif"
        p.write_text("", encoding="utf-8")
        text = p.read_text(encoding="utf-8")
        assert not _has_version(text)
        assert _version_value(text) is None

    def test_single_quoted_version(self, tmp_path):
        p = tmp_path / "single_quoted.aif"
        p.write_text("_audit_aif_version '1.0.0'\n", encoding="utf-8")
        text = p.read_text(encoding="utf-8")
        assert _version_value(text) == "1.0.0"

    def test_double_quoted_version(self, tmp_path):
        p = tmp_path / "double_quoted.aif"
        p.write_text('_audit_aif_version "1.0.0"\n', encoding="utf-8")
        text = p.read_text(encoding="utf-8")
        assert _version_value(text) == "1.0.0"

    def test_loop_with_zero_rows_is_consistent(self, tmp_path):
        content = (
            "data_test\n"
            '    _audit_aif_version "__AIF_VERSION__"\n'
            "    loop_\n"
            "        _adsorp_pressure\n"
            "        _adsorp_loading\n"
        )
        text = content
        ok, msg = _loop_columns_consistent(text)
        assert ok, msg

    def test_multiple_loops_all_consistent(self, tmp_path):
        content = (
            "data_test\n"
            '    _audit_aif_version "__AIF_VERSION__"\n'
            "    loop_\n"
            "        _adsorp_pressure\n"
            "        _adsorp_loading\n"
            "        100.0 0.5\n"
            "        200.0 1.0\n"
            "    loop_\n"
            "        _desorp_pressure\n"
            "        _desorp_loading\n"
            "        200.0 1.0\n"
            "        100.0 0.5\n"
        )
        ok, msg = _loop_columns_consistent(content)
        assert ok, msg
