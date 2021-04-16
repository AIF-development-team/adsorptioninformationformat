# Adsorption Information File
This repository contains the details of an universal file format for gas adsorption experiments.

## Core dictionary
The current dictionary of data items used by adsorption information files can be found below:

| data name | description |
| --- | --- |
| _exptl_operator | name of the person who ran the experiment (string) |
| _exptl_date | date of the experiment (string in ISO 8601 format)|
| _exptl_instrument | instrument id used for the experiment (string)    | 
| _exptl_adsorptive |  name of the adsorptive (string)    | 
| _exptl_temperature | temperature of the experiment (float)    | 
| _exptl_sample_mass | mass of the sample (float)   | 
| _exptl_p0	| saturation pressure of the experiment at the temperature of the experiment (float) |
| _sample_id | unique identifying code used by the operator (string)  | 
| _sample_material_id | designated name for the material (string)   | 
| _units_temperature | units of temperature (string)  | 
| _units_pressure | units of pressure (string)   | 
| _units_mass | units of mass (string)  | 
| _units_loading | units of amount adsorbed (string)   | 
| _adsorp_pressure | equilibrium pressure of the adsorption measurement (float)  | 
| _adsorp_p0 |  saturation pressure of the adsorption measurement at the temperature of the experiment(float)   | 
| _adsorp_amount  | amount adsorbed during the adsorption measurement (float)   | 
| _desorp_pressure | equilibrium  pressure of the desorption measurement at the temperature of the experiment (float)   | 
| _desorp_p0 | saturation pressure of the desorption measurement at the temperature of the experiment (float)   | 
| _desorp_amount |  amount adsorbed during the desorption measurement (float)   | 

## raw2aif converter
A simple program was produced for windows computers to facilitate the production of adsorption information files from raw analysis text files exported by Quantachrome software (*.txt*) and the Belsorb software raw data files (*.DAT*) and xls files exported by Micromeritics software (*.xls*).

The current versions of this program can be found on the [release page](https://github.com/jackevansadl/adsorptioninformationformat/releases/tag/v0.0.4),
of this repository.

The steps to using this program is straightforward. Once opened browse to the location of an adsorption raw file.

![screenshot of home window](/screenshots/screenshot_1.png)

Then once you have located a raw data file and labelled a material ID press the *start* button to convert the data to AIF format.

![screenshot of home window with information filled in](/screenshots/screenshot_2.png)

The conversion is successful. From here you can restart the program to convert another file.

![screenshot of a successful conversion](/screenshots/screenshot_3.png)

If there are any errors please contact the Jack Evans with the data file that was unable to be converted.

## Citation
Jack D. Evans, Volodymyr Bon, Irena Senkovska, and Stefan Kaskel, *Langmuir*, **2021**.
[10.1021/acs.langmuir.1c00122](https://dx.doi.org/10.1021/acs.langmuir.1c00122)
  
