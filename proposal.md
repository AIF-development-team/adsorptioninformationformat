# AIF Dictionary Improvement Proposal

---

## 1. Summary

This proposal introduces **new data names** to the AIF dictionary, organized
into **several new categories**. These additions have been prototyped in example AIF
files under `examples/aif/` and are fully tested with `gemmi`-based read tests.
The goal is to extend the format's coverage from basic isotherm recording to a
broader range of sorption science workflows — including calorimetry, surface
analysis, simulation metadata, quality assurance, and data provenance — while
remaining backward-compatible with v1.0.0.

All new fields are **optional**. No existing required fields change. The schema's
`additionalProperties: true` policy is preserved.

---

## 2. Proposed New Sections

### 2.1 Adsorptive Information and Properties (`_adsorptive_*`)

Physical and chemical identifiers for the adsorptive molecule. Enables
machine-readable gas identification and thermodynamic calculations (e.g.
fugacity corrections, kinetic selectivity estimates) directly from the AIF
file without external lookups. Some examples include:

| Data name | Type | Description | Example value |
|---|---|---|---|
| `_adsorptive_cas` | string | CAS Registry Number | `"124-38-9"` |
| `_adsorptive_inchi` | string | IUPAC InChI identifier | `"InChI=1S/CO2/c2-1-3"` |
| `_adsorptive_smiles` | string | Canonical SMILES string | `"O=C=O"` |
| `_adsorptive_molecular_weight` | number | Molecular weight of the adsorptive (see `_units_molecular_weight`) | `44.01` |
| `_adsorptive_critical_temperature` | number | Critical temperature (see `_units_temperature`) | `304.13` |
| `_adsorptive_critical_pressure` | number | Critical pressure (see `_units_pressure`) | `7377300.0` |
| `_adsorptive_kinetic_diameter` | number | Kinetic diameter (see `_units_kinetic_diameter`) | `3.3` |
| `_adsorptive_quadrupole_moment` | number | Quadrupole moment of the adsorptive | `4.3` |

**Used in:** [02_full_featured.aif](../examples/aif/02_full_featured.aif),
[04_water_vapor.aif](../examples/aif/04_water_vapor.aif),
[06_co2_calorimetry.aif](../examples/aif/06_co2_calorimetry.aif),
[11_high_pressure_ch4.aif](../examples/aif/11_high_pressure_ch4.aif)

**Rationale:** Current AIF files identify the adsorptive with only a free-text
name (`_exptl_adsorptive`). This is ambiguous (e.g. "Nitrogen" vs "N2" vs
"nitrogen") and insufficient for automated processing. CAS numbers, InChI,
and SMILES provide unambiguous chemical identification, while critical
constants enable equation-of-state calculations without external databases.

---

### 2.2 Adsorbent Extra Information (`_adsnt_*`)

Links the adsorbent to crystallographic databases and provides structural
metadata essential for computational screening and structure-property analysis.
Records the provenance and condition of the adsorbent sample, which is critical
for reproducibility and for interpreting multi-cycle degradation studies. 
Link to MPIF?

| Data name | Type | Description | Example value |
|---|---|---|---|
| `_adsnt_structure_csd_refcode` | string | Cambridge Structural Database (CSD) reference code | `"FIQCEN"` |
| `_adsnt_structure_topology` | string | Network topology descriptor (e.g. RCSR symbol) | `"tbo"` |
| `_adsnt_structure_smiles` | string | SMILES of the organic linker or building block | `"OC(=O)c1cc(C(O)=O)cc(C(O)=O)c1"` |
| `_adsnt_composition` | string | Chemical composition or formula of the adsorbent | `"Cu3(BTC)2"` |
| `_adsnt_molar_mass` | number | Molar mass of the adsorbent formula unit (see `_units_molecular_weight`) | `604.87` |
| `_adsnt_synthesis_method` | string | Synthesis route used, e.g. solvothermal, mechanochemical | `"solvothermal"` |
| `_adsnt_synthesis_reference` | string | DOI or citation for the synthesis protocol | `"10.1021/ja8057953"` |
| `_adsnt_activation_method` | string | Post-synthesis activation procedure | `"methanol exchange, vacuum at 120C for 16h"` |
| `_adsnt_batch_id` | string | Batch or lot identifier for the sample | `"UiO66-A1"` |
| `_adsnt_cycle_number` | integer | Adsorption-desorption cycle index (1-based) | `3` |
| `_adsnt_surface_area_reported` | number | Pre-reported or literature surface area (see `_units_surface_area`) | `1187.0` |

