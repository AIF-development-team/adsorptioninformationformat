from gemmi import cif
import matplotlib.pyplot as plt
import numpy as np
import sys

filename = sys.argv[1]

aif = cif.read(filename)
block = aif.sole_block()
ads_press = np.array(block.find_loop('_adsorp_pressure'), dtype=float)
ads_amount = np.array(block.find_loop('_adsorp_loading'), dtype=float)
des_press = np.array(block.find_loop('_desorp_pressure'), dtype=float)
des_amount = np.array(block.find_loop('_desorp_loading'), dtype=float)

material_id = block.find_pair('_sample_material_id')[-1]
print(material_id)

plt.plot(ads_press, ads_amount, 'o-')
plt.plot(des_press, des_amount, 'o-')
plt.show()
