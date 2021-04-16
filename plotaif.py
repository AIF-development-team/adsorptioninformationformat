from gemmi import cif
import matplotlib.pyplot as plt
import numpy as np
import sys
import os

filename = sys.argv[1]

aif = cif.read(filename)
block = aif.sole_block()
ads_press = np.array(block.find_loop('_adsorp_pressure'), dtype=float)
ads_amount = np.array(block.find_loop('_adsorp_amount'), dtype=float)
des_press = np.array(block.find_loop('_desorp_pressure'), dtype=float)
des_amount = np.array(block.find_loop('_desorp_amount'), dtype=float)

material_id = block.find_pair('_sample_material_id')[-1]

plt.plot(ads_press, ads_amount, 'o-', color="C0")
plt.plot(des_press, des_amount, 'o-', color="C0", markerfacecolor='white')

plt.ylabel("quantity adsorbed / "+block.find_pair('_units_loading')[-1])
plt.xlabel("pressure / "+block.find_pair('_units_pressure')[-1])
plt.title(block.find_pair('_exptl_adsorptive')[-1]+" on "+material_id+" at "+block.find_pair('_exptl_temperature')[-1]+"K")
plt.savefig(os.path.splitext(filename)[0]+'.pdf')
