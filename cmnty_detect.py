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
import matplotlib.pyplot as plt


def prep_uwv_tensors(this_k):
    """Read outputted MultiTensor data files holding u and v matrices and
    w tensor into numpy arrays"""
    # Read u matrix file to a dataframe and then convert to np array
    u_df = pd.read_table(os.path.join(MT_UWV_OUTPUT, 'u_K'+this_k+'.dat'),
                         delim_whitespace=True, skiprows=[0],
                         header=None, index_col=0)
    u_matrix = np.asarray(u_df.values)

    # Read v matrix file to a dataframe and then convert to np array
    v_df = pd.read_table(os.path.join(MT_UWV_OUTPUT, 'v_K'+this_k+'.dat'),
                         delim_whitespace=True, skiprows=[0],
                         header=None, index_col=0)
    v_matrix = np.asarray(v_df.values)

    # Create placeholder 3d tensor. Read thru file and build tensor out
    w_tensor = np.zeros((int(this_k), int(this_k), 14))
    layer_matrix = np.zeros((int(this_k), int(this_k))) # Dummy var to avoid assign b4 define

    with open(os.path.join(MT_UWV_OUTPUT, 'w_K'+this_k+'.dat'), 'r') as infile:
        infile.readline() #Skip info on first row
        for line in infile:
            line = line.strip()
            if line:
                if "layer" in line:
                    this_layer = int(re.findall(r'\d+', line)[0])
                    if this_layer > 0:
                        w_tensor[:, :, this_layer-1] = layer_matrix
                    layer_matrix = np.zeros((int(this_k), int(this_k)))
                    counter = 0

                else:
                    layer_array = np.asarray(line.split(" "), dtype=np.float64)
                    layer_matrix[counter, :] = layer_array
                    counter += 1

    # Add final matrix for last layers
    w_tensor[:, :, this_layer] = layer_matrix

    print "Shapes --> U:", np.shape(u_matrix), "W:", np.shape(w_tensor), "V:", np.shape(v_matrix)

    # Ordered node names to use in comparison
    node_list = list(v_df.index)

    return u_matrix, w_tensor, v_matrix, node_list

#
def multiply_uwv(u_matrix, w_tensor, v_matrix):
    """Matrix multiply u, each layer of w and v. Product shape is N x N x L"""
    u_dot_w_dot_v = np.zeros((np.shape(u_matrix)[0], np.shape(u_matrix)[0], 14))
    for lyr in range(14):
        u_dot_w = np.mat(u_matrix) * np.mat(w_tensor[:, :, lyr])
        u_dot_w_dot_v[:, :, lyr] = u_dot_w * np.mat(v_matrix.T)

    return u_dot_w_dot_v

#
def build_exp_act_tups(u_dot_w_dot_v, actual_ew_df, node_list):
    """Build dict of lists of tuples of (expected_ew, actual_ew) for AUC calculation"""
    exp_act_ew_dict = {lyr: [] for lyr in range(1, 15)}

    for row in actual_ew_df.itertuples():
        try:
            pol_idx = node_list.index(row[1])
        except ValueError:
            pol_idx = 'x'

        try:
            plt_idx = node_list.index(row[2])
        except ValueError:
            plt_idx = 'x'

        for idx, act_edg_wght in enumerate(row[3:]):
            if pol_idx != 'x' and plt_idx != 'x':
                expected_ew = u_dot_w_dot_v[pol_idx, plt_idx, idx]
            else:
                # If either the plant or the pollinator was not in the training set, so
                #  no estimate is available, use expected edge weight of zero
                expected_ew = 0.0
            # Add tuple to correct layer
            exp_act_ew_dict[idx+1].append((expected_ew, act_edg_wght))

    return exp_act_ew_dict

#
def calculate_directed_auc(exp_act_ew_dict):
    """Calculate area under the ROC curve. Ideal is for the ordering of expected
    edge weights to match to ordering of actual edge weights.
    sorted_m is a list of tuples (expected_ij, actual_ij) order ascending by
    actuals"""
    sum_layers_auc = 0.0

    for layer in range(1, 15):
        sorted_m = sorted(exp_act_ew_dict[layer], key=lambda tup: tup[0])
        max_actual_integer = max(exp_act_ew_dict[layer], key=lambda tup: tup[1])[1]
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
    # python main.py -a="AllSites_adjacency.dat" -f="all_layer_adjacency" -l=14 -k=2
    checked_ks = []
    all_auc = {}

    for file_name in os.listdir(MT_UWV_OUTPUT):
        current_k = re.findall(r'\d+', file_name)[0]
        if current_k not in checked_ks:
            print "K =", current_k
            checked_ks.append(current_k)
            u_mat, w_tens, v_mat, node_names = prep_uwv_tensors(current_k)
            expect_edg_wght = multiply_uwv(u_mat, w_tens, v_mat)

            # Read in actual edge weights from holdout file
            col_names = ["Pollinator", "Plant"] + ["L"+str(l) for l in range(1, 15)]
            actual_edg_wgt_df = pd.read_table(os.path.join(ALL_ADJ_DIR, 'AllSites_holdout.dat'),
                                              delim_whitespace=True,
                                              header=None, index_col=False,
                                              names=col_names,
                                              usecols=[i for i in range(1, 17)])

            exp_act = build_exp_act_tups(expect_edg_wght, actual_edg_wgt_df, node_names)
            summed_auc = calculate_directed_auc(exp_act)
            print "Summed AUC:", summed_auc, "\n"
            all_auc[int(current_k)] = summed_auc

    # Plot auc values for each k
    x = np.array(all_auc.keys())
    y = np.array(all_auc.values())

    x_sort_arg = np.argsort(x)
    plt.plot(x[x_sort_arg], y[x_sort_arg])
    plt.title("Summed AUC by K Communities")
    plt.show()

#
if __name__ == "__main__":
    ALL_ADJ_DIR = os.path.join("data", "all_layer_adjacency")
    MT_UWV_OUTPUT = os.path.join("data", "multitensor_output")
    select_k()
