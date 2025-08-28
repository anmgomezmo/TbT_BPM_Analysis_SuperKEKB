import numpy as np
import os
import sys

import pandas as pd
from datetime import datetime
import random

###################################################
### Define input and output parameters
###################################################

studies_output_dir = "./Outputdata"
sdds_folder = "./Outputdata"
Q_prime_x = 1.5
Q_prime_y = 1.5

add_noise = 0

for ff in os.listdir(studies_output_dir):
    if "tracking_x" in ff: 
        X_tracking = ff
        x = os.path.join(studies_output_dir, ff)
    elif "tracking_y" in ff: 
        Y_tracking = ff
        y = os.path.join(studies_output_dir, ff)


###################################################
### Create one sdds file
###################################################
sdds = "tracking.sdds"
if len(sys.argv) > 1:  # Name can be given as input
    sdds = sys.argv[1]

sdds_file = os.path.join(sdds_folder, sdds)
so = open(sdds_file, "w")
so.write("# SDDSASCIIFORMAT v1 \r\n")
so.close()

for plane in [x,y]:
    if "Y" in plane:
        ax = "y"
    else:
        ax = "x"

    sdds_temp = open(plane[:-4]+"_TMP.dat", "w")
    with open(plane, "r") as ff:
        for ind, line in enumerate(ff):
            # print(ind, line)
            if ind==0: bpms = [ii for ii in line.split('"') if "MQ" in ii]
            elif ind==1: S = np.array([float(ii) for ii in line[5:-2].split(",")])
            elif ind==2: numpart = int(line.split()[2])
            elif ind==3: turns = int(line.split()[2])
            elif ind==10: break
        len_bpm=len(bpms)
        # print(len_bpm)
        # print(numpart)
        # print(turns)

        if add_noise == 1:
            noise_2D = []
            random.seed(0)
            for i in range(turns):
                turns_noise = []
                for j in range(len_bpm):
                    # val = random.random()
                    val = random.gauss(0,0)
                    turns_noise.append(val)
                noise_2D.append(turns_noise)


        for pos in S:
            pos = f"{pos:23.12f}"
            sdds_temp.write(str(pos))
        sdds_temp.write("\n")

        for pos in S:
            pos = f"{pos:23.12f}"
            sdds_temp.write(str(pos))
        sdds_temp.write("\n")

        for pos in S:
            pos = f"{pos:23.12f}"
            sdds_temp.write(str(pos))
        sdds_temp.write("\n")

        pos_for_turn=[]


        for ind, line in enumerate(ff):
            if "# TurnNumber" in line: 
                # print(line)
                turn = int(line.split()[2])
            elif "#" in line: pass
            else: 
                if numpart==1: 
                    pos_for_turn.append(float(line[1:-2]))
                else: 
                    line = np.array([float(ii) for ii in line[1:-2].split(",")])
                    # pos_for_turn.append(np.sqrt(np.mean(line**2)))
                    pos_for_turn.append(np.mean(line))
                if len(pos_for_turn)==len_bpm:
                    if add_noise == 1:
                        turn_noise = noise_2D[turn-1]
                        pos_for_turn = np.array(pos_for_turn) + np.array(turn_noise)
                    for pos in pos_for_turn:
                        pos = f"{pos:23.12f}"
                        sdds_temp.write(str(pos))
                    sdds_temp.write("\n")
                    # print(pos_for_turn)
                    # quit()
                    pos_for_turn=[]


    sdds_temp.close()
    # print(sdds_temp)
    sdds_temp = plane[:-4]+"_TMP.dat"
    # print(sdds_temp)
    # quit()

    df = pd.read_fwf(sdds_temp, header=None)
    df.loc[0] = np.zeros(len_bpm) if plane == x else np.zeros(len_bpm)+1 
    df.loc[1] = bpms
    df.loc[2] = S
    dfT=df.transpose()
    columns = ["XY", "BPM", "LOC"]
    for i in range(len(dfT.columns)-3):
        columns.append(str(i+1))

    dfT.columns = columns
    dfT[["XY"]] = dfT[["XY"]].astype("int64")
    print(dfT)
    # quit()

    dfT.to_csv(sdds_file, header=None, index=None, sep=" ", mode="a")

    os.system("rm " + sdds_temp)

df_test = pd.read_csv(sdds_file)
print(df_test)
print(sdds_file)

#os.system("rm Outputdata/lattice_LER_IK_H_2019_12_06_chroma_1.5_1.5.sad")
# os.system("rm "+x)
# os.system("rm "+y)

