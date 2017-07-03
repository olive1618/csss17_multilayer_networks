"""Utility file of helper functions to process data or create lookup tables"""
import os
import re
import string
import itertools

import pandas as pd
import numpy as np


def create_node_names():
    """Create lookup table where keys are full plant/pollinator names from the
    files and values are the summary form. If species provided, shorten to genus
    first initial & whole species. If not provided, shorten to whole genus. If
    gender or count provided, add to end."""
    pollinator_key = {}
    plant_key = {}

    for file_name in os.listdir(SITE_DIR_LOC):
        df = pd.read_csv(os.path.join(SITE_DIR_LOC, file_name), header=0, index_col=0)

        # Pollinators are rows and plants are columns
        for poll in df.index:
            if poll not in pollinator_key:
                # Remove punctuation and create list of strings
                temp = poll.translate(None, string.punctuation).split(' ')
                
                if "Waiting" in temp[-1]:
                    name = temp[0]
                elif temp[1]=="cf":
                    name = temp[0] + '_' + temp[-1]
                elif temp[1]=="sp" and temp[-1].isdigit():
                    name = temp[0] + '_' + temp[-1]
                elif temp[1]=="sp" and temp[-2].isdigit():
                    name = temp[0] + '_' + temp[-2]
                elif temp[1] not in ['sp', 'cf'] and temp[-1] not in ['f', 'm']:
                    name = temp[0][0:3] + '_' + temp[1]
                elif temp[1] not in ['sp', 'cf'] and temp[-1] in ['f', 'm']:
                    name = temp[0][0:3] + '_' + temp[1] + '_' + temp[-1]
                else:
                    name = temp[0]
                # Drop non ascii characters
                name = ''.join([i if ord(i) < 128 else ' ' for i in name])
                pollinator_key[poll] = name

        for plnt in df.columns:
            if plnt not in plant_key:
                temp = plnt.translate(None, string.punctuation).split(' ')
                if "Waiting" in temp[-1]:
                    name = temp[0]
                elif temp[1]=="cf":
                    name = temp[0] + '_' + temp[-1]
                elif temp[1]=="sp" and temp[-1].isdigit():
                    name = temp[0] + '_' + temp[-1]
                elif temp[1]=="sp" and temp[-2].isdigit():
                    name = temp[0] + '_' + temp[-2]
                elif temp[1] not in ['sp', 'cf'] and temp[-1] not in ['f', 'm']:
                    name = temp[0][0:3] + '_' + temp[1]
                elif temp[1] not in ['sp', 'cf'] and temp[-1] in ['f', 'm']:
                    name = temp[0][0:3] + '_' + temp[1] + '_' + temp[-1]
                else:
                    name = temp[0]

                name = ''.join([i if ord(i) < 128 else ' ' for i in name])
                plant_key[plnt] = name

    return pollinator_key, plant_key

#
def row_col_matching(a_df, b_df):
    """Algorithm to add plant/pollinator counts to base df if pair exists.
    If pair does not exist, add it."""
    for row_name in a_df.index:
        for col_name in a_df.columns:
            try:
                # Add count if that plant/pollinator pair already exists
                b_df.loc[row_name, col_name] += a_df.loc[row_name, col_name]
            except KeyError:
                # If column does not exist, add it
                if col_name not in b_df.columns:
                    b_df[col_name] = 0
                # If row does not exist, add it
                if row_name not in b_df.index:
                    temp_array = np.array([0]*len(b_df.columns))
                    row_data = np.reshape(temp_array, (1, len(b_df.columns)))
                    ndf = pd.DataFrame(data=row_data, columns=b_df.columns, index=[row_name])
                    b_df = pd.concat([b_df, ndf])
                try:
                    b_df.loc[row_name, col_name] += a_df.loc[row_name, col_name]
                except KeyError:
                    print('WTF! Row: {}  Col: {}'.format(row_name, col_name))

    return b_df

#
def collapse_to_islands():
    """Each island has two site files. Collapse both sites on each island to a single file"""
    collapsed_islands = []
    site_list = os.listdir(SITE_DIR_LOC)

    for file_name in site_list:
        base_df = pd.read_csv(os.path.join(SITE_DIR_LOC, file_name), header=0, index_col=0)
        site_name = file_name.split('_')[1].split('.')[0][:-1]

        if site_name not in collapsed_islands:
            collapsed_islands.append(site_name)
            print("File name: ", file_name)
            for site_file in site_list:
                # Find other site on island and confirm it isn't the same site
                if site_name in site_file and site_file != file_name:
                    add_df = pd.read_csv(os.path.join(SITE_DIR_LOC, site_file),
                                         header=0, index_col=0)
                    print("Match: ", site_file, '/n')
                    base_df = row_col_matching(add_df, base_df)
                    base_df.to_csv('data/islands/'+site_name+'.csv')
                    break

