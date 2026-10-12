"""Unit tests for dev/check_aif_format.py.

Covers every exported function plus an integration smoke-test that runs
``main()`` against the real repository files.
"""

import json
import re
import sys
import pytest

import check_aif_format as caf

PLACEHOLDER = caf.PLACEHOLDER

# ── _is_valid_version ────────────────────────────────────────────────────────


class TestIsValidVersion:
    @pytest.mark.parametrize("v", [PLACEHOLDER])
    def test_placeholder_is_valid(self, v):
        assert caf._is_valid_version(v)

    @pytest.mark.parametrize(
        "v", ["1.0.0", "0.1.0", "10.20.30", "v1.2.3", "v0.0.1", "1.0.0-beta", "1.0.0-rc.1"]
    )
    def test_semver_variants_are_valid(self, v):
        assert caf._is_valid_version(v)

    @pytest.mark.parametrize(
        "v",
        [
            "",
            "1.0",
            "1",
            "1.0.0.0",
            "1.0.x",
            "latest",
            "v",
            "v1",
            "1.0.0-",
            "1.0.0-beta..1",
            "1.0.0+build",
            "release/1.0.0",
        ],
    )
    def test_invalid_strings_are_rejected(self, v):
        assert not caf._is_valid_version(v)


# ── check_json ───────────────────────────────────────────────────────────────


