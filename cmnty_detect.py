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
import seaborn as sns


def prep_uwv_tensors(file_dir, file_end, this_k, num_layers):
    """Read outputted MultiTensor data files holding u and v matrices and
    w tensor into numpy arrays"""
    # Read u matrix file to a dataframe and then convert to np array
    u_df = pd.read_table(os.path.join(file_dir, 'u_K'+file_end),
                         delim_whitespace=True, skiprows=[0],
                         header=None, index_col=0)
    u_matrix = np.asarray(u_df.values) # Shape N * K

    # Read v matrix file to a dataframe and then convert to np array
    v_df = pd.read_table(os.path.join(file_dir, 'v_K'+file_end),
                         delim_whitespace=True, skiprows=[0],
                         header=None, index_col=0)
    v_matrix = np.asarray(v_df.values) # Shape N * K

    # Create placeholder 3d tensor. Read thru file and build tensor out
    w_tensor = np.zeros((int(this_k), int(this_k), num_layers)) # Shape K * K * L
    layer_matrix = np.zeros((int(this_k), int(this_k))) # Dummy var to avoid assign b4 define

    with open(os.path.join(file_dir, 'w_K'+file_end), 'r') as infile:
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

    # Add final matrix for last layer
    w_tensor[:, :, this_layer] = layer_matrix

    print "Shapes --> U:", np.shape(u_matrix), "W:", np.shape(w_tensor), "V:", np.shape(v_matrix)

    # Ordered node names to use in comparison
    node_list = list(v_df.index)

    return u_matrix, w_tensor, v_matrix, node_list

#
def multiply_uwv(u_matrix, w_tensor, v_matrix, num_layers):
    """Matrix multiply u, each layer of w and v. Product shape is N x N x L"""
    u_dot_w_dot_v = np.zeros((np.shape(u_matrix)[0], np.shape(u_matrix)[0], num_layers))
    for lyr in range(num_layers):
        u_dot_w = np.mat(u_matrix) * np.mat(w_tensor[:, :, lyr])
        u_dot_w_dot_v[:, :, lyr] = u_dot_w * np.mat(v_matrix.T)

    return u_dot_w_dot_v

#
def build_exp_act_tups(u_dot_w_dot_v, actual_ew_df, node_list, num_layers):
    """Build dict of lists of tuples of (expected_ew, actual_ew) for AUC calculation"""
    if num_layers == 14:
        exp_act_ew_dict = {lyr: [] for lyr in range(1, num_layers+1)}
        plus_i = 0
    elif num_layers == 2:
        test_lyr = int(list(actual_ew_df.columns)[-1][1:])
        exp_act_ew_dict = {test_lyr: []}
        plus_i = 1

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
                expected_ew = u_dot_w_dot_v[pol_idx, plt_idx, idx+plus_i]
            else:
                # If either the plant or the pollinator was not in the training set, so
                #  no estimate is available, use expected edge weight of zero
                expected_ew = 0.0
            # Add tuple to correct layer
            if num_layers == 14:
                exp_act_ew_dict[idx+1].append((expected_ew, act_edg_wght))
            elif num_layers == 2:
                exp_act_ew_dict[test_lyr].append((expected_ew, act_edg_wght))

    return exp_act_ew_dict

#
def calculate_directed_auc(exp_act_ew_dict):
    """Calculate area under the ROC curve. Ideal is for the ordering of expected
    edge weights to match to ordering of actual edge weights.
    sorted_m is a list of tuples (expected_ij, actual_ij) order ascending by
    actuals"""
    sum_layers_auc = 0.0

    for layer in exp_act_ew_dict.keys():
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
            u_mat, w_tens, v_mat, node_names = prep_uwv_tensors(file_dir=MT_UWV_OUTPUT,
                                                                file_end=current_k+'.dat',
                                                                this_k=current_k, num_layers=14)
            expect_edg_wght = multiply_uwv(u_mat, w_tens, v_mat, num_layers=14)

            # Read in actual edge weights from holdout file
            col_names = ["Pollinator", "Plant"] + ["L"+str(l) for l in range(1, 15)]
            actual_edg_wgt_df = pd.read_table(os.path.join(ALL_ADJ_DIR, 'AllSites_holdout.dat'),
                                              delim_whitespace=True,
                                              header=None, index_col=False,
                                              names=col_names,
                                              usecols=[i for i in range(1, 17)])

            exp_act = build_exp_act_tups(expect_edg_wght, actual_edg_wgt_df,
                                         node_names, num_layers=14)
            summed_auc = calculate_directed_auc(exp_act)
            print "Summed AUC:", summed_auc, "\n"
            all_auc[int(current_k)] = summed_auc

    def plot_auc_by_k():
        """Plot auc values for each k to select global k"""
        x_vals = np.array(all_auc.keys())
        y_vals = np.array(all_auc.values())

        x_sort_arg = np.argsort(x_vals)
        plt.plot(x_vals[x_sort_arg], y_vals[x_sort_arg])
        plt.title("Summed AUC by K Communities")
        plt.show()

    plot_auc_by_k()

