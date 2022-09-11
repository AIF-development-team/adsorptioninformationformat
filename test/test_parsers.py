# -*- coding: utf-8 -*-
# pylint: disable-msg=invalid-name # to allow non-conforming variable names
"""
Test all parsers for all manufacturers
"""

import json
import sys

import filecmp
from pathlib import Path

import pytest
from .conftest import (BELcsv_data, BELcsv_JIS_data, NIST_data, bel_data, mic_data, qnt_data)

from parsers import NISTjson


def run_raw2aif(args):
    from raw2aif import main as raw2aif_main
    sys.argv = ["raw2aif.py"] + args
    raw2aif_main()


def run_plotaif(args):
    from plotaif import main as plotaif_main
    sys.argv = ["plotaif.py"] + args
    plotaif_main()


@pytest.mark.parametrize("mat_id, file", bel_data)
def test_bel_parser(mat_id, file):
    """Test BEL Parser"""
    infile = Path(f"./test/database/{file}")
    testfile = infile.with_suffix(".aif_tst")
    run_raw2aif([infile, "BELSORP-max", mat_id])
    filecmp.cmp(infile, testfile, shallow=False)


@pytest.mark.parametrize("mat_id, file", bel_data)
def test_bel_output(mat_id, file):
    """Check BEL output"""
    outfile = Path(file).with_suffix('.aif')
    run_plotaif([f"./test/database/{outfile}"])


@pytest.mark.parametrize("mat_id, file", BELcsv_data)
def test_BELcsv_parser(mat_id, file):
    """Test BEL CSV Parser"""
    infile = Path(f"./test/database/{file}")
    testfile = infile.with_suffix(".aif_tst")
    run_raw2aif([infile, "BEL-csv", mat_id])
    filecmp.cmp(infile, testfile, shallow=False)


@pytest.mark.parametrize("mat_id, file", BELcsv_data)
def test_BELcsv_output(mat_id, file):
    """Check BEL CSV output"""
    outfile = Path(file).with_suffix('.aif')
    run_plotaif([f"./test/database/{outfile}"])


@pytest.mark.parametrize("mat_id, file", BELcsv_JIS_data)
def test_BELcsv_JIS_parser(mat_id, file):
    """Test BEL CSV Parser (Japanese)"""
    infile = Path(f"./test/database/{file}")
    testfile = infile.with_suffix(".aif_tst")
    run_raw2aif([infile, "BEL-csv_JIS", mat_id])
    filecmp.cmp(infile, testfile, shallow=False)


@pytest.mark.parametrize("mat_id, file", BELcsv_JIS_data)
def test_BELcsv_JIS_output(mat_id, file):
    """Check BEL CSV output (Japanese)"""
    outfile = Path(file).with_suffix('.aif')
    run_plotaif([f"./test/database/{outfile}"])


@pytest.mark.parametrize("mat_id, file", qnt_data)
def test_qnt_parser(mat_id, file):
    """Test Quantachrome Parser"""
    infile = Path(f"./test/database/{file}")
    testfile = infile.with_suffix(".aif_tst")
    run_raw2aif([infile, "quantachrome", mat_id])
    filecmp.cmp(infile, testfile, shallow=False)


@pytest.mark.parametrize("mat_id, file", qnt_data)
def test_qnt_output(mat_id, file):
    """Check Quantachrome output"""
    outfile = Path(file).with_suffix('.aif')
    run_plotaif([f"./test/database/{outfile}"])


@pytest.mark.parametrize("mat_id, file", mic_data)
def test_mic_parser(mat_id, file):
    """Test Micromeritics Parser"""
    infile = Path(f"./test/database/{file}")
    testfile = infile.with_suffix(".aif_tst")
    run_raw2aif([infile, "micromeritics", mat_id])
    filecmp.cmp(infile, testfile, shallow=False)


@pytest.mark.parametrize("mat_id, file", mic_data)
def test_mic_output(mat_id, file):
    """Check Micromeritics output"""
    outfile = Path(file).with_suffix('.aif')
    run_plotaif([f"./test/database/{outfile}"])


@pytest.mark.parametrize("mat_id, file", NIST_data)
def test_NISTjson_parser(mat_id, file):
    """Test NIST JSON Parser"""
    infile = Path(f"./test/database/{file}")
    testfile = infile.with_suffix(".aif_tst")
    run_raw2aif([infile, "NIST-json", mat_id])
    filecmp.cmp(infile, testfile, shallow=False)


@pytest.mark.parametrize("mat_id, file", NIST_data)
def test_NISTjson_output(mat_id, file):
    """Check NIST JSON Parser"""
    outfile = Path(file).with_suffix('.aif')
    run_plotaif([f"./test/database/{outfile}"])


def test_aif2NISTjson():
    """Test AIF to NIST JSON Parser"""
    jsonout = NISTjson.aif2json('examples/NK_DUT-6_LP_N2_114PKT.aif')
    try:
        json.loads(jsonout)
    except ValueError as e:
        raise ValueError('Error in AIF to JSON Conversion') from e