class TestCheckJson:
    def _write_json(self, tmp_path, data: dict, name="test.json"):
        p = tmp_path / name
        p.write_text(json.dumps(data), encoding="utf-8")
        return p

    def _minimal_valid(self):
        return {
            "version": PLACEHOLDER,
            "$id": f"https://example.com/tree/{PLACEHOLDER}/schema.json",
            "required": ["_audit_aif_version"],
            "definitions": {
                "audit": {
                    "properties": {
                        "_audit_aif_version": {"const": PLACEHOLDER}
                    }
                }
            },
        }

    def test_valid_json_returns_one_version_no_errors(self, tmp_path):
        p = self._write_json(tmp_path, self._minimal_valid())
        versions, errors = caf.check_json(p)
        assert errors == []
        assert set(versions) == {PLACEHOLDER}

    def test_missing_top_level_version_key(self, tmp_path):
        data = self._minimal_valid()
        del data["version"]
        p = self._write_json(tmp_path, data)
        _, errors = caf.check_json(p)
        assert any("version" in e for e in errors)

    def test_unparseable_id_url(self, tmp_path):
        data = self._minimal_valid()
        data["$id"] = "https://example.com/no-version-here"
        p = self._write_json(tmp_path, data)
        _, errors = caf.check_json(p)
        assert any("$id" in e for e in errors)

    def test_missing_audit_aif_version_const(self, tmp_path):
        data = self._minimal_valid()
        del data["definitions"]["audit"]["properties"]["_audit_aif_version"]["const"]
        p = self._write_json(tmp_path, data)
        _, errors = caf.check_json(p)
        assert any("const" in e for e in errors)

    def test_audit_aif_version_not_in_required(self, tmp_path):
        data = self._minimal_valid()
        data["required"] = []
        p = self._write_json(tmp_path, data)
        _, errors = caf.check_json(p)
        assert any("required" in e for e in errors)

    def test_internal_version_mismatch(self, tmp_path):
        data = self._minimal_valid()
        data["definitions"]["audit"]["properties"]["_audit_aif_version"]["const"] = "9.9.9"
        p = self._write_json(tmp_path, data)
        _, errors = caf.check_json(p)
        assert any("mismatch" in e.lower() for e in errors)

    def test_invalid_json_returns_error(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("{not valid json", encoding="utf-8")
        versions, errors = caf.check_json(p)
        assert versions == []
        assert any("invalid JSON" in e for e in errors)

    def test_missing_file_raises(self, tmp_path):
        """check_json propagates FileNotFoundError for a missing file."""
        p = tmp_path / "nonexistent.json"
        with pytest.raises(FileNotFoundError):
            caf.check_json(p)


# ── check_dic ────────────────────────────────────────────────────────────────


class TestCheckDic:
    def _minimal_valid(self) -> str:
        return (
            f"_dictionary.version {PLACEHOLDER}\n"
            f"save_audit.aif_version\n"
            f"  _enumeration.default {PLACEHOLDER}\n"
            f"save_\n"
        )

    def test_valid_dic_no_errors(self, tmp_path):
        p = tmp_path / "test.dic"
        p.write_text(self._minimal_valid(), encoding="utf-8")
        versions, errors = caf.check_dic(p)
        assert errors == []
        assert set(versions) == {PLACEHOLDER}

    def test_missing_dictionary_version(self, tmp_path):
        text = (
            f"save_audit.aif_version\n"
            f"  _enumeration.default {PLACEHOLDER}\n"
            f"save_\n"
        )
        p = tmp_path / "test.dic"
        p.write_text(text, encoding="utf-8")
        _, errors = caf.check_dic(p)
        assert any("_dictionary.version" in e for e in errors)

    def test_missing_save_frame(self, tmp_path):
        text = f"_dictionary.version {PLACEHOLDER}\n"
        p = tmp_path / "test.dic"
        p.write_text(text, encoding="utf-8")
        _, errors = caf.check_dic(p)
        assert any("save_audit.aif_version" in e for e in errors)

    def test_missing_enumeration_default_inside_frame(self, tmp_path):
        text = (
            f"_dictionary.version {PLACEHOLDER}\n"
            f"save_audit.aif_version\n"
            f"  # (intentionally empty frame)\n"
            f"save_\n"
        )
        p = tmp_path / "test.dic"
        p.write_text(text, encoding="utf-8")
        _, errors = caf.check_dic(p)
        assert any("_enumeration.default" in e for e in errors)

    def test_version_mismatch(self, tmp_path):
        text = (
            f"_dictionary.version {PLACEHOLDER}\n"
            f"save_audit.aif_version\n"
            f"  _enumeration.default 9.9.9\n"
            f"save_\n"
        )
        p = tmp_path / "test.dic"
        p.write_text(text, encoding="utf-8")
        _, errors = caf.check_dic(p)
        assert any("mismatch" in e.lower() for e in errors)

    def test_missing_file_returns_error(self, tmp_path):
        p = tmp_path / "nonexistent.dic"
        versions, errors = caf.check_dic(p)
        assert errors != []
        assert versions == []


# ── check_yaml ───────────────────────────────────────────────────────────────


class TestCheckYaml:
    def _minimal_valid(self) -> str:
        return (
            f'version: "{PLACEHOLDER}"\n'
            f"\n"
            f"slots:\n"
            f"  audit_aif_version:\n"
            f"    description: test\n"
            f"    required: true\n"
        )

    def test_valid_yaml_no_errors(self, tmp_path):
        p = tmp_path / "test.yaml"
        p.write_text(self._minimal_valid(), encoding="utf-8")
        versions, errors = caf.check_yaml(p)
        assert errors == []
        assert set(versions) == {PLACEHOLDER}

    def test_missing_version_key(self, tmp_path):
        text = (
            "slots:\n"
            "  audit_aif_version:\n"
            "    required: true\n"
        )
        p = tmp_path / "test.yaml"
        p.write_text(text, encoding="utf-8")
        _, errors = caf.check_yaml(p)
        assert any("version" in e for e in errors)

    def test_audit_aif_version_slot_missing(self, tmp_path):
        text = f'version: "{PLACEHOLDER}"\n'
        p = tmp_path / "test.yaml"
        p.write_text(text, encoding="utf-8")
        _, errors = caf.check_yaml(p)
        assert any("audit_aif_version" in e for e in errors)

    def test_audit_aif_version_not_required(self, tmp_path):
        text = (
            f'version: "{PLACEHOLDER}"\n'
            f"\n"
            f"slots:\n"
            f"  audit_aif_version:\n"
            f"    description: test\n"
            f"    # required omitted\n"
        )
        p = tmp_path / "test.yaml"
        p.write_text(text, encoding="utf-8")
        _, errors = caf.check_yaml(p)
        assert any("required" in e for e in errors)

    def test_missing_file_returns_error(self, tmp_path):
        p = tmp_path / "nonexistent.yaml"
        versions, errors = caf.check_yaml(p)
        assert errors != []
        assert versions == []


# ── check_example_file ───────────────────────────────────────────────────────


class TestCheckExampleFile:
    def test_valid_example_no_errors(self, tmp_path):
        text = f'_audit_aif_version "{PLACEHOLDER}"\n'
        p = tmp_path / "test.aif"
        p.write_text(text, encoding="utf-8")
        versions, errors = caf.check_example_file(p)
        assert errors == []
        assert versions == [PLACEHOLDER]

    def test_quoted_semver_version(self, tmp_path):
        text = '_audit_aif_version "1.2.3"\n'
        p = tmp_path / "test.aif"
        p.write_text(text, encoding="utf-8")
        versions, errors = caf.check_example_file(p)
        assert errors == []
        assert versions == ["1.2.3"]

    def test_missing_version_line(self, tmp_path):
        text = "_adsnt_material_id SomeMaterial\n"
        p = tmp_path / "test.aif"
        p.write_text(text, encoding="utf-8")
        versions, errors = caf.check_example_file(p)
        assert errors != []
        assert versions == []

    def test_missing_file_returns_error(self, tmp_path):
        p = tmp_path / "nonexistent.aif"
        versions, errors = caf.check_example_file(p)
        assert errors != []
        assert versions == []


# ── main() integration ───────────────────────────────────────────────────────


@pytest.mark.integration
def test_main_passes_on_real_repo():
    """``main()`` must exit 0 against the actual repository files."""
    rc = caf.main()
    assert rc == 0, "check_aif_format.main() reported errors on the real repo"


# ── strict release mode ──────────────────────────────────────────────────────


class TestReleaseTag:
    @pytest.mark.parametrize(
        "tag,expected",
        [
            ("v1.2.3", "1.2.3"),
            ("1.2.3", "1.2.3"),
            ("v10.0.1", "10.0.1"),
            ("v1.0.0-beta", "1.0.0-beta"),
            ("v1.0.0-rc.1", "1.0.0-rc.1"),
        ],
    )
    def test_version_from_tag(self, tag, expected):
        assert caf.release_version_from_tag(tag) == expected

    @pytest.mark.parametrize(
        "tag", ["", "v1.2", "v1.2.3.4", "v1.2.3-", "release/1.2.3", "latest"]
    )
    def test_invalid_tag_rejected(self, tag):
        with pytest.raises(ValueError):
            caf.release_version_from_tag(tag)


class TestReleaseMode:
    """Run ``main(--release-tag)`` against a stamped copy of the real artifacts."""

    @pytest.fixture
    def repo(self, tmp_path, monkeypatch):
        real = caf.REPO_ROOT
        # The real tree may hold the placeholder (develop) or a stamped release.
        current = caf.check_json(real / "aif_dictionary.json")[0][0]
        names = ["aif_dictionary.json", "aif_dictionary.dic",
                 "aif_dictionary.yaml", "example.aif"]
        for name in names:
            text = (real / name).read_text(encoding="utf-8")
            (tmp_path / name).write_text(
                text.replace(current, "1.2.3"), encoding="utf-8"
            )
        for src in (real / "examples").rglob("*.aif"):
            dest = tmp_path / src.relative_to(real)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(
                src.read_text(encoding="utf-8").replace(current, "1.2.3"),
                encoding="utf-8",
            )
        monkeypatch.setattr(caf, "REPO_ROOT", tmp_path)
        return tmp_path

    def test_stamped_tree_passes(self, repo, capsys):
        assert caf.main(["--release-tag", "v1.2.3"]) == 0

    def test_bare_tag_without_v_passes(self, repo):
        assert caf.main(["--release-tag", "1.2.3"]) == 0

    def test_tag_mismatch_fails(self, repo, capsys):
        assert caf.main(["--release-tag", "v2.0.0"]) == 1
        assert "does not match release" in capsys.readouterr().err

    def test_invalid_tag_fails(self, repo):
        assert caf.main(["--release-tag", "v1.2"]) == 1

    def test_placeholder_in_example_fails(self, repo, capsys):
        example = next((repo / "examples").rglob("*.aif"))
        example.write_text(
            example.read_text(encoding="utf-8").replace("1.2.3", PLACEHOLDER),
            encoding="utf-8",
        )
        assert caf.main(["--release-tag", "v1.2.3"]) == 1

    def test_placeholder_in_dictionary_url_fails(self, repo):
        """A leftover placeholder in a non-version field (e.g. a URL) is caught."""
        p = repo / "aif_dictionary.yaml"
        p.write_text(
            p.read_text(encoding="utf-8") + f"\n# see /tree/{PLACEHOLDER}/\n",
            encoding="utf-8",
        )
        assert caf.main(["--release-tag", "v1.2.3"]) == 1

    def test_stale_example_fails(self, repo):
        example = next((repo / "examples").rglob("*.aif"))
        example.write_text(
            example.read_text(encoding="utf-8").replace("1.2.3", "1.1.0"),
            encoding="utf-8",
        )
        assert caf.main(["--release-tag", "v1.2.3"]) == 1

    def test_missing_file_fails(self, repo):
        (repo / "aif_dictionary.dic").unlink()
        assert caf.main(["--release-tag", "v1.2.3"]) == 1

    def test_default_mode_still_accepts_placeholder(self, repo):
        """Without --release-tag, a stamped tree is simply consistent."""
        assert caf.main([]) == 0

    def test_prerelease_tree_passes(self, repo):
        for path in [*repo.glob("*.*"), *(repo / "examples").rglob("*.aif")]:
            path.write_text(
                path.read_text(encoding="utf-8").replace("1.2.3", "1.2.3-beta.1"),
                encoding="utf-8",
            )
        assert caf.main(["--release-tag", "v1.2.3-beta.1"]) == 0
        # the final release tag must not accept a beta-stamped tree
        assert caf.main(["--release-tag", "v1.2.3"]) == 1

    def test_expect_placeholder_rejects_stamped_tree(self, repo, capsys):
        assert caf.main(["--expect-placeholder"]) == 1
        assert "development branches must keep" in capsys.readouterr().err

    def test_expect_placeholder_accepts_placeholder_tree(self, repo):
        for path in [*repo.glob("*.*"), *(repo / "examples").rglob("*.aif")]:
            path.write_text(
                path.read_text(encoding="utf-8").replace("1.2.3", PLACEHOLDER),
                encoding="utf-8",
            )
        assert caf.main(["--expect-placeholder"]) == 0

    def test_modes_are_mutually_exclusive(self, repo):
        with pytest.raises(SystemExit):
            caf.main(["--expect-placeholder", "--release-tag", "v1.2.3"])
