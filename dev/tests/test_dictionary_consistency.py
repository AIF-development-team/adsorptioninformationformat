"""Tests that verify all three dictionary formats (JSON, DIC, YAML) are
internally consistent with one another and with the JSON schema's field list.
"""

import json
import re
from pathlib import Path

import pytest

import sync_dictionaries as sd

REPO_ROOT = Path(__file__).parent.parent.parent
PLACEHOLDER = "__AIF_VERSION__"
SEMVER_RE = re.compile(r"^v?\d+\.\d+\.\d+$")


# ── Helpers ──────────────────────────────────────────────────────────────────


def _json_all_fields(schema: dict) -> set[str]:
    """Return the full set of CIF field names defined in the JSON schema."""
    fields: set[str] = set()
    for section in schema.get("definitions", {}).values():
        fields.update(section.get("properties", {}).keys())
    return fields


def _json_required_fields(schema: dict) -> set[str]:
    """Return the set of fields marked as required in the top-level ``required`` array."""
    return set(schema.get("required", []))


def _yaml_defined_aliases(yaml_text: str) -> set[str]:
    """Extract all aliases declared in the YAML (quoted strings starting with _)."""
    return set(re.findall(r'"(_\w+)"', yaml_text))


def _dic_save_frames(dic_text: str) -> set[str]:
    """Return a set of CIF names reconstructed from ``save_<cat>.<item>`` blocks."""
    names: set[str] = set()
    for m in re.finditer(r"save_(\w+)\.(\w+)", dic_text):
        names.add(f"_{m.group(1)}_{m.group(2)}")
    return names


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def json_schema():
    path = REPO_ROOT / "aif_dictionary.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def dic_text():
    return (REPO_ROOT / "aif_dictionary.dic").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def yaml_text():
    return (REPO_ROOT / "aif_dictionary.yaml").read_text(encoding="utf-8")


# ── Existence checks ─────────────────────────────────────────────────────────


def test_all_three_dictionary_files_exist():
    for name in ("aif_dictionary.json", "aif_dictionary.dic", "aif_dictionary.yaml"):
        assert (REPO_ROOT / name).exists(), f"{name} is missing from the repo root"


# ── Version extraction helpers ────────────────────────────────────────────────


def _version_from_json(schema: dict) -> str:
    return schema.get("version", "")


def _version_from_dic(text: str) -> str:
    m = re.search(r"_dictionary\.version\s+(\S+)", text)
    return m.group(1) if m else ""


def _version_from_yaml(text: str) -> str:
    m = re.search(r'^version:\s*["\']?([^"\'#\n]+)["\']?', text, re.MULTILINE)
    return m.group(1).strip() if m else ""


# ── Cross-format version consistency ─────────────────────────────────────────


def test_json_version_is_present(json_schema):
    assert json_schema.get("version"), "aif_dictionary.json is missing a 'version' key"


def test_dic_version_is_present(dic_text):
    assert _version_from_dic(dic_text), "aif_dictionary.dic is missing _dictionary.version"


def test_yaml_version_is_present(yaml_text):
    assert _version_from_yaml(yaml_text), "aif_dictionary.yaml is missing a 'version' key"


def test_all_three_versions_are_identical(json_schema, dic_text, yaml_text):
    v_json = _version_from_json(json_schema)
    v_dic = _version_from_dic(dic_text)
    v_yaml = _version_from_yaml(yaml_text)
    assert v_json == v_dic == v_yaml, (
        f"Version mismatch across dictionaries: "
        f"JSON={v_json!r}, DIC={v_dic!r}, YAML={v_yaml!r}"
    )


def test_version_is_placeholder_or_semver(json_schema):
    v = _version_from_json(json_schema)
    valid = v == PLACEHOLDER or bool(SEMVER_RE.match(v))
    assert valid, f"Version '{v}' is neither the placeholder nor valid semver"


# ── Field presence in derived formats ────────────────────────────────────────


def test_json_fields_have_aliases_in_yaml(json_schema, yaml_text):
    """Every CIF field in the JSON schema must appear as an alias in the YAML."""
    json_fields = _json_all_fields(json_schema)
    yaml_aliases = _yaml_defined_aliases(yaml_text)
    missing = json_fields - yaml_aliases
    assert not missing, (
        f"{len(missing)} JSON field(s) have no alias in aif_dictionary.yaml:\n"
        + "\n".join(f"  {f}" for f in sorted(missing))
    )


def test_json_fields_have_save_frames_in_dic(json_schema, dic_text):
    """Every CIF field in the JSON schema must have a save_ frame in the DIC."""
    json_fields = _json_all_fields(json_schema)
    dic_names = _dic_save_frames(dic_text)
    missing = json_fields - dic_names
    assert not missing, (
        f"{len(missing)} JSON field(s) have no save frame in aif_dictionary.dic:\n"
        + "\n".join(f"  {f}" for f in sorted(missing))
    )


# ── Required field consistency ────────────────────────────────────────────────


def test_audit_aif_version_is_required_in_json(json_schema):
    required = _json_required_fields(json_schema)
    assert "_audit_aif_version" in required, (
        "_audit_aif_version must be listed in the JSON schema's top-level 'required' array"
    )


