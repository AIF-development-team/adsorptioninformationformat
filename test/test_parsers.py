# -*- coding: utf-8 -*-
# pylint: disable-msg=invalid-name # to allow non-conforming variable names
"""
Test all parsers for all manufacturers
"""

import filecmp
import difflib
import json
import sys
from pathlib import Path

import pytest

from parsers import NISTjson
from .conftest import (BELcsv_data, BELcsv_JIS_data, NIST_data, bel_data, mic_data, qnt_data)


def run_raw2aif(args):
    from raw2aif import main as raw2aif_main
    sys.argv = ["raw2aif.py"] + args
    raw2aif_main()


def run_plotaif(args):
    from plotaif import main as plotaif_main
    sys.argv = ["plotaif.py"] + args
    plotaif_main()


def general_parser(mat_id, file, ftype):
    infile = Path(f"./test/database/{file}")
    outfile = infile.with_suffix(".aif")
    testfile = infile.with_suffix(".aif_tst")
    run_raw2aif([infile, ftype, mat_id])
    if not filecmp.cmp(outfile, testfile, shallow=False):
        with open(outfile) as f, open(testfile) as g:
            flines = f.readlines()
            glines = g.readlines()
        d = difflib.Differ()
        diffs = [x for x in d.compare(flines, glines) if x[0] in ('+', '-')]
        if diffs:
            # all rows with changes
            print("\n".join(diffs))
        else:
            print('No changes')
        assert False  # two files are not the same, check print for difference


@pytest.mark.parametrize("mat_id, file", bel_data)
def test_bel_parser(mat_id, file):
    """Test BEL Parser"""
    general_parser(mat_id, file, "BELSORP-max")


@pytest.mark.parametrize("mat_id, file", bel_data)
def test_bel_output(mat_id, file):
    """Check BEL output"""
    outfile = Path(file).with_suffix('.aif')
    run_plotaif([f"./test/database/{outfile}"])


@pytest.mark.parametrize("mat_id, file", BELcsv_data)
def test_BELcsv_parser(mat_id, file):
    """Test BEL CSV Parser"""
    general_parser(mat_id, file, "BEL-csv")


@pytest.mark.parametrize("mat_id, file", BELcsv_data)
def test_BELcsv_output(mat_id, file):
    """Check BEL CSV output"""
    outfile = Path(file).with_suffix('.aif')
    run_plotaif([f"./test/database/{outfile}"])


@pytest.mark.parametrize("mat_id, file", BELcsv_JIS_data)
def test_BELcsv_JIS_parser(mat_id, file):
    """Test BEL CSV Parser (Japanese)"""
    general_parser(mat_id, file, "BEL-csv_JIS")


@pytest.mark.parametrize("mat_id, file", BELcsv_JIS_data)
def test_BELcsv_JIS_output(mat_id, file):
    """Check BEL CSV output (Japanese)"""
    outfile = Path(file).with_suffix('.aif')
    run_plotaif([f"./test/database/{outfile}"])


@pytest.mark.parametrize("mat_id, file", qnt_data)
def test_qnt_parser(mat_id, file):
    """Test Quantachrome Parser"""
    general_parser(mat_id, file, "quantachrome")


@pytest.mark.parametrize("mat_id, file", qnt_data)
def test_qnt_output(mat_id, file):
    """Check Quantachrome output"""
    outfile = Path(file).with_suffix('.aif')
    run_plotaif([f"./test/database/{outfile}"])


@pytest.mark.parametrize("mat_id, file", mic_data)
def test_mic_parser(mat_id, file):
    """Test Micromeritics Parser"""
    general_parser(mat_id, file, "micromeritics")


@pytest.mark.parametrize("mat_id, file", mic_data)
def test_mic_output(mat_id, file):
    """Check Micromeritics output"""
    outfile = Path(file).with_suffix('.aif')
    run_plotaif([f"./test/database/{outfile}"])


@pytest.mark.parametrize("mat_id, file", NIST_data)
def test_NISTjson_parser(mat_id, file):
    """Test NIST JSON Parser"""
    general_parser(mat_id, file, "NIST-json")


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
