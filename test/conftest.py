# -*- coding: utf-8 -*-
"""pytest-specific test configurations."""
import glob
import os

import pytest

RECREATE_FILES = False


@pytest.fixture(scope='session', autouse=True)
def setup(request):
    """remove aif and pdf test files before and after testing"""
    print('\nCleaning files')
    aifs = glob.glob('./test/database/*/*.aif')
    pdfs = glob.glob('./test/database/*/*.pdf')
    for filename in aifs + pdfs:
        os.remove(filename)

    def fin():
        print('\nCleaning files')
        aifs = glob.glob('./test/database/*/*.aif')
        pdfs = glob.glob('./test/database/*/*.pdf')
        if RECREATE_FILES:
            for filename in aifs:
                os.replace(filename, filename + '_tst')
            for filename in pdfs:
                os.remove(filename)
        else:
            for filename in aifs + pdfs:
                print(filename)
                os.remove(filename)

    request.addfinalizer(fin)


bel_data = [
    ('unknown', 'Ar_test/1.DAT'), ('Sample_E', 'bel/Sample_E.DAT'),
    ('DUT-13', 'DUT-13/BF010_DUT-13_CH4_111K_run2.DAT'),
    ('DUT-13', 'DUT-13/BF010_DUT-13_CH4_111K.DAT'),
    ('DUT-49', 'DUT-49/DUT-49_nbutane_273K_viele_Punkte.DAT'),
    ('DUT-49', 'DUT-49/DUT-49_nbutane_298K_viele_Punkte_hohe_masse.DAT'),
    ('DUT-49', 'DUT-49/DUT-49-SKDM017_SCD5dEtOH+act150C22h_N277K_run1.DAT'),
    ('DUT-49', 'DUT-49/DUT-49-SKDM019_SCDEtOH_Act.150C_Ar_87K.DAT'),
    ('DUT-67', 'DUT-67/DUT-67_H2O_298K.DAT'),
    ('DUT-67', 'DUT-67/DUT-67-N2_77K.DAT'),
    ('DUT-67', 'DUT-67/DUT67_1_Garching_acetone_298K.DAT'),
    ('DUT-67', 'DUT-67/DUT67_1_Garching_DCM_298K.DAT'),
    ('DUT-67', 'DUT-67/DUT67_1_Garching_EtOH_298K.DAT'),
    ('DUT-67', 'DUT-67/DUT67_1_Garching_hexane_298K.DAT'),
    ('DUT-67', 'DUT-67/DUT67_1_Garching_isopropanol_298K.DAT'),
    ('DUT-67', 'DUT-67/DUT67_1_Garching_MeOH_298K.DAT'),
    ('DUT-67', 'DUT-67/DUT67_1_Garching_toluol_298K.DAT'),
    ('DUT-67', 'DUT-67/DUT67_1_Garching_wasser_298K.DAT'),
    ('DUT-8', 'DUT-8/la-133_dut-8_zn_isp_cp_etoh_298k.DAT')
]

qnt_data = [
    ('DUT-6', r'DUT-6/NK_DUT-6_LP_N2_114PKT (Raw Analysis Data).txt'),
    ('DUT-13', r'DUT-13/BF001 (Raw Analysis Data).txt'),
    ('DUT-60', r'DUT-60/ih_DUT-60_183b (Raw Analysis Data).txt'),
    ('DUT-75', r'DUT-75/US_540_DUT75_N2 (Raw Analysis Data).txt'),
    ('DUT-23',
     r'DUT-23/NK_CU(BIPY)(BTB)_10-11_DMF-ETOH_CO2_84PKT_N2_N2 (Raw Analysis Data).txt'
     ),
    ('TEST', 'NovaWin/test.txt'),
    ('RE-22', r'NovaWin/RE-22 (Raw Analysis Data).txt'),
]

mic_data = [
    ('Sample_A', 'micromeritics/Sample_A.xls'),
    ('Sample_C', 'micromeritics/Sample_C.xls'),
    ('Sample_D', 'micromeritics/Sample_D.xls'),
    ('Sample_E', 'micromeritics/Sample_E.xls'),
    ('Sample_F', 'micromeritics/Sample_F.xls'),
    ('Sample_G', 'micromeritics/Sample_G.xls'),
    ('Sample_H', 'micromeritics/Sample_H.xls'),
    ('Sample_I', 'micromeritics/Sample_I.xls'),
    ('Sample_J', 'micromeritics/Sample_J.xls'),
    ('Sample_K', 'micromeritics/Sample_K.xls'),
    ('Sample_L', 'micromeritics/Sample_L.xls'),
    ('Sample_M', 'micromeritics/Sample_M.xls'),
    ('Sample_N', 'micromeritics/Sample_N.xls'),
]

BELcsv_data = [('DUT-32', r'DUT-32/RGE-343-DUT32-7dCO2_Nitrogen(BelMax).csv'),
               ('DUT-13', 'DUT-13/BF-010-DUT-13-CH4-190K-run1-export.csv')]

BELcsv_JIS_data = [
    ('DMOF', 'DMOF/ASch082C_Zntmbdcdabco_C2H6_Exp190819a.csv'),
    ('DMOF',
     r'DMOF/ASch082B_Zndmbdcdabco_C2H4_Exp191004a_weight correction.csv'),
    ('DMOF', 'DMOF/Asch065B_C2H6_298K_Exp190327a.csv')
]

NIST_data = [
    ('isotherm1', 'NIST/10.1021Jp400480q.Isotherm2.json'),
]
