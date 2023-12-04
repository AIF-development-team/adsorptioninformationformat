# -*- coding: utf-8 -*-
"""
Parse BEL CSV to AIF
Handles both western and JIS encoded text
"""
# pylint: disable-msg=invalid-name # to allow non-conforming variable names
# pylint: disable-msg=too-many-locals
# pylint: disable-msg=too-many-branches
# pylint: disable-msg=too-many-statements
import dateutil.parser
import numpy as np
import pandas as pd

# for parsing csv files exported by BEL software
# uses internal dictionary to read both JIS and western text encoding

_BEL_DICT = {
    'operator': {
        'ENG': 'COMMENT2',
        'JPN': 'コメント２'
    },
    'date': {
        'ENG': 'Date of measurement',
        'JPN': '測定日'
    },
    'serialnumber': {
        'ENG': 'Serial number',
        'JPN': 'シリアルナンバー'
    },
    's/n': {
        'ENG': 'S/N',
        'JPN': 'シリアルナンバー'
    },
    'adsorptive': {
        'ENG': 'Adsorptive,',
        'JPN': '吸着質名称'
    },
    'temperature': {
        'ENG': 'Adsorption temperature',
        'JPN': '吸着温度'
    },
    'sample_mass': {
        'ENG': 'Sample weight',
        'JPN': 'サンプル質量'
    },
    'sample_id': {
        'ENG': 'COMMENT1',
        'JPN': 'コメント１'
    }
}


def parse(path, lang='ENG'):
    """
    Get the isotherm and sample data from a BEL Japan .csv file.
    Parameters
    ----------
    path : str
        Path to the file to be read.
    Returns
    -------
    dataDF
    """

    # set encoding
    if lang == 'ENG':
        encoding = 'ISO-8859-1'
    else:
        encoding = 'shift_jis'

    with open(path, 'r', encoding=encoding) as fp:
        lines = fp.readlines()

    # get experimental and material parameters
    data_meta = {}
    columns = []
    data = []

    for index, line in enumerate(lines):
        if _BEL_DICT['operator'][lang] in line:
            operator = line.split(',')[-1]
            data_meta['user'] = operator.strip('\n')
        if _BEL_DICT['date'][lang] in line:
            date = line.split(',')[-1]
            date = dateutil.parser.parse(date.split(':')[-1], yearfirst=True)
            data_meta['date'] = date.isoformat()
        if _BEL_DICT['serialnumber'][lang] in line:
            instrument = line.split(',')[-1]
            data_meta['apparatus'] = 'BEL ' + instrument.strip('\n')
        if _BEL_DICT['s/n'][lang] in line:
            instrument = line.split(',')[-1]
            data_meta['apparatus'] = 'BEL ' + instrument.strip('\n')
        if _BEL_DICT['adsorptive'][lang] in line:
            adsorptive = line.split(',')[-1]
            data_meta['adsorbate'] = adsorptive.strip('\n')
        if _BEL_DICT['temperature'][lang] in line:
            temperature = float(line.split(',')[1])
            data_meta['temperature'] = temperature
            data_meta['temperature_unit'] = line.split(',')[-1].strip('[]\n')
        if _BEL_DICT['sample_mass'][lang] in line:
            sample_mass = float(line.split(',')[1])
            data_meta['mass'] = sample_mass
            data_meta['adsorbent_unit'] = line.split(',')[-1].strip('[]\n')
        if _BEL_DICT['sample_id'][lang] in line:
            sample_id = line.split(',')[-1]
            data_meta['sample_id'] = sample_id.strip('\n')

        if line.startswith('No,'):
            for column in line.split(','):
                columns.append(column.split('/')[0].strip('\n'))
                if column.startswith('pe'):
                    data_meta['pressure_unit'] = column.split('/')[-1]
                if column.startswith('Va'):
                    data_meta['loading_unit'] = column.split('/')[-1].strip(
                        '\n')

        if line.startswith('ADS'):
            ads_start = index + 1

    # get the adsorption data
    for index, line in enumerate(lines):
        if index >= ads_start:
            if line.split(',')[0] != 'DES\n':
                if int(line.split(',')[0]) > 0:
                    if index >= ads_start:
                        data.append(line.split(','))

    # create pandas dataframe of adsorption data
    data = np.array(data, dtype=float)
    df = pd.DataFrame(data, columns=columns)

    # split ads / desorption branches
    turning_point = df['pe'].argmax() + 1
    # santize vital column names for use with raw2aif
    df.columns = df.columns.str.replace('pe', 'pressure')
    df.columns = df.columns.str.replace('Va', 'loading')
    df.columns = df.columns.str.replace('p0', 'pressure_saturation')
    #if two or more loadings are present save the last column
    if isinstance(df['loading'], pd.DataFrame):
        df = df.loc[:, ~df.columns.duplicated(keep='last')]
    return data_meta, df[:turning_point], df[turning_point:]
