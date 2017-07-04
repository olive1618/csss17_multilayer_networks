"""
Steps:
- Replace fillna 0 with x
- Use prediction accuracy on all layers to select K
- Run multitensor on all site pairs
- Create mask in update functions to only use intersection in denominator
- Calculate uwv product for each pair
- Compare expected value to actual edge weight using Cat penalty code
- Detect assortativeness by layer with rotation
"""
import os
import re

import pandas as pd
import numpy as np


def calculate_directed_auc(exp_act_ew_dict):
    """Calculate area under the ROC curve. Ideal is for the ordering of expected
    edge weights to match to ordering of actual edge weights.
    sorted_m is a list of tuples (expected_ij, actual_ij) order ascending by
    actuals"""
    print "\nCalculate AUC for layer "
    sum_layers_auc = 0.0

    for layer in range(1, 15):
        print layer, "..",
        sorted_m = sorted(exp_act_ew_dict[layer], key=lambda tup: tup[0])
        max_actual_integer = max(exp_act_ew_dict[layer], key=lambda tup: tup[1])[1]
        print "Max actual integer:", max_actual_integer
        observed_actuals = np.zeros(max_actual_integer+1)
        penalty = 0.

        for _, act in sorted_m:
            # Increment position of value already encountered
            observed_actuals[int(round(act))] += 1
            for q in range(int(round(act))+1, max_actual_integer+1):
                # Increment the penality by the number of entries with
                #  A_ij>act already encoutered
                penalty += observed_actuals[q]
        
        # Calculate denominator to normalize
        denom = 0.
        for k in range(max_actual_integer+1):
            m = 0.
            for p in range(k+1, max_actual_integer+1):
                m += observed_actuals[p]
            denom += m * observed_actuals[k]
        
        sum_layers_auc += 1. - (penalty / denom)
    
    return sum_layers_auc

#
def select_k():
    """Select global parameter k, which is number of communities
    MultiTensor divides the network layers into. Use 80% of all
    edges to predict remaining edges. Pick k with max accuracy.
    Steps:
    - Input AllSites_adjacency.dat to MultiTensor main.py
    - Confirm dimensions of 3 outputted matrices u, v, w
    - Get product of u * w * v. Output matrix should be size N * N * L
    - Compare E(edge weight) with actual with AUC calculation
    - Put those steps in a loop for multiple values of k
    - Select k with highest prediction accuracy
    """
    #python main.py -a="AllSites_adjacency.dat" -f="all_layer_adjacency" -l=14 -k=2
    checked_ks = []

    for file_name in os.listdir(ALL_ADJ_DIR):
        if file_name.split('_')[0] in ['u', 'v', 'w']:
            this_k = re.findall(r'\d+', file_name)[0]
            if this_k not in checked_ks:
                print "K =", this_k
                checked_ks.append(this_k)
                # Read u matrix file to a dataframe and then convert to np array
                u_df = pd.read_table(os.path.join(ALL_ADJ_DIR, 'u_K'+this_k+'.dat'),
                                     delim_whitespace=True, skiprows=[0],
                                     header=None, index_col=0)
                u_mat = np.asarray(u_df.values)

                # Read v matrix file to a dataframe and then convert to np array
                v_df = pd.read_table(os.path.join(ALL_ADJ_DIR, 'v_K'+this_k+'.dat'),
                                     delim_whitespace=True, skiprows=[0],
                                     header=None, index_col=0)
                v_mat = np.asarray(v_df.values)

                # Create placeholder 3d tensor. Read thru file and build tensor out
                w_mat = np.zeros((int(this_k), int(this_k), 14))
                with open(os.path.join(ALL_ADJ_DIR, 'w_K'+this_k+'.dat'), 'r') as infile:
                    infile.readline() #Skip info on first row
                    flag = 0
                    for line in infile:
                        if "layer" in line:
                            this_layer = int(re.findall(r'\d+', line)[0])
                            flag = 1
                            continue
                        if flag == 1:
                            layer1_array = np.asarray(line.split(" "), dtype=np.float64)
                            flag = 2
                            continue
                        if flag == 2:
                            layer2_array = np.asarray(line.split(" "), dtype=np.float64)
                            w_mat[:, :, this_layer] = np.asarray((layer1_array, layer2_array))
                            flag = 0
                
                print "U shape:", np.shape(u_mat), "V shape:", np.shape(v_mat), "W shape:", np.shape(w_mat)

                # Matrix multiply u and each layer of w and then multiply by v. Product shape is N x N x L
                expect_edg_wght = np.zeros((np.shape(u_mat)[0], np.shape(u_mat)[0], 14))
                for lyr in range(14):
                    u_dot_w = np.mat(u_mat) * np.mat(w_mat[:, :, lyr])
                    expect_edg_wght[:, :, lyr] = u_dot_w * np.mat(v_mat.T)
                
                # Ordered node names to use in comparison
                node_names = list(v_df.index)

                # Read in actual edge weights from holdout file
                col_names = ["Pollinator", "Plant"] + ["L"+str(l) for l in range(1, 15)]
                actual_edg_wght_df = pd.read_table(os.path.join(ALL_ADJ_DIR, 'AllSites_holdout.dat'),
                                                   delim_whitespace=True,
                                                   header=None, index_col=False,
                                                   names=col_names, usecols=[i for i in range(1, 17)])

                # Build dictionary of lists of tuples of (expected_ew, actual_ew) for AUC calculation
                exp_act = {lyr: [] for lyr in range(1, 15)}

                for row in actual_edg_wght_df.itertuples():
                    try:
                        pol_idx = node_names.index(row[1])
                    except ValueError:
                        pol_idx = 'x'
                    
                    try:
                        plt_idx = node_names.index(row[2])
                    except ValueError:
                        plt_idx = 'x'
                    
                    for idx, act_edg_wght in enumerate(row[3:]):
                        if pol_idx != 'x' and plt_idx != 'x':
                            expected_ew = expect_edg_wght[pol_idx, plt_idx, idx]
                        else:
                            # If either the plant or the pollinator was not in the training set, so
                            #  no estimate is available, use expected edge weight of zero
                            expected_ew = 0.0
                        # Add tuple to correct layer
                        exp_act[idx+1].append((expected_ew, act_edg_wght))
                
                summed_auc = calculate_directed_auc(exp_act)
                print summed_auc




if __name__ == "__main__":
    ALL_ADJ_DIR = os.path.join("data", "all_layer_adjacency")
    # AllSites_holdout.dat
    select_k()
