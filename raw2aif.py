import sys
import os
from gemmi import cif


# parse input file
def parse(filetype, filename):
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
    return(data_meta, data_ads, data_des)

# write adsorption file
def makeAIF(data_meta, data_ads, data_des, material_id, filename):
    # initialize aif block
    d = cif.Document()
    d.add_new_block('data_raw2aifv006')

    block = d.sole_block()

    # write metadata
    if data_meta["user"] == '':
        block.set_pair('_exptl_operator', 'unknown')
    else:
        block.set_pair('_exptl_operator', "'"+data_meta["user"]+"'")
    block.set_pair('_exptl_date', data_meta["date"])
    if "apparatus" not in data_meta:
        block.set_pair('_exptl_instrument', 'unknown') 
    else:
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
            loop_des = block.init_loop('_desorp_', ['pressure', 'p0', 'amount'])
            loop_des.set_all_values([
                list(data_des['pressure'].astype(str)),
                list(data_des['pressure_saturation'].astype(str)),
                list(data_des['loading'].astype(str))
            ])

    elif len(list(data_meta['pressure_saturation'])) == 1:
        block.set_pair('_exptl_p0', str(data_meta["pressure_saturation"][0]))
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

    outputfilename = os.path.splitext(filename)[0]+'.aif'
    d.write_file(outputfilename)
    return

if __name__=="__main__":
    filename = sys.argv[1]
    filetype = sys.argv[2]
    material_id = sys.argv[3]

    data_meta, data_ads, data_des = parse(filetype,filename)
    makeAIF(data_meta, data_ads, data_des, material_id, filename)
