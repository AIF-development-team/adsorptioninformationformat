import numpy as np
from gemmi import cif

aif = cif.read_file('database/DUT-60/ih_DUT-60_183b.aif')
block = aif.sole_block()
ads_press = np.array(block.find_loop('_adsorption_pressure'),dtype=float)
ads_amount = np.array(block.find_loop('_adsorption_amount'),dtype=float)
des_press = np.array(block.find_loop('_desorption_pressure'),dtype=float)
des_amount = np.array(block.find_loop('_desorption_amount'),dtype=float)

material_id = block.find_pair('_material_id')[-1]
material_mass = block.find_pair('_sample_mass')[-1]
print(material_id)

#convert to mol/g to cm3/g
ads_amount=ads_amount*0.001
#ads_amount = ads_amount / 4.5e-3
# ads_amount = ads_amount*float(material_mass)
# ads_amount = ads_amount*1e-6


#n2 properties
p0 = 101860.98004799998
ads_cross = 0.162

pp0=ads_press/p0

roq_consistency = ads_amount*(1-pp0)

import matplotlib.pyplot as plt
print(np.argmax(roq_consistency))
plt.plot(roq_consistency, 'o-')
plt.show()

lo_limit = 0
hi_limit= np.argmax(roq_consistency)

# plt.plot(pp0[lo_limit:hi_limit],roq_consistency[lo_limit:hi_limit], 'o-')
# plt.show()

#transform to limits

pp0 =  pp0[lo_limit:hi_limit]
roq_consistency = roq_consistency[lo_limit:hi_limit]
BETeq = pp0/roq_consistency



plt.plot(pp0,BETeq,'o-')
plt.show()

from scipy.stats import linregress

def rolling_window(a, window):
    shape = a.shape[:-1] + (a.shape[-1] - window + 1, window)
    strides = a.strides + (a.strides[-1],)
    return np.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)

BETeq_window = rolling_window(BETeq,3)
pp0_window = rolling_window(pp0,3)



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
    if c > 0 and r2>0.995:
        n_monolayer = 1/(intercept * c)
        p_monolayer = 1/(np.sqrt(c) + 1)
        BET_area = n_monolayer * ads_cross * (10**(-18)) * 6.022E23
        output.append([c,n_monolayer,p_monolayer,BET_area,np.min(pp0_window[window]),np.max(pp0_window[window]),np.mean(pp0_window[window])])

output=np.array(output)

print(output[:,0])
print(output[:,1])
print(output[:,3])

plt.plot(output[:,-1],output[:,-2],'--')
plt.plot(output[:,-1],output[:,-3],'--')
plt.plot(output[:,-1],output[:,2], 'o')
plt.show()

plt.plot(output[:,-1],output[:,3], 'o')
plt.xlabel('p/p$_0$')
plt.ylabel('BET area / m$^2 \,$g$^{-1}$')
plt.show()

# # plt.plot(pp0[:np.argmax(firstcond)+1],firstcond[:np.argmax(firstcond)+1])
# pp0max = (pp0[np.argmax(firstcond)+1])

# BETeq = pp0/(ads_amount*(1-pp0))

# #apply limits
# BETeq = BETeq[:np.argmax(firstcond)+1]
# pp0 = pp0[:np.argmax(firstcond)+1]

# plt.plot(pp0,BETeq,'o-')
# plt.show()
# # plt.xlim([0,pp0max])
# # plt.ylim([0, BETeq[np.argmax(firstcond)+1]])

# from scipy.stats import linregress

# def rolling_window(a, window):
#     shape = a.shape[:-1] + (a.shape[-1] - window + 1, window)
#     strides = a.strides + (a.strides[-1],)
#     return np.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)

# BETeq_window = rolling_window(BETeq,6)
# pp0_window = rolling_window(pp0,6)

# output = []
# for window in range(len(BETeq_window)):
#     fit = linregress(pp0_window[window],BETeq_window[window])
#     slope = fit[0]
#     intercept = fit[1]
#     r2 = fit[2]
#     c = 1+(slope/intercept)
#     if c > 0 and r2>0.995:
#         output.append([slope,intercept,np.mean(pp0_window[window])])

# output=np.array(output)
# slopes = output[:,0]
# intercepts = output[:,1]

# nm = 1/(slopes+intercepts)
# c = 1+(slopes/intercepts)

# print(nm)
# print(c)
# ads_cross = 1.62e-19

# stotal = (nm*6.022e23*ads_cross)/(float(material_mass)*22400)
# print(stotal)
# plt.plot(output[:,2],stotal)
# plt.show()

# # print(1/(output[:,0]-output[:,1]))
# # print(1+(output[:,0]/output[:,1]))

# # nm = 1/(output[:,0]-output[:,1])
# # ads_cross = 1.62e-19

# # SBET = nm*ads_cross
# # print(SBET)




# # BETeq = (pp0) / (ads_amount*(1-pp0))

# # import matplotlib.pyplot as plt

# # plt.plot(ads_press/p0,BETeq, 'o-')
# # plt.xlim([0.05,0.3])
# # plt.show()