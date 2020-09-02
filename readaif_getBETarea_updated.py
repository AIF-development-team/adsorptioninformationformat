import numpy as np
from gemmi import cif

aif = cif.read_file('database/DUT-75/US_540_DUT75_N2.aif')
block = aif.sole_block()
ads_press = np.array(block.find_loop('_adsorption_pressure'),dtype=float)
ads_amount = np.array(block.find_loop('_adsorption_amount'),dtype=float)
des_press = np.array(block.find_loop('_desorption_pressure'),dtype=float)
des_amount = np.array(block.find_loop('_desorption_amount'),dtype=float)

material_id = block.find_pair('_material_id')[-1]
material_mass = block.find_pair('_sample_mass')[-1]
print(material_id)

#convert to mol/g from cm3/g
ads_amount=ads_amount*0.001
#ads_amount = ads_amount / 4.5e-3
# ads_amount = ads_amount*float(material_mass)
# ads_amount = ads_amount*1e-6


#n2 properties
p0 = 101860.98004799998
ads_cross = 0.162

pp0=ads_press/p0

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from scipy.stats import linregress

def rolling_window(a, window):
    shape = a.shape[:-1] + (a.shape[-1] - window + 1, window)
    strides = a.strides + (a.strides[-1],)
    return np.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)


def BETanalysis(pp0, ads):
    
    #N2 properties
    ads_cross = 0.162

    #roq consistency criteria
    roq_consistency = ads_amount*(1-pp0)

    #set limits until maximum
    lo_limit = 0
    hi_limit= np.argmax(roq_consistency)

    #transform to limits
    pp0_limited =  pp0[lo_limit+1:hi_limit]
    roq_consistency_limited = roq_consistency[lo_limit+1:hi_limit]

    #compute BET equation
    BETeq = pp0_limited/roq_consistency_limited

    #separate into 3-point windowss
    BETeq_window = rolling_window(BETeq,3)
    pp0_window = rolling_window(pp0_limited,3)

    #get slope and BET parameters
    output = []
    for window in range(len(BETeq_window)):
        c=[]
        slope=[]
        intercept=[]
        fit = linregress(pp0_window[window],BETeq_window[window])
        slope = fit[0]
        intercept = fit[1]
        r2 = fit[2]
        c = 1+(slope/intercept)
        if c > 0 and r2>0.995 and intercept > 0:
            n_monolayer = 1/(intercept * c)
            pp0_monolayer = 1/(np.sqrt(c) + 1)
            BET_area = n_monolayer * ads_cross * (10**(-18)) * 6.022E23
            output.append([c,n_monolayer,BET_area,pp0_monolayer,np.min(pp0_window[window]),np.max(pp0_window[window]),np.mean(pp0_window[window]),r2, np.abs(pp0_monolayer-np.mean(pp0_window[window]))])

    df = pd.DataFrame(output, columns=["c", "n_monolayer",  "BET_area", "pp0_monolayer", "pp0_min", "pp0_max", "pp0_mean", "r2", "monolayer_difference"])

    return roq_consistency, lo_limit, hi_limit, pp0_limited, BETeq, df


# data = np.genfromtxt('/Users/jevans/Documents/GitHub/friendly-disco/isotherms/'+isotherm+'.csv',delimiter=',')
# #convert to cm3/g to mol/g
# ads_amount=data[:,1]/22400
roq_consistency, lo_limit, hi_limit, pp0_limited, BETeq, results = BETanalysis(pp0,ads_amount)


# plot isotherm
# plt.plot(pp0,ads_amount,'o-')
# plt.xlabel('p/p$_0$')
# plt.ylabel('amount adsorbed / mol$\,$g$^{-1}$')
# #plt.savefig(results_dir+isotherm+"_isotherm.pdf")
# plt.show()

# # plot consistency region
# plt.plot(pp0,roq_consistency, 'o-')
# plt.xlabel('p/p$_0$')
# plt.ylabel('$n_a(1-p/p_0)$ / mol$\,$g$^{-1}$')
# plt.vlines(pp0[hi_limit],0,max(roq_consistency)*1.1)
# plt.vlines(pp0[lo_limit],0,max(roq_consistency)*1.1)
# #plt.savefig(results_dir+isotherm+"_consistencyregion.pdf")
# plt.show()

# # plot BET equation
# plt.plot(pp0_limited,BETeq,'o-')
# plt.xlabel('p/p$_0$')
# plt.ylabel(r'$\frac{p/p_0}{n_a(1-p/p_0)}$ / mol$\,$g$^{-1}$')
# #plt.savefig(results_dir+isotherm+"_BETequation.pdf")
# plt.show()

# # #plot p/p0 value corresponding to the monolayer capacity
# # plt.plot(results["pp0_monolayer"],results["pp0_mean"], 'o')
# # plt.plot(results["pp0_monolayer"],results["pp0_max"], '^', color='grey')
# # plt.plot(results["pp0_monolayer"],results["pp0_min"], 'v')
# # plt.ylabel('p/p$_0$')
# # plt.xlabel('p/p$_0$ ($n_m$)')
# # plt.savefig(results_dir+isotherm+"_monolayercapacity.pdf")
# # plt.clf()

# # plot variation of BET area
# plt.scatter(results["pp0_mean"],results["BET_area"])
# plt.xlabel('p/p$_0$')
# plt.ylabel('BET area / m$^2 \,$g$^{-1}$')
# #plt.savefig(results_dir+isotherm+"_BETarea.pdf")
# plt.show()

# save results as csv sort by difference in monolayer
results_sorted = results.sort_values("c")
print(results_sorted)