# -*- coding: utf-8 -*-
"""Parse NIST JSON to AIF"""
# pylint: disable-msg=invalid-name # to allow non-conforming variable names
#built from the suggestion of https://github.com/dwsideriusNIST described here https://github.com/dwsideriusNIST/adsorptioninformationformat/blob/sandbox/JSON_Sandbox/Example_AIF_and_JSON_Conversions.ipynb # pylint: disable-msg=line-too-long
import json
from gemmi import cif  # pylint: disable-msg=no-name-in-module
import numpy as np

#define some equivalency table

equivalency_table = [
    {
        'AIF': '_exptl_temperature',
        'JSON': 'temperature',
        'dtype': float
    },
    {
        'AIF': '_adsnt_material_id',
        'JSON': 'adsorbent',
        'dtype': str
    },
    {
        'AIF': '_citation_doi',
        'JSON': 'DOI',
        'dtype': str
    },
    {
        'AIF': '_citation_source',
        'JSON': 'articleSource',
        'dtype': str
    },
    {
        'AIF': '_exptl_digitizer',
        'JSON': 'digitizer',
        'dtype': str
    },
    {
        'AIF': '_units_loading',
        'JSON': 'adsorptionUnits',
        'dtype': str
    },
    {
        'AIF': '_units_pressure',
        'JSON': 'pressureUnits',
        'dtype': str
    },
    {
        'AIF': '_units_composition',
        'JSON': 'compositionType',
        'dtype': str
    },
    {
        'AIF': '_exptl_method"',
        'JSON': 'category',
        'dtype': str
    },
    {
        'AIF': '_exptl_adsorptive',
        'JSON': 'adsorbate',
        'dtype': str
    },
    {
        'AIF': '_exptl_sample_mass',
        'JSON': 'exptl_sample_mass',
        'dtype': float
    },
    #allow JSON arrays to be parsed
    {
        'AIF': 'adsorbates',
        'JSON': 'adsorbates',
        'dtype': float
    },
    #{'AIF': '', 'JSON': ''},
    #{'AIF': '', 'JSON': ''},

    # AIF Keys without JSON equivalents
    # _exptl_operator
    # _exptl_instrument
    # _exptl_date

    # JSON Keys without AIF equivalents
    # digitizer
]

#define how to cross reference


def crossreference_keys(table, key, informat):
    """
    Input syntax:
    table: list of cross-referenced AIF<->JSON equivalencies
    key: key to cross reference
    informat: format of input key, either AIF or JSON

    Output syntax:
    outformat: format of the output key (opposite the informat)
    Returns the outformat value of the informat key

    If the informat key is not in the equivalency table, the
    script uses a fallback handler:
       JSON key "inkey" -> AIF key "_inkey"
       AIF key "_inkey" -> JSON key "inkey"
    """

    if informat == 'AIF':
        outformat = 'JSON'
    elif informat == 'JSON':
        outformat = 'AIF'
    else:
        raise AssertionError('Unknown informat: ' + informat)

    # Cross reference the input format against the list
    #  IS THERE A BETTER WAY TO DO THIS???
    tmp_list = [x[informat] for x in table]
    if key in tmp_list:
        index = tmp_list.index(key)
        #print(table[index])
        return table[index][outformat], table[index]['dtype']

    # Handler for unknown keys:
    if informat == 'AIF':
        #strip leading "_"
        return key[1:], str
    # will be JSON, add leading "_"
    return '_unsupported_' + key, str


