# -*- coding: utf-8 -*-
"""Parse BEL to AIF"""
# pylint: disable-msg=invalid-name # to allow non-conforming variable names
# pylint: disable-msg=use-a-generator
# pylint: disable-msg=too-many-branches
from datetime import datetime
import numpy as np
import pandas as pd

# from PyGAPS https://github.com/pauliacomi/pyGAPS/blob/develop/src/pygaps/parsing/bel.py
# Adapted from the work of https://github.com/pauliacomi

_FIELDS = {
    'material': {
        'text': ['comment1'],
        'name': 'sample_id',
    },
    'adsorbate': {
        'text': ['adsorptive'],
        'name': 'adsorbate',
    },
    'temperature': {
        'text': ['meas. temp'],
        'name': 'temperature',
    },
    'user': {
        'text': ['comment2'],
        'name': 'user',
    },
    'serialnumber': {
        'text': ['instrument'],
        'name': 'serialnumber',
    },
    'mass': {
        'text': ['sample weight'],
        'name': 'mass',
    },
    'exp_param1': {
        'text': ['comment3'],
        'name': 'exp_param1',
    },
    'exp_param2': {
        'text': ['comment4'],
        'name': 'exp_param2',
    },
    'date': {
        'text': ['date of measurement'],
        'name': 'date',
    },
    'time': {
        'text': ['time of measurement'],
        'name': 'time',
    },
    'cell_volume': {
        'text': ['vs/'],
        'name': 'cell_volume',
    },
    'isotherm_data': {
        'no.': 'measurement',
        'pe/': 'pressure',
        'p0/': 'pressure_saturation',
        'vd/': 'deadvolume',
        'v/': 'loading',
        'n/': 'loading',
    }
}


def parse(path):
    """
    Get the isotherm and sample data from a BEL Japan .dat file.
    Parameters
    ----------
    path : str
        Path to the file to be read.
    Returns
    -------
    dataDF
    """
    material_info = {}
    columns = []
    data_ads = []
    data_des = []

    with open(path) as file:
        line = file.readline().rstrip()
        while line:
            values = line.split('\t')
            line = file.readline().rstrip()

            if len(values) < 2:  # If "title" section
                if values[0].strip().lower().startswith('adsorption data'):
                    line = file.readline().rstrip()  # header
                    file_headers = line.replace('"', '').split('\t')

                    for h in file_headers:
                        txt = next((_FIELDS['isotherm_data'][a]
                                    for a in _FIELDS['isotherm_data']
                                    if h.lower().startswith(a)), h)
                        columns.append(txt)

                        if txt == 'loading':
                            material_info['loading_basis'] = 'molar'
                            material_info['loading_unit'] = h.split('/')[-1]

                        if txt == 'pressure':
                            material_info['pressure_mode'] = 'absolute'
                            material_info['pressure_unit'] = h.split('/')[-1]

                    # read adsorption section
                    line = file.readline()  # firstline
                    while not line.startswith('0'):
                        data_ads.append(list(map(float, line.split())))
                        line = file.readline()
                    data_ads = np.array(data_ads)

                elif values[0].strip().lower().startswith('desorption data'):
                    file.readline()  # header - discard
                    line = file.readline()  # firstline
                    while not line.startswith('0'):
                        data_des.append(list(map(float, line.split())))
                        line = file.readline()
                    data_des = np.array(data_des)

                else:
                    continue

            else:
                values = [v.strip('"') for v in values]
                key = values[0].lower()
                try:
                    # TODO: rewrite following using a generator # pylint: disable-msg=fixme
                    field = next(
                        v for k, v in _FIELDS.items()
                        if any([key.startswith(n) for n in v.get('text', [])]))
                except StopIteration:
                    continue
                material_info[field['name']] = values[1]
                # TODO better temperature unit handling # pylint: disable-msg=fixme
                if 'Meas. Temp./K:' in values:
                    material_info['temperature_unit'] = 'K'

                if 'Sample weight/g:' in values:
                    material_info['adsorbent_unit'] = 'g'

        material_info['date'] = datetime.strptime(material_info['date'],
                                                  r'%y/%m/%d').isoformat()
        material_info['apparatus'] = 'BEL ' + material_info['serialnumber']

        # create pandas dataframe of adsorption and desorption data
        data_ads = pd.DataFrame(data_ads, columns=columns)
        # exception if desorption is empty
        if len(data_des) > 0:
            data_des = pd.DataFrame(data_des, columns=columns)

        # TODO deal with units # pylint: disable-msg=fixme
        # pressure from Torr to Pa
        # amount adsorbed from mL/g to mmol/g
        # data_ads[columns.index('pressure')
        #          ] = data_ads[columns.index('pressure')] * 1e3
        # data_ads[columns.index('pressure_saturation')
        #          ] = data_ads[columns.index('pressure_saturation')] * 1e3
        # data_ads[columns.index('loading')
        #          ] = data_ads[columns.index('loading')] / 22.414

        # if len(data_des) > 0:
        #     data_des[columns.index('pressure')
        #              ] = data_des[columns.index('pressure')] * 1e3
        #     data_des[columns.index('pressure_saturation')
        #              ] = data_des[columns.index('pressure_saturation')] * 1e3
        #     data_des[columns.index('loading')
        #              ] = data_des[columns.index('loading')] / 22.414

        #alternatively lets define the units in the AIF file so that
        # we dont alter information from the raw data file
    return material_info, data_ads, data_des
