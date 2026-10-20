"""Parametrized tests that validate every .aif example file in the repo.

Each test is parametrized over all .aif files found under:
  - examples/           (recursive)
  - example.aif         (repo root)

Tests are deliberately kept at the file level so a single bad file
produces a clearly labelled failure without masking the others.
"""

import json
import re
from pathlib import Path

import pytest

# ── Helpers ──────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).parent.parent.parent
PLACEHOLDER = "__AIF_VERSION__"
SEMVER_RE = re.compile(r"^v?\d+\.\d+\.\d+(?:-[0-9A-Za-z.]+)?$")

VALID_ISOTHERM_TYPE = {"absolute", "excess", "net"}


def _all_aif_files() -> list[Path]:
    files: list[Path] = []
    root_example = REPO_ROOT / "example.aif"
    if root_example.exists():
        files.append(root_example)
    examples_dir = REPO_ROOT / "examples"
    if examples_dir.exists():
        files.extend(sorted(examples_dir.rglob("*.aif")))
    return files


def _idfn(path: Path) -> str:
    """Short ID for parametrize display."""
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return path.name


def _parse_loops(text: str) -> list[tuple[list[str], list[list[str]]]]:
    """Return a list of (headers, data_rows) for every loop_ block.

    Headers are lines starting with ``_``.
    Data rows are the non-header, non-empty lines that follow.

    Parsing stops when another STAR directive/data name starts, so scalar
    items after a loop are not misinterpreted as loop rows.
    """
    loops = []
    blocks = re.split(r"\bloop_\b", text, flags=re.IGNORECASE)
    for block in blocks[1:]:  # skip content before first loop_
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
                if ln.startswith("_"):
                    break
                if ln.startswith("loop_") or ln.startswith("data_") or ln.startswith("save_"):
                    break
                data_lines.append(ln)
        data_rows = []
        for dl in data_lines:
            data_rows.append(dl.split())
        loops.append((headers, data_rows))
    return loops


# ── Parametrized fixtures ─────────────────────────────────────────────────────

ALL_AIF_FILES = _all_aif_files()


@pytest.fixture(
    params=ALL_AIF_FILES,
    ids=[_idfn(p) for p in ALL_AIF_FILES],
    scope="module",
)
def aif_text(request) -> tuple[Path, str]:
    path: Path = request.param
    return path, path.read_text(encoding="utf-8")


# ── Per-file tests ────────────────────────────────────────────────────────────


def test_has_audit_aif_version(aif_text):
    """Every AIF file must declare _audit_aif_version."""
    path, text = aif_text
    assert re.search(r"_audit_aif_version", text), (
        f"{path.name}: missing _audit_aif_version"
    )


def test_audit_aif_version_is_valid(aif_text):
    """_audit_aif_version must be the placeholder or a valid semver."""
    path, text = aif_text
    m = re.search(r"_audit_aif_version\s+[\"']?([^\"'\s]+)[\"']?", text)
    assert m, f"{path.name}: could not parse _audit_aif_version value"
    version = m.group(1)
    valid = version == PLACEHOLDER or bool(SEMVER_RE.match(version))
    assert valid, f"{path.name}: invalid _audit_aif_version value '{version}'"


def test_exptl_isotherm_type_enum_valid(aif_text):
    """If _exptl_isotherm_type is present its value must be in the allowed enum."""
    path, text = aif_text
    m = re.search(r"_exptl_isotherm_type\s+[\"']?(\w+)[\"']?", text)
    if m is None:
        pytest.skip("_exptl_isotherm_type not present")
    value = m.group(1).strip('"\'')
    assert value in VALID_ISOTHERM_TYPE, (
        f"{path.name}: _exptl_isotherm_type '{value}' is not a valid enum value "
        f"(allowed: {sorted(VALID_ISOTHERM_TYPE)})"
    )


def test_loop_blocks_have_consistent_column_counts(aif_text):
    """Every loop_ data row must contain exactly as many tokens as declared headers."""
    path, text = aif_text
    loops = _parse_loops(text)
    assert loops, f"{path.name}: no loop_ blocks found"
    for idx, (headers, data_rows) in enumerate(loops, start=1):
        n_headers = len(headers)
        for row_idx, row in enumerate(data_rows, start=1):
            assert len(row) == n_headers, (
                f"{path.name}: loop #{idx}, row {row_idx} has {len(row)} tokens "
                f"but {n_headers} headers are declared"
            )


