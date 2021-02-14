import sys
import os
from gemmi import cif

import numpy as np
from gooey import Gooey, GooeyParser
import argparse

def convert(filename, material_id, filetype):
    if filetype == "BELSORP-max":
        from parsers import BEL
        data_meta, data_ads, data_des = BEL.parse(filename)
    elif filetype == "BEL-csv":
        from parsers import BEL_csv
        data_meta, data_ads, data_des = BEL_csv.parse(filename)
    elif filetype == "BEL-csv_JIS":
        from parsers import BEL_csv_JIS
        data_meta, data_ads, data_des = BEL_csv_JIS.parse(filename)
    elif filetype == "quantachrome":
        from parsers import quantachrome
        data_meta, data_ads, data_des = quantachrome.parse(filename)
    elif filetype == "micromeritics":
        from parsers import micromeritics
        data_meta, data_ads, data_des = micromeritics.parse(filename)
    else:
        raise Exception("This file type is unknown or currently not supported.")

    # write adsorption file

    # initialize aif block
    d = cif.Document()
    d.add_new_block('data_raw2aifv003')

    block = d.sole_block()

    # write metadata
    if data_meta["user"] == '':
        block.set_pair('_exptl_operator', 'unknown')
    else:
        block.set_pair('_exptl_operator', "'"+data_meta["user"]+"'")
    block.set_pair('_exptl_date', data_meta["date"])
    block.set_pair('_exptl_instrument', "'" + data_meta["apparatus"] + "'")
    block.set_pair('_exptl_adsorptive', data_meta["adsorbate"])
    block.set_pair('_exptl_temperature', str(data_meta["temperature"]))
    block.set_pair('_exptl_sample_mass', str(data_meta["mass"]))

    block.set_pair('_sample_id', "'" + data_meta["sample_id"] + "'")
    block.set_pair('_sample_material_id', "'" + material_id + "'")

    block.set_pair('_units_temperature', data_meta["temperature_unit"])
    block.set_pair('_units_pressure', data_meta["pressure_unit"])
    block.set_pair('_units_mass', data_meta["adsorbent_unit"])
    block.set_pair('_units_loading',"'"+data_meta["loading_unit"]+"'")

    # write adsorption data
    loop_ads = block.init_loop('_adsorp_', ['pressure', 'p0', 'loading'])
    loop_ads.set_all_values([
        list(data_ads['pressure'].astype(str)),
        list(data_ads['pressure_saturation'].astype(str)),
        list(data_ads['loading'].astype(str))
    ])

    # write desorption data
    if len(data_des > 0):
        loop_des = block.init_loop('_desorp_', ['pressure', 'p0', 'loading'])
        loop_des.set_all_values([
            list(data_des['pressure'].astype(str)),
            list(data_des['pressure_saturation'].astype(str)),
            list(data_des['loading'].astype(str))
        ])

    outputfilename = os.path.splitext(filename)[0]+'.aif'


    print (f'Writing output to {outputfilename}')
    
    d.write_file(outputfilename)

@Gooey(required_cols=1, optional_cols=1, default_size = (300, 600),  
    menu=[{
        'name': 'Help',
        'items': [{
                'type': 'AboutDialog',
                'menuTitle': 'About',
                'name': 'RAW to AIF Converter',
                'description': 'Towards a universal file format for gas adsorption experiments',
                'version': '0.0.3',
                'copyright': '2021',
                'website': 'https://github.com/jackevansadl/adsorptioninformationfile',
                'developer': '@jackevansadl, GUI + Compilation by @renkoh',
                'license': 'GNU GPLv3'
            }]
    }])

def main():
    parser = GooeyParser(description="raw2aif converter")

    group = parser.add_argument_group()
    group.add_argument('filename', widget='FileChooser')
    
    group.add_argument('material_id')

    input_type = group.add_mutually_exclusive_group(required=True, 
        gooey_options={
            'initial_selection': 0,
            'title': "filetype"
        })
    input_type.add_argument('-quantachrome', metavar='Quantachrome (.txt)', action="store_true")
    input_type.add_argument('-belsorp-max', metavar='BELSORP-max (.dat)', action="store_true")
    input_type.add_argument('-belsorp-csv', metavar='BEL-csv (.csv)', action="store_true")
    input_type.add_argument('-belsorp-csv-JIS', metavar='BEL-csv JIS encoding (.csv)', action="store_true")
    input_type.add_argument('-micromeritics', metavar='Micromeritics (.xls)', action="store_true")

    args = parser.parse_args()

    filetype = None

    if args.quantachrome:
        filetype = "quantachrome"
    elif args.belsorp_max:
        filetype = "BELSORP-max"
    elif args.belsorp_csv:
        filetype = "BEL-csv"
    elif args.belsorp_csv_JIS:
        filetype = "BEL-csv_JIS"
    elif args.micromeritics:
        filetype = "micromeritics"

    convert(args.filename, args.material_id, filetype)

main()