# Adsorption Information File
This repository contains the details of an universal file format for gas adsorption experiments.

## Core dictionary
The current dictionary of data items used by adsorption information files can be found below:

| data name | description |
| --- | --- |
| _exptl_operator | name of the person who ran the experiment (string) |
| _exptl_date | date and time of the experiment (date-time string representation)|
| _exptl_instrument | instrument id used for the experiment (string)    | 
| _exptl_adsorptive |  name of the adsorptive (string)    | 
| _exptl_temperature | temperature of the experiment (float)    | 
| _exptl_sample_mass | mass of the sample (float, gram)   | 
| _sample_id | unique identifying code used by the operator (string)  | 
| _sample_material_name | designated name for the material (string)   | 
| _adsorp_pressure | equilibrium pressure of the adsorption measurement (float, pascal)  | 
| _adsorp_p0 |  saturation pressure of the adsorption measurement at the temperature of the experiment(float, pascal)   | 
| _adsorp_amount  | amount adsorbed during the adsorption measurement (float, mol.kg<sup>-1</sup>)   | 
| _desorp_pressure | equilibrium  pressure of the desorption measurement at the temperature of the experiment (float, pascal)   | 
| _desorp_p0 | saturation pressure of the desorption measurement at the temperature of the experiment (float, pascal)   | 
| _desorp_amount |  amount adsorbed during the desorption measurement (float, mol.kg<sup>-1</sup>)   | 

## raw2aif converter
A simple program was produced for windows and mac computers to facilitate the production of adsorption information files from raw analysis text files exported by Quantachrome software (*.txt*) and the raw data files (*.DAT*) and CSV files exported by Belsorb software.

The current versions of these programs can be found on the [release page](https://github.com/jackevansadl/jubilant-waddle/releases),
of this repository.

## Citation
Jack D. Evans, Volodymyr Bon, Irena Senkovska, and Stefan Kaskel, *preprint*, **2021**, preprint.
  DOI: [10.26434/chemrxiv.13562798](https://dx.doi.org/10.26434/chemrxiv.13562798)
  