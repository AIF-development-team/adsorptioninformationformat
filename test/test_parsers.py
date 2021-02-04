import subprocess

bel_data = [
    ("unknown", "Ar_test/1.DAT"),
    ("Sample_E", "bel/Sample_E.DAT"),
    ('DUT-13', "DUT-13/BF010_DUT-13_CH4_111K_run2.DAT"),
    ('DUT-13', "DUT-13/BF010_DUT-13_CH4_111K.DAT"),
    ("DUT-49", "DUT-49/DUT-49_nbutane_273 K_viele Punkte.DAT"),
    ("DUT-49", "DUT-49/DUT-49_nbutane_298 K_viele Punkte_hohe masse.DAT"),
    ("DUT-49", "DUT-49/DUT-49-SKDM017_SCD5dEtOH+act150°C22h_N277K_run1.DAT"),
    ("DUT-49", "DUT-49/DUT-49-SKDM019_SCDEtOH_Act.150°C_Ar_87K.DAT"),
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
]

qnt_data = [
    ("DUT-6", "DUT-6/NK_DUT-6_LP_N2_114PKT (Raw Analysis Data).txt"),
    ("DUT-60", "DUT-60/ih_DUT-60_183b (Raw Analysis Data).txt"),
    ("DUT-75", "DUT-75/US_540_DUT75_N2 (Raw Analysis Data).txt"),
    (
        "DUT-23",
        "DUT-23/NK_CU(BIPY)(BTB)_10-11_DMF-ETOH_CO2_84PKT_N2_N2 (Raw Analysis Data).txt"
    ),
]

mic_data = [
    ("Sample A", "micromeritics/Sample_A.xls"),
    # ("Sample B", "micromeritics/Sample_B.xls"),
]


def test_bel_parser():
    for id, file in bel_data:
        p = subprocess.run(
            f"python raw2aif_update.py \"database/{file}\" BELSORP-max {id}",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        if p.stderr:
            for line in p.stderr.decode(encoding='utf-8').split('\n'):
                print(line)
            raise Exception(file)


def test_qnt_parser():
    for id, file in qnt_data:
        p = subprocess.run(
            f"python raw2aif_update.py \"database/{file}\" quantachrome {id}",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        if p.stderr:
            for line in p.stderr.decode(encoding='utf-8').split('\n'):
                print(line)
            raise Exception(file)


def test_mic_parser():
    for id, file in mic_data:
        p = subprocess.run(
            f"python raw2aif_update.py \"database/{file}\" micromeritics {id}",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        if p.stderr:
            for line in p.stderr.decode(encoding='utf-8').split('\n'):
                print(line)
            raise Exception(file)
