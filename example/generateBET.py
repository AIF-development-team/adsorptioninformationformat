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
            output.append([c,n_monolayer,BET_area,pp0_monolayer,np.min(pp0_window[window]),np.max(pp0_window[window]),np.mean(pp0_window[window]),r2, np.abs(np.min(np.mean(pp0_window[window]-pp0_monolayer)))])

    df = pd.DataFrame(output, columns=["c", "n_monolayer","BET_area",  "pp0_monolayer", "pp0_min", "pp0_max", "pp0_mean", "r2", "monolayer_difference"])

    return roq_consistency, lo_limit, hi_limit, pp0_limited, BETeq, df

import os
import string

#make result folder
results_dir = './results/'
#os.mkdir(results_dir)

isotherm="new"
#data = np.genfromtxt('example/Default Dataset.csv',delimiter=',',skip_header=1)
from gemmi import cif

aif = cif.read_file('example/nk_DUT-6_LP_N2_114pkt.aif')
block = aif.sole_block()
ads_press = np.array(block.find_loop('_adsorp_pressure'),dtype=float)
ads_p0 = np.array(block.find_loop('_adsorp_p0'),dtype=float)
ads_amount = np.array(block.find_loop('_adsorp_amount'),dtype=float)
des_press = np.array(block.find_loop('_desorp_pressure'),dtype=float)
des_p0 = np.array(block.find_loop('_desorp_p0'),dtype=float)
des_amount = np.array(block.find_loop('_desorp_amount'),dtype=float)


#convert to cm3/g to mol/g
ads_amount=ads_amount/1000
pp0=ads_press/ads_p0
roq_consistency, lo_limit, hi_limit, pp0_limited, BETeq, results = BETanalysis(pp0,ads_amount)


# plot isotherm
plt.plot(pp0,ads_amount,'o-')
plt.xlabel('p/p$_0$')
plt.ylabel('amount adsorbed / mol$\,$g$^{-1}$')
plt.savefig(results_dir+isotherm+"_isotherm.pdf")
plt.clf()

# plot consistency region
plt.plot(pp0,roq_consistency, 'o-')
plt.xlabel('p/p$_0$')
plt.ylabel('$n_a(1-p/p_0)$ / mol$\,$g$^{-1}$')
plt.vlines(pp0[hi_limit],0,max(roq_consistency)*1.1)
plt.vlines(pp0[lo_limit],0,max(roq_consistency)*1.1)
plt.savefig(results_dir+isotherm+"_consistencyregion.pdf")
plt.clf()

# plot BET equation
plt.plot(pp0_limited,BETeq,'o-')
plt.xlabel('p/p$_0$')
plt.ylabel(r'$\frac{p/p_0}{n_a(1-p/p_0)}$ / mol$\,$g$^{-1}$')
plt.savefig(results_dir+isotherm+"_BETequation.pdf")
plt.clf()

# plot variation of BET area
plt.scatter(results["pp0_mean"],results["BET_area"])
plt.xlabel('p/p$_0$')
plt.ylabel('BET area / m$^2 \,$g$^{-1}$')
plt.savefig(results_dir+isotherm+"_BETarea.pdf")
plt.clf()

# save results as csv sort by c value
results_sorted = results.sort_values("c")
results_sorted.to_csv(results_dir+isotherm+'_results.csv',index=False)
print(results_sorted.head(n=10))