def aif2json(infile):
    """Convert AIF to JSON"""
    data = cif.read(infile).sole_block()

    data_dict = {}

    # wrapper for metadata
    for item in data:
        if item.pair is not None:
            #print('a', item.pair)
            inkey = item.pair[0]
            outkey, dtype = crossreference_keys(equivalency_table,
                                                inkey,
                                                informat='AIF')
            if dtype == float:
                data_dict[outkey] = float(item.pair[-1])
            elif dtype == str:
                data_dict[outkey] = str(item.pair[-1])
            elif dtype == int:
                data_dict[outkey] = int(item.pair[-1])

    # wrapper for isotherm loop
    isotherm_data = []
    ads_press = np.array(data.find_loop('_adsorp_pressure'), dtype=float)
    ads_amount = np.array(data.find_loop('_adsorp_amount'), dtype=float)
    try:
        ads_p0 = np.array(data.find_loop('_adsorp_p0'), dtype=float)
        output_p0 = True
    except ValueError:
        output_p0 = False

    # single component only
    for p, a in zip(ads_press, ads_amount):
        isotherm_data.append({
            'pressure':
            p,
            'branch':
            'adsorp',
            'species_data': [{
                'name': data_dict['adsorbate'],
                'composition': 1.0,
                'adsorption': a
            }]
        })
        if output_p0:
            pindex = np.where(ads_press == p)
            isotherm_data[-1]['p0'] = ads_p0[pindex][0]
    data_dict['isotherm_data'] = isotherm_data

    return json.dumps(data_dict, indent=4)


def json2aif(json_dict):
    """Convert NIST json_dict to AIF"""
    # pylint: disable-msg=too-many-branches
    # initialize aif block
    d = cif.Document()
    d.add_new_block(json_dict['filename'])  #fix this

    block = d.sole_block()

    for inkey in json_dict:
        if inkey != 'isotherm_data':
            outkey, _ = crossreference_keys(equivalency_table,
                                            inkey,
                                            informat='JSON')
            if json_dict[inkey] == '':
                #Ignore blank keys
                continue

            if '_unsupported_' in outkey:
                # ignore unknown datanames from JSON format?
                continue

            if inkey == 'adsorbates':
                # Temporary kludge for adsorptives
                if len(json_dict[inkey]) == 1:
                    outkey = '_exptl_adsorptive'
                    outstring = json_dict[inkey][0]['name']
                    block.set_pair(outkey, outstring)
                else:
                    raise ValueError(
                        'This script is only for pure component adsorption right now'
                    )
            elif isinstance(json_dict[inkey], (str, float, int)):
                block.set_pair(outkey, str(json_dict[inkey]))
            elif isinstance(json_dict[inkey], dict):
                # Temporary kludge for adsorbents
                if 'name' in json_dict[inkey]:
                    block.set_pair(outkey, str(json_dict[inkey]['name']))
                    block.set_pair('_adsnt_sample_id',
                                   str(json_dict[inkey]['hashkey']))
            else:
                print(inkey, json_dict[inkey], outkey)
                raise ValueError('Script unable to handle this key set')

    # Measurements
    #   Default to adsorption branch, state as desorption ONLY if specified
    pressure_adsorp = []
    amount_adsorp = []
    pressure_desorp = []
    amount_desorp = []
    for point in json_dict['isotherm_data']:
        if 'branch' in point:
            if point['branch'] == 'adsorp':
                pressure_adsorp.append(point['pressure'])
                amount_adsorp.append(point['species_data'][0]['adsorption'])
            elif point['branch'] == 'desorp':
                pressure_desorp.append(point['pressure'])
                amount_desorp.append(point['species_data'][0]['adsorption'])
            else:
                raise ValueError('ERROR: unknown branch type:',
                                 point['branch'])
        else:  #default=adsorp
            pressure_adsorp.append(point['pressure'])
            amount_adsorp.append(point['species_data'][0]['adsorption'])

    loop_ads = block.init_loop('_adsorp_', ['pressure', 'amount'])
    loop_ads.set_all_values([
        list(np.array(pressure_adsorp).astype(str)),
        list(np.array(amount_adsorp).astype(str))
    ])

    if len(pressure_desorp) != 0:
        loop_ads = block.init_loop('_desorp_', ['pressure', 'amount'])
        loop_ads.set_all_values([
            list(np.array(pressure_desorp).astype(str)),
            list(np.array(amount_desorp).astype(str))
        ])
    return d
