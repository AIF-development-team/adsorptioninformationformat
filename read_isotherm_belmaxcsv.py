import numpy as np
import sys
from dateutil.parser import parse

filename = 'database/DUT-32/RGE-343-DUT32-7dCO2_Nitrogen (BelMax).csv'
filetype = "BELSORP-max-csv"
material_id = "DUT-32"

if filetype == "BELSORP-max-csv":

    #load datafile
    with open(filename, "r", encoding="ISO-8859-1") as fp:
        lines = fp.readlines()


    # get experimental and material parameters

    for index,line in enumerate(lines):
        if "COMMENT2" in line:
            operator = line.split(',')[-1]
        if "Date of measurement" in line:
            date = line.split(',')[-1]
            date = parse(date.split(':')[-1])
        if "Serial number" in line:
            instrument = line.split(',')[-1]
            instrument = "BELSORP-max-"+str(instrument)
        if "Adsorptive" in line:
            adsorptive = line.split(',')[-1]
        if "Adsorption temperature" in line:
            temperature = float(line.split(',')[1])
        if "Sample weight" in line:
            sample_mass = float(line.split(',')[1])
        if "COMMENT1" in line:
            sample_id = line.split(',')[-1]

        if "ADS" in line:
            ads_start = index+1
 
    # # get the adsorption data

    raw_press = []
    raw_p0 = []
    raw_vol = []
    for index,line in enumerate(lines):
        if index >= ads_start:
            if line.split(',')[0] != "DES\n":
                if int(line.split(',')[0]) > 0:
                    if index >= ads_start:
                        raw_press.append(float(line.split(',')[2]))
                        raw_p0.append(float(line.split(',')[3]))
                        raw_vol.append(float(line.split(',')[-1]))


    # change units to standard units

    #pressure from kPa to Pa
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


    # # write adsorption file
    # from collections import OrderedDict
    # from pymatgen.io.cif import CifBlock
    # from pymatgen.io.cif import CifFile
    # from monty.io import zopen

    # block = OrderedDict()
    # loops = []

    # block["_operator"] = operator
    # block["_date"] = date
    # block["_instrument"] = instrument
    # block["_adsorptive"] = adsorptive
    # block["_temperature"] = temperature
    # block["_sample_mass"] = sample_mass
    # block["_sample_id"] = sample_id
    # block["_material_id"] = material_id

    # block["_adsorption_pressure"] = ads_press
    # block["_adsorption_p0"] = ads_p0
    # block["_adsorption_amount"] = ads_vol

    # loops.append(["_adsorption_pressure","_adsorption_p0", "_adsorption_amount"])


    # block["_desorption_pressure"] = des_press
    # block["_desorption_p0"] = des_p0
    # block["_desorption_amount"] = des_vol

    # loops.append(["_desorption_pressure","_desorption_p0", "_desorption_amount"])

    # d = OrderedDict()
    # header = "raw2ciftest"
    # d[header] = CifBlock(block, loops,header)
    # out = CifFile(d)

    # with zopen(str(sample_id)+'.aif', "wt") as f:
    #     f.write(out.__str__())

