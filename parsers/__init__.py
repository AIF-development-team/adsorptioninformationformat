import numpy as np
import pandas as pd


def aif_data_standardise(meta, data):

    # change pressure modes
    p_key = "pressure"
    if "pressure" not in data:
        if "pressure_relative" in data and "pressure_saturation" in data:
            data["pressure"] = [
                a * b for a, b in zip(data["pressure_relative"], data["pressure_saturation"])
            ]
            meta['pressure_mode'] = "relative"
            meta['pressure_unit'] = meta["pressure_saturation_unit"]
        else:
            p_key = "pressure_relative"

    # Get to original unparsed strings
    if meta.get("original_pressure_string"):
        meta["pressure_unit"] = meta.pop("original_pressure_string")
    if meta.get("original_loading_string"):
        meta["loading_unit"] = meta.pop("original_loading_string")

    # ensure something is passed
    if meta['pressure_unit'] is None:
        meta['pressure_unit'] = "relative"

    # split ads / desorption branches
    if "branch" in data:
        if 1 in data["branch"]:
            turnp = data["branch"].index(1)
        else:
            turnp = len(data["branch"])
        del data["branch"]
    else:
        turnp = np.argmax(data[p_key]) + 1

    data_ads = {}
    data_des = {}

    for k, v in data.items():
        data_ads[k] = v[:turnp]
        data_des[k] = v[turnp:]

    data_ads = pd.DataFrame(data_ads)
    data_des = pd.DataFrame(data_des)

    return meta, data_ads, data_des