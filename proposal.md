# Proposal: Optional Time-Resolved (Transient) Data in AIF

## Motivation

Modern adsorption instruments routinely log high-frequency time-resolved data—
instantaneous pressure, temperature, and sometimes mass or loading—during each
dosing or evacuation step. This transient data is valuable for:

- **Kinetic analysis** — determining diffusion coefficients, rate constants, and
  mass-transfer parameters.
- **Equilibrium verification** — confirming that the system reached equilibrium
  before the next step.
- **Quality assurance** — detecting leaks, temperature drifts, or instrument
  artefacts that are invisible in the equilibrium isotherm alone.
- **Reproducibility** — enabling independent re-analysis of raw instrument
  traces without returning to proprietary software.

Currently the AIF format records only the final equilibrium point per step. This
proposal adds optional loop blocks that carry the full time-resolved trace while
preserving complete backward compatibility.

## Design Principles

1. **Optional** — Transient loops are not required. Files without them remain
   valid AIF files.
2. **Single-block** — The file retains a single `data_` block, preserving the
   `sole_block()` assumption in all existing parsers (e.g. gemmi, pycifrw).
3. **Branch-mirrored naming** — Adsorption transient columns use the `_adsorp_transient_`
   prefix; desorption uses `_desorp_transient_`. This mirrors the existing
   `_adsorp_` / `_desorp_` split.
4. **Step-indexed** — A `_step` column (1-based integer) links each transient
   row to the corresponding equilibrium point in the parent `_adsorp_` or
   `_desorp_` loop.
5. **Extensible** — Additional columns (e.g. `_adsorp_transient_amount`,
   `_adsorp_transient_mass`) can be added as needed without breaking the schema.
6. **Uncertainty-compatible** — The existing `*_uncertainty` pattern property
   applies: `_adsorp_transient_pressure_uncertainty` is automatically valid.

## New Data Names

### Adsorption transient loop

| Data name                            | Type    | Description |
|--------------------------------------|---------|-------------|
| `_adsorp_transient_step`             | integer | 1-based index of the corresponding equilibrium point in the adsorption loop |
| `_adsorp_transient_elapsed_time`     | number  | Time elapsed since the start of this dosing step (see `_units_time`) |
| `_adsorp_transient_pressure`         | number  | Instantaneous pressure during the dosing step (see `_units_pressure`) |
| `_adsorp_transient_temperature`      | number  | Instantaneous temperature during the dosing step (see `_units_temperature`) |
| `_adsorp_transient_amount`           | number  | Instantaneous amount adsorbed during the dosing step (see `_units_loading`) |

### Desorption transient loop

| Data name                            | Type    | Description |
|--------------------------------------|---------|-------------|
| `_desorp_transient_step`             | integer | 1-based index of the corresponding equilibrium point in the desorption loop |
| `_desorp_transient_elapsed_time`     | number  | Time elapsed since the start of this desorption step (see `_units_time`) |
| `_desorp_transient_pressure`         | number  | Instantaneous pressure during the desorption step (see `_units_pressure`) |
| `_desorp_transient_temperature`      | number  | Instantaneous temperature during the desorption step (see `_units_temperature`) |
| `_desorp_transient_amount`           | number  | Instantaneous amount adsorbed during the desorption step (see `_units_loading`) |

## File Layout

Transient data appears as additional `loop_` blocks within the same `data_`
block, after the equilibrium loops:

```
data_example

    # --- scalar metadata (unchanged) ---
    _audit_aif_version    "__AIF_VERSION__"
    _exptl_adsorptive     "Nitrogen"
    _adsnt_material_id    "UiO-66"
    _adsnt_sample_id      "sample-01"
    _units_time           "s"
    ...

    # --- equilibrium adsorption data (unchanged) ---
    loop_
        _adsorp_pressure
        _adsorp_p0
        _adsorp_amount
        0.050   101.325   0.120
        0.100   101.325   0.450

    # --- NEW: adsorption transient data (optional) ---
    loop_
        _adsorp_transient_step
        _adsorp_transient_elapsed_time
        _adsorp_transient_pressure
        _adsorp_transient_temperature
        1    0.0    0.080   77.36
        1    5.0    0.065   77.35
        1   10.0    0.052   77.35
        1   15.0    0.050   77.35
        2    0.0    0.160   77.36
        2    5.0    0.125   77.35
        2   10.0    0.105   77.35
        2   15.0    0.100   77.35
```

## Backward Compatibility

- Existing AIF readers that do not know the `_*_transient_*` data names will
  simply skip the transient loops — this is standard CIF behaviour.
- The `_units_time` field already exists in the dictionary and is reused for
  transient time values.
- No existing data names are modified or removed.
- `additionalProperties: true` in the JSON schema ensures unknown properties
  (including transient ones) do not cause validation errors in older schema
  versions.

