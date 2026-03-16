# Proposal: Multicomponent Adsorption Support in AIF

## 1 — Summary

The AIF dictionary currently describes **single-component** adsorption only. The
example file `03_multicomponent_co2_n2.aif` demonstrates a binary CO₂/N₂ mixture
measurement that introduces **new data names** not present in the dictionary.
This proposal analyses those names, identifies structural design issues with the
current approach, presents alternative representations, and recommends a path
forward.

---

## 2 — Proposal

### Change to `_exptl_adsorptive`

For multicomponent data, `_exptl_adsorptive` should be set to the **reserved
value** `"mixture"`. The dictionary should formally document this:

> When `_exptl_adsorptive` is set to `"mixture"`, the individual gas species
> are specified in the `_adsorptive_component_*` loop, and
> `_exptl_adsorptive_name` may optionally hold a short mixture label
> (e.g. `"CO2/N2 15:85"`).

### Units

`_units_composition_type` | Already in dictionary ✓ |

### Component definition loop

These appear in a `loop_` that defines the gas mixture composition:

Option 1

| Data name | Value example | Purpose |
|---|---|---|
| `_adsorptive_mixture_component_id` | `1` | Integer key identifying each component |
| `_adsorptive_mixture_component_name` | `"CO2"` | Chemical name or formula |
| `_adsorptive_mixture_component_mole_fraction` | `0.15` | Feed (bulk-gas) mole fraction |
| `_adsorptive_mixture_component_cas` | `"124-38-9"` | CAS Registry Number |
| `...` | `...` | ... |


### Data loop columns (extending `_adsorp_*` and `_desorp_*`)

These appear alongside the existing `_adsorp_pressure` in the data loop:

Option 1

| Data name | Value example | Purpose |
|---|---|---|
| `_adsorp_amount_component_1` | `0.82` | Amount adsorbed of component 1 |
| `_adsorp_amount_component_2` | `0.05` | Amount adsorbed of component 2 |
| `_adsorp_composition_component_1` | `0.942` | Adsorbed-phase mole fraction of component 1 |
| `_adsorp_composition_component_2` | `0.058` | Adsorbed-phase mole fraction of component 2 |
| `_adsorp_pressure` | `1` | Pressure - total |
| `....` | `...` | ... |

| Pros | Cons |
|---|---|
| Compact, one row per pressure point | Unbounded data names — cannot pre-define in dictionary |
| Easy to read visually | Parsers need regex matching on column names |
| Familiar tabular layout | DDLm/LinkML cannot express parameterised names |
| | Adding a component changes the schema |


Option 2

| Data name | Type | Description |
|---|---|---|
| `_adsorp_component_id` | integer | Foreign key linking this row to a component defined in the `_adsorptive_component_*` loop. For single-component data, this column is omitted. |
| `_adsorp_composition` | number | Mole fraction (or other basis, see `_units_composition_type`) of this component in the adsorbed phase at equilibrium. |
| `_adsorp_pressure` | `1` | Pressure - total |
| `....` | `...` | ... |


| Pros | Cons |
|---|---|
| **Fixed data names** — all defined in dictionary | Pressure values repeated once per component |
| Scales to any number of components | More rows (N × M instead of M) |
| Uses existing `_adsorp_amount` / `_adsorp_pressure` | Slightly less visually compact |
| Foreign key in data, not in column names | Parsers must group rows by pressure |
| CIF-idiomatic (standard relational loop) | |
| DDLm and LinkML can express it natively | |

---

## 3 — Other items to discuss

1. **Meaning of _pressure in multicomponent data** It can mean total, or partial.

2. **Should `_adsorp_amount` in a multicomponent context be the *total*
   adsorbed amount or the *per-component* amount?** The recommendation above
   uses it as per-component (tied to `_adsorp_component_id`). If total amount
   is also desired, a separate `_adsorp_amount_total` or a row with a special
   component ID (e.g. `0` = total) could be defined.

3. **Should selectivity be a first-class data name?** Selectivity
   (α₁₂ = (x₁/x₂)/(y₁/y₂)) is a commonly reported quantity for mixture
   adsorption. It can be derived from composition and feed fractions, but a
   dedicated `_adsorp_selectivity` column could be convenient. This is left
   for a follow-up proposal.

4. **Mass-fraction and volume-fraction compositions.** The existing
   `_units_composition_type` supports `mole_fraction` and `mass_fraction`.
   Are additional composition bases needed (e.g. `volume_fraction`,
   `partial_pressure`)?

5. **Fugacity per component.** High-pressure multicomponent data may require
   per-component fugacity. Should `_adsorp_fugacity` be usable per-component
   (when `_adsorp_component_id` is present), or does a separate
   `_adsorp_fugacity_component` name need to exist?
