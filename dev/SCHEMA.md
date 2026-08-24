# AIF custom JSON Schema keywords

The AIF schema is stored in `aif_dictionary.json` and is used as the source of truth for generating both the LinkML schema and the DDLm/DIC dictionary. To make that conversion explicit and stable, the project adds a small set of custom JSON Schema extension keys under the `x-` namespace.

These keywords are not part of the base JSON Schema standard, but they carry metadata that the dictionary-generation script consumes when producing `aif_dictionary.yaml` and `aif_dictionary.dic`.

## Purpose of the extension keys

The extension keys fall into a few groups:

- schema metadata and provenance
- LinkML generation hints
- DDLm/DIC category metadata
- per-property semantic metadata
- enum metadata

The generator logic is implemented in `dev/sync_dictionaries.py`, and the keys intentionally mirror the information that the generated YAML/DIC files need.


## Notes on convention and usage

These keys are intentionally namespaced as `x-*` to avoid colliding with standard JSON Schema keywords while still keeping them machine-readable.
This makes the JSON Schema both valid as a general JSON document and expressive enough to drive schema generation for the AIF ecosystem.

---

## Summary table

| Keyword | Scope | Goal | Default |
| --- | --- | --- | --- |
| `x-citation` | root | publication metadata | none |
| `x-schema-guide` | root | reference for this schema guide | none |
| `x-schema-date` | root | revision date | `2026-01-01` |
| `x-schema-star-ddl-compliance` | root | DDL specification compatibility | none |
| `x-schema-star-definition-id` | section | category identifier | auto-derived prefix |
| `x-schema-star-definition-class` | section | DIC/STAR class | `Head`/`Loop`/`Set` based on key/comment |
| `x-schema-star-category-key` | section | loop key field(s) | none |
| `x-schema-star-type-purpose` | property | DIC `_type.purpose` | `Describe`/`Measurand` by type |
| `x-schema-star-type-source` | property | DIC `_type.source` | `Recorded` or `Assigned` by context |
| `x-schema-star-type-container` | property | DIC `_type.container` | `Single` |
| `x-linkml-name` | root | LinkML schema name | none |
| `x-linkml-license` | root | schema license | none |
| `x-linkml-prefixes` | root | namespace mapping | none |
| `x-linkml-imports` | root | LinkML imports | `['linkml:types']` |
| `x-linkml-default-range` | root | default property type | `string` |
| `x-enum-name` | enum | explicit enum name | none |
| `x-enum-description` | enum | enum description | none |
| `x-enum-descriptions` | enum | enum value descriptions | none |
| `x-deprecation-message` | property | deprecation note | none |

---

## Top-level schema metadata

These appear at the root of the schema object.

### `x-citation`

Type: object

Purpose: metadata for the publication or dataset associated with the schema.

Typical contents:

- `authors`
- `journal`
- `doi`

Default: none. This is informational only and is copied into the generated dictionary metadata.

### `x-schema-guide`

Type: string

Purpose: URL pointing to the human-readable schema reference document.

Default: none.

### `x-schema-date`

Type: string

Purpose: date of the schema revision or documentation snapshot.

Default in generator logic: `2026-01-01` when no explicit date is provided.

### `x-schema-star-ddl-compliance`

Type: string

Purpose: records the DDL compliance level or STAR format compatibility version.

Default: none.

### `x-linkml-name`

Type: string

Purpose: schema name used in the generated LinkML file.

Default: none. In the AIF schema it is set to `aif`.

### `x-linkml-license`

Type: string

Purpose: the license for the schema.

Default: none. Usually set to `MIT`.

### `x-linkml-prefixes`

Type: object

Purpose: namespace prefix map used by LinkML, for example mapping the local `aif` prefix or standard ontology prefixes such as `linkml`, `schema`, and `qudt`.

Default: none.

### `x-linkml-imports`

Type: array of strings

Purpose: list of imports to include in the generated LinkML schema.

Default: `['linkml:types']`.

### `x-linkml-default-range`

Type: string

Purpose: fallback LinkML range for properties that do not define a more specific type.

Default: `string`.

---

## Section-level metadata

These keys live on a section object inside `definitions`.

### `x-schema-star-definition-id`

Type: string

Purpose: canonical STAR/DIC category identifier for the section.

Example: `audit`, `exptl`, `adsnt`, `_units`.

Default: derived automatically from the common prefix shared by the properties in the section, or otherwise inferred from the section key.

This is important because the generator uses it to name the DIC category and to configure the exported YAML/DDL identifiers.

### `x-schema-star-definition-class`

Type: string

Purpose: tells the generator what class of STAR/DIC definition a section is.

Valid/used values in AIF include:

- `Set`
- `Loop`
- `Head`

Default: auto-detected from section content:

- if the section key is `audit`, default to `Head`
- if `$comment` mentions `loop`, default to `Loop`
- otherwise default to `Set`

### `x-schema-star-category-key`

Type: string or array of strings

Purpose: identifies the key field or fields that define a loop row in a STAR `Loop` section.

Default: none. When absent, no category key is emitted for that section.

This is used by the generator to set the DIC `_category_key.name` information for loop-like sections such as adsorption or desorption data.

### `x-deprecation-message`

Type: string

Purpose: custom deprecation note for a property.

Default: none. If present, it is used in generated deprecation notes.

---

## Per-property metadata

These keys appear on individual properties.

### `x-schema-star-type-purpose`

Type: string

Purpose: sets the DIC `_type.purpose` value for a property.

Default: inferred from the JSON type:

- `string` → `Describe`
- `number` → `Measurand`
- `integer` → `Describe`

This is used to classify whether a field is descriptive metadata or a measured quantity.

### `x-schema-star-type-source`

Type: string

Purpose: sets the DIC `_type.source` value for a property.

Default: inferred from the JSON type:

- `string` → `Recorded`
- `number` → `Recorded`
- `integer` → `Recorded`

The AIF schema often sets this explicitly to `Assigned` for identifiers or labels that are not measured directly.

---

## Enum metadata

These help generate readable enum definitions and descriptions in the derived schema.

### `x-enum-name`

Type: string

Purpose: explicit enum class name to generate in the derived schema.

Default: none; the generator falls back to a reasonable name if needed.

### `x-enum-description`

Type: string

Purpose: description for the enum as a whole.

Default: none.

### `x-enum-descriptions`

Type: object

Purpose: map from allowed value names to human-readable descriptions.

Default: none.

This is used for enum domains such as experimental methods or digitization methods so the generated schema can carry clear documentation for each option.

---

