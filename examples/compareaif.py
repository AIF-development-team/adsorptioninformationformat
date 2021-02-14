import numpy as np
from gemmi import cif



aif = cif.read_file('database/DUT-6/NK_DUT-6_LP_N2_114PKT (Raw Analysis Data).aif')
block = aif.sole_block()
ads_press = np.array(block.find_loop('_adsorp_pressure'),dtype=float)
ads_p0 = np.array(block.find_loop('_adsorp_p0'),dtype=float)
ads_amount = np.array(block.find_loop('_adsorp_amount'),dtype=float)
des_press = np.array(block.find_loop('_desorp_pressure'),dtype=float)
des_p0 = np.array(block.find_loop('_desorp_p0'),dtype=float)
des_amount = np.array(block.find_loop('_desorp_amount'),dtype=float)


import matplotlib as mpl
import matplotlib.pyplot as plt

mpl.rcParams['pdf.fonttype'] = 42

plt.rcParams.update({'font.size': 6})

f, (ax1, ax2) = plt.subplots(1, 2, sharey=True, sharex=True)

f.tight_layout()
f.set_size_inches(3,2.2)

ax2.semilogx(ads_press/ads_p0,ads_amount, 'o', color='tab:blue', ms=5)
ax2.plot(des_press/des_p0,des_amount, 'o', markerfacecolor='white', color='tab:blue', ms=5)

digit_ads_press = np.genfromtxt("example/Default Dataset.csv", delimiter=',')[:,0]
digit_ads_amount = np.genfromtxt("example/Default Dataset.csv", delimiter=',')[:,1]

digit_des_press = np.genfromtxt("example/Default Dataset2.csv", delimiter=',')[:,0]
digit_des_amount = np.genfromtxt("example/Default Dataset2.csv", delimiter=',')[:,1]

#convert units
digit_ads_amount = digit_ads_amount/22.414
digit_des_amount = digit_des_amount/22.414

ax1.semilogx(digit_ads_press,digit_ads_amount , 'o', color='tab:orange', ms=5)
ax1.semilogx(digit_des_press,digit_des_amount , 'o', markerfacecolor='white', color='tab:orange', ms=5)

ax1.set_ylabel("amount adsorbed / mol$\,$kg$^{-1}$")
ax2.set_xlabel(r'relative pressure / $p/p_0$')

plt.savefig('example/exampleplot.pdf', dpi=600, bbox_inches='tight')