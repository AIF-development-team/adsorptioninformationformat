"""Parse Quantachrome output files."""

import numpy as np
import pandas as pd
import re
import dateutil.parser

_FIELDS = {
    'material': {
        'text': ['Sample ID'],
        'name': 'sample_id',
    },
    'adsorbate': {
        'text': ['Analysis gas'],
        'name': 'adsorbate',
    },
    'temperature': {
        'text': ['Bath temp.'],
        'name': 'temperature',
    },
    'user': {
        'text': ['Operator'],
        'name': 'user',
    },
    'apparatus': {
        'text': ['Instrument:'],
        'name': 'apparatus',
    },
    'mass': {
        'text': ['Sample Weight'],
        'name': 'mass',
    },
    'date': {
        'text': ['Date'],
        'name': 'date',
    },
    'sample_description': {
        'text': ['Sample Desc'],
        'name': 'sample_description',
    },
    'analysis_time': {
        'text': ['Analysis Time'],
        'name': 'analysis_time',
    },
    'comment': {
        'text': ['Comment'],
        'name': 'comment',
    },
    'time_outgas': {
        'text': ['Outgas Time'],
        'name': 'time_outgas',
    },
    'nonideality': {
        'text': ['Non-ideality'],
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

    # load datafile
    with open(path, "r", encoding="ISO-8859-1") as fp:
        lines = fp.readlines()

    # get experimental and material parameters

    material_info = {}
    columns = []
    raw_data = []

    for index, line in enumerate(lines):

        if any(
            v for k, v in _FIELDS.items()
            if any(t in line for t in v.get('text', []))
        ):
            data = re.split(r"\s{2,}|(?<=\D:)", line.strip())

            # TODO Are quantachrome files always saved with these mistakes?
            for i, d in enumerate(data):
                for mistake in ["Operator:", "Filename:", "Comment:"]:
                    if re.search(r"\w+" + mistake, d):
                        data[i] = d.split(mistake)[0]
                        data.insert(i + 1, mistake)

            for i, d in enumerate(data):
                name = next((
                    v.get('name', None)
                    for k, v in _FIELDS.items()
                    if any(t in d for t in v.get('text', []))
                ), None)
                if name not in material_info:
                    if not data[i + 1].endswith(":"):
                        material_info[name] = data[i + 1]
                    else:
                        material_info[name] = ' '

        if "Press" in line:
            ads_start = (index + 4)

    # get the adsorption data

    for index, line in enumerate(lines):

        #get column names

        if index == ads_start - 4:
            for col in re.split(r'\s{2,}', line):
                if col != '':
                    columns.append(col.strip("\n"))
        
        # get units
        elif index == ads_start - 2:
            material_info['pressure_unit'] = line.split()[0]
            material_info['loading_unit'] = line.split()[2]

        elif index >= ads_start:
            raw_data.append(list(map(float, line.split())))

    data = np.array(raw_data,dtype=float)
    df = pd.DataFrame(data, columns=columns)

    # change units to standard units
    material_info['adsorbent_unit'] = material_info['mass'].split()[-1]
    material_info['mass'] = float(material_info['mass'].split()[0])
    material_info['temperature_unit'] = material_info['temperature'].split()[-1]
    material_info['temperature'] = float(material_info['temperature'].split()[0])
   
    material_info['date'] = dateutil.parser.parse(material_info['date']
                                                  ).isoformat()


    # split ads / desorption branches
    turning_point = df["Press"].argmax()+1

    # santize vital column names for use with raw2aif
    df.columns = df.columns.str.replace('Press','pressure')
    df.columns = df.columns.str.replace('P0','pressure_saturation')
    df.columns = df.columns.str.replace('Volume @ STP','loading')

    return (
        material_info,
        df[:turning_point],
        df[turning_point:]
    )