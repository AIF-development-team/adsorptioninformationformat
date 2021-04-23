import subprocess
import os

bel_data = [
    ("unknown", "Ar_test/1.DAT"),
    ("Sample_E", "bel/Sample_E.DAT"),
    ('DUT-13', "DUT-13/BF010_DUT-13_CH4_111K_run2.DAT"),
    ('DUT-13', "DUT-13/BF010_DUT-13_CH4_111K.DAT"),
    ("DUT-49", "DUT-49/DUT-49_nbutane_273K_viele_Punkte.DAT"),
    ("DUT-49", "DUT-49/DUT-49_nbutane_298K_viele_Punkte_hohe_masse.DAT"),
    ("DUT-49", "DUT-49/DUT-49-SKDM017_SCD5dEtOH+act150C22h_N277K_run1.DAT"),
    ("DUT-49", "DUT-49/DUT-49-SKDM019_SCDEtOH_Act.150C_Ar_87K.DAT"),
    ("DUT-67", "DUT-67/DUT-67_H2O_298K.DAT"),
    ("DUT-67", "DUT-67/DUT-67-N2_77K.DAT"),
    ("DUT-67", "DUT-67/DUT67_1_Garching_acetone_298K.DAT"),
    ("DUT-67", "DUT-67/DUT67_1_Garching_DCM_298K.DAT"),
    ("DUT-67", "DUT-67/DUT67_1_Garching_EtOH_298K.DAT"),
    ("DUT-67", "DUT-67/DUT67_1_Garching_hexane_298K.DAT"),
    ("DUT-67", "DUT-67/DUT67_1_Garching_isopropanol_298K.DAT"),
    ("DUT-67", "DUT-67/DUT67_1_Garching_MeOH_298K.DAT"),
    ("DUT-67", "DUT-67/DUT67_1_Garching_toluol_298K.DAT"),
    ("DUT-67", "DUT-67/DUT67_1_Garching_wasser_298K.DAT"),
    ("DUT-8",  "DUT-8/la-133_dut-8_zn_isp_cp_etoh_298k.DAT")
]

qnt_data = [
    ("DUT-6", r"DUT-6/NK_DUT-6_LP_N2_114PKT\ \(Raw\ Analysis\ Data\).txt"),
    ("DUT-13", r"DUT-13/BF001\ \(Raw\ Analysis\ Data\).txt"),
    ("DUT-60", r"DUT-60/ih_DUT-60_183b\ \(Raw\ Analysis\ Data\).txt"),
    ("DUT-75", r"DUT-75/US_540_DUT75_N2\ \(Raw\ Analysis\ Data\).txt"),
    (
        "DUT-23",
        r"DUT-23/NK_CU\(BIPY\)\(BTB\)_10-11_DMF-ETOH_CO2_84PKT_N2_N2\ \(Raw\ Analysis\ Data\).txt"
    ),
    ("TEST", "NovaWin/test.txt"),
    ("RE-22", r"NovaWin/RE-22\ \(Raw\ Analysis\ Data\).txt")
]

mic_data = [
    ("Sample_A", "micromeritics/Sample_A.xls"),
    ("Sample_C", "micromeritics/Sample_C.xls"),
    ("Sample_D", "micromeritics/Sample_D.xls"),
    ("Sample_E", "micromeritics/Sample_E.xls"),
    ("Sample_F", "micromeritics/Sample_F.xls"),
]

BELcsv_data = [
    ("DUT-32", "DUT-32/RGE-343-DUT32-7dCO2_Nitrogen\(BelMax\).csv"),
    ("DUT-13", "DUT-13/BF-010-DUT-13-CH4-190K-run1-export.csv")
]

BELcsv_JIS_data = [
    ("DMOF", "DMOF/ASch082C_Zntmbdcdabco_C2H6_Exp190819a.csv"),
    ("DMOF", "DMOF/ASch082B_Zndmbdcdabco_C2H4_Exp191004a_weight\ correction.csv"),
    ("DMOF", "DMOF/Asch065B_C2H6_298K_Exp190327a.csv")
]

