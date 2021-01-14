from gemmi import cif
import matplotlib.pyplot as plt
import numpy as np

aif = cif.read('database/Ar_test/1.DAT.aif')
block = aif.sole_block()
ads_press = np.array(block.find_loop('_adsorp_pressure'), dtype=float)
ads_amount = np.array(block.find_loop('_adsorp_amount'), dtype=float)
des_press = np.array(block.find_loop('_desorp_pressure'), dtype=float)
des_amount = np.array(block.find_loop('_desorp_amount'), dtype=float)

material_id = block.find_pair('_sample_material_id')[-1]
print(material_id)

plt.semilogx(ads_press, ads_amount, 'o-')
plt.show()