#
def collaps_to_main_islands():
    """Collaspe all islands to a single file and collapse the two western sahara
    mainland sites to a single file"""

    main1_df = pd.read_csv(os.path.join(SITE_DIR_LOC, "Site1_WesternSahara1.csv"),
                           header=0, index_col=0)
    main2_df = pd.read_csv(os.path.join(SITE_DIR_LOC, "Site2_WesternSahara2.csv"),
                           header=0, index_col=0)
    main_df = row_col_matching(main1_df, main2_df)
    main_df.to_csv('data/mainland_islands/Mainlands.csv')

    base_df = pd.read_csv(os.path.join(SITE_DIR_LOC, "Site3_Fuerteventura1.csv"),
                          header=0, index_col=0)

    collapsed_islands = ["Site1_WesternSahara1.csv", "Site2_WesternSahara2.csv",
                         "Site3_Fuerteventura1.csv"]
    for file_name in os.listdir(SITE_DIR_LOC):
        if file_name not in collapsed_islands:
            collapsed_islands.append(file_name)
            add_df = pd.read_csv(os.path.join(SITE_DIR_LOC, file_name),
                                 header=0, index_col=0)
            base_df = row_col_matching(add_df, base_df)

    base_df.to_csv('data/mainland_islands/Islands.csv')

#
def collapse_to_single_layer():
    """Collapse all sites to a single file"""
    base_df = pd.read_csv(os.path.join(SITE_DIR_LOC, "Site1_WesternSahara1.csv"),
                          header=0, index_col=0)

    collapsed_islands = ["Site1_WesternSahara1.csv"]
    for file_name in os.listdir(SITE_DIR_LOC):
        if file_name not in collapsed_islands:
            collapsed_islands.append(file_name)
            add_df = pd.read_csv(os.path.join(SITE_DIR_LOC, file_name),
                                 header=0, index_col=0)
            base_df = row_col_matching(add_df, base_df)

    base_df.to_csv('data/all_sites/AllSites.csv')

#
def create_single_layer_adjacency():
    """Create single adjacency matrices for eventual use in MultiTensor software.
    Pollinators are rows and plants are columns. Directed so node1 --> node2"""
    all_sites_df = pd.read_csv(ALL_SITES_FILE_LOC, header=0, index_col=0)
    all_plants = list(all_sites_df.columns)
    all_pollinators = list(all_sites_df.index)

    print "Single site adjacency",
    for file_name in os.listdir(SITE_DIR_LOC):
        site_df = pd.read_csv(os.path.join(SITE_DIR_LOC, file_name), header=0, index_col=0)
        site_num = re.findall(r'\d+', file_name)[0]
        print site_num, "..",

        # Create list of all possible pollinator-plant pairs
        all_pol_plt_pairs = list(itertools.product(all_pollinators, all_plants))

        outfile_name = "Site" + site_num + "_Adjacency.dat"
        with open(os.path.join(ONE_ADJ_DIR_LOC, outfile_name), 'w') as outfile:
            for pair in all_pol_plt_pairs:
                try:
                    pol_pretty_name = POLLINATOR_LOOKUP[pair[0]]
                except KeyError:
                    print("Pollinator not found: ", pair[0])
                    pol_pretty_name = pair[0]

                try:
                    plt_pretty_name = PLANT_LOOKUP[pair[1]]
                except KeyError:
                    print("Plant not found: ", pair[1])
                    plt_pretty_name = pair[1]

                # Check if pol-plt have interaction in any layer
                if all_sites_df.loc[pair[0], pair[1]] > 0:
                    # Row format: E node1name node2name L1wght L2wght L3wght ...
                    row = ['E', pol_pretty_name, plt_pretty_name] + ['0'] * 14
                    # Add pol/plt count at this layer if exists, else retain 0
                    try:
                        row[2+int(site_num)] = str(site_df.loc[pair[0], pair[1]])
                    except KeyError:
                        pass

                    outfile.write(" ".join(row)+'\n')

