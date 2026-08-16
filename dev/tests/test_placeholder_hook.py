"""Tests for dev/check_placeholder_on_tag_push.py.

The hook reads pushed refs from stdin and only acts when a tag ref is
being pushed.  We test the three key scenarios:
  1. No tag pushed → always passes (exit 0)
  2. Tag pushed, dictionary files contain the placeholder → fails (exit 1)
  3. Tag pushed, dictionary files do not contain the placeholder → passes (exit 0)
"""

import io
import pytest

import check_placeholder_on_tag_push as hook

PLACEHOLDER = hook.PLACEHOLDER


# ── Helper ────────────────────────────────────────────────────────────────────


def _run_main(stdin_text: str, monkeypatch, dict_files: list) -> int:
    """Run hook.main() with controlled stdin and DICT_FILES."""
    monkeypatch.setattr(hook, "DICT_FILES", dict_files)
    monkeypatch.setattr("sys.stdin", io.StringIO(stdin_text))
    return hook.main()


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestNonTagPush:
    def test_branch_push_passes_when_placeholder_present(self, tmp_path, monkeypatch):
        """A branch push should always return 0, even with the placeholder."""
        dic = tmp_path / "aif_dictionary.json"
        dic.write_text(f'"version": "{PLACEHOLDER}"', encoding="utf-8")

        stdin = "refs/heads/develop abc123 refs/heads/develop def456\n"
        rc = _run_main(stdin, monkeypatch, [dic])
        assert rc == 0

    def test_empty_stdin_passes(self, tmp_path, monkeypatch):
        dic = tmp_path / "aif_dictionary.json"
        dic.write_text(f'"version": "{PLACEHOLDER}"', encoding="utf-8")

        rc = _run_main("", monkeypatch, [dic])
        assert rc == 0

    def test_feature_branch_push_passes(self, tmp_path, monkeypatch):
        dic = tmp_path / "aif_dictionary.yaml"
        dic.write_text(f'version: "{PLACEHOLDER}"', encoding="utf-8")

        stdin = "refs/heads/feature/v10hackathon abc refs/heads/feature/v10hackathon def\n"
        rc = _run_main(stdin, monkeypatch, [dic])
        assert rc == 0


class TestTagPushWithPlaceholder:
    def test_single_file_with_placeholder_fails(self, tmp_path, monkeypatch):
        dic = tmp_path / "aif_dictionary.json"
        dic.write_text(f'"version": "{PLACEHOLDER}"', encoding="utf-8")

        stdin = "refs/tags/v1.0.0 abc123 refs/tags/v1.0.0 def456\n"
        rc = _run_main(stdin, monkeypatch, [dic])
        assert rc == 1

    def test_multiple_files_with_placeholder_fails(self, tmp_path, monkeypatch):
        files = []
        for name in ("aif_dictionary.json", "aif_dictionary.dic", "aif_dictionary.yaml"):
            p = tmp_path / name
            p.write_text(f"version {PLACEHOLDER}", encoding="utf-8")
            files.append(p)

        stdin = "refs/tags/v2.0.0 abc refs/tags/v2.0.0 def\n"
        rc = _run_main(stdin, monkeypatch, files)
        assert rc == 1

    def test_error_message_names_bad_files(self, tmp_path, monkeypatch, capsys):
        dic = tmp_path / "aif_dictionary.json"
        dic.write_text(f'"version": "{PLACEHOLDER}"', encoding="utf-8")

        stdin = "refs/tags/v1.0.0 abc refs/tags/v1.0.0 def\n"
        _run_main(stdin, monkeypatch, [dic])
        captured = capsys.readouterr()
        assert "aif_dictionary.json" in captured.err


class TestTagPushWithoutPlaceholder:
    def test_files_without_placeholder_pass(self, tmp_path, monkeypatch):
        files = []
        for name in ("aif_dictionary.json", "aif_dictionary.dic", "aif_dictionary.yaml"):
            p = tmp_path / name
            p.write_text('"version": "1.0.0"', encoding="utf-8")
            files.append(p)

        stdin = "refs/tags/v1.0.0 abc refs/tags/v1.0.0 def\n"
        rc = _run_main(stdin, monkeypatch, files)
        assert rc == 0

    def test_missing_dict_file_does_not_block_tag_push(self, tmp_path, monkeypatch):
        """A missing file cannot contain the placeholder, so it must not block."""
        nonexistent = tmp_path / "does_not_exist.json"

        stdin = "refs/tags/v1.0.0 abc refs/tags/v1.0.0 def\n"
        rc = _run_main(stdin, monkeypatch, [nonexistent])
        assert rc == 0

    def test_partial_placeholder_text_does_not_trigger(self, tmp_path, monkeypatch):
        """Only the exact placeholder string should trigger a failure."""
        dic = tmp_path / "aif_dictionary.json"
        # Contains a fragment but not the full placeholder
        dic.write_text('"version": "AIF_VERSION"', encoding="utf-8")

        stdin = "refs/tags/v1.0.0 abc refs/tags/v1.0.0 def\n"
        rc = _run_main(stdin, monkeypatch, [dic])
        assert rc == 0
