
# i.keshelashvili@gsi.de

import pandas as pd

chambers = [("FPF2", 2), # FPF
            ("FPF3", 1),
            ("FPF4", 2),

            ("FMF1", 2), # FMF
            ("FMF2", 2),
            ("FMF3", 2),

            ("FHF1", 3) # FHF
            ]

sfp_dev = [ (0, 1, 2, 3, 4, 5),
            (0, 1),
            (0, 1, 2, 3, 4, 5),
            (0, 1)]

sensors = ["FPGA", "SIPM", "FEB"]

bias = ["SET", "RBV", "STATE"]

###############################################################################
##
def generate_scifi_temperature_csv(csv_path: str, write_flags: bool = False):
    """
    Create a CSV file with all combinations of chambers, SciFi numbers, SFPs, DEVs, and sensors.
    """
    rows_temperature=[]
    for ch_name, scifi_number in chambers:
        for nn_scifi in range(scifi_number):
            for sfp in range(len(sfp_dev)):
                for dev in sfp_dev[sfp]:
                    for sensor in sensors:
                        print(f"Processing: {ch_name} {nn_scifi + 1} {sensor} SFP{str(sfp)} DEV{str(dev)}")
                        rows_temperature.append([ch_name, nn_scifi + 1, sfp, dev, sensor])

    if write_flags:
        df=pd.DataFrame(rows_temperature, columns=["CHAMBER", "SCIFI_NUMBER", "SFP", "DEV", "SENSOR"])
        df.to_csv(csv_path,index=False)
        print(df.head())
        print(len(df))  

###############################################################################
##
def generate_scifi_bias_csv(csv_path: str, write_flags: bool = False):
    """
    Create a CSV file with all combinations of chambers, SciFi numbers, SFPs, DEVs, and sensors for bias.
    """
    rows_bias=[]
    for ch_name, scifi_number in chambers:
        for nn_scifi in range(scifi_number):
            for sfp in range(len(sfp_dev)):
                for dev in sfp_dev[sfp]:
                    for bias_par in bias:
                        print(f"Processing: {ch_name} {nn_scifi + 1} SFP{str(sfp)} DEV{str(dev)} {bias_par}")
                        rows_bias.append([ch_name, nn_scifi + 1, sfp, dev, bias_par])

    if write_flags:
        df=pd.DataFrame(rows_bias, columns=["CHAMBER", "SCIFI_NUMBER", "SFP", "DEV", "BIAS_PARAMETER"])
        df.to_csv(csv_path,index=False)
        print(df.head())
        print(len(df))

###############################################################################
##
def generate_scifi_threshold_csv(csv_path: str, write_flags: bool = False):
    """
    Create a CSV file with all combinations of chambers, SciFi numbers, SFPs, DEVs, and sensors for threshold.
    """
    rows_threshold=[]
    for ch_name, scifi_number in chambers:
        for nn_scifi in range(scifi_number):
            for sfp in range(len(sfp_dev)):
                for dev in sfp_dev[sfp]:
                    print(f"Processing: {ch_name} {nn_scifi + 1} SFP{str(sfp)} DEV{str(dev)}")
                    rows_threshold.append([ch_name, nn_scifi + 1, sfp, dev])

    if write_flags:
        df=pd.DataFrame(rows_threshold, columns=["CHAMBER", "SCIFI_NUMBER", "SFP", "DEV"])
        df.to_csv(csv_path,index=False)
        print(df.head())
        print(len(df))

###############################################################################
##
def generate_scifi_mask_csv(csv_path: str, write_flags: bool = False):
    """
    Create a CSV file with all combinations of chambers, SciFi numbers, SFPs, DEVs, and sensors for mask.
    """
    rows_mask=[]
    for ch_name, scifi_number in chambers:
        for nn_scifi in range(scifi_number):
            for sfp in range(len(sfp_dev)):
                for dev in sfp_dev[sfp]:
                    print(f"Processing: {ch_name} {nn_scifi + 1} SFP{str(sfp)} DEV{str(dev)}")
                    rows_mask.append([ch_name, nn_scifi + 1, sfp, dev])

    if write_flags:
        df=pd.DataFrame(rows_mask, columns=["CHAMBER", "SCIFI_NUMBER", "SFP", "DEV"])
        df.to_csv(csv_path,index=False)
        print(df.head())
        print(len(df))


###############################################################################
###############################################################################
## 
if __name__ == "__main__":

    # generate_scifi_temperature_csv("data/scifi_temperature.csv", False)

    # generate_scifi_bias_csv("data/scifi_bias.csv", False)

    # generate_scifi_threshold_csv("data/scifi_threshold.csv", True)

    # generate_scifi_mask_csv("data/scifi_mask.csv", True)

