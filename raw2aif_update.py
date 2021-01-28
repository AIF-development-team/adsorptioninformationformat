from dateutil.parser import parse
import re
import sys

from gemmi import cif
import numpy as np

filename = sys.argv[1]
filetype = sys.argv[2]
material_id = sys.argv[3]

if filetype == "BELSORP-max":
    
    # load datafile
    from parsers import BEL
    data_meta, data_ads, data_des = BEL.isotherm_from_bel(filename)

    # write adsorption file

    # initialize aif block
    d = cif.Document()
    d.add_new_block('data_raw2aif')
    block = d.sole_block()
   
    # write metadata
    block.set_pair('_exptl_operator', data_meta["user"])
    block.set_pair('_exptl_date', data_meta["date"])
    block.set_pair('_exptl_instrument',  "'"+data_meta["apparatus"]+"'")
    block.set_pair('_exptl_adsorptive',  data_meta["adsorbate"])
    block.set_pair('_exptl_temperature', data_meta["temperature"])
    block.set_pair('_exptl_sample_mass', data_meta["mass"])


    block.set_pair('_sample_id', "'"+data_meta["comment1"]+"'")
    block.set_pair('_sample_material_id', material_id)

    block.set_pair('_units_mass', data_meta["adsorbent_unit"])
    block.set_pair('_units_mass', data_meta["temperature_unit"])
    block.set_pair('_units_pressure', data_meta["pressure_unit"])
    block.set_pair('_units_loading', str(data_meta["loading_unit"]+"/"+data_meta["adsorbent_unit"]))

    #write adsorption data
    loop_ads = block.init_loop('_adsorp_', ['pressure', 'p0', 'loading'])
    loop_ads.set_all_values([list(data_ads['pressure'].astype(str)), list(data_ads['saturation'].astype(str)), list(data_ads['loading'].astype(str))])
    
    # write desorption data
    loop_des = block.init_loop('_desorp_', ['pressure', 'p0', 'loading'])
    loop_des.set_all_values([list(data_des['pressure'].astype(str)), list(data_des['saturation'].astype(str)), list(data_des['loading'].astype(str))])


outputfilename = filename+".aif"
d.write_file(outputfilename)
