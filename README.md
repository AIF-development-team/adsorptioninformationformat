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
| _sample_id | unique identifying code used by the operator (string)  | 
| _sample_material_id | designated name for the material (string)   | 
| _units_temperature | units of temperature (string)  | 
| _units_pressure | units of pressure (string)   | 
| _units_mass | units of mass (string)  | 
| _units_loading | units of amount adsorbed (string)   | 
| _adsorp_pressure | equilibrium pressure of the adsorption measurement (float)  | 
| _adsorp_p0 |  saturation pressure of the adsorption measurement at the temperature of the experiment(float)   | 
| _adsorp_loading  | amount adsorbed during the adsorption measurement (float)   | 
| _desorp_pressure | equilibrium  pressure of the desorption measurement at the temperature of the experiment (float)   | 
| _desorp_p0 | saturation pressure of the desorption measurement at the temperature of the experiment (float)   | 
| _desorp_loading |  amount adsorbed during the desorption measurement (float)   | 

## raw2aif converter
A simple program was produced for windows computers to facilitate the production of adsorption information files from raw analysis text files exported by Quantachrome software (*.txt*) and the Belsorb software raw data files (*.DAT*) and xls files exported by Micromeritics software (*.xls*).

The current versions of this program can be found on the [release page](https://github.com/jackevansadl/adsorptioninformationformat/releases),
of this repository.

## Citation
Jack D. Evans, Volodymyr Bon, Irena Senkovska, and Stefan Kaskel, *preprint*, **2021**, preprint.
  DOI: [10.26434/chemrxiv.13562798](https://dx.doi.org/10.26434/chemrxiv.13562798)
  