#
def two_site_community_detection():
    """
    python main.py -a="Sites_1_1_adjacency.dat" -f="two_layer_adjacency" -l=2 -k=3 -E="_1_1.dat"
    """
    processed_site_pairs = []
    all_auc = {}

    for file_name in os.listdir(MT_TWO_DIR):
        current_site_pair = (re.findall(r'\d+', file_name)[1], re.findall(r'\d+', file_name)[2])
        if current_site_pair not in processed_site_pairs:
            print "Site pair:", current_site_pair
            processed_site_pairs.append(current_site_pair)

            mt_output_filename = '3_{}_{}.dat'.format(current_site_pair[0], current_site_pair[1])
            u_mat, w_tens, v_mat, node_names = prep_uwv_tensors(file_dir=MT_TWO_DIR,
                                                                file_end=mt_output_filename,
                                                                this_k=3, num_layers=2)
            expect_edg_wght = multiply_uwv(u_mat, w_tens, v_mat, num_layers=2)

            # Read in actual edge weights from holdout file
            holdout_file = "Sites_{}_{}_holdout.dat".format(current_site_pair[0],
                                                            current_site_pair[1])
            col_names = ["Pollinator", "Plant", "L"+current_site_pair[1]]
            actual_edg_wgt_df = pd.read_table(os.path.join(TWO_ADJ_HOLDOUT_DIR, holdout_file),
                                              delim_whitespace=True,
                                              header=None, index_col=False,
                                              names=col_names, usecols=[1, 2, 3])

            exp_act = build_exp_act_tups(expect_edg_wght, actual_edg_wgt_df,
                                         node_names, num_layers=2)
            pair_auc = calculate_directed_auc(exp_act)
            print "Pair AUC:", pair_auc, "\n"
            all_auc[(int(current_site_pair[0]), int(current_site_pair[1]))] = pair_auc

    def plot_pairwise_auc():
        """Plot the pairwise directed AUC for every site pair"""
        hm_npa = np.zeros((14, 14))
        for site_pair, calc_auc in all_auc.items():
            train_site = int(site_pair[0]) - 1
            test_site = int(site_pair[1]) - 1
            hm_npa[train_site, test_site] = calc_auc
        ax = sns.heatmap(hm_npa, cmap="YlGnBu", cbar=True,
                         linewidths=0.1, center=0.67,
                         xticklabels=[i for i in range(1, 15)],
                         yticklabels=[i for i in range(1, 15)],
                         cbar_kws={'orientation': 'horizontal'})
        plt.title("Pairwise Community Detection")
        sns.plt.show()

    def plot_auc_histogram():
        """Plot histogram of all AUC values to get center for heatmap"""
        ax = sns.distplot(all_auc.values())
        plt.title("AUC Histogram")
        sns.plt.show()

    plot_pairwise_auc()
    plot_auc_histogram()

#
if __name__ == "__main__":
    ALL_ADJ_DIR = os.path.join("data", "all_layer_adjacency")
    MT_UWV_OUTPUT = os.path.join("data", "multitensor_output_k_select")
    MT_TWO_DIR = os.path.join("data", "multitensor_output_2_layer")
    TWO_ADJ_HOLDOUT_DIR = os.path.join("data", "two_layer_holdout")
    # select_k()
    two_site_community_detection()
