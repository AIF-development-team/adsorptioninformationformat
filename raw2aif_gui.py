import sys
import os
from gemmi import cif

import numpy as np
from gooey import Gooey, GooeyParser
import argparse
from raw2aif import parse, makeAIF

def convert(filename, material_id, filetype):
    data_meta, data_ads, data_des = parse(filetype, filename)
    outputfilename = os.path.splitext(filename)[0]+'.aif'
    print (f'Writing output to {outputfilename}')
    makeAIF(data_meta, data_ads, data_des, material_id, filename)

@Gooey(required_cols=1, optional_cols=1, default_size = (300, 675),  
    menu=[{
        'name': 'Help',
        'items': [{
                'type': 'AboutDialog',
                'menuTitle': 'About',
                'name': 'RAW to AIF Converter',
                'description': 'A universal file format for gas adsorption experiments',
                'version': '0.0.5',
                'copyright': '2021',
                'website': 'https://github.com/jackevansadl/adsorptioninformationfile',
                'developer': '@jackevansadl, GUI + Compilation by @renkoh',
                'license': 'MIT License'
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