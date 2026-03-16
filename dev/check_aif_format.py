"""Check version consistency across all AIF dictionary formats.

Validates that:
- All version locations within each file agree
- All three files (JSON, DIC, LinkML YAML) carry the same version
- The version is either the __AIF_VERSION__ placeholder or valid semver
- Required fields are present in each format
"""

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
PLACEHOLDER = "__AIF_VERSION__"
# Accept optional leading 'v' in version strings (e.g. 'v1.2.3').
SEMVER_RE = re.compile(r"^v?\d+\.\d+\.\d+$")

# ── Helpers ──────────────────────────────────────────────────────────────────

def _fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)


def _is_valid_version(v: str) -> bool:
    # Versions may be the placeholder or a semver string, optionally
    # prefixed with 'v'.
    return v == PLACEHOLDER or bool(SEMVER_RE.match(v))


# ── JSON schema checks ──────────────────────────────────────────────────────

def check_json(path: Path) -> tuple[list[str], list[str]]:
    """Return (versions_found, errors)."""
    errors: list[str] = []
    versions: list[str] = []

    try:
        with open(path, encoding="utf-8") as f:
            schema = json.load(f)
    except json.JSONDecodeError as exc:
        return [], [f"{path.name}: invalid JSON – {exc}"]

    # Top-level "version"
    top_version = schema.get("version")
    if top_version is None:
        errors.append(f'{path.name}: missing top-level "version" key')
    else:
        versions.append(top_version)

    # $id – extract the version segment from the URL
    id_url = schema.get("$id", "")
    id_match = re.search(r"/tree/([^/]+)/", id_url)
    if id_match:
        versions.append(id_match.group(1))
    else:
        errors.append(f'{path.name}: could not extract version from "$id"')

    # _audit_aif_version.const (nested inside definitions.audit)
    const_version = (
        schema.get("definitions", {})
        .get("audit", {})
        .get("properties", {})
        .get("_audit_aif_version", {})
        .get("const")
    )
    if const_version is None:
        errors.append(
            f'{path.name}: missing "const" in _audit_aif_version property'
        )
    else:
        versions.append(const_version)

    # _audit_aif_version must be required
    required = schema.get("required", [])
    if "_audit_aif_version" not in required:
        errors.append(
            f'{path.name}: "_audit_aif_version" is not in the "required" array'
        )

    # Internal consistency
    if versions and len(set(versions)) != 1:
        errors.append(
            f"{path.name}: version mismatch within file – "
            f"found {versions}"
        )

    return versions, errors


# ── DDLm DIC checks ─────────────────────────────────────────────────────────

def check_dic(path: Path) -> tuple[list[str], list[str]]:
    """Return (versions_found, errors)."""
    errors: list[str] = []
    versions: list[str] = []

    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return [], [f"{path.name}: file not found"]

    # _dictionary.version
    m = re.search(r"_dictionary\.version\s+(\S+)", text)
    if m:
        versions.append(m.group(1))
    else:
        errors.append(f"{path.name}: missing _dictionary.version")

    # _enumeration.default inside the audit.aif_version save frame
    # We look for the save_audit.aif_version block and extract _enumeration.default
    block = re.search(
        r"save_audit\.aif_version(.*?)save_",
        text,
        re.DOTALL,
    )
    if block:
        em = re.search(r"_enumeration\.default\s+(\S+)", block.group(1))
        if em:
            versions.append(em.group(1))
        else:
            errors.append(
                f"{path.name}: missing _enumeration.default in "
                "audit.aif_version save frame"
            )
    else:
        errors.append(
            f"{path.name}: could not locate save_audit.aif_version block"
        )

    # Internal consistency
    if versions and len(set(versions)) != 1:
        errors.append(
            f"{path.name}: version mismatch within file – "
            f"found {versions}"
        )

    return versions, errors


# ── LinkML YAML checks ──────────────────────────────────────────────────────

def check_yaml(path: Path) -> tuple[list[str], list[str]]:
    """Return (versions_found, errors).

    Uses regex instead of a YAML library to avoid extra dependencies.
    """
    errors: list[str] = []
    versions: list[str] = []

    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return [], [f"{path.name}: file not found"]

    # Top-level version (unquoted or quoted)
    m = re.search(r'^version:\s*["\']?([^"\'#\n]+)["\']?', text, re.MULTILINE)
    if m:
        versions.append(m.group(1).strip())
    else:
        errors.append(f"{path.name}: missing top-level version key")

    # audit_aif_version slot must be required
    slot_block = re.search(
        r"audit_aif_version:\s*\n((?:[ \t]+\S.*\n)*)", text
    )
    if slot_block:
        if "required: true" not in slot_block.group(1):
            errors.append(
                f"{path.name}: audit_aif_version slot is not marked required"
            )
    else:
        errors.append(
            f"{path.name}: could not locate audit_aif_version slot"
        )

    return versions, errors


# ── Main ─────────────────────────────────────────────────────────────────────


# ── Example files checks ────────────────────────────────────────────────────

def check_example_file(path: Path) -> tuple[list[str], list[str]]:
    """Return (versions_found, errors) for an example AIF file.

    We look for a line beginning with `_audit_aif_version` and capture the
    quoted value. Example files should either contain the placeholder or a
    valid semver version number; they all must agree with one another and with
    the dictionary files.
    """
    errors: list[str] = []
    versions: list[str] = []

    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return [], [f"{path.name}: file not found"]

    m = re.search(r"_audit_aif_version\s+[\"']([^\"']+)[\"']", text)
    if m:
        versions.append(m.group(1))
    else:
        errors.append(f"{path.name}: missing _audit_aif_version line")

    return versions, errors


def main() -> int:
    json_path = REPO_ROOT / "aif_dictionary.json"
    dic_path = REPO_ROOT / "aif_dictionary.dic"
    yaml_path = REPO_ROOT / "aif_dictionary.yaml"
    aif_path = REPO_ROOT / "example.aif"

    all_errors: list[str] = []
    all_versions: list[str] = []

    for checker, path in [
        (check_json, json_path),
        (check_dic, dic_path),
        (check_yaml, yaml_path),
        (check_example_file, aif_path),
    ]:
        if not path.exists():
            all_errors.append(f"{path.name}: file not found")
            continue
        versions, errors = checker(path)
        all_errors.extend(errors)
        all_versions.extend(versions)

    # include example files
    examples_dir = REPO_ROOT / "examples"
    if examples_dir.exists():
        for path in examples_dir.rglob("*.aif"):
            versions, errors = check_example_file(path)
            all_errors.extend(errors)
            all_versions.extend(versions)

    # Cross-file consistency
    unique = set(all_versions)
    if len(unique) > 1:
        all_errors.append(
            f"Cross-file version mismatch: {sorted(unique)}"
        )

    # Format validation
    for v in unique:
        if not _is_valid_version(v):
            all_errors.append(
                f'Invalid version format: "{v}" '
                f"(expected semver X.Y.Z or {PLACEHOLDER})"
            )

    # Report
    if all_errors:
        for e in all_errors:
            _fail(e)
        return 1

    version_str = next(iter(unique)) if unique else "(no versions found)"
    print(f"All version checks passed: {version_str}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
