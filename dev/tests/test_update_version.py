"""Unit tests for dev/update_version.py.

Covers ``parse_version_string``, ``is_newer_version``, and
``replace_version_placeholder`` without invoking external processes.
"""

import pytest
import update_version as uv

PLACEHOLDER = uv.PLACEHOLDER


# ── parse_version_string ─────────────────────────────────────────────────────


class TestParseVersionString:
    @pytest.mark.parametrize(
        "ref, expected",
        [
            ("1.2.3", "1.2.3"),
            ("v1.2.3", "1.2.3"),
            ("0.1.0", "0.1.0"),
            ("10.20.30", "10.20.30"),
            ("release/1.2.3", "1.2.3"),
            ("release/v1.2.3", "1.2.3"),
            ("release/10.0.0", "10.0.0"),
        ],
    )
    def test_valid_inputs(self, ref, expected):
        assert uv.parse_version_string(ref) == expected

    @pytest.mark.parametrize(
        "ref",
        [
            "",
            "latest",
            "1.0",
            "1",
            "abc",
            "release/",
            "release/bad",
            "feature/1.0.0",
            PLACEHOLDER,
        ],
    )
    def test_invalid_inputs_raise_value_error(self, ref):
        with pytest.raises(ValueError):
            uv.parse_version_string(ref)


# ── is_newer_version ─────────────────────────────────────────────────────────


class TestIsNewerVersion:
    def test_newer_returns_true(self):
        assert uv.is_newer_version("1.0.0", "1.0.1") is True
        assert uv.is_newer_version("1.0.0", "1.1.0") is True
        assert uv.is_newer_version("1.0.0", "2.0.0") is True

    def test_older_returns_false(self):
        assert uv.is_newer_version("2.0.0", "1.0.0") is False
        assert uv.is_newer_version("1.1.0", "1.0.9") is False

    def test_equal_returns_false(self):
        assert uv.is_newer_version("1.2.3", "1.2.3") is False

    def test_placeholder_old_treated_as_zero(self):
        # placeholder is treated as (0, 0, 0) so any real version is "newer"
        assert uv.is_newer_version(PLACEHOLDER, "0.0.1") is True
        assert uv.is_newer_version(PLACEHOLDER, "1.0.0") is True

    def test_minor_patch_ordering(self):
        assert uv.is_newer_version("1.9.9", "2.0.0") is True
        assert uv.is_newer_version("1.0.9", "1.1.0") is True


# ── replace_version_placeholder ──────────────────────────────────────────────


class TestReplaceVersionPlaceholder:
    def test_placeholder_is_replaced_in_json(self, tmp_path, monkeypatch):
        """Placeholder is replaced in a patched MAIN_FILES list."""
        json_file = tmp_path / "aif_dictionary.json"
        json_file.write_text(f'"version": "{PLACEHOLDER}"', encoding="utf-8")

        monkeypatch.setattr(uv, "MAIN_FILES", [json_file])
        # Provide a non-existent examples dir so the rglob is a no-op
        monkeypatch.setattr(uv, "REPO_ROOT", tmp_path)

        uv.replace_version_placeholder("1.2.3")
        assert '"version": "1.2.3"' in json_file.read_text(encoding="utf-8")

    def test_file_without_placeholder_is_skipped(self, tmp_path, monkeypatch, capsys):
        """A file that already has a real version is not modified."""
        json_file = tmp_path / "aif_dictionary.json"
        original = '"version": "0.9.0"'
        json_file.write_text(original, encoding="utf-8")

        monkeypatch.setattr(uv, "MAIN_FILES", [json_file])
        monkeypatch.setattr(uv, "REPO_ROOT", tmp_path)

        uv.replace_version_placeholder("1.2.3")
        assert json_file.read_text(encoding="utf-8") == original

    def test_aif_example_files_are_updated(self, tmp_path, monkeypatch):
        """AIF files in the examples subtree have their placeholder replaced."""
        (tmp_path / "examples").mkdir()
        aif_file = tmp_path / "examples" / "sample.aif"
        aif_file.write_text(f'_audit_aif_version "{PLACEHOLDER}"', encoding="utf-8")

        monkeypatch.setattr(uv, "MAIN_FILES", [])
        monkeypatch.setattr(uv, "REPO_ROOT", tmp_path)

        uv.replace_version_placeholder("2.0.0")
        assert '"2.0.0"' in aif_file.read_text(encoding="utf-8")
