# -*- coding: utf-8 -*-
"""Parse Quantachrome output files."""
# pylint: disable-msg=invalid-name # to allow non-conforming variable names
import re

import dateutil.parser
import numpy as np
import pandas as pd

_FIELDS = {
    'material': {
        'text': ['sample id'],
        'name': 'sample_id',
    },
    'adsorbate': {
        'text': ['analysis gas'],
        'name': 'adsorbate',
    },
    'temperature': {
        'text': ['bath temp'],
        'name': 'temperature',
    },
    'user': {
        'text': ['operator'],
        'name': 'user',
    },
    'apparatus': {
        'text': ['instrument:'],
        'name': 'apparatus',
    },
    'mass': {
        'text': ['sample weight'],
        'name': 'mass',
    },
    'date': {
        'text': ['date'],
        'name': 'date',
    },
    'sample_description': {
        'text': ['sample desc'],
        'name': 'sample_description',
    },
    'analysis_time': {
        'text': ['analysis time'],
        'name': 'analysis_time',
    },
    'comment': {
        'text': ['comment'],
        'name': 'comment',
    },
    'time_outgas': {
        'text': ['outgas time'],
        'name': 'time_outgas',
    },
    'nonideality': {
        'text': ['non-ideality'],
        'name': 'nonideality',
    },
    'isotherm_data': {
        'press': 'pressure',
        'p0': 'pressure_saturation',
        'volume': 'loading',
        'time': 'measurement_time',
        'tol': 'tolerance',
        'equ': 'equilibrium',
    }
}


def parse(path):
    """
    Get the isotherm and sample data from a Quantachrome File
    Parameters
    ----------
    path : str
        Path to the file to be read.
    Returns
    -------
    dataDF
    """
    # pylint: disable-msg=too-many-locals
    # pylint: disable-msg=too-many-branches
    # pylint: disable-msg=too-many-statements
    # load datafile
    with open(path, 'r', encoding='ISO-8859-1', errors='ignore') as fp:
        lines = fp.readlines()

    # get experimental and material parameters

    material_info = {}
    columns = []
    raw_data = []

    for index, line in enumerate(lines):
        # set to lower case as different versions of outfiles will have different cases in metadata
        line = line.lower()

        if any(v for k, v in _FIELDS.items() if any(t in line for t in v.get('text', []))):
            data = re.split(r'\s{2,}|(?<=\D:)', line.strip())

            # TODO Are quantachrome files always saved with these mistakes? # pylint: disable-msg=fixme
            for i, d in enumerate(data):
                for mistake in ['operator:', 'filename:', 'comment:']:
                    if re.search(r'\w+' + mistake, d):
                        data[i] = d.split(mistake)[0]
                        data.insert(i + 1, mistake)

            for i, d in enumerate(data):
                name = next((
                    v.get('name', None)
                    for k, v in _FIELDS.items()
                    if any(t in d for t in v.get('text', []))
                ), None)
                if name not in material_info:
                    if not data[i + 1].endswith(':'):
                        material_info[name] = data[i + 1]
                    else:
                        material_info[name] = ' '

        ads_start = 0
        if 'press' in line:
            ads_start = index + 4
        elif 'p/po' in line:
            ads_start = index + 4
    # get the adsorption data

    for index, line in enumerate(lines):

        #get column names

        if index == ads_start - 4:
            for col in re.split(r'\s{2,}', line):
                if col != '':
                    columns.append(col.strip('\n'))

        # get units
        elif index == ads_start - 2:
            if len(line.split()) == 2:
                material_info['pressure_unit'] = line.split()[0]
                material_info['loading_unit'] = line.split()[1]
            else:
                material_info['pressure_unit'] = line.split()[0]
                material_info['loading_unit'] = line.split()[2]

        elif index >= ads_start:
            raw_data.append(list(map(float, line.split())))

    data = np.array(raw_data, dtype=float)
    df = pd.DataFrame(data, columns=columns)

    # get units
    material_info['adsorbent_unit'] = material_info['mass'].split()[-1]
    material_info['mass'] = float(material_info['mass'].split()[0])
    material_info['temperature_unit'] = material_info['temperature'].split(
    )[-1]
    material_info['temperature'] = float(
        material_info['temperature'].split()[0])

    material_info['date'] = dateutil.parser.parse(
        material_info['date']).isoformat()

    if 'Press' in df.columns:
        df.columns = df.columns.str.replace('Press', 'pressure')
    elif 'P/Po' in df.columns:
        df['pressure'] = df['P/Po'] * df['Po']

    # split ads / desorption branches
    turning_point = df['pressure'].argmax() + 1

    # santize vital column names for use with raw2aif
    if 'P0' in df.columns:
        df.columns = df.columns.str.replace('P0', 'pressure_saturation')
    elif 'Po' in df.columns:
        df.columns = df.columns.str.replace('Po', 'pressure_saturation')
    df.columns = df.columns.str.replace('Volume @ STP', 'loading')

    return (material_info, df[:turning_point], df[turning_point:])