**Used in:** [06_mof_structure_link.aif](../examples/aif/06_mof_structure_link.aif),
[12_simulation_gcmc.aif](../examples/aif/12_simulation_gcmc.aif),
[02_full_featured.aif](../examples/aif/02_full_featured.aif), [07_cycling_stability.aif](../examples/aif/07_cycling_stability.aif),

**Rationale:** 
Irreproducibility is a major issue in adsorption science.
Recording synthesis and activation details alongside the isotherm data —
rather than only in a cited paper — improves long-term interpretability.
The cycle number enables a series of AIF files to represent multi-cycle
degradation studies, which are common for stability assessment.
Adsorption databases increasingly cross-reference crystal
structures. A CSD refcode provides a single-point link to full structural
data. Topology codes enable filtering in computational screening studies.
Chemical composition is needed for unit conversions (e.g. per-formula-unit
to per-gram loading).

---

### 2.3 Analysis Fields e.g. Surface & Pore Characterization (`_analysis_*`)

Derived quantities from standard analysis methods (BET, Langmuir, BJH/DFT
pore size distribution).

| Data name | Type | Description | Example value |
|---|---|---|---|
| `_analysis_methods` | string | Analysis methods/description used for derived quantities | `"BET and HK"` |
| `_analysis_bet_area` | number | BET surface area (see `_units_surface_area`) | `820.5` |
| `_analysis_bet_c_constant` | number | BET C constant (dimensionless) | `145.3` |
| `_analysis_bet_pressure_range_min` | number | Lower bound of the relative pressure range used for BET fitting | `0.05` |
| `_analysis_bet_pressure_range_max` | number | Upper bound of the relative pressure range used for BET fitting | `0.30` |
| `_analysis_langmuir_area` | number | Langmuir surface area (see `_units_surface_area`) | `1105.2` |
| `_analysis_micropore_volume` | number | Micropore volume from t-plot or DR analysis (see `_units_pore_volume`) | `0.02` |
| `_analysis_total_pore_volume` | number | Total pore volume (see `_units_pore_volume`) | `1.05` |
| `_analysis_total_pore_volume_pp0` | number | Relative pressure p/p0 at which total pore volume was evaluated | `0.99` |
| `_analysis_psd_method` | string | Method for determining pore size distribution (see `_units_pore_diameter`) | `NLDFT-Carbon-N2 (Micromeritics)` |
| `_analysis_psd_diameter` | number | Pore diameter in a pore-size distribution loop (see `_units_pore_diameter`) | `5.0` |
| `_analysis_psd_dv_dd` | number | Differential pore volume dV/dD at each diameter in a PSD loop | `0.089` |

**Used in:** [05_bet_pore_analysis.aif](../examples/aif/05_bet_pore_analysis.aif),
[02_full_featured.aif](../examples/aif/02_full_featured.aif)

**Rationale:** BET area and pore volume are the most commonly reported derived
quantities in adsorption publications. Storing them alongside the raw isotherm
with the fitting parameters (C constant, p/p0 range) makes the analysis
transparent and reproducible. The PSD loop enables storage of pore size
distributions alongside the source isotherm for the first time in AIF.

---

### 2.4 Isotherm Model Fitting (`_analysis_fit_*`) in analysis

Loop fields for recording one or more fitted isotherm models and their
parameters — essential for archiving the parametric description of an
isotherm and for comparing alternative models.

Split the fit information into **two loops linked by an integer key**
(`_fit_id` / `_fit_param_id`). This follows the same parent–child
ID-linking pattern used extensively in mmCIF/PDBx.