def test_audit_aif_version_is_required_in_yaml(yaml_text):
    """The audit_aif_version slot must be marked ``required: true`` in the YAML."""
    slot_block = re.search(
        r"audit_aif_version:\s*\n((?:[ \t]+\S.*\n)*)", yaml_text
    )
    assert slot_block, "Could not find audit_aif_version slot in aif_dictionary.yaml"
    assert "required: true" in slot_block.group(1), (
        "audit_aif_version slot is not marked 'required: true' in aif_dictionary.yaml"
    )


def test_adsnt_material_name_is_required_in_json(json_schema):
    required = _json_required_fields(json_schema)
    assert "_adsnt_material_name" in required or any(
        "_adsnt_material_name" in sec.get("required", [])
        for sec in json_schema.get("definitions", {}).values()
    ), "_adsnt_material_name should be required in aif_dictionary.json"


def test_adsnt_sample_name_exists_in_json(json_schema):
    all_fields = _json_all_fields(json_schema)
    assert "_adsnt_sample_name" in all_fields, (
        "_adsnt_sample_name should be present in aif_dictionary.json"
    )


# ── Enum consistency ──────────────────────────────────────────────────────────


def test_exptl_method_enum_consistent_across_formats(json_schema, yaml_text, dic_text):
    """The ExperimentalMethod enum values must appear in all three formats."""
    expected_values = {"volumetric", "gravimetric", "chromatographic", "simulation", "other"}

    # JSON
    method_prop = (
        json_schema.get("definitions", {})
        .get("experimental", {})
        .get("properties", {})
        .get("_exptl_method", {})
    )
    json_enum = set(method_prop.get("enum", []))
    assert json_enum == expected_values, (
        f"JSON _exptl_method enum mismatch: {json_enum}"
    )

    # YAML – look for the ExperimentalMethod enum block
    for val in expected_values:
        assert re.search(rf"^\s+{val}:", yaml_text, re.MULTILINE), (
            f"Value '{val}' not found in ExperimentalMethod enum in aif_dictionary.yaml"
        )

    # DIC – each value should appear as an _enumeration.set entry
    for val in expected_values:
        assert val in dic_text, (
            f"Value '{val}' not found in aif_dictionary.dic"
        )


# ── Required-field note consistency (DIC) ─────────────────────────────────────


def _dic_item_block(dic_text: str, save_name: str) -> str:
    """Return the body of a ``save_<save_name>`` item frame in the DIC text."""
    match = re.search(rf"save_{re.escape(save_name)}(.*?)\nsave_\n", dic_text, re.DOTALL)
    assert match is not None, f"No save_{save_name} block found in aif_dictionary.dic"
    return match.group(1)


def _all_pname_save_names(json_schema: dict) -> dict[str, str]:
    """Map every JSON field name to its DIC ``save_<category>.<item>`` name."""
    save_names: dict[str, str] = {}
    for sk, sec in json_schema.get("definitions", {}).items():
        meta = sd._build_section_meta(sk, sec)
        for pname in sec.get("properties", {}):
            save_names[pname] = sd._dic_save_name(pname, meta["prefix"])
    return save_names


def test_unconditionally_required_fields_have_required_note_in_dic(json_schema, dic_text):
    """Every field required via the top-level 'required' array or a singleton
    'anyOf' must carry a 'Required field.' note in its DIC common text."""
    req_index = sd._build_required_index(json_schema)
    save_names = _all_pname_save_names(json_schema)
    for pname in sorted(req_index.unconditional):
        block = _dic_item_block(dic_text, save_names[pname])
        assert "Required field." in block, (
            f"{pname} is unconditionally required but its DIC entry has no "
            "'Required field.' note"
        )


def test_alt_group_fields_have_required_unless_note_in_dic(json_schema, dic_text):
    """Fields in a multi-member top-level 'anyOf' group must carry an accurate
    'Required unless <other member> is provided.' note, not an unconditional one."""
    req_index = sd._build_required_index(json_schema)
    save_names = _all_pname_save_names(json_schema)
    for group in req_index.alt_groups:
        for pname in group:
            block = _dic_item_block(dic_text, save_names[pname])
            others = " or ".join(sorted(group - {pname}))
            expected = f"Required unless {others} is provided."
            assert expected in block, (
                f"{pname} is part of alternative-required group {sorted(group)} "
                f"but its DIC entry is missing: {expected!r}"
            )


def test_no_unrelated_field_claims_required_field_in_dic(json_schema, dic_text):
    """Guards against a field's x-dic-common text claiming 'Required field.'
    when the JSON schema does not actually require it unconditionally."""
    req_index = sd._build_required_index(json_schema)
    alt_members = {p for group in req_index.alt_groups for p in group}
    save_names = _all_pname_save_names(json_schema)
    for pname, save_name in save_names.items():
        if pname in req_index.unconditional or pname in alt_members:
            continue
        block = _dic_item_block(dic_text, save_name)
        assert "Required field." not in block, (
            f"{pname} is not required by the JSON schema but its DIC entry "
            "claims 'Required field.'"
        )