def test_bel_parser():
    for id, file in bel_data:
        p = subprocess.run(
            "python raw2aif.py ./test/database/"+file+" BELSORP-max "+id,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True
        )

        if p.stderr:
            for line in p.stderr.decode(encoding='utf-8').split('\n'):
                print(line)
            raise Exception(file)

def test_bel_output():
    for id, file in bel_data:
        outfile = os.path.splitext(file)[0]+'.aif'
        p = subprocess.run(
            "python plotaif.py ./test/database/"+outfile,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True
        )

        if p.stderr:
            for line in p.stderr.decode(encoding='utf-8').split('\n'):
                print(line)
            raise Exception(file)

def test_qnt_parser():
    for id, file in qnt_data:
        p = subprocess.run(
            "python raw2aif.py ./test/database/"+file+" quantachrome "+id,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True
        )

        if p.stderr:
            for line in p.stderr.decode(encoding='utf-8').split('\n'):
                print(line)
            raise Exception(file)

def test_qnt_output():
    for id, file in qnt_data:
        outfile = os.path.splitext(file)[0]+'.aif'
        p = subprocess.run(
            "python plotaif.py ./test/database/"+outfile,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True
        )

        if p.stderr:
            for line in p.stderr.decode(encoding='utf-8').split('\n'):
                print(line)
            raise Exception(file)


def test_mic_parser():
    for id, file in mic_data:
        p = subprocess.run(
            "python raw2aif.py ./test/database/"+file+" micromeritics "+id,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True
        )

        if p.stderr:
            for line in p.stderr.decode(encoding='utf-8').split('\n'):
                print(line)
            raise Exception(file)

def test_mic_output():
    for id, file in mic_data:
        outfile = os.path.splitext(file)[0]+'.aif'
        p = subprocess.run(
            "python plotaif.py ./test/database/"+outfile,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True
        )

        if p.stderr:
            for line in p.stderr.decode(encoding='utf-8').split('\n'):
                print(line)
            raise Exception(file)

def test_BELcsv_parser():
    for id, file in BELcsv_data:
        p = subprocess.run(
            "python raw2aif.py ./test/database/"+file+" BEL-csv "+id,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True
        )

        if p.stderr:
            for line in p.stderr.decode(encoding='utf-8').split('\n'):
                print(line)
            raise Exception(file)

def test_BELcsv_output():
    for id, file in BELcsv_data:
        outfile = os.path.splitext(file)[0]+'.aif'
        p = subprocess.run(
            "python plotaif.py ./test/database/"+outfile,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True
        )

        if p.stderr:
            for line in p.stderr.decode(encoding='utf-8').split('\n'):
                print(line)
            raise Exception(file)

def test_BELcsv_JIS_parser():
    for id, file in BELcsv_JIS_data:
        p = subprocess.run(
            "python raw2aif.py ./test/database/"+file+" BEL-csv_JIS "+id,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True
        )

        if p.stderr:
            for line in p.stderr.decode(encoding='utf-8').split('\n'):
                print(line)
            raise Exception(file)

def test_BELcsv_JIS_output():
    for id, file in BELcsv_JIS_data:
        outfile = os.path.splitext(file)[0]+'.aif'
        p = subprocess.run(
            "python plotaif.py ./test/database/"+outfile,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True
        )

        if p.stderr:
            for line in p.stderr.decode(encoding='utf-8').split('\n'):
                print(line)
            raise Exception(file)

# subprocess.call("find ./test/database -name '*.aif' -delete", shell=True)
# subprocess.call("find ./test/database -name '*.pdf' -delete", shell=True)
# test_bel_parser()
# test_bel_output()
# test_qnt_parser()
# test_qnt_output()
# test_mic_parser()
# test_mic_output()
# test_BELcsv_parser()
# test_BELcsv_output()
# test_BELcsv_JIS_parser()
# test_BELcsv_JIS_output()