**Loop 1 — Fit summary** (one row per model):

| Data name | Type | Description | Example value |
|---|---|---|---|
| `_fit_id` | integer | Unique integer key identifying this fit within the file | `1` |
| `_fit_model` | string | Name of the fitted isotherm model | `"Langmuir"` |
| `_fit_r_squared` | number | Coefficient of determination (R²) | `0.9987` |
| `_fit_rmse` | number | Root-mean-square error (see `_units_loading`) | `0.045` |

**Loop 2 — Fit parameters** (one row per parameter, linked to Loop 1):

| Data name | Type | Description | Example value |
|---|---|---|---|
| `_fit_param_id` | integer | Foreign key referencing `_fit_id` in Loop 1 | `1` |
| `_fit_param_name` | string | Name of the parameter | `"q_max"` |
| `_fit_param_value` | number | Fitted value | `5.67` |
| `_fit_param_uncertainty` | number | Uncertainty of the fitted value | `0.12` |
| `_fit_param_unit` | string | Unit of the parameter | `"mmol/g"` |

**Used in:** [12_simulation_gcmc.aif](../examples/aif/12_simulation_gcmc.aif),
[02_full_featured.aif](../examples/aif/02_full_featured.aif)

**Rationale:** Fitted model parameters are widely used for interpolation,
extrapolation, and in process simulation. The two-loop relational design
accommodates any number of models, each with an arbitrary number of
parameters (Langmuir, DSL, Toth, Sips, etc.), using name-value-unit rows
rather than model-specific fields. This keeps the schema generic while
enabling multi-model comparison in a single file.

---

### 2.5 Instrument Info and Metadata (`_instrument_*`)

Detailed instrument provenance for traceability and quality management.

| Data name | Type | Description | Example value |
|---|---|---|---|
| `_instrument_manufacturer` | string | Manufacturer of the adsorption instrument | `"Micromeritics"` |
| `_instrument_model` | string | Model name or number | `"ASAP 2020"` |
| `_instrument_firmware_version` | string | Firmware or software version of the instrument | `"V4.05"` |
| `_instrument_last_calibration_date` | string | Date of last instrument calibration (ISO 8601) | `"2024-11-15T10:00:00Z"` |
| `_instrument_lab_temperature` | number | Ambient laboratory temperature during measurement (see `_units_temperature`) | `22.3` |
| `_instrument_lab_humidity` | number | Ambient laboratory relative humidity (%) | `45.0` |
| `_instrument_bath_type` | string | Type of temperature bath used | `"liquid N2"` |
| `_instrument_equilibration_criterion` | string | Criterion used to determine equilibrium at each point | `"pressure stability < 0.01% over 30s"` |
| `_instrument_leak_rate` | number | Measured leak rate of the manifold (see `_units_leak_rate`) | `0.00005` |
| `_instrument_dead_volume` | number | Total dead (free-space) volume (see `_units_dead_volume`) | `12.34` |
| `_instrument_cold_dead_volume` | number | Cold zone dead volume (see `_units_dead_volume`) | `5.67` |
| `_instrument_warm_dead_volume` | number | Warm zone dead volume (see `_units_dead_volume`) | `6.67` |
| `_instrument_reference_material` | string | Certified reference material used for validation | `"BAM-PM-104 certified reference"` |
| `_instrument_reference_agreement` | number | Deviation from reference value (%) | `1.2` |

**Used in:** [13_instrument_quality.aif](../examples/aif/13_instrument_quality.aif),
[02_full_featured.aif](../examples/aif/02_full_featured.aif)

**Rationale:** `_exptl_instrument` is a single free-text field that provides
no structure. Instrument manufacturer, model, firmware, and calibration date
are essential for audit trails, inter-laboratory comparisons, and round-robin
studies. Lab conditions (temperature, humidity) can affect dead-volume
calibration and equilibrium readings.

---

### 2.6 Data Provenance, Related Data & Linkage (`_data_*`)

Cross-references to other AIF files, databases, and datasets. 
Authorship, access control, and licensing metadata for FAIR data practices.

