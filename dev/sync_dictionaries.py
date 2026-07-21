"""Generate aif_dictionary.yaml and aif_dictionary.dic from aif_dictionary.json.

The JSON schema is the single source of truth for the AIF data-name
dictionary.  This script reads it and produces:

  - aif_dictionary.yaml  — LinkML schema
  - aif_dictionary.dic   — DDLm CIF dictionary

New sections added to ``definitions`` in the JSON schema are automatically
picked up — no script changes required.  Section metadata (DIC class,
prefix, label, category description) is derived from the ``$comment`` and
property names, with optional ``x-*`` overrides on sections or individual
properties when the defaults aren't right.

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

REPO_ROOT = Path(__file__).resolve().parent.parent
JSON_PATH = REPO_ROOT / "aif_dictionary.json"
YAML_PATH = REPO_ROOT / "aif_dictionary.yaml"
DIC_PATH = REPO_ROOT / "aif_dictionary.dic"

# ── Type-mapping tables ─────────────────────────────────────────────────────

# (JSON type, JSON format) → LinkML range
_YAML_RANGE: dict[tuple[str, str | None], str] = {
    ("string", None): "string",
    ("number", None): "float",
    ("integer", None): "integer",
    ("string", "date-time"): "datetime",
}

# (JSON type, JSON format) → DDLm _type.contents
_DIC_CONTENTS: dict[tuple[str, str | None], str] = {
    ("string", None): "Text",
    ("number", None): "Real",
    ("integer", None): "Integer",
    ("string", "date-time"): "DateTime",
}

# Default DIC _type.purpose / _type.source by JSON type
_DIC_PURPOSE_DEFAULT = {"string": "Describe", "number": "Measurand", "integer": "Describe"}
_DIC_SOURCE_DEFAULT = {"string": "Recorded", "number": "Recorded", "integer": "Recorded"}

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


def _detect_prefix(properties: dict[str, dict]) -> str:
    """Derive the common CIF prefix shared by all property names.

    CIF convention: ``_<category>_<item>``.  The prefix is the longest
    leading sequence of underscore-delimited segments shared by every
    property, but never the full name of any property (there must always
    be at least one trailing segment left for the item name).

    For ``{'_exptl_operator': …, '_exptl_date': …}`` returns ``'exptl'``.
    For ``{'_audit_aif_version': …}`` returns ``'audit'`` (not the full name).
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


def _build_section_meta(
    section_key: str, section: dict
) -> dict[str, str]:
    """Build the metadata dict for one definitions section.

    Respects ``x-dic-id``, ``x-dic-class``, ``x-dic-prefix``,
    ``x-label``, and ``x-dic-description`` overrides on the section
    object, falling back to auto-detection.
    """
    comment = section.get("$comment", "")
    properties = section.get("properties", {})

    prefix = section.get("x-dic-prefix", _detect_prefix(properties))
    dic_id = section.get("x-dic-id", prefix.upper())
    dic_class = section.get("x-dic-class", _detect_dic_class(section_key, comment))
    label = section.get("x-label", _detect_label(section_key, comment))
    dic_desc = section.get(
        "x-dic-description",
        _generate_dic_category_desc(dic_id, comment),
    )

    return {
        "dic_id": dic_id,
        "dic_class": dic_class,
        "prefix": prefix,
        "yaml_label": label,
        "dic_desc": dic_desc,
    }


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
    """DIC ``_type.purpose`` — from ``x-dic-purpose`` or type default."""
    if "x-dic-purpose" in prop:
        return prop["x-dic-purpose"]
    return _DIC_PURPOSE_DEFAULT.get(prop.get("type", "string"), "Describe")


def _prop_source(prop: dict) -> str:
    """DIC ``_type.source`` — from ``x-dic-source`` or type default."""
    if "x-dic-source" in prop:
        return prop["x-dic-source"]
    return _DIC_SOURCE_DEFAULT.get(prop.get("type", "string"), "Recorded")


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


def _slot_name(cif_name: str) -> str:
    """``'_exptl_operator'`` → ``'exptl_operator'``."""
    return cif_name.lstrip("_")


def _dic_save_name(cif_name: str, cat_prefix: str) -> str:
    """``'_exptl_operator'`` → ``'exptl.operator'``."""
    bare = cif_name.lstrip("_")
    rest = bare[len(cat_prefix) + 1 :]
    return f"{cat_prefix}.{rest}"