#
def create_two_layer_adjacency():
    """Create two adjacency matrices for input to MultiTensor software.
    All permutations of length 2 of the sites are created. Whichever
    site is test site has 20% of edges separated for testing prediction."""
    all_site_pairs = list(itertools.permutations(os.listdir(ONE_ADJ_DIR_LOC), 2))
    print "\nNumber of ordered site pairs", len(all_site_pairs)
    col_names = ["Edge", "Pollinator", "Plant"]

    for site_pair in all_site_pairs:
        train_site_num = re.findall(r'\d+', site_pair[0])[0]
        train_site = pd.read_table(os.path.join(ONE_ADJ_DIR_LOC, site_pair[0]),
                                   delim_whitespace=True,
                                   header=None, index_col=False,
                                   names=col_names+['L'+train_site_num],
                                   usecols=[0, 1, 2, 2+int(train_site_num)])

        test_site_num = re.findall(r'\d+', site_pair[1])[0]
        test_site = pd.read_table(os.path.join(ONE_ADJ_DIR_LOC, site_pair[1]),
                                  delim_whitespace=True,
                                  header=None, index_col=False,
                                  names=col_names+['L'+test_site_num],
                                  usecols=[0, 1, 2, 2+int(test_site_num)])

        # Select 20% of test for holdout and drop from test df
        test_holdout = test_site.sample(frac=0.2)
        test_site.drop(test_holdout.index, inplace=True)

        # Combine two layers into single adjacency matrix
        two_adj_mat = pd.merge(train_site, test_site, how='inner',
                               on=["Edge", "Pollinator", "Plant"])
        # TODO Use mask instead of 0 fill value
        two_adj_mat.fillna(value=0, inplace=True)

        combine_outfile_name = "Sites_" + train_site_num + "_" + test_site_num + "_adjacency.dat"
        two_adj_mat.to_csv(os.path.join("data", "two_layer_adjacency", combine_outfile_name),
                           header=None, index=None, sep=" ")

        hold_outfile_name = "Sites_" + train_site_num + "_" + test_site_num + "_holdout.dat"
        test_holdout.to_csv(os.path.join("data", "two_layer_holdout", hold_outfile_name),
                            header=None, index=None, sep=" ")

#
def create_all_layer_adjacency():
    """Create one adjacency matrix that has edges for full network.
    Use to select K by maximizing prediction accuracy."""
    col_names = ["Edge", "Pollinator", "Plant"]
    print "\nAll site adjacency",
    for adj_file in os.listdir(ONE_ADJ_DIR_LOC):
        site_num = re.findall(r'\d+', adj_file)[0]
        print site_num, "..",
        adj_mat = pd.read_table(os.path.join(ONE_ADJ_DIR_LOC, adj_file),
                                delim_whitespace=True,
                                header=None, index_col=False,
                                names=col_names+['L'+site_num],
                                usecols=[0, 1, 2, 2+int(site_num)])

        try:
            combined_adj_mat = pd.merge(combined_adj_mat, adj_mat,
                                        how='inner',
                                        on=["Edge", "Pollinator", "Plant"])
        except NameError:
            combined_adj_mat = adj_mat

    combined_adj_mat = combined_adj_mat[["Edge", "Pollinator", "Plant", "L1", "L2", "L3",
                                         "L4", "L5", "L6", "L7", "L8", "L9", "L10", "L11",
                                         "L12", "L13", "L14"]]

    # Split adjacency matrix in 80% train and 20% test
    combined_holdout_mat = combined_adj_mat.sample(frac=0.2)
    combined_adj_mat.drop(combined_holdout_mat.index, inplace=True)

    combined_adj_mat.to_csv(os.path.join("data", "all_layer_adjacency", "AllSites_adjacency.dat"),
                            header=None, index=None, sep=" ")
    combined_holdout_mat.to_csv(os.path.join("data", "all_layer_adjacency", "AllSites_holdout.dat"),
                                header=None, index=None, sep=" ")

#
if __name__ == "__main__":
    SITE_DIR_LOC = os.path.join("data", "sites")
    ONE_ADJ_DIR_LOC = os.path.join("data", "one_layer_adjacency")
    ALL_SITES_FILE_LOC = os.path.join("data", "all_sites", "AllSites.csv")

    POLLINATOR_LOOKUP, PLANT_LOOKUP = create_node_names()
    # collapse_to_islands()
    # collaps_to_main_islands()
    # collapse_to_single_layer()
    create_single_layer_adjacency()
    create_two_layer_adjacency()
    create_all_layer_adjacency()