| Data name | Type | Description | Example value |
|---|---|---|---|
| `_data_license` | string | License under which the data is distributed (SPDX identifier preferred) | `"CC-BY-4.0"` |
| `_data_orcid` | string | ORCID iD of the data author or contact person | `"0000-0001-2345-6789"` |
| `_data_contact_email` | string | Contact email for inquiries about the data | `"nina.johansson@example.se"` |
| `_data_related_dataset_url` | string | URL to the dataset in an external repository | `"https://adsorption.nist.gov/..."` |
| `_data_related_nist_isodb_id` | string | NIST/ARPA-E ISODB identifier | `"ISODB-12345"` |
| `_data_related_aif_file` | string | Filename of a related AIF file | `"07b_cycling_stability_c1.aif"` |
| `_data_related_aif_relationship` | string | Description of the relationship to the related file | `"cycle 1 of same sample"` |

**Used in:** [14_linked_datasets.aif](../examples/aif/14_linked_datasets.aif),
[07_cycling_stability.aif](../examples/aif/07_cycling_stability.aif),
[02_full_featured.aif](../examples/aif/02_full_featured.aif), 
[12_simulation_gcmc.aif](../examples/aif/12_simulation_gcmc.aif)

**Rationale:** Adsorption datasets are often part of a family — different
gases on the same sample, multiple cycles, isotherm-plus-characterization
pairs. Explicit cross-references prevent data fragmentation and are essential
for database ingestion. The NIST ISODB is the largest public adsorption
database; a dedicated field for its IDs enables bidirectional linking.
**Rationale:** FAIR data principles require that data carry machine-readable
licensing and attribution. ORCID provides unambiguous author identification.
A contact email enables data consumers to ask clarification questions. These
fields are the minimum necessary for a data file to be self-describing with
respect to its terms of use.

---

### 2.7 Additional Units (`_units_*`)

New unit fields, some required by the sections above.

| Data name | Type | Description | Example value |
|---|---|---|---|
| `_units_enthalpy` | string | Unit of enthalpy values, e.g. kJ/mol | `"kJ/mol"` |
| `_units_surface_area` | string | Unit of surface area values, e.g. m2/g | `"m2/g"` |
| `_units_pore_volume` | string | Unit of pore volume values, e.g. cm3/g | `"cm3/g"` |
| `_units_pore_diameter` | string | Unit of pore diameter values, e.g. nm | `"nm"` |
| `_units_molecular_weight` | string | Unit of molecular weight values, e.g. g/mol | `"g/mol"` |
| `_units_kinetic_diameter` | string | Unit of kinetic diameter values, e.g. angstrom | `"angstrom"` |
| `_units_dead_volume` | string | Unit of dead volume values, e.g. cm3 | `"cm3"` |
| `_units_leak_rate` | string | Unit of leak rate values, e.g. Pa/min | `"Pa/min"` |
| `_units_quadrupole_moment` | string | Unit of quadrupolar moment, e.g. Debye·Å | `"Debye·Å"` |

---

### 2.8 Other Data in Loops: e.g. (`_adsorp_enthalpy_*`)

Per-point enthalpy columns for the adsorption loop, enabling storage of
simultaneous calorimetry data.

| Data name | Type | Description | Example value |
|---|---|---|---|
| `_adsorp_enthalpy_differential` | number | Differential enthalpy of adsorption at each point (see `_units_enthalpy`) | `-35.2` |
| `_adsorp_enthalpy_integral` | number | Integral (cumulative) enthalpy up to each point (see `_units_enthalpy`) | `-5.73` |

**Used in:** [06_co2_calorimetry.aif](../examples/aif/06_co2_calorimetry.aif),
[02_full_featured.aif](../examples/aif/02_full_featured.aif)

**Rationale:** Microcalorimetry coupled with adsorption measurements is a
standard characterization technique. Currently, enthalpy data must be stored
in a separate file or ad-hoc field. Adding these as loop columns alongside
pressure and amount allows the thermodynamic data to be read in the same
`loop_` as the isotherm without any structural changes to the format.

---
