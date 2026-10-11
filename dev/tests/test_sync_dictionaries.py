"""Tests for dev/sync_dictionaries.py.

Covers the helper functions (unit tests) and an integration smoke-test that
verifies the committed YAML and DIC are in sync with the JSON schema.
"""

import subprocess
import sys
import re
import pytest

import sync_dictionaries as sd


# ── _detect_prefix ───────────────────────────────────────────────────────────


class TestDetectPrefix:
    def test_single_segment_prefix(self):
        props = {"_exptl_operator": {}, "_exptl_date": {}, "_exptl_method": {}}
        assert sd._detect_prefix(props) == "exptl"

    def test_multi_segment_prefix(self):
        # audit.aif_version — common prefix is just "audit"
        props = {"_audit_aif_version": {}, "_audit_creation_date": {}}
        assert sd._detect_prefix(props) == "audit"

    def test_adsorp_prefix(self):
        props = {"_adsorp_pressure": {}, "_adsorp_loading": {}, "_adsorp_p0": {}}
        assert sd._detect_prefix(props) == "adsorp"

    def test_single_property_returns_first_segment(self):
        props = {"_citation_doi": {}}
        assert sd._detect_prefix(props) == "citation"

    def test_empty_properties_returns_empty_string(self):
        assert sd._detect_prefix({}) == ""


# ── _detect_dic_class ────────────────────────────────────────────────────────


class TestDetectDicClass:
    def test_audit_section_is_head(self):
        assert sd._detect_dic_class("audit", "some comment") == "Head"

    def test_loop_in_comment_is_loop(self):
        assert sd._detect_dic_class("adsorption_data", "Loop data points") == "Loop"
        assert sd._detect_dic_class("adsorption_data", "loop_ block") == "Loop"

    def test_non_loop_non_audit_is_set(self):
        assert sd._detect_dic_class("experimental", "Experiment metadata") == "Set"
        assert sd._detect_dic_class("units", "Unit definitions") == "Set"


# ── _detect_label ────────────────────────────────────────────────────────────


class TestDetectLabel:
    def test_label_from_comment_with_section_prefix(self):
        comment = "Section 2 — Experimental: conditions and methods"
        assert sd._detect_label("experimental", comment) == "Experimental"

    def test_label_from_comment_without_section_prefix(self):
        comment = "Adsorbent: sample and material info"
        assert sd._detect_label("adsorbent", comment) == "Adsorbent"

    def test_label_strips_secondary_part(self):
        comment = "Adsorbent / Sample: info"
        label = sd._detect_label("adsorbent", comment)
        assert "/" not in label

    def test_no_colon_uses_full_comment_text(self):
        # _COMMENT_LABEL_RE always matches; when there is no colon the full
        # comment text is captured as the label.
        comment = "some description without a colon"
        label = sd._detect_label("my_section", comment)
        assert "colon" in label.lower() or label  # non-empty label is returned


# ── _build_required_index / _required_note ───────────────────────────────────


class TestBuildRequiredIndex:
    def test_unconditional_from_required_array(self):
        schema = {"required": ["_audit_aif_version"], "allOf": []}
        idx = sd._build_required_index(schema)
        assert "_audit_aif_version" in idx.unconditional
        assert idx.alt_groups == ()

    def test_singleton_anyof_counts_as_unconditional(self):
        schema = {
            "required": [],
            "allOf": [{"anyOf": [{"required": ["_exptl_temperature"]}]}],
        }
        idx = sd._build_required_index(schema)
        assert "_exptl_temperature" in idx.unconditional
        assert idx.alt_groups == ()

    def test_multi_member_anyof_is_alt_group(self):
        schema = {
            "required": [],
            "allOf": [
                {
                    "anyOf": [
                        {"required": ["_adsorptive_name"]},
                        {"required": ["_adsorptive_component_name"]},
                    ]
                }
            ],
        }
        idx = sd._build_required_index(schema)
        assert idx.unconditional == frozenset()
        assert (
            frozenset({"_adsorptive_name", "_adsorptive_component_name"})
            in idx.alt_groups
        )

    def test_if_then_anyof_clause_is_ignored(self):
        # if/then expresses a value-dependent constraint, not an alternative.
        schema = {
            "required": [],
            "allOf": [
                {
                    "if": {"anyOf": [{"required": ["_simltn_code"]}]},
                    "then": {"properties": {"_exptl_method": {"const": "simulation"}}},
                }
            ],
        }
        idx = sd._build_required_index(schema)
        assert idx.unconditional == frozenset()
        assert idx.alt_groups == ()


