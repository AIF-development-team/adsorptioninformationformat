# -*- coding: utf-8 -*-
"""Convert raw file (format agnostic) to AIF"""
# pylint: disable-msg=invalid-name # to allow non-conforming variable names
# pylint: disable-msg=inconsistent-return-statements
import sys
import os
import json
from gemmi import cif  # pylint: disable-msg=no-name-in-module
from parsers import BEL, BEL_csv, quantachrome, micromeritics, NISTjson


# parse input file
def parse(filetype, filename):
    """Fork to correct parser"""
    if filetype == 'BELSORP-max':
        data_meta, data_ads, data_des = BEL.parse(filename)
    elif filetype == 'BEL-csv':
        data_meta, data_ads, data_des = BEL_csv.parse(filename, lang='ENG')
    elif filetype == 'BEL-csv_JIS':
        data_meta, data_ads, data_des = BEL_csv.parse(filename, lang='JPN')
    elif filetype == 'quantachrome':
        data_meta, data_ads, data_des = quantachrome.parse(filename)
    elif filetype == 'micromeritics':
        data_meta, data_ads, data_des = micromeritics.parse(filename)
    elif filetype == 'NIST-json':
        with open(filename, 'r', encoding='utf-8') as json_file:
            json_dict = json.load(json_file)
        d = NISTjson.json2aif(json_dict)
        return d  # TODO make consistent with other parsers # pylint: disable-msg=fixme
    else:
        raise Exception(
            'This file type is unknown or currently not supported.')
    if filetype != 'NIST-json':
        return (data_meta, data_ads, data_des)


# write adsorption file
def makeAIF(data_meta, data_ads, data_des, material_id, filename):
    """Compose AIF dictionary and output to file"""
    # initialize aif block
    d = cif.Document()
    d.add_new_block('raw2aif')

    block = d.sole_block()

    # write metadata
    if data_meta['user'] == '':
        block.set_pair('_exptl_operator', 'unknown')
    else:
        block.set_pair('_exptl_operator', "'" + data_meta['user'] + "'")
    block.set_pair('_exptl_date', data_meta['date'])
    if 'apparatus' not in data_meta:
        block.set_pair('_exptl_instrument', 'unknown')
    else:
        block.set_pair('_exptl_instrument', "'" + data_meta['apparatus'] + "'")
    block.set_pair('_exptl_adsorptive', data_meta['adsorbate'])
    block.set_pair('_exptl_temperature', str(data_meta['temperature']))
    block.set_pair('_adsnt_sample_mass', str(data_meta['mass']))

    block.set_pair('_adsnt_sample_id', "'" + data_meta['sample_id'] + "'")
    block.set_pair('_adsnt_material_id', "'" + material_id + "'")

    block.set_pair('_units_temperature', data_meta['temperature_unit'])
    block.set_pair('_units_pressure', data_meta['pressure_unit'])
    block.set_pair('_units_mass', data_meta['adsorbent_unit'])
    block.set_pair('_units_loading', "'" + data_meta['loading_unit'] + "'")
    block.set_pair('_audit_aif_version', 'd546195')

    #check if saturation pressure is for every point
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
            loop_des = block.init_loop('_desorp_',
                                       ['pressure', 'p0', 'amount'])
            loop_des.set_all_values([
                list(data_des['pressure'].astype(str)),
                list(data_des['pressure_saturation'].astype(str)),
                list(data_des['loading'].astype(str))
            ])

    elif 'pressure_saturation' in data_ads and len(
            list(data_meta['pressure_saturation'])) == 1:
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
        data_ads['pressure_saturation'] = (
            1 / data_ads['pressure_relative']) * data_ads['pressure']
        loop_ads = block.init_loop('_adsorp_', ['pressure', 'p0', 'amount'])
        loop_ads.set_all_values([
            list(data_ads['pressure'].astype(str)),
            list(data_ads['pressure_saturation'].astype(str)),
            list(data_ads['loading'].astype(str))
        ])

        # write desorption data
        if len(data_des > 0):
            data_des['pressure_saturation'] = (
                1 / data_des['pressure_relative']) * data_des['pressure']
            loop_des = block.init_loop('_desorp_',
                                       ['pressure', 'p0', 'amount'])
            loop_des.set_all_values([
                list(data_des['pressure'].astype(str)),
                list(data_des['pressure_saturation'].astype(str)),
                list(data_des['loading'].astype(str))
            ])

    outputfilename = os.path.splitext(filename)[0] + '.aif'
    d.write_file(outputfilename)


if __name__ == '__main__':
    filename_in = sys.argv[1]
    filetype_in = sys.argv[2]
    material_id_in = sys.argv[3]

    if filetype_in != 'NIST-json':
        data_meta_out, data_ads_out, data_des_out = parse(
            filetype_in, filename_in)
        makeAIF(data_meta_out, data_ads_out, data_des_out, material_id_in,
                filename_in)
    if filetype_in == 'NIST-json':
        cif_doc = parse(filetype_in, filename_in)
        filename_out = os.path.splitext(filename_in)[0] + '.aif'
        cif_doc.write_file(filename_out)
