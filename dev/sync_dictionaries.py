"""Generate aif_dictionary.yaml and aif_dictionary.dic from aif_dictionary.json.

The JSON schema is the single source of truth for the AIF data-name
dictionary.  This script reads it and produces:

  - aif_dictionary.yaml  — LinkML schema
  - aif_dictionary.dic   — DDLm CIF dictionary

New sections added to ``definitions`` in the JSON schema are automatically
picked up — no script changes required. Section metadata (DIC class, prefix,
label, category description) is derived from the ``$comment`` and property
names, with optional ``x-*`` overrides on sections or individual properties when
the defaults aren't right. ``x-deprecation-message`` is a supported override key
not currently used by any section in aif_dictionary.json — they remain available
for future sections/deprecations that need custom text.

Usage
-----
Regenerate both derived files::

    python dev/sync_dictionaries.py

Check that the current files match (for CI / pre-commit)::

    python dev/sync_dictionaries.py --check
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import textwrap
from pathlib import Path
from typing import Any, NamedTuple

REPO_ROOT = Path(__file__).resolve().parent.parent
JSON_PATH = REPO_ROOT / "aif_dictionary.json"
YAML_PATH = REPO_ROOT / "aif_dictionary.yaml"
DDLM_PATH = REPO_ROOT / "aif_dictionary.dic"

# ── Type-mapping tables ─────────────────────────────────────────────────────

# (JSON type, JSON format) → LinkML range
_YAML_RANGE: dict[tuple[str, str | None], str] = {
    ("string", None): "string",
    ("number", None): "float",
    ("integer", None): "integer",
    ("string", "date-time"): "datetime",
}

# (JSON type, JSON format) → DDLm _type.contents
_DDLm_TYPE_CONTENTS: dict[tuple[str, str | None], str] = {
    ("string", None): "Text",
    ("number", None): "Real",
    ("integer", None): "Integer",
    ("string", "date-time"): "DateTime",
}

# Default DIC _type.purpose / _type.source by JSON type
_DDLm_TYPE_PURPOSE_DEFAULT = {
    "string": "Describe",
    "number": "Measurand",
    "integer": "Describe",
}
_DDLm_TYPE_SOURCE_DEFAULT = {
    "string": "Recorded",
    "number": "Recorded",
    "integer": "Recorded",
}

# Regex to extract a unit reference from a property description,
# e.g. "(see _units_pressure)" → "see _units_pressure"
_UNITS_RE = re.compile(r"\(see (_units_\w+)\)")

# Regex to extract the label from a $comment:
#   "Section 3 — Adsorbent: ..."   → "Adsorbent"
#   "Adsorbent / Sample: ..."      → "Adsorbent"
_COMMENT_LABEL_RE = re.compile(
    r"(?:Section\s+\d+\s*[—–-]\s*)?([^:]+)"
)


# ── Section metadata discovery ──────────────────────────────────────────────


class SectionMeta(NamedTuple):
    """Derived metadata for one definitions section."""

    dic_id: str
    dic_class: str
    prefix: str
    yaml_label: str
    dic_desc: str
    category_keys: list
    parent_id: str = "AIF_CORE"


def _detect_prefix(properties: dict[str, dict]) -> str:
    """Derive the common CIF prefix shared by all property names.

    CIF convention: ``_<category>_<item>``.  The prefix is the longest
    leading sequence of underscore-delimited segments shared by every
    property, but never the full name of any property (there must always
    be at least one trailing segment left for the item name).

    For ``{'_exptl_operator': …, '_exptl_date': …}`` returns ``'exptl'``.
    For ``{'_audit_aif_version': …, '_audit_creation_date': …}`` returns
    ``'audit'`` because "aif" and "creation" differ at position 1.

    Note: with a *single* property whose name has N segments, the prefix
    extends to segment N-2 (e.g. a lone ``_audit_aif_version`` would yield
    ``'audit_aif'``).  In practice every section has multiple properties,
    so the divergence logic kicks in before that limit is reached.
    """
    names = [k.lstrip("_") for k in properties]
    if not names:
        return ""
    splits = [n.split("_") for n in names]
    prefix_parts: list[str] = []
    # Never consume the last segment of the shortest name — that's the item.
    max_prefix_len = min(len(s) for s in splits) - 1
    for i, parts in enumerate(zip(*splits)):
        if i >= max_prefix_len:
            break
        if len(set(parts)) == 1:
            prefix_parts.append(parts[0])
        else:
            break
    return "_".join(prefix_parts) if prefix_parts else splits[0][0]


def _section_properties(section: dict) -> dict[str, dict]:
    """Return a section's item properties, whether it's a flat object or an
    array (sub-loop) section — for array sections, properties live under
    ``items.properties`` rather than directly on the section.
    """
    if section.get("type") == "array":
        return section.get("items", {}).get("properties", {})
    return section.get("properties", {})


def _detect_dic_class(section_key: str, comment: str) -> str:
    """Derive DIC class from section key and ``$comment``.

    - ``'audit'`` → Head
    - comment mentioning "Loop" → Loop
    - otherwise → Set
    """
    if section_key == "audit":
        return "Head"
    if "loop" in comment.lower():
        return "Loop"
    return "Set"


def _detect_label(section_key: str, comment: str) -> str:
    """Derive a human label for a section.

    Tries to extract from $comment "Section N — Label: …", falling back
    to title-casing the definition key.
    """
    m = _COMMENT_LABEL_RE.search(comment)
    if m:
        raw = m.group(1).strip()
        # Remove secondary parts after " / " (e.g. "Adsorbent / Sample")
        return raw.split("/")[0].strip()
    return section_key.replace("_", " ").title()


def _generate_dic_category_desc(dic_id: str, comment: str) -> str:
    """Build a DIC category description from the ``$comment``.

    Extracts the text after the colon in "Section N — Label: <desc>."
    Falls back to a generic sentence.
    """
    colon_idx = comment.find(":")
    if colon_idx != -1:
        desc_text = comment[colon_idx + 1 :].strip().rstrip(".")
        return (
            f"Data items in the {dic_id} category record {desc_text[0].lower()}"
            f"{desc_text[1:]}."
        )
    return f"Data items in the {dic_id} category."


def _build_section_meta(section_key: str, section: dict) -> SectionMeta:
    """Build metadata for one definitions section.

    Respects ``x-schema-star-*`` overrides, falling back to auto-detection.
    ``x-schema-star-definition-class`` drives both DIC ``_definition.class``
    and YAML Loop/DataPoint-class detection.
    ``x-schema-star-category-key`` names the DDLm key item(s) for Loop categories.
    ``x-schema-star-parent-id`` overrides the default AIF_CORE parent category.
    """
    comment = section.get("$comment", "")
    properties = _section_properties(section)

    # x-schema-star-definition-id stores the bare DDLm category prefix; strip
    # any accidental leading underscore so _ddlm_save_name arithmetic stays correct.
    raw_id = section.get("x-schema-star-definition-id")
    prefix = raw_id.lstrip("_") if raw_id is not None else _detect_prefix(properties)
    dic_id = raw_id.lstrip("_") if raw_id is not None else prefix.upper()
    dic_class = section.get(
        "x-schema-star-definition-class", _detect_dic_class(section_key, comment)
    )
    label = section.get("x-linkml-label", _detect_label(section_key, comment))
    dic_desc = _generate_dic_category_desc(dic_id, comment)
    category_key = section.get("x-schema-star-category-key")
    category_keys = (
        [category_key] if isinstance(category_key, str) else list(category_key or [])
    )
    parent_id = section.get("x-schema-star-parent-id", "AIF_CORE")

    return SectionMeta(
        dic_id=dic_id,
        dic_class=dic_class,
        prefix=prefix,
        yaml_label=label,
        dic_desc=dic_desc,
        category_keys=category_keys,
        parent_id=parent_id,
    )


# ── Required-field detection ────────────────────────────────────────────────


class RequiredIndex(NamedTuple):
    """Fields required unconditionally vs. groups of mutually-alternative ones."""

    unconditional: frozenset[str]
    alt_groups: tuple[frozenset[str], ...]
    item_required: frozenset[str] = frozenset()


def _build_required_index(schema: dict) -> RequiredIndex:
    """Derive required-field info from the schema's ``required`` and ``allOf``.

    Reads the top-level ``required`` array plus any bare ``anyOf`` clause in
    the top-level ``allOf`` (skipping ``if``/``then`` conditionals, which
    express value-dependent requirements rather than alternatives). A
    single-member ``anyOf`` group has no real alternative and is treated as
    unconditional; a multi-member group means each member is required only
    if none of the others are present.

    Also collects ``item_required``: fields marked ``required`` inside an
    array (sub-loop) section's ``items`` — mandatory in every row of that
    sub-loop, but not unconditionally required for the file as a whole.
    """
    unconditional: set[str] = set(schema.get("required", []))
    alt_groups: list[frozenset[str]] = []

    for clause in schema.get("allOf", []):
        if "if" in clause or "anyOf" not in clause:
            continue
        members = {
            name for alt in clause["anyOf"] for name in alt.get("required", [])
        }
        if len(members) <= 1:
            unconditional.update(members)
        else:
            alt_groups.append(frozenset(members))

    item_required: set[str] = set()
    for section in schema.get("definitions", {}).values():
        if section.get("type") == "array":
            item_required.update(section.get("items", {}).get("required", []))

    return RequiredIndex(
        unconditional=frozenset(unconditional),
        alt_groups=tuple(alt_groups),
        item_required=frozenset(item_required),
    )


def _required_note(pname: str, req_index: RequiredIndex) -> str | None:
    """DIC ``_description.common`` note describing whether *pname* is required."""
    if pname in req_index.unconditional:
        return "Required field."
    for group in req_index.alt_groups:
        if pname in group:
            others = " or ".join(sorted(group - {pname}))
            return f"Required unless {others} is provided."
    if pname in req_index.item_required:
        return "Required field within each row of this loop."
    return None


# ── Per-property helpers ────────────────────────────────────────────────────


def _prop_units(prop: dict) -> str | None:
    """Return the DIC ``_units.code`` for a property, or *None*.

    Checks ``x-dic-units`` first, then auto-extracts from description.
    """
    if "x-dic-units" in prop:
        return prop["x-dic-units"]
    m = _UNITS_RE.search(prop.get("description", ""))
    if m:
        return f"see {m.group(1)}"
    return None


def _prop_purpose(prop: dict) -> str:
    """DIC ``_type.purpose`` — from ``x-schema-star-type-purpose`` or type default."""
    if "x-schema-star-type-purpose" in prop:
        return prop["x-schema-star-type-purpose"]
    return _DDLm_TYPE_PURPOSE_DEFAULT.get(prop.get("type", "string"), "Describe")


def _prop_source(prop: dict) -> str:
    """DIC ``_type.source`` — from ``x-schema-star-type-source`` or type default."""
    if "x-schema-star-type-source" in prop:
        return prop["x-schema-star-type-source"]
    return _DDLm_TYPE_SOURCE_DEFAULT.get(prop.get("type", "string"), "Recorded")

def _prop_container(prop: dict) -> str:
    """DIC ``_type.container`` — from ``x-schema-star-type-container`` or default."""
    if "x-schema-star-type-container" in prop:
        return prop["x-schema-star-type-container"]
    return "Single"

def _prop_is_deprecated(prop: dict) -> bool:
    """Whether the JSON schema marks this property as deprecated."""
    return bool(prop.get("deprecated", False))


def _prop_dic_deprecation_common(prop: dict) -> str | None:
    """Optional DIC ``_description.common`` text for deprecated properties."""
    if not _prop_is_deprecated(prop):
        return None
    note = prop.get("x-deprecation-message")
    if note:
        return f"Deprecated: {note}"
    return (
        "Deprecated. This data name may be removed in a future "
        "version of the AIF schema."
    )


# ── Formatting helpers ──────────────────────────────────────────────────────

def _pascal_case(snake_case: str) -> str:
    """Convert snake_case to PascalCase."""
    return "".join(part.title() for part in snake_case.split("_"))

def _slot_name(cif_name: str) -> str:
    """``'_exptl_operator'`` → ``'exptl_operator'``."""
    return cif_name.lstrip("_")


def _ddlm_save_name(cif_name: str, cat_prefix: str) -> tuple[str, str]:
    """``'_exptl_operator'`` → ``'exptl.operator'``."""
    bare = cif_name.lstrip("_")
    rest = bare[len(cat_prefix) + 1 :]
    return f"{cat_prefix}.{rest}", rest


def _yaml_range(name, prop: dict) -> str | None:
    """LinkML range, or *None* when the default (``string``) applies."""
    if "enum" in prop:
        return _pascal_case(name)
    rng = _YAML_RANGE.get(
        (prop.get("type", "string"), prop.get("format")),
        "string",
    )
    return rng if rng != "string" else None


def _ddlm_contents(prop: dict) -> str:
    return _DDLm_TYPE_CONTENTS.get(
        (prop.get("type", "string"), prop.get("format")),
        "Text",
    )


def _ddlm_kv(key: str, value: str, col: int = 33) -> str:
    """DIC key-value line with values aligned at column *col*."""
    left = f"    {key}"
    pad = max(1, col - len(left))
    return f"{left}{' ' * pad}{value}"


def _ddlm_text_block(key: str, text: str, *, preserve_blank_lines: bool = False) -> list[str]:
    """Semicolon-delimited DDLm/CIF text block for *key*."""
    if "\n" in text:
        indented = "\n".join(
            (f"    {ln}" if ln else "") if preserve_blank_lines else f"    {ln}"
            for ln in text.split("\n")
        )
    else:
        indented = textwrap.fill(
            text, width=68, initial_indent="    ", subsequent_indent="    "
        )
    return [f"    {key}", ";", indented, ";"]


def _ddlm_description(text: str) -> str:
    """Format a ``_description.text`` entry for a DIC save frame."""
    if len(text) <= 60 and "'" not in text and "\n" not in text:
        return _ddlm_kv("_description.text", f"'{text}'")
    return "\n".join(_ddlm_text_block("_description.text", text))


def _ddlm_banner(title: str) -> str:
    """Centered DIC section banner (78 chars wide)."""
    border = "#" * 78
    inner = f"#{' ' * 76}#"
    centered = title.center(76)
    title_line = f"#{centered}#"
    return f"\n{border}\n{inner}\n{title_line}\n{inner}\n{border}\n"


def _yaml_section_sep(name: str, indent: int = 2) -> str:
    prefix = f"{' ' * indent}# ── {name} "
    return prefix + "─" * max(1, 48 - len(prefix))


def _yaml_header(name: str) -> str:
    sep = "# " + "─" * 46
    return f"{sep}\n#  {name}\n{sep}"


def _yaml_scalar(value: Any) -> str:
    """Return a YAML-safe scalar string for a description-like field."""
    if value is None:
        return '""'

    text = str(value)
    if not text:
        return '""'

    if re.search(r"[\n\r\t\"':#{}\[\],&*?!|>@%`\\]", text):
        escaped = text.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{escaped}"'

    return text


def _format_common(text: str) -> list[str]:
    """Format a ``_description.common`` CIF block and return lines."""
    # Blank paragraph separators must stay truly empty, not "    ".
    return _ddlm_text_block("_description.common", text, preserve_blank_lines=True)


def _loop_class_name(section_key: str) -> str:
    """``'adsorption_data'`` → ``'AdsorptionDataPoint'``; ``'adsorptive_component'`` → ``'AdsorptiveComponent'``."""
    if section_key.endswith("_data"):
        base = section_key.replace("_data", "").title()
        return f"{base}DataPoint"
    return "".join(part.title() for part in section_key.split("_"))


def _loop_class_description(section_key: str, yaml_label: str) -> list[str]:
    if section_key.endswith("_data"):
        direction = section_key.replace("_data", "")
        return [
            f"      A single data point in the {direction} branch of an isotherm.",
            f"      Corresponds to a row in an AIF loop_ block for {direction}.",
        ]
    return [
        f"      A single row of the {yaml_label} sub-loop.",
        "      Corresponds to a row in an AIF loop_ block.",
    ]


def _loop_attribute_description(section_key: str, yaml_label: str) -> str:
    if section_key.endswith("_data"):
        direction = section_key.replace("_data", "")
        return f"{direction.title()} branch data points (loop_ block)."
    return f"{yaml_label} sub-loop rows (loop_ block)."


def _build_item_common_notes(
    pname: str, prop: dict, req_index: RequiredIndex
) -> str | None:
    """Compose the _description.common text for a DIC item save frame."""
    parts: list[str] = []
    note = _required_note(pname, req_index)
    if note:
        parts.append(note)
    dep = _prop_dic_deprecation_common(prop)
    if dep:
        parts.append(dep)
    return "\n\n".join(parts) if parts else None


def load_schema() -> dict:
    with open(JSON_PATH, encoding="utf-8") as fh:
        return json.load(fh)


# ── YAML generator ──────────────────────────────────────────────────────────


def _yaml_preamble(schema: dict) -> list[str]:
    lines: list[str] = []
    lines.append(f"id: {schema['$id'].replace('.json', '.yaml')}")
    lines.append(f"name: {schema['x-linkml-name']}")
    lines.append(f"title: {schema['title']}")
    lines.append("description: >-")
    citation = schema["x-citation"]
    first_author = citation["authors"].split(";")[0].split(",")[0].strip()
    desc_ref = (
        schema["description"]
        + f" Reference: {first_author} et al., {citation['journal']}"
    )
    for wl in textwrap.wrap(desc_ref, width=70):
        lines.append(f"  {wl}")
    lines.append(f'version: "{schema["version"]}"')
    lines.append(f"license: {schema['x-linkml-license']}")
    lines.append("")
    lines.append("prefixes:")
    for pfx, uri in schema["x-linkml-prefixes"].items():
        lines.append(f"  {pfx}: {uri}")
    lines.append("")
    lines.append("imports:")
    for imp in schema.get("x-linkml-imports", ["linkml:types"]):
        lines.append(f"  - {imp}")
    lines.append("")
    lines.append(f"default_range: {schema.get('x-linkml-default-range', 'string')}")
    lines.append("")
    return lines


def _yaml_enums(definitions: dict, section_keys: list[str]) -> list[str]:
    enums: dict[str, dict] = {}
    for sk in section_keys:
        for pname, prop in _section_properties(definitions[sk]).items():
            if "enum" not in prop:
                continue
            ename = _pascal_case(pname)
            enums[ename] = {
                "description": prop.get(
                    "x-enum-description", f"Enumeration for {pname}."
                ),
                "values": {
                    v: prop.get("x-enum-descriptions", {}).get(v, "")
                    for v in prop.get("enum", [])
                },
            }
    if not enums:
        return []
    lines: list[str] = []
    lines.append(_yaml_header("Enumerations"))
    lines.append("")
    lines.append("enums:")
    lines.append("")
    for ename, edata in enums.items():
        lines.append(f"  {ename}:")
        lines.append(f"    description: {_yaml_scalar(edata['description'])}")
        lines.append("    permissible_values:")
        for val, vdesc in edata["values"].items():
            lines.append(f"      {val}:")
            lines.append(f"        description: {_yaml_scalar(vdesc)}")
    lines.append("")
    return lines


def _yaml_slots(
    definitions: dict,
    section_keys: list[str],
    section_metas: dict[str, SectionMeta],
    required_set: frozenset[str],
) -> list[str]:
    lines: list[str] = []
    lines.append(_yaml_header("Slots (data items / fields)"))
    lines.append("")
    lines.append("slots:")
    lines.append("")
    for sk in section_keys:
        meta = section_metas[sk]
        lines.append(_yaml_section_sep(meta.yaml_label))
        lines.append("")
        for pname, prop in _section_properties(definitions[sk]).items():
            slot = _slot_name(pname)
            desc = prop.get("description", "")
            rng = _yaml_range(pname, prop)
            lines.append(f"  {slot}:")
            lines.append(f'    aliases: ["{pname}"]')
            lines.append(f"    description: {_yaml_scalar(desc)}")
            if pname in required_set:
                lines.append("    required: true")
            if rng:
                lines.append(f"    range: {rng}")
            if _prop_is_deprecated(prop):
                lines.append("    deprecated: true")
            lines.append("")
    return lines


def _yaml_classes(
    definitions: dict,
    section_keys: list[str],
    section_metas: dict[str, SectionMeta],
) -> list[str]:
    lines: list[str] = []
    lines.append(_yaml_header("Classes"))
    lines.append("")
    lines.append("classes:")
    lines.append("")

    loop_sections: dict[str, list[str]] = {}
    for sk in section_keys:
        if section_metas[sk].dic_class == "Loop":
            loop_sections[sk] = list(_section_properties(definitions[sk]).keys())

    for lsk, prop_names in loop_sections.items():
        cls_name = _loop_class_name(lsk)
        lines.append(f"  {cls_name}:")
        lines.append("    description: >-")
        lines.extend(_loop_class_description(lsk, section_metas[lsk].yaml_label))
        lines.append("    slots:")
        for pn in prop_names:
            lines.append(f"      - {_slot_name(pn)}")
        lines.append("")

    lines.append("  AdsorptionInformationFile:")
    lines.append("    description: >-")
    lines.append(
        "      Root class representing a complete AIF data block. Contains"
    )
    lines.append(
        "      metadata about the experiment or simulation, units, citation"
    )
    lines.append(
        "      information, and the adsorption/desorption data points."
    )
    lines.append("    tree_root: true")
    lines.append("    slots:")
    for sk in section_keys:
        meta = section_metas[sk]
        if meta.dic_class == "Loop":
            continue
        lines.append(f"      # {meta.yaml_label}")
        for pn in _section_properties(definitions[sk]).keys():
            lines.append(f"      - {_slot_name(pn)}")

    if loop_sections:
        lines.append("    attributes:")
        for lsk in loop_sections:
            cls_name = _loop_class_name(lsk)
            lines.append(f"      {lsk}:")
            lines.append(
                f"        description: {_yaml_scalar(_loop_attribute_description(lsk, section_metas[lsk].yaml_label))}"
            )
            lines.append(f"        range: {cls_name}")
            lines.append("        multivalued: true")
            lines.append("        inlined_as_list: true")

    lines.append("")
    return lines


def generate_yaml(schema: dict) -> str:
    definitions = schema.get("definitions", {})
    section_keys = list(definitions.keys())
    section_metas = {
        sk: _build_section_meta(sk, definitions[sk]) for sk in section_keys
    }
    required_set = _build_required_index(schema).unconditional
    return "\n".join([
        *_yaml_preamble(schema),
        *_yaml_enums(definitions, section_keys),
        *_yaml_slots(definitions, section_keys, section_metas, required_set),
        *_yaml_classes(definitions, section_keys, section_metas),
    ])


# ── DIC generator ───────────────────────────────────────────────────────────


def _ddlm_header(schema: dict) -> list[str]:
    citation = schema["x-citation"]
    ddlm_date = schema.get("x-schema-date", "2026-01-01")
    version = schema.get("version", "__AIF_VERSION__")
    lines: list[str] = []
    lines.append(r"#\#CIF_2.0")
    lines.append(_ddlm_banner(f"{schema['title'].upper()} DDLm DICTIONARY"))
    lines.append("data_AIF_DIC")
    lines.append("")
    lines.append(_ddlm_kv("_dictionary.title", "AIF_DIC"))
    lines.append(_ddlm_kv("_dictionary.class", "Instance"))
    lines.append(_ddlm_kv("_dictionary.version", version))
    lines.append(_ddlm_kv("_dictionary.date", ddlm_date))
    lines.append("    _dictionary.uri")
    lines.append(f"        {schema['$id'].replace('.json', '.dic')}")
    lines.append("    _dictionary.guide")
    lines.append(f"        {schema['x-schema-guide']}")
    lines.append(_ddlm_kv("_dictionary.ddl_conformance", schema["x-schema-star-ddl-compliance"]))
    lines.append(_ddlm_kv("_dictionary.namespace", "AIFCore"))
    lines.append("    _description.text")
    lines.append(";")
    lines.append(f"    {schema['title']}: {schema['description']}")
    lines.append("")
    lines.append("    Reference:")
    lines.append(f"    {citation['authors']}")
    lines.append(f"    {citation['journal']}")
    lines.append(f"    DOI: {citation['doi']}")
    lines.append(";")
    return lines


def _ddlm_parent_category(ddlm_date: str) -> list[str]:
    lines: list[str] = []
    lines.append("")
    lines.append("save_AIF_CORE")
    lines.append(_ddlm_kv("_definition.id", "AIF_CORE"))
    lines.append(_ddlm_kv("_definition.scope", "Category"))
    lines.append(_ddlm_kv("_definition.class", "Head"))
    lines.append(_ddlm_kv("_definition.update", ddlm_date))
    lines.append(_ddlm_description("Parent category for all AIF data items."))
    lines.append(_ddlm_kv("_name.category_id", "AIF_CORE"))
    lines.append(_ddlm_kv("_name.object_id", "AIF_CORE"))
    lines.append("save_")
    return lines


def _ddlm_category_block(sk: str, meta: SectionMeta, ddlm_date: str) -> list[str]:
    ddlm_definition_id = meta.dic_id.upper()
    lines: list[str] = []
    lines.append(_ddlm_banner(f"{sk.upper()} CATEGORY"))
    lines.append(f"save_{ddlm_definition_id}")
    lines.append(_ddlm_kv("_definition.id", ddlm_definition_id))
    lines.append(_ddlm_kv("_definition.scope", "Category"))
    lines.append(_ddlm_kv("_definition.class", meta.dic_class))
    lines.append(_ddlm_kv("_definition.update", ddlm_date))
    if meta.dic_desc:
        lines.append(_ddlm_description(meta.dic_desc))
    lines.append(_ddlm_kv("_name.category_id", meta.parent_id))
    lines.append(_ddlm_kv("_name.object_id", ddlm_definition_id))
    if meta.dic_class == "Loop":
        if not meta.category_keys:
            raise ValueError(
                f"Loop section '{sk}' has no x-schema-star-category-key"
                " — required by DDLm."
            )
        lines.append(_ddlm_kv("_category.key_id", meta.category_keys[0]))
    lines.append("save_")
    return lines


def _ddlm_item_block(
    pname: str,
    prop: dict,
    cat_prefix: str,
    ddlm_definition_id: str,
    ddlm_date: str,
    req_index: RequiredIndex,
) -> list[str]:
    save_name, rest_name = _ddlm_save_name(pname, cat_prefix)
    lines: list[str] = []
    lines.append("")
    lines.append(f"save_{save_name}")
    lines.append(_ddlm_kv("_definition.id", f"'{save_name}'"))
    lines.append(_ddlm_kv("_definition.scope", "Item"))
    lines.append(_ddlm_kv("_definition.class", "Datum"))
    lines.append(_ddlm_kv("_definition.update", ddlm_date))
    lines.append(_ddlm_description(prop.get("description", "")))
    lines.append(_ddlm_kv("_name.category_id", ddlm_definition_id))
    lines.append(_ddlm_kv("_name.object_id", rest_name))
    lines.append(_ddlm_kv("_type.purpose", _prop_purpose(prop)))
    lines.append(_ddlm_kv("_type.source", _prop_source(prop)))
    lines.append(_ddlm_kv("_type.container", _prop_container(prop)))
    lines.append(_ddlm_kv("_type.contents", _ddlm_contents(prop)))
    units = _prop_units(prop)
    if units:
        lines.append(_ddlm_kv("_units.code", f"'{units}'"))
    if "enum" in prop and "x-enum-descriptions" in prop:
        lines.append("    loop_")
        lines.append("        _enumeration_set.state")
        lines.append("        _enumeration_set.detail")
        for val in prop["enum"]:
            val_desc = prop["x-enum-descriptions"].get(val, "")
            lines.append(f"        {val:<17s}'{val_desc}'")
    if "const" in prop:
        lines.append(_ddlm_kv("_enumeration.default", prop["const"]))
    common = _build_item_common_notes(pname, prop, req_index)
    if common:
        lines.extend(_format_common(common))
    lines.append("save_")
    return lines


def generate_ddlm(schema: dict) -> str:
    definitions = schema.get("definitions", {})
    ddlm_date = schema.get("x-schema-date", "2026-01-01")
    section_keys = list(definitions.keys())
    section_metas = {
        sk: _build_section_meta(sk, definitions[sk]) for sk in section_keys
    }
    req_index = _build_required_index(schema)

    lines: list[str] = [
        *_ddlm_header(schema),
        *_ddlm_parent_category(ddlm_date),
    ]

    for sk in section_keys:
        meta = section_metas[sk]
        lines.extend(_ddlm_category_block(sk, meta, ddlm_date))
        for pname, prop in _section_properties(definitions[sk]).items():
            lines.extend(
                _ddlm_item_block(
                    pname, prop, meta.prefix, meta.dic_id.upper(), ddlm_date, req_index
                )
            )

    pattern_props = schema.get("patternProperties", {})
    unc_prop = pattern_props.get(".*_uncertainty$")
    if unc_prop:
        unc_comment = unc_prop.get("$comment", "")
        lines.append(_ddlm_banner("UNCERTAINTY (PATTERN PROPERTY)"))
        lines.append("save_UNCERTAINTY")
        lines.append(_ddlm_kv("_definition.id", "UNCERTAINTY"))
        lines.append(_ddlm_kv("_definition.scope", "Category"))
        lines.append(_ddlm_kv("_definition.class", "Set"))
        lines.append(_ddlm_kv("_definition.update", ddlm_date))
        if unc_comment:
            lines.append(_ddlm_description(unc_comment))
        lines.append("save_")

    lines.append("")
    return "\n".join(lines)


# ── Main ────────────────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Synchronize YAML and DIC dictionaries from the JSON schema.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Dry-run: exit 1 if files would change (for CI).",
    )
    args = parser.parse_args()

    schema = load_schema()
    yaml_content = generate_yaml(schema)
    dic_content = generate_ddlm(schema)

    if args.check:
        ok = True
        for path, content in [(YAML_PATH, yaml_content), (DDLM_PATH, dic_content)]:
            if not path.exists():
                print(f"MISSING: {path.name}", file=sys.stderr)
                ok = False
                continue
            existing = path.read_text(encoding="utf-8")
            if existing != content:
                print(f"OUT OF SYNC: {path.name}", file=sys.stderr)
                ok = False
            else:
                print(f"OK: {path.name}")
        return 0 if ok else 1

    for path, content in [(YAML_PATH, yaml_content), (DDLM_PATH, dic_content)]:
        path.write_text(content, encoding="utf-8")
        print(f"  Wrote {path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