class TestRequiredNote:
    def test_unconditional_field_note(self):
        idx = sd.RequiredIndex(unconditional=frozenset({"_audit_aif_version"}), alt_groups=())
        assert sd._required_note("_audit_aif_version", idx) == "Required field."

    def test_alt_group_member_note_names_the_other_member(self):
        idx = sd.RequiredIndex(
            unconditional=frozenset(),
            alt_groups=(frozenset({"_adsorptive_name", "_adsorptive_component_name"}),),
        )
        note = sd._required_note("_adsorptive_name", idx)
        assert note == "Required unless _adsorptive_component_name is provided."

    def test_unrelated_field_returns_none(self):
        idx = sd.RequiredIndex(unconditional=frozenset({"_audit_aif_version"}), alt_groups=())
        assert sd._required_note("_adsnt_info", idx) is None


# ── _slot_name / _ddlm_save_name ─────────────────────────────────────────────


class TestNamingHelpers:
    def test_slot_name_strips_leading_underscore(self):
        assert sd._slot_name("_exptl_operator") == "exptl_operator"

    def test_dic_save_name_formats_correctly(self):
        assert sd._ddlm_save_name("_exptl_operator", "exptl") == ("exptl.operator", "operator")
        assert sd._ddlm_save_name("_audit_aif_version", "audit") == ("audit.aif_version", "aif_version")


class TestYamlDescriptionEscaping:
    def test_generate_yaml_quotes_descriptions_with_special_characters(self):
        schema = {
            "x-linkml-name": "aif",
            "title": "AIF",
            "description": "AIF schema",
            "version": "1.0",
            "$id": "https://example.com/aif_dictionary.json",
            "x-linkml-license": "MIT",
            "x-linkml-prefixes": {},
            "x-linkml-imports": ["linkml:types"],
            "x-linkml-default-range": "string",
            "x-citation": {
                "authors": "Evans, J. D.",
                "journal": "Langmuir 2021, 37, 4222-4226.",
                "doi": "10.1021/acs.langmuir.1c00122",
            },
            "required": [],
            "definitions": {
                "experimental": {
                    "$comment": "Section 1 — Experimental: conditions",
                    "properties": {
                        "_exptl_operator": {
                            "description": "Uses a colon: this should stay valid YAML",
                            "type": "string",
                        }
                    },
                }
            },
        }

        yaml_text = sd.generate_yaml(schema)

        assert 'description: "Uses a colon: this should stay valid YAML"' in yaml_text


# ── deprecated propagation ───────────────────────────────────────────────────


class TestDeprecatedPropagation:
    def test_generate_yaml_marks_deprecated_slots(self):
        schema = sd.load_schema()
        yaml_text = sd.generate_yaml(schema)

        deprecated_slots = []
        for section in schema.get("definitions", {}).values():
            for name, prop in sd._section_properties(section).items():
                if prop.get("deprecated") is True:
                    deprecated_slots.append(name.lstrip("_"))

        if not deprecated_slots:
            assert "deprecated: true" not in yaml_text
            return

        for slot in deprecated_slots:
            start = yaml_text.index(f"  {slot}:")
            end = yaml_text.index("\n\n", start)
            slot_block = yaml_text[start:end]
            assert "deprecated: true" in slot_block

    def test_generate_ddlm_adds_common_deprecation_note(self):
        schema = sd.load_schema()
        ddlm_text = sd.generate_ddlm(schema)

        deprecated_items = []
        for section in schema.get("definitions", {}).values():
            section_props = sd._section_properties(section)
            section_prefix = sd._detect_prefix(section_props)
            for name, prop in section_props.items():
                if prop.get("deprecated") is True:
                    deprecated_items.append((name, section_prefix))

        if not deprecated_items:
            assert "Deprecated." not in ddlm_text
            return

        for name, section_prefix in deprecated_items:
            save_name, _ = sd._ddlm_save_name(name, section_prefix)
            match = re.search(rf"save_{re.escape(save_name)}(.*?)\nsave_\n", ddlm_text, re.DOTALL)
            assert match is not None
            ddlm_block = match.group(1)
            assert "_description.common" in ddlm_block
            assert "Deprecated." in ddlm_block

    def test_generate_yaml_includes_unconditional_allof_requirements(self):
        schema = sd.load_schema()
        yaml_text = sd.generate_yaml(schema)

        temperature_start = yaml_text.index("  exptl_temperature:")
        temperature_end = yaml_text.index("\n\n", temperature_start)
        temperature_block = yaml_text[temperature_start:temperature_end]
        assert "required: true" in temperature_block

        concentration_start = yaml_text.index("  units_concentration:")
        concentration_end = yaml_text.index("\n\n", concentration_start)
        concentration_block = yaml_text[concentration_start:concentration_end]
        assert "required: true" not in concentration_block


# ── integration: --check must pass on the committed files ───────────────────


@pytest.mark.integration
def test_sync_check_passes_on_real_repo():
    """``python dev/sync_dictionaries.py --check`` must exit 0."""
    result = subprocess.run(
        [sys.executable, "dev/sync_dictionaries.py", "--check"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "sync_dictionaries.py --check failed.\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )
