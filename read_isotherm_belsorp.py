import numpy as np
import sys
from dateutil.parser import parse

filename = 'database/DUT-67/DUT67_1_Garching_acetone_298K.DAT'
filetype = "BELSORP-max"
material_id = "DUT-67"

if filetype == "BELSORP-max":

    # load datafile
    with open(filename, "r", encoding="ISO-8859-1") as fp:
        lines = fp.readlines()


    # get experimental and material parameters

    for index, line in enumerate(lines):
        if "Comment2" in line:
            operator = line.split()[1][1:-1]
        if "Date of measurement" in line:
            date = line.split()[-1]
            date = parse(date.split(':')[-1])
        if "Instrument S/N" in line:
            instrument = line.split()[-1]
            instrument = "BELSORP-max-"+str(instrument)
        if "Adsorptive" in line:
            adsorptive = line.split()[-1]
        if "Meas. Temp./K" in line:
            temperature = float(line.split()[-1])
        if "Sample weight/g" in line:
            sample_mass = float(line.split()[-1])
        if "Comment1" in line:
            sample_id = line.split()[-1]
            sample_id = sample_id[1:-1]

        if "Adsorption data" in line:
            ads_start = (index+3)
        if "Desorption data" in line:
            des_start = (index+3)

    # # get the adsorption data

    raw_press = []
    raw_p0 = []
    raw_vol = []
    for index, line in enumerate(lines):
        try:
            if int(line.split()[0]) > 0:
                if index >= ads_start:
                    raw_press.append(float(line.split()[1]))
                    raw_p0.append(float(line.split()[2]))
                    raw_vol.append(float(line.split()[-1]))
                if index >= des_start:
                    raw_press.append(float(line.split()[1]))
                    raw_p0.append(float(line.split()[2]))
                    raw_vol.append(float(line.split()[-1]))
        except:
            pass


    # change units to standard units

    # pressure from kPa to Pa
    raw_press = np.array(raw_press)*1000
    raw_p0 = np.array(raw_p0)*1000

    # amount adsorbed from mL/g to mmol/g
    raw_vol = np.array(raw_vol)/22.414

    print(raw_press)

    # split ads / desorption branches

    turning_point = np.argmax(raw_press)

    ads_press = raw_press[:turning_point+1]
    des_press = raw_press[turning_point+1:]

    ads_p0 = raw_p0[:turning_point+1]
    des_p0 = raw_p0[turning_point+1:]

    ads_vol = raw_vol[:turning_point+1]
    des_vol = raw_vol[turning_point+1:]


    # write adsorption file
    from collections import OrderedDict
    from pymatgen.io.cif import CifBlock
    from pymatgen.io.cif import CifFile
    from monty.io import zopen

    block = OrderedDict()
    loops = []

    block["_operator"] = operator
    block["_date"] = date
    block["_instrument"] = instrument
    block["_adsorptive"] = adsorptive
    block["_temperature"] = temperature
    block["_sample_mass"] = sample_mass
    block["_sample_id"] = sample_id
    block["_material_id"] = material_id

    block["_adsorption_pressure"] = ads_press
    block["_adsorption_p0"] = ads_p0
    block["_adsorption_amount"] = ads_vol

    loops.append(["_adsorption_pressure", "_adsorption_p0", "_adsorption_amount"])


    block["_desorption_pressure"] = des_press
    block["_desorption_p0"] = des_p0
    block["_desorption_amount"] = des_vol

    loops.append(["_desorption_pressure", "_desorption_p0", "_desorption_amount"])

    d = OrderedDict()
    header = "raw2ciftest"
    d[header] = CifBlock(block, loops, header)
    out = CifFile(d)

    with zopen(str(sample_id)+'.aif', "wt") as f:
        f.write(out.__str__())
