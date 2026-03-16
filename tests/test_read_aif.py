"""Tests for reading AIF files with transient data using gemmi."""

import os
import pytest
from gemmi import cif

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOLUMETRIC_AIF = os.path.join(REPO_ROOT, "examples", "various", "volumetric_with_transient.aif")
GRAVIMETRIC_AIF = os.path.join(REPO_ROOT, "examples", "various", "gravimetric_full_transient.aif")
EXAMPLE_AIF = os.path.join(REPO_ROOT, "example.aif")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def vol_block():
    return cif.read_file(VOLUMETRIC_AIF).sole_block()


@pytest.fixture(scope="module")
def grav_block():
    return cif.read_file(GRAVIMETRIC_AIF).sole_block()


@pytest.fixture(scope="module")
def example_block():
    return cif.read_file(EXAMPLE_AIF).sole_block()


# ---------------------------------------------------------------------------
# Basic reading — example.aif (no transient data)
# ---------------------------------------------------------------------------

class TestExampleBasic:
    def test_file_exists(self):
        assert os.path.isfile(EXAMPLE_AIF)

    def test_block_name(self, example_block):
        assert example_block.name == "example_isotherm_aif"

    def test_aif_version(self, example_block):
        assert cif.as_string(example_block.find_value("_audit_aif_version")) != ""

    def test_adsorp_loop_exists(self, example_block):
        assert example_block.find_loop("_adsorp_pressure")

    def test_adsorp_amount_length(self, example_block):
        assert len(list(example_block.find_loop("_adsorp_amount"))) > 0

    def test_no_transient_in_example(self, example_block):
        """example.aif should have no transient data."""
        assert not example_block.find_loop("_adsorp_transient_step")
        assert not example_block.find_loop("_desorp_transient_step")


# ---------------------------------------------------------------------------
# Volumetric transient file
# ---------------------------------------------------------------------------

class TestVolumetricFileReading:
    def test_file_exists(self):
        assert os.path.isfile(VOLUMETRIC_AIF)

    def test_block_name(self, vol_block):
        assert vol_block.name == "volumetric_N2_transient"

    def test_single_block(self):
        doc = cif.read_file(VOLUMETRIC_AIF)
        assert len(doc) == 1


class TestVolumetricMetadata:
    def test_operator(self, vol_block):
        assert cif.as_string(vol_block.find_value("_exptl_operator")) == "Alice Martin"

    def test_adsorptive(self, vol_block):
        assert cif.as_string(vol_block.find_value("_exptl_adsorptive")) == "Nitrogen"

    def test_temperature(self, vol_block):
        assert float(vol_block.find_value("_exptl_temperature")) == pytest.approx(77.35)

    def test_method(self, vol_block):
        assert cif.as_string(vol_block.find_value("_exptl_method")) == "volumetric"

    def test_material_id(self, vol_block):
        assert cif.as_string(vol_block.find_value("_adsnt_material_id")) == "UiO-66"

    def test_units_time(self, vol_block):
        assert cif.as_string(vol_block.find_value("_units_time")) == "s"

    def test_units_pressure(self, vol_block):
        assert cif.as_string(vol_block.find_value("_units_pressure")) == "kPa"


class TestVolumetricEquilibriumData:
    def test_adsorp_pressure_exists(self, vol_block):
        assert vol_block.find_loop("_adsorp_pressure")

    def test_adsorp_3_points(self, vol_block):
        assert len(list(vol_block.find_loop("_adsorp_pressure"))) == 3

    def test_adsorp_first_pressure(self, vol_block):
        p = [float(v) for v in vol_block.find_loop("_adsorp_pressure")]
        assert p[0] == pytest.approx(0.050)

    def test_adsorp_first_amount(self, vol_block):
        a = [float(v) for v in vol_block.find_loop("_adsorp_amount")]
        assert a[0] == pytest.approx(0.120)

    def test_no_desorption_loop(self, vol_block):
        assert not vol_block.find_loop("_desorp_pressure")