def _yaml_range(prop: dict) -> str | None:
    """LinkML range, or *None* when the default (``string``) applies."""
    if "x-enum-name" in prop:
        return prop["x-enum-name"]
    rng = _YAML_RANGE.get(
        (prop.get("type", "string"), prop.get("format")),
        "string",
    )
    return rng if rng != "string" else None


def _dic_contents(prop: dict) -> str:
    return _DIC_CONTENTS.get(
        (prop.get("type", "string"), prop.get("format")),
        "Text",
    )


def _dic_kv(key: str, value: str, col: int = 33) -> str:
    """DIC key-value line with values aligned at column *col*."""
    left = f"    {key}"
    pad = max(1, col - len(left))
    return f"{left}{' ' * pad}{value}"


def _dic_description(text: str) -> str:
    """Format a ``_description.text`` entry for a DIC save frame."""
    if len(text) <= 60 and "'" not in text and "\n" not in text:
        return _dic_kv("_description.text", f"'{text}'")
    if "\n" in text:
        indented = "\n".join(f"    {ln}" for ln in text.split("\n"))
    else:
        indented = textwrap.fill(
            text, width=68, initial_indent="    ", subsequent_indent="    "
        )
    return f"    _description.text\n;\n{indented}\n;"


def _dic_banner(title: str) -> str:
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


def _format_common(text: str) -> list[str]:
    """Format a ``_description.common`` CIF block and return lines."""
    if "\n" in text:
        indented = "\n".join(f"    {ln}" for ln in text.split("\n"))
    else:
        indented = textwrap.fill(
            text, width=68, initial_indent="    ", subsequent_indent="    "
        )
    return ["    _description.common", ";", indented, ";"]


def _datapoint_class_name(section_key: str) -> str:
    """``'adsorption_data'`` → ``'AdsorptionDataPoint'``."""
    base = section_key.replace("_data", "").title()
    return f"{base}DataPoint"


def _datapoint_description(section_key: str) -> list[str]:
    direction = section_key.replace("_data", "")
    return [
        f"      A single data point in the {direction} branch of an isotherm.",
        f"      Corresponds to a row in an AIF loop_ block for {direction}.",
    ]


# ── Load ────────────────────────────────────────────────────────────────────


def load_schema() -> dict:
    with open(JSON_PATH, encoding="utf-8") as fh:
        return json.load(fh)


# ── YAML generator ──────────────────────────────────────────────────────────


