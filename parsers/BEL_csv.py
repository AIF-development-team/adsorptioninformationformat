from datetime import datetime
import dateutil.parser
import numpy as np
import pandas as pd

# for parsing csv files exported by BEL software (western text encoding)

def parse(path):
    with open(path, "r", encoding="ISO-8859-1") as fp:
        lines = fp.readlines()


    # get experimental and material parameters
    data_meta = {}
    columns = []
    data = []

    for index, line in enumerate(lines):
        if "COMMENT2" in line:
            operator = line.split(',')[-1]
            data_meta["user"] = operator.strip("\n")
        if "Date of measurement" in line:
            date = line.split(',')[-1]
            date = dateutil.parser.parse(date.split(':')[-1], yearfirst=True)
            data_meta["date"] = date.isoformat()
        if "Serial number" in line:
            instrument = line.split(',')[-1]
            data_meta["apparatus"] = instrument.strip("\n")
        if "Adsorptive," in line:
            adsorptive = line.split(',')[-1]
            data_meta["adsorbate"] = adsorptive.strip("\n")
        if "Adsorption temperature" in line:
            temperature = float(line.split(',')[1])
            data_meta["temperature"] = temperature
            data_meta["temperature_unit"] = line.split(',')[-1].strip("[]\n")
        if "Sample weight" in line:
            sample_mass = float(line.split(',')[1])
            data_meta["mass"] = sample_mass
            data_meta["adsorbent_unit"] = line.split(',')[-1].strip("[]\n")
        if "COMMENT1" in line:
            sample_id = line.split(',')[-1]
            data_meta["sample_id"] = sample_id.strip("\n")

        if line.startswith("No,"):
            for column in line.split(','):
                columns.append(column.split('/')[0].strip("\n"))
                if column.startswith("pe"):
                    data_meta["pressure_unit"] = column.split("/")[-1]
                if column.startswith("Va"):
                    data_meta["loading_unit"] = column.split("/")[-1].strip("\n")
        
       
        if line.startswith("ADS"):
            ads_start = index+1

    # get the adsorption data
    for index, line in enumerate(lines):
        if index >= ads_start:
            if line.split(',')[0] != "DES\n":
                if int(line.split(',')[0]) > 0:
                    if index >= ads_start:
                        data.append(line.split(','))

    # create pandas dataframe of adsorption data
    data = np.array(data,dtype=float)
    df = pd.DataFrame(data, columns=columns)

    # split ads / desorption branches
    turning_point = df["pe"].argmax()+1
    # santize vital column names for use with raw2aif
    df.columns = df.columns.str.replace('pe','pressure')
    df.columns = df.columns.str.replace('Va','loading')
    df.columns = df.columns.str.replace('p0','pressure_saturation')
    return data_meta, df[:turning_point], df[turning_point:]