class TestVolumetricTransientData:
    def test_transient_step_exists(self, vol_block):
        assert vol_block.find_loop("_adsorp_transient_step")

    def test_transient_time_exists(self, vol_block):
        assert vol_block.find_loop("_adsorp_transient_elapsed_time")

    def test_transient_pressure_exists(self, vol_block):
        assert vol_block.find_loop("_adsorp_transient_pressure")

    def test_transient_temperature_exists(self, vol_block):
        assert vol_block.find_loop("_adsorp_transient_temperature")

    def test_transient_columns_same_length(self, vol_block):
        steps = list(vol_block.find_loop("_adsorp_transient_step"))
        times = list(vol_block.find_loop("_adsorp_transient_elapsed_time"))
        press = list(vol_block.find_loop("_adsorp_transient_pressure"))
        temps = list(vol_block.find_loop("_adsorp_transient_temperature"))
        assert len(steps) == len(times) == len(press) == len(temps)

    def test_transient_total_rows(self, vol_block):
        steps = list(vol_block.find_loop("_adsorp_transient_step"))
        # 3 equilibrium points × 7 time points each = 21
        assert len(steps) == 21

    def test_step_values_are_integers(self, vol_block):
        steps = [int(v) for v in vol_block.find_loop("_adsorp_transient_step")]
        assert all(isinstance(s, int) for s in steps)

    def test_step_values_match_equilibrium_points(self, vol_block):
        steps = set(int(v) for v in vol_block.find_loop("_adsorp_transient_step"))
        n_eq = len(list(vol_block.find_loop("_adsorp_pressure")))
        assert steps == set(range(1, n_eq + 1))

    def test_step1_time_starts_at_zero(self, vol_block):
        steps = [int(v) for v in vol_block.find_loop("_adsorp_transient_step")]
        times = [float(v) for v in vol_block.find_loop("_adsorp_transient_elapsed_time")]
        step1_times = [t for s, t in zip(steps, times) if s == 1]
        assert step1_times[0] == pytest.approx(0.0)

    def test_step1_pressure_decays(self, vol_block):
        """In volumetric adsorption, pressure should decrease over time."""
        steps = [int(v) for v in vol_block.find_loop("_adsorp_transient_step")]
        press = [float(v) for v in vol_block.find_loop("_adsorp_transient_pressure")]
        step1_press = [p for s, p in zip(steps, press) if s == 1]
        assert step1_press[0] > step1_press[-1]

    def test_step1_final_pressure_matches_equilibrium(self, vol_block):
        """Last transient pressure for step 1 should match equilibrium pressure."""
        steps = [int(v) for v in vol_block.find_loop("_adsorp_transient_step")]
        tr_press = [float(v) for v in vol_block.find_loop("_adsorp_transient_pressure")]
        eq_press = [float(v) for v in vol_block.find_loop("_adsorp_pressure")]
        step1_press = [p for s, p in zip(steps, tr_press) if s == 1]
        assert step1_press[-1] == pytest.approx(eq_press[0])

    def test_no_desorp_transient(self, vol_block):
        assert not vol_block.find_loop("_desorp_transient_step")

    def test_transient_values_all_numeric(self, vol_block):
        for col in ["_adsorp_transient_step",
                     "_adsorp_transient_elapsed_time",
                     "_adsorp_transient_pressure",
                     "_adsorp_transient_temperature"]:
            for val in vol_block.find_loop(col):
                float(val)


# ---------------------------------------------------------------------------
# Gravimetric full transient file
# ---------------------------------------------------------------------------

class TestGravimetricFileReading:
    def test_file_exists(self):
        assert os.path.isfile(GRAVIMETRIC_AIF)

    def test_block_name(self, grav_block):
        assert grav_block.name == "gravimetric_CO2_transient"

    def test_single_block(self):
        doc = cif.read_file(GRAVIMETRIC_AIF)
        assert len(doc) == 1


class TestGravimetricMetadata:
    def test_operator(self, grav_block):
        assert cif.as_string(grav_block.find_value("_exptl_operator")) == "Bob Zhang"

    def test_adsorptive(self, grav_block):
        assert cif.as_string(grav_block.find_value("_exptl_adsorptive")) == "Carbon dioxide"

    def test_temperature(self, grav_block):
        assert float(grav_block.find_value("_exptl_temperature")) == pytest.approx(298.15)

    def test_method(self, grav_block):
        assert cif.as_string(grav_block.find_value("_exptl_method")) == "gravimetric"

    def test_material_id(self, grav_block):
        assert cif.as_string(grav_block.find_value("_adsnt_material_id")) == "Zeolite-13X"

    def test_degas_summary(self, grav_block):
        val = cif.as_string(grav_block.find_value("_adsnt_degas_summary"))
        assert "350" in val


