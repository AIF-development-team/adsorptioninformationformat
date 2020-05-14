import numpy as np
from gemmi import cif

aif = cif.read_file('database/DUT-6/nk_DUT-6_LP_N2_114pkt.aif')
block = aif.sole_block()
ads_press = np.array(block.find_loop('_adsorption_pressure'),dtype=float)
ads_amount = np.array(block.find_loop('_adsorption_amount'),dtype=float)
des_press = np.array(block.find_loop('_desorption_pressure'),dtype=float)
des_amount = np.array(block.find_loop('_desorption_amount'),dtype=float)

material_id = block.find_pair('_material_id')[-1]
print(material_id)

import matplotlib.pyplot as plt

plt.semilogx(ads_press,ads_amount, 'o-')
plt.show()