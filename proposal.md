# AIF Dictionary Improvement Proposal

## 1 — Motivation

The current AIF dictionary (`aif_dictionary.json`, `.dic`, `.yaml`) defines 51
data names covering isothermal adsorption and desorption measurements. However,
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
`_isobar_amount`, and `_isobar_pressure`.

### Proposed data names

A new **ISOBAR** category (Section 9 in the JSON Schema) with three loop
columns:

| Data name | Type | Description |
|---|---|---|
| `_exptl_pressure` | number | Pressure held constant during the isobar measurement, analogue of `_exptl_temperature` for an isotherm (see `_units_temperature`) |
| `_isobar_temperature` | number | Temperature at each isobar data point (see `_units_temperature`) |
| `_isobar_amount` | number | Amount adsorbed at each isobar data point (see `_units_loading`) |
| `_isobar_pressure` | number | Pressure held constant during the isobar measurement, recorded per row to allow multi-pressure datasets in a single loop (see `_units_pressure`) |

### Design questions

1. **What is the cycle up/down naming?**.

2. **Possible extensions.**
   - `_isobar_amount_excess`, `_isobar_amount_absolute`, `_isobar_amount_net`
     — mirroring the isotherm's three loading conventions.
   - `_isobar_fugacity` — for high-pressure isobars where fugacity corrections
     are needed.
   These can be added in a follow-up proposal if there is demand.

---

## 5 — Version impact

Adding a new data category is a **backward-compatible** change (new optional
fields only), so it warrants a **minor** version bump under SemVer.