def generate_yaml(schema: dict) -> str:
    lines: list[str] = []
    definitions = schema.get("definitions", {})
    required_set = set(schema.get("required", []))

    # Build section metadata for every definition
    section_keys = list(definitions.keys())
    section_metas = {
        sk: _build_section_meta(sk, definitions[sk]) for sk in section_keys
    }

    # ── Preamble ─────────────────────────────────────────────────
    lines.append(f"id: {schema['x-linkml-id']}")
    lines.append(f"name: {schema['x-linkml-name']}")
    lines.append(f"title: {schema['title']}")
    lines.append("description: >-")
    desc_ref = (
        schema["description"]
        + " Reference: Evans et al., Langmuir 2021, 37, 4222-4226."
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
    lines.append(
        f"default_range: {schema.get('x-linkml-default-range', 'string')}"
    )
    lines.append("")

    # ── Collect enum definitions ─────────────────────────────────
    enums: dict[str, dict] = {}
    for sk in section_keys:
        for pname, prop in definitions[sk].get("properties", {}).items():
            if "x-enum-name" not in prop:
                continue
            ename = prop["x-enum-name"]
            enums[ename] = {
                "description": prop.get(
                    "x-enum-description", f"Enumeration for {pname}."
                ),
                "values": {
                    v: prop.get("x-enum-descriptions", {}).get(v, "")
                    for v in prop.get("enum", [])
                },
            }

    if enums:
        lines.append(_yaml_header("Enumerations"))
        lines.append("")
        lines.append("enums:")
        lines.append("")
        for ename, edata in enums.items():
            lines.append(f"  {ename}:")
            lines.append(f"    description: {edata['description']}")
            lines.append("    permissible_values:")
            for val, vdesc in edata["values"].items():
                lines.append(f"      {val}:")
                lines.append(f"        description: {vdesc}")
        lines.append("")

    # ── Slots ────────────────────────────────────────────────────
    lines.append(_yaml_header("Slots (data items / fields)"))
    lines.append("")
    lines.append("slots:")
    lines.append("")

    for sk in section_keys:
        sec = definitions[sk]
        meta = section_metas[sk]
        lines.append(_yaml_section_sep(meta["yaml_label"]))
        lines.append("")
        for pname, prop in sec.get("properties", {}).items():
            slot = _slot_name(pname)
            desc = prop.get("description", "")
            rng = _yaml_range(prop)
            lines.append(f"  {slot}:")
            lines.append(f'    aliases: ["{pname}"]')
            lines.append(f"    description: {desc}")
            if pname in required_set:
                lines.append("    required: true")
            if rng:
                lines.append(f"    range: {rng}")
            if _prop_is_deprecated(prop):
                lines.append("    deprecated: true")
            lines.append("")

    # ── Classes ──────────────────────────────────────────────────
    lines.append(_yaml_header("Classes"))
    lines.append("")
    lines.append("classes:")
    lines.append("")

    # Collect loop sections → DataPoint classes
    loop_sections: dict[str, list[str]] = {}
    for sk in section_keys:
        if section_metas[sk]["dic_class"] == "Loop":
            loop_sections[sk] = list(
                definitions[sk].get("properties", {}).keys()
            )

    for lsk, prop_names in loop_sections.items():
        cls_name = _datapoint_class_name(lsk)
        lines.append(f"  {cls_name}:")
        lines.append("    description: >-")
        lines.extend(_datapoint_description(lsk))
        lines.append("    slots:")
        for pn in prop_names:
            lines.append(f"      - {_slot_name(pn)}")
        lines.append("")

    # Root class
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
        if meta["dic_class"] == "Loop":
            continue
        sec = definitions[sk]
        lines.append(f"      # {meta['yaml_label']}")
        for pn in sec.get("properties", {}).keys():
            lines.append(f"      - {_slot_name(pn)}")

    # Loop attributes
    if loop_sections:
        lines.append("    attributes:")
        for lsk in loop_sections:
            attr_name = lsk  # e.g. "adsorption_data"
            cls_name = _datapoint_class_name(lsk)
            direction = lsk.replace("_data", "")
            lines.append(f"      {attr_name}:")
            lines.append(
                f"        description: {direction.title()} branch data points (loop_ block)."
            )
            lines.append(f"        range: {cls_name}")
            lines.append("        multivalued: true")
            lines.append("        inlined_as_list: true")

    lines.append("")
    return "\n".join(lines)


# ── DIC generator ───────────────────────────────────────────────────────────


def generate_dic(schema: dict) -> str:
    lines: list[str] = []
    definitions = schema.get("definitions", {})
    version = schema.get("version", "__AIF_VERSION__")
    dic_date = schema.get("x-dic-date", "2026-01-01")

    section_keys = list(definitions.keys())
    section_metas = {
        sk: _build_section_meta(sk, definitions[sk]) for sk in section_keys
    }

    # ── Header ───────────────────────────────────────────────────
    lines.append(r"#\#CIF_2.0")
    lines.append(
        _dic_banner("ADSORPTION INFORMATION FORMAT (AIF) DDLm DICTIONARY")
    )
    lines.append("data_AIF_DIC")
    lines.append("")
    lines.append(_dic_kv("_dictionary.title", "AIF_DIC"))
    lines.append(_dic_kv("_dictionary.class", "Instance"))
    lines.append(_dic_kv("_dictionary.version", version))
    lines.append(_dic_kv("_dictionary.date", dic_date))
    lines.append("    _dictionary.uri")
    lines.append(
        "        https://github.com/AIF-development-team/"
        "adsorptioninformationformat"
    )
    lines.append(_dic_kv("_dictionary.ddl_conformance", "4.2.0"))
    lines.append(_dic_kv("_dictionary.namespace", "AifDic"))
    lines.append("    _description.text")
    lines.append(";")
    lines.append(
        "    Dictionary for STAR format adsorption experiment and simulation data"
    )
    lines.append(
        "    files, known as the Adsorption Information Format (AIF)."
    )
    lines.append("")
    lines.append("    Reference:")
    lines.append("    Evans, J. D.; Bon, V.; Senkovska, I.; Kaskel, S.")
    lines.append("    Langmuir 2021, 37, 4222-4226.")
    lines.append("    DOI: 10.1021/acs.langmuir.1c00122")
    lines.append(";")

    # ── Sections ─────────────────────────────────────────────────
    for sk in section_keys:
        sec = definitions[sk]
        meta = section_metas[sk]
        dic_id = meta["dic_id"]
        dic_class = meta["dic_class"]
        cat_prefix = meta["prefix"]
        cat_desc = meta["dic_desc"]

        # Category banner
        lines.append(_dic_banner(f"{dic_id} CATEGORY"))

        # Category save block
        lines.append(f"save_{dic_id}")
        lines.append(_dic_kv("_definition.id", dic_id))
        lines.append(_dic_kv("_definition.scope", "Category"))
        lines.append(_dic_kv("_definition.class", dic_class))
        lines.append(_dic_kv("_definition.update", dic_date))
        if cat_desc:
            lines.append(_dic_description(cat_desc))
        lines.append("save_")

        # Item save blocks
        for pname, prop in sec.get("properties", {}).items():
            save_name = _dic_save_name(pname, cat_prefix)
            desc = prop.get("description", "")
            purpose = _prop_purpose(prop)
            source = _prop_source(prop)
            contents = _dic_contents(prop)
            units = _prop_units(prop)

            lines.append("")
            lines.append(f"save_{save_name}")
            lines.append(_dic_kv("_definition.id", f"'{pname}'"))
            lines.append(_dic_kv("_definition.scope", "Item"))
            lines.append(_dic_kv("_definition.class", "Datum"))
            lines.append(_dic_kv("_definition.update", dic_date))
            lines.append(_dic_description(desc))
            lines.append(_dic_kv("_type.purpose", purpose))
            lines.append(_dic_kv("_type.source", source))
            lines.append(_dic_kv("_type.container", "Single"))
            lines.append(_dic_kv("_type.contents", contents))

            # Optional units reference
            if units:
                lines.append(_dic_kv("_units.code", f"'{units}'"))

            # Enum values
            if "enum" in prop and "x-enum-descriptions" in prop:
                lines.append("    loop_")
                lines.append("        _enumeration_set.state")
                lines.append("        _enumeration_set.detail")
                for val in prop["enum"]:
                    val_desc = prop["x-enum-descriptions"].get(val, "")
                    lines.append(f"        {val:<17s}'{val_desc}'")

            # Enumeration default (for const values, e.g. _audit_aif_version)
            if "const" in prop:
                lines.append(
                    _dic_kv("_enumeration.default", prop["const"])
                )

            # Common description (from x-dic-common on the property)
            common_parts: list[str] = []
            common_text = prop.get("x-dic-common")
            if common_text:
                common_parts.append(common_text)

            deprecation_common = _prop_dic_deprecation_common(prop)
            if deprecation_common:
                common_parts.append(deprecation_common)

            if common_parts:
                lines.extend(_format_common("\n\n".join(common_parts)))

            lines.append("save_")

    # ── Uncertainty category ─────────────────────────────────────
    pattern_props = schema.get("patternProperties", {})
    unc_prop = pattern_props.get(".*_uncertainty$")
    if unc_prop:
        unc_comment = unc_prop.get("$comment", "")
        lines.append(_dic_banner("UNCERTAINTY (PATTERN PROPERTY)"))
        lines.append("save_UNCERTAINTY")
        lines.append(_dic_kv("_definition.id", "UNCERTAINTY"))
        lines.append(_dic_kv("_definition.scope", "Category"))
        lines.append(_dic_kv("_definition.class", "Set"))
        lines.append(_dic_kv("_definition.update", dic_date))
        if unc_comment:
            lines.append(_dic_description(unc_comment))
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
    dic_content = generate_dic(schema)

    if args.check:
        ok = True
        for path, content in [(YAML_PATH, yaml_content), (DIC_PATH, dic_content)]:
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

    for path, content in [(YAML_PATH, yaml_content), (DIC_PATH, dic_content)]:
        path.write_text(content, encoding="utf-8")
        print(f"  Wrote {path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
