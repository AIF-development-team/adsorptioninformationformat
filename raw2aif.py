import numpy as np
import sys
from dateutil.parser import parse
import re

filename = sys.argv[1]
filetype = sys.argv[2]
material_id = sys.argv[3]

if filetype == "quantachrome":

    #load datafile
    with open(filename, "r", encoding="ISO-8859-1") as fp:
        lines = fp.readlines()

    # get experimental and material parameters

    for index,line in enumerate(lines):
        if "Operator" in line:
            operator = line.split()[1]
            if operator.split(":")[0] == "Date":
                operator = ' '
        if "Date" in line:
            date = []
            for index,element in enumerate(line.split()):
                if element.startswith('Date'):
                    date.append(line.split()[index])
            date = date[0]
            date = parse(date.split(':')[-1])
        if "Instrument" in line:
            for index,element in enumerate(line.split()):
                if element == "Instrument:":
                    instrument = line.split()[index+1]
        if "Analysis gas" in line:
            adsorptive = line.split()[2]
        if "Bath temp." in line:
            temperature = line.split()[-2]
        if "Sample Weight" in line:
            for index,element in enumerate(line.split()):
                if element == "Weight:":
                    sample_mass = float(line.split()[index+1])
        if "Sample ID:" in line:
            sample_id = line.split()[2]
            sample_id = sample_id.split("Filename")[0]

        if "Press" in line:
            ads_start = (index+4)
        
    # get the adsorption data

    raw_press = []
    raw_p0 = []
    raw_vol = []
    for index,line in enumerate(lines):
        if index >= ads_start:
            raw_press.append(float(line.split()[0]))
            raw_p0.append(float(line.split()[1]))
            raw_vol.append(float(line.split()[2]))


    # change units to standard units

    #pressure from Torr to Pa
    raw_press = np.array(raw_press)*133.3224
    raw_p0 = np.array(raw_p0)*133.3224

    # amount adsorbed from cc to mmol/g
    raw_vol = (np.array(raw_vol)/sample_mass)/22.414


    # split ads / desorption branches

    turning_point = np.argmax(raw_press)

    ads_press = raw_press[:turning_point+1]
    des_press = raw_press[turning_point+1:]

    ads_p0 = raw_p0[:turning_point+1]
    des_p0 = raw_p0[turning_point+1:]

    ads_vol = raw_vol[:turning_point+1]
    des_vol = raw_vol[turning_point+1:]


if filetype == "BELSORP-max":

    #load datafile
    with open(filename, "r", encoding="ISO-8859-1") as fp:
        lines = fp.readlines()


    # get experimental and material parameters

    for index,line in enumerate(lines):
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
    for index,line in enumerate(lines):
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

    #pressure from kPa to Pa
    raw_press = np.array(raw_press)*1000
    raw_p0 = np.array(raw_p0)*1000

    # amount adsorbed from mL/g to mmol/g
    raw_vol = np.array(raw_vol)/22.414

    # split ads / desorption branches

    turning_point = np.argmax(raw_press)

    ads_press = raw_press[:turning_point+1]
    des_press = raw_press[turning_point+1:]

    ads_p0 = raw_p0[:turning_point+1]
    des_p0 = raw_p0[turning_point+1:]

    ads_vol = raw_vol[:turning_point+1]
    des_vol = raw_vol[turning_point+1:]



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
        if "Adsorptive," in line:
            adsorptive = line.split(',')[-1]
        if "Adsorption temperature" in line:
            temperature = float(line.split(',')[1])
        if "Sample weight" in line:
            sample_mass = float(line.split(',')[1])
        if "COMMENT1" in line:
            sample_id = line.split(',')[-1]
            sample_id = sample_id.rstrip()

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


    # split ads / desorption branches

    turning_point = np.argmax(raw_press)

    ads_press = raw_press[:turning_point+1]
    des_press = raw_press[turning_point+1:]

    ads_p0 = raw_p0[:turning_point+1]
    des_p0 = raw_p0[turning_point+1:]

    ads_vol = raw_vol[:turning_point+1]
    des_vol = raw_vol[turning_point+1:]


#clean sampleid

sample_id = re.sub('[^a-zA-Z0-9-_*.]', '', sample_id)


# write adsorption file
from collections import OrderedDict
from pymatgen.io.cif import CifBlock
from pymatgen.io.cif import CifFile
from monty.io import zopen

block = OrderedDict()
loops = []

block["_exptl_operator"] = operator
block["_exptl_date"] = date
block["_exptl_instrument"] = instrument
block["_exptl_adsorptive"] = adsorptive
block["_exptl_temperature"] = temperature
block["_exptl_sample_mass"] = sample_mass
block["_sample_id"] = sample_id
block["_sample_material_id"] = material_id

block["_adsorp_pressure"] = ads_press
block["_adsorp_p0"] = ads_p0
block["_adsorp_amount"] = ads_vol

loops.append(["_adsorp_pressure","_adsorp_p0", "_adsorp_amount"])


block["_desorp_pressure"] = des_press
block["_desorp_p0"] = des_p0
block["_desorp_amount"] = des_vol

loops.append(["_desorp_pressure","_desorp_p0", "_desorp_amount"])

d = OrderedDict()
header = "raw2ciftest"
d[header] = CifBlock(block, loops,header)
out = CifFile(d)

with zopen(str(sample_id)+'.aif', "wt") as f:
    f.write(out.__str__())