def test_numeric_loop_columns_contain_numbers(aif_text):
    """Columns declared as _adsorp_pressure/_loading etc. must be numeric."""
    path, text = aif_text
    numeric_prefixes = (
        "_adsorp_pressure", "_adsorp_loading", "_adsorp_p0", "_adsorp_index",
        "_desorp_pressure", "_desorp_loading", "_desorp_p0", "_desorp_index",
        "_exptl_temperature",
    )
    loops = _parse_loops(text)
    for headers, data_rows in loops:
        for col_idx, header in enumerate(headers):
            if not any(header.startswith(p) for p in numeric_prefixes):
                continue
            for row_idx, row in enumerate(data_rows, start=1):
                if col_idx >= len(row):
                    continue  # column-count mismatch caught elsewhere
                val = row[col_idx]
                try:
                    float(val)
                except ValueError:
                    pytest.fail(
                        f"{path.name}: column '{header}' row {row_idx} "
                        f"value '{val}' is not numeric"
                    )


def test_has_adsorp_or_desorp_loop(aif_text):
    """AIF files should contain at least one adsorption or desorption data loop."""
    path, text = aif_text
    has_data = bool(
        re.search(r"_adsorp_pressure|_adsorp_loading|_desorp_pressure|_desorp_loading", text)
    )
    assert has_data, (
        f"{path.name}: no adsorption or desorption data columns found"
    )


# ── Schema-driven checks ─────────────────────────────────────────────────────

_SCHEMA = json.loads((REPO_ROOT / "aif_dictionary.json").read_text(encoding="utf-8"))


def _loop_key_index() -> dict[str, list[str]]:
    """Map every field of a Loop section to that section's category key(s)."""
    index: dict[str, list[str]] = {}
    for sec in _SCHEMA["definitions"].values():
        keys = sec.get("x-schema-star-category-key")
        if sec.get("x-schema-star-definition-class") != "Loop" or not keys:
            continue
        keys = [keys] if isinstance(keys, str) else list(keys)
        for pname in sec.get("properties", {}):
            index[pname] = keys
    return index


LOOP_KEYS = _loop_key_index()


def _data_names(text: str) -> set[str]:
    return set(re.findall(r"^\s*(_\w+)", text, re.MULTILINE))


def _column(headers: list[str], rows: list[list[str]], name: str) -> list[str]:
    i = headers.index(name)
    return [row[i].strip("'\"") for row in rows if i < len(row)]


def test_loops_include_category_keys(aif_text):
    """A loop must carry every category key of the section its columns belong to."""
    path, text = aif_text
    for idx, (headers, _) in enumerate(_parse_loops(text), start=1):
        required = {k for h in headers for k in LOOP_KEYS.get(h, [])}
        missing = required - set(headers)
        assert not missing, f"{path.name}: loop #{idx} is missing key column(s) {sorted(missing)}"


def test_loop_category_key_values_are_unique(aif_text):
    path, text = aif_text
    for idx, (headers, rows) in enumerate(_parse_loops(text), start=1):
        keys = next((LOOP_KEYS[h] for h in headers if h in LOOP_KEYS), None)
        if not keys or not set(keys) <= set(headers):
            continue
        tuples = list(zip(*(_column(headers, rows, k) for k in keys)))
        dupes = {t for t in tuples if tuples.count(t) > 1}
        assert not dupes, f"{path.name}: loop #{idx} has duplicate key values {sorted(dupes)}"


def test_dependent_required_fields_present(aif_text):
    """Every field listed in the schema's dependentRequired must bring its dependencies."""
    path, text = aif_text
    present = _data_names(text)
    for pname, deps in _SCHEMA.get("dependentRequired", {}).items():
        if pname in present:
            missing = [d for d in deps if d not in present]
            assert not missing, f"{path.name}: {pname} requires {missing}"


def test_analysis_fit_parameters_reference_existing_fits(aif_text):
    path, text = aif_text
    loops = _parse_loops(text)
    fits = [(h, r) for h, r in loops if "_analysis_fit_index" in h]
    params = [(h, r) for h, r in loops if "_analysis_fit_param_index" in h]
    if not params:
        pytest.skip("no analysis fit parameter loop")
    assert fits, f"{path.name}: fit parameters given without a fit summary loop"
    fit_ids = {v for h, r in fits for v in _column(h, r, "_analysis_fit_index")}
    for h, r in params:
        orphan = set(_column(h, r, "_analysis_fit_param_index")) - fit_ids
        assert not orphan, f"{path.name}: fit parameters reference unknown fit(s) {sorted(orphan)}"


def test_analysis_examples_present():
    """Keep at least one example exercising each analysis section."""
    combined = "\n".join(p.read_text(encoding="utf-8") for p in ALL_AIF_FILES)
    for name in (
        "_analysis_bet_area",
        "_analysis_pore_size_method",
        "_analysis_psd_size",
        "_analysis_fit_index",
        "_analysis_fit_param_index",
    ):
        assert re.search(rf"^\s*{name}\b", combined, re.MULTILINE), f"no example uses {name}"