class TestGravimetricEquilibriumData:
    def test_adsorp_3_points(self, grav_block):
        assert len(list(grav_block.find_loop("_adsorp_pressure"))) == 3

    def test_desorp_3_points(self, grav_block):
        assert len(list(grav_block.find_loop("_desorp_pressure"))) == 3

    def test_desorp_first_pressure(self, grav_block):
        p = [float(v) for v in grav_block.find_loop("_desorp_pressure")]
        assert p[0] == pytest.approx(100.0)


class TestGravimetricAdsorpTransient:
    def test_transient_step_exists(self, grav_block):
        assert grav_block.find_loop("_adsorp_transient_step")

    def test_transient_amount_exists(self, grav_block):
        assert grav_block.find_loop("_adsorp_transient_amount")

    def test_transient_columns_same_length(self, grav_block):
        cols = ["_adsorp_transient_step",
                "_adsorp_transient_elapsed_time",
                "_adsorp_transient_pressure",
                "_adsorp_transient_temperature",
                "_adsorp_transient_amount"]
        lengths = [len(list(grav_block.find_loop(c))) for c in cols]
        assert len(set(lengths)) == 1

    def test_step_values(self, grav_block):
        steps = set(int(v) for v in grav_block.find_loop("_adsorp_transient_step"))
        assert steps == {1, 2, 3}

    def test_step3_final_amount_matches_equilibrium(self, grav_block):
        steps = [int(v) for v in grav_block.find_loop("_adsorp_transient_step")]
        tr_amount = [float(v) for v in grav_block.find_loop("_adsorp_transient_amount")]
        eq_amount = [float(v) for v in grav_block.find_loop("_adsorp_amount")]
        step3_amount = [a for s, a in zip(steps, tr_amount) if s == 3]
        assert step3_amount[-1] == pytest.approx(eq_amount[2])


class TestGravimetricDesorpTransient:
    def test_transient_step_exists(self, grav_block):
        assert grav_block.find_loop("_desorp_transient_step")

    def test_transient_amount_exists(self, grav_block):
        assert grav_block.find_loop("_desorp_transient_amount")

    def test_transient_columns_same_length(self, grav_block):
        cols = ["_desorp_transient_step",
                "_desorp_transient_elapsed_time",
                "_desorp_transient_pressure",
                "_desorp_transient_temperature",
                "_desorp_transient_amount"]
        lengths = [len(list(grav_block.find_loop(c))) for c in cols]
        assert len(set(lengths)) == 1

    def test_step_values(self, grav_block):
        steps = set(int(v) for v in grav_block.find_loop("_desorp_transient_step"))
        assert steps == {1, 2, 3}

    def test_step3_final_amount_matches_equilibrium(self, grav_block):
        steps = [int(v) for v in grav_block.find_loop("_desorp_transient_step")]
        tr_amount = [float(v) for v in grav_block.find_loop("_desorp_transient_amount")]
        eq_amount = [float(v) for v in grav_block.find_loop("_desorp_amount")]
        step3_amount = [a for s, a in zip(steps, tr_amount) if s == 3]
        assert step3_amount[-1] == pytest.approx(eq_amount[2])

    def test_desorp_transient_all_numeric(self, grav_block):
        for col in ["_desorp_transient_step",
                     "_desorp_transient_elapsed_time",
                     "_desorp_transient_pressure",
                     "_desorp_transient_temperature",
                     "_desorp_transient_amount"]:
            for val in grav_block.find_loop(col):
                float(val)


# ---------------------------------------------------------------------------
# Missing transient fields
# ---------------------------------------------------------------------------

class TestMissingTransientFields:
    def test_missing_transient_loop_is_falsy(self, example_block):
        assert not example_block.find_loop("_adsorp_transient_step")

    def test_missing_desorp_transient_loop_is_falsy(self, example_block):
        assert not example_block.find_loop("_desorp_transient_step")

    def test_nonexistent_transient_column(self, vol_block):
        assert not vol_block.find_loop("_adsorp_transient_nonexistent")
