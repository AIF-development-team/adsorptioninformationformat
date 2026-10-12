# AIF Dictionary Improvement Proposal

## 1 — Motivation

The AIF dictionary (`aif_dictionary.json`, `.dic`, `.yaml`) defines data names covering isothermal adsorption and desorption measurements. However,
files already present in this repository use data names that fall outside the
dictionary. This proposal catalogues those names and recommends how to
incorporate them.

---

## 2 — Proposal A: Isobar Data Category

### Background

An isobar measures the adsorbed amount as a function of **temperature** at a
**constant pressure** — the complement of an isotherm (amount vs pressure at
constant temperature). This is a standard experiment in adsorption science, and
the AIF format should be able to represent it natively.

The example file `examples/various/isobar.aif` already demonstrates the
pattern: a `loop_` block with columns `_isobar_temperature`,
`_isobar_amount`, with the constant pressure given by the top-level `_exptl_pressure`.

### Proposed data names

A new **ISOBAR** category with an index key and two loop
columns (implemented as the `isobar` section of `aif_dictionary.json`):

| Data name | Type | Description |
|---|---|---|
| `_isobar_index` | number | Index of the isobar data point, starting from 1 (loop key, as for `_adsorp_index`) |
| `_exptl_pressure` | number | Pressure held constant during the isobar measurement, analogue of `_exptl_temperature` for an isotherm (see `_units_pressure`) |
| `_isobar_temperature` | number | Temperature at each isobar data point (see `_units_temperature`) |
| `_isobar_amount` | number | Amount adsorbed at each isobar data point (see `_units_sorbed_amount`) |

### Design questions

1. **What is the cycle up/down naming?**.

2. **Possible extensions.**
   - `_isobar_amount_excess`, `_isobar_amount_absolute`, `_isobar_amount_net`
     — mirroring the isotherm's three loading conventions.
   - `_isobar_fugacity` — for high-pressure isobars where fugacity corrections
     are needed.
   These can be added in a follow-up proposal if there is demand.

### Outstanding issues

1. **Required `_exptl_temperature`.** The dictionary requires `_exptl_temperature`
   in every file (enforced in the generated YAML/DIC and by a test), which does not
   fit an isobar where temperature varies. `isobar.aif` currently omits it. Options:
   allow `_isobar_temperature` as an alternative, or carry a nominal
   `_exptl_temperature` in isobar files.
2. **Single pressure per data block.** With only the top-level `_exptl_pressure`,
   a multi-pressure isobar series must be split into separate data blocks.
3. **`_exptl_isotherm_type` in an isobar file.** The tag is isotherm-named but
   `isobar.aif` uses it to classify the amount reported. Decide whether to reuse it
   or introduce an isobar-neutral name.
4. **Test scope.** `test_has_adsorp_or_desorp_loop` was widened to accept
   `_isobar_amount`; confirm this is the intended way to admit non-isotherm examples.
5. **Up/down (cycle) naming** for heating and cooling branches (see design
   question 1).
6. **No dependency on `_exptl_pressure` beyond `_units_pressure`.** Consider whether
   an isobar loop should require `_exptl_pressure` to be present.

---

## 5 — Version impact

Adding a new data category is a **backward-compatible** change (new optional
fields only), so it warrants a **minor** version bump under SemVer.

