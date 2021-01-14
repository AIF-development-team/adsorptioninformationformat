import numpy as np
from dateutil.parser import parse
import re

import tkinter as tk
from tkinter import Tk, filedialog, Button, Label, mainloop, Radiobutton, Entry, Toplevel

# load tkinter
root = Tk()
root.title('raw2aif')

# define a browse file function
def browsefunc():
    global filename
    filename = filedialog.askopenfilename()
    pathlabel.config(text=filename)

# # for debuging
# def writetofile():
#     print(filename)
#     print(var.get())
#     print(matID.get())
#     outputfilename = filename+".aif"
#     print(outputfilename)


# covert txt files to aif
def convertAIF():
    filetype = var.get()
    material_id = matID.get()

    if filetype == "quantachrome":

        # load datafile
        with open(filename, "r", encoding="ISO-8859-1") as fp:
            lines = fp.readlines()

        # get experimental and material parameters

        for index, line in enumerate(lines):
            if "Operator" in line:
                operator = line.split()[1]
                if operator.split(":")[0] == "Date":
                    operator = ' '
            if "Date" in line:
                date = []
                for index, element in enumerate(line.split()):
                    if element.startswith('Date'):
                        date.append(line.split()[index])
                date = date[0]
                date = parse(date.split(':')[-1])
            if "Instrument" in line:
                for index, element in enumerate(line.split()):
                    if element == "Instrument:":
                        instrument = line.split()[index+1]
            if "Analysis gas" in line:
                adsorptive = line.split()[2]
            if "Bath temp." in line:
                temperature = line.split()[-2]
            if "Sample Weight" in line:
                for index, element in enumerate(line.split()):
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
        for index, line in enumerate(lines):
            if index >= ads_start:
                raw_press.append(float(line.split()[0]))
                raw_p0.append(float(line.split()[1]))
                raw_vol.append(float(line.split()[2]))


        # change units to standard units

        # pressure from Torr to Pa
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

        # load datafile
        with open(filename, "r", encoding="ISO-8859-1") as fp:
            lines = fp.readlines()


        # get experimental and material parameters

        for index, line in enumerate(lines):
            if "Comment2" in line:
                operator = line.split()[1][1:-1]
            if "Date of measurement" in line:
                date = line.split()[-1]
                date = parse(date.split(':')[-1], yearfirst=True)
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

        # split ads / desorption branches

        turning_point = np.argmax(raw_press)

        ads_press = raw_press[:turning_point+1]
        des_press = raw_press[turning_point+1:]

        ads_p0 = raw_p0[:turning_point+1]
        des_p0 = raw_p0[turning_point+1:]

        ads_vol = raw_vol[:turning_point+1]
        des_vol = raw_vol[turning_point+1:]



    if filetype == "BELSORP-max-csv":

        # load datafile
        with open(filename, "r", encoding="ISO-8859-1") as fp:
            lines = fp.readlines()


        # get experimental and material parameters

        for index, line in enumerate(lines):
            if "COMMENT2" in line:
                operator = line.split(',')[-1]
            if "Date of measurement" in line:
                date = line.split(',')[-1]
                date = parse(date.split(':')[-1], yearfirst=True)
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
        for index, line in enumerate(lines):
            if index >= ads_start:
                if line.split(',')[0] != "DES\n":
                    if int(line.split(',')[0]) > 0:
                        if index >= ads_start:
                            raw_press.append(float(line.split(',')[2]))
                            raw_p0.append(float(line.split(',')[3]))
                            raw_vol.append(float(line.split(',')[-1]))


        # change units to standard units

        # pressure from kPa to Pa
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


    # clean sampleid

    sample_id = re.sub('[^a-zA-Z0-9-_*.]', '', sample_id)


    # write adsorption file
    from gemmi import cif

    # initialize aif block
    d = cif.Document()
    d.add_new_block('data_raw2aif')
    block = d.sole_block()

    # write metadata
    block.set_pair('_exptl_operator', operator)
    block.set_pair('_exptl_date', str(date.date()))
    block.set_pair('_exptl_instrument', instrument)
    block.set_pair('_exptl_adsorptive', adsorptive)
    block.set_pair('_exptl_temperature', str(temperature))
    block.set_pair('_exptl_sample_mass', str(sample_mass))
    block.set_pair('_sample_id', sample_id)
    block.set_pair('_sample_material_id', material_id)

    # write adsorption data
    loop_ads = block.init_loop('_adsorp_', ['pressure', 'p0', 'amount'])
    loop_ads.set_all_values([list(ads_press.astype(str)), list(ads_p0.astype(str)), list(ads_vol.astype(str))])

    # write desorption data
    loop_des = block.init_loop('_desorp_', ['pressure', 'p0', 'amount'])
    loop_des.set_all_values([list(des_press.astype(str)), list(des_p0.astype(str)), list(des_vol.astype(str))])

    outputfilename = filename+".aif"
    d.write_file(outputfilename)

    # tkinter popup
    toplevel = Toplevel()
    popupmessage = "AIF file created"
    label = Label(toplevel, text=popupmessage, height=0, width=100)
    label.pack()
    toplevel.focus_force()


# gui details

browsebutton = Button(root, text="Browse", command=browsefunc)
browsebutton.pack()

pathlabel = Label(root)
pathlabel.pack()


var = tk.StringVar()
r1 = tk.Radiobutton(root, text='Quantachrome (.txt)', variable=var, value='quantachrome')
r1.pack()
r2 = tk.Radiobutton(root, text='BELSORP-max (.dat)', variable=var, value='BELSORP-max')
r2.pack()
r3 = tk.Radiobutton(root, text='BELSORP-max-csv (.csv)', variable=var, value='BELSORP-max-csv')
r3.pack()

matID = tk.StringVar()
inputVarName = Entry(root, textvariable=str(matID))
matID.set(str("material-ID"))
inputVarName.pack()

applyButton = Button(root, text="convert", command=convertAIF)
applyButton.pack()

mainloop()
