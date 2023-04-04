# -*- coding: utf-8 -*-
"""Convert raw file (format agnostic) to AIF"""
# pylint: disable-msg=invalid-name # to allow non-conforming variable names
# pylint: disable-msg=inconsistent-return-statements
import sys
import os
import json
from gemmi import cif  # pylint: disable-msg=no-name-in-module
from parsers import NISTjson
from adsorption_file_parser import read as afp_read
from parsers import aif_data_standardise


def quoted(text):
    return "'" + text + "'"


# parse input file
def parse(filetype, filename):
    """Fork to correct parser"""
    if filetype == 'BELSORP-max':
        meta, data = afp_read(path=filename, manufacturer='bel', fmt='dat')
    elif filetype == 'BEL-csv':
        meta, data = afp_read(path=filename, manufacturer='bel', fmt='csv', lang='ENG')
    elif filetype == 'BEL-csv_JIS':
        meta, data = afp_read(path=filename, manufacturer='bel', fmt='csv', lang='JPN')
    elif filetype == 'BELSORP-max_xl':
        meta, data = afp_read(path=filename, manufacturer='bel', fmt='xl')
    elif filetype == 'quantachrome':
        meta, data = afp_read(path=filename, manufacturer='qnt', fmt='txt-raw')
    elif filetype == 'micromeritics':
        meta, data = afp_read(path=filename, manufacturer='mic', fmt='xl')
    elif filetype == 'SMS DVS':
        meta, data = afp_read(path=filename, manufacturer='smsdvs', fmt='xlsx')
    elif filetype == 'NIST-json':
        with open(filename, 'r', encoding='utf-8') as json_file:
            json_dict = json.load(json_file)
        d = NISTjson.json2aif(json_dict)
        return d  # TODO make consistent with other parsers # pylint: disable-msg=fixme
    else:
        raise Exception('This file type is unknown or currently not supported.')

    data_meta, data_ads, data_des = aif_data_standardise(meta, data)
    return (data_meta, data_ads, data_des)


# write adsorption file
def makeAIF(data_meta, data_ads, data_des, material_id, filename):
    """Compose AIF dictionary and output to file"""
    # initialize aif block
    d = cif.Document()

    d.add_new_block('raw2aif')

    block = d.sole_block()

    # write metadata
    if not data_meta['operator'] or data_meta['operator'] == '':
        block.set_pair('_exptl_operator', quoted('unknown'))
    else:
        block.set_pair('_exptl_operator', quoted(data_meta['operator']))
    block.set_pair('_exptl_date', data_meta['date'])
    if 'apparatus' not in data_meta:
        block.set_pair('_exptl_instrument', 'unknown')
    else:
        block.set_pair('_exptl_instrument', quoted(data_meta['apparatus']))
    block.set_pair('_exptl_adsorptive', quoted(data_meta['adsorbate']))
    block.set_pair('_exptl_temperature', str(data_meta['temperature']))
    block.set_pair('_adsnt_sample_mass', str(data_meta['material_mass']))

    block.set_pair('_adsnt_sample_id', quoted(data_meta['material']))
    block.set_pair('_adsnt_material_id', quoted(material_id))

    block.set_pair('_units_temperature', quoted(data_meta['temperature_unit']))
    block.set_pair('_units_pressure', quoted(data_meta['pressure_unit']))
    block.set_pair('_units_mass', quoted(data_meta['material_unit']))
    block.set_pair('_units_loading', quoted(data_meta['loading_unit']))
    block.set_pair('_audit_aif_version', '2263286')

    #check if saturation pressure is for every point
    # TODO: what if none of these conditions are correct i.e. saturation_pressure is not given at all?
    if 'pressure_saturation' in data_ads:
        # write adsorption data
        loop_ads = block.init_loop('_adsorp_', ['pressure', 'p0', 'amount'])
        loop_ads.set_all_values([
            list(data_ads['pressure'].astype(str)),
            list(data_ads['pressure_saturation'].astype(str)),
            list(data_ads['loading'].astype(str))
        ])

        # write desorption data
        if len(data_des > 0):
            loop_des = block.init_loop('_desorp_', ['pressure', 'p0', 'amount'])
            loop_des.set_all_values([
                list(data_des['pressure'].astype(str)),
                list(data_des['pressure_saturation'].astype(str)),
                list(data_des['loading'].astype(str))
            ])

    # TODO: this branch can never be reached
    elif 'pressure_saturation' in data_ads and len(list(data_meta['pressure_saturation'])) == 1:
        block.set_pair('_exptl_p0', str(data_meta['pressure_saturation'][0]))
        # write adsorption data
        loop_ads = block.init_loop('_adsorp_', ['pressure', 'amount'])
        loop_ads.set_all_values([
            list(data_ads['pressure'].astype(str)),
            list(data_ads['loading'].astype(str))
        ])

        # write desorption data
        if len(data_des > 0):
            loop_des = block.init_loop('_desorp_', ['pressure', 'amount'])
            loop_des.set_all_values([
                list(data_des['pressure'].astype(str)),
                list(data_des['loading'].astype(str))
            ])

    elif 'pressure_saturation' not in data_ads and 'pressure_relative' in data_ads:
        # write adsorption data
        data_ads['pressure_saturation'] = (1 / data_ads['pressure_relative']) * data_ads['pressure']
        loop_ads = block.init_loop('_adsorp_', ['pressure', 'p0', 'amount'])
        loop_ads.set_all_values([
            list(data_ads['pressure'].astype(str)),
            list(data_ads['pressure_saturation'].astype(str)),
            list(data_ads['loading'].astype(str))
        ])

        # write desorption data
        if len(data_des > 0):
            data_des['pressure_saturation'] = (1 /
                                               data_des['pressure_relative']) * data_des['pressure']
            loop_des = block.init_loop('_desorp_', ['pressure', 'p0', 'amount'])
            loop_des.set_all_values([
                list(data_des['pressure'].astype(str)),
                list(data_des['pressure_saturation'].astype(str)),
                list(data_des['loading'].astype(str))
            ])

    else:
        # write adsorption data
        loop_ads = block.init_loop('_adsorp_', ['pressure', 'amount'])
        loop_ads.set_all_values([
            list(data_ads['pressure'].astype(str)),
            list(data_ads['loading'].astype(str))
        ])

        # write desorption data
        if len(data_des > 0):
            loop_des = block.init_loop('_desorp_', ['pressure', 'amount'])
            loop_des.set_all_values([
                list(data_des['pressure'].astype(str)),
                list(data_des['loading'].astype(str))
            ])

    outputfilename = os.path.splitext(filename)[0] + '.aif'
    d.write_file(outputfilename)


def main():
    filename_in = sys.argv[1]
    filetype_in = sys.argv[2]
    material_id_in = sys.argv[3]

    if filetype_in != 'NIST-json':
        data_meta_out, data_ads_out, data_des_out = parse(filetype_in, filename_in)
        makeAIF(data_meta_out, data_ads_out, data_des_out, material_id_in, filename_in)
    if filetype_in == 'NIST-json':
        cif_doc = parse(filetype_in, filename_in)
        filename_out = os.path.splitext(filename_in)[0] + '.aif'
        cif_doc.write_file(filename_out)


if __name__ == '__main__':
    main()