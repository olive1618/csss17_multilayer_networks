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
                if temp[1] != "sp":
                    name = temp[0][0] + '_' + temp[1]
                else:
                    name = temp[0]
                if len(temp) == 3:
                    name += '_' + temp[2]
                name = ''.join([i if ord(i) < 128 else ' ' for i in name])
                pollinator_key[poll] = name

        for plnt in df.columns:
            if plnt not in plant_key:
                temp = plnt.translate(None, string.punctuation).split(' ')
                if temp[1] != "sp":
                    name = temp[0][0] + '_' + temp[1]
                else:
                    name = temp[0]
                if len(temp) == 3:
                    name += '_' + temp[2]
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

    for file_name in os.listdir(SITE_DIR_LOC):
        site_df = pd.read_csv(os.path.join(SITE_DIR_LOC, file_name), header=0, index_col=0)
        site_num = re.findall(r'\d+', file_name)[0]
        print "Site Number: ", site_num

        # Create list of all possible pollinator-plant pairs
        all_pol_plt_pairs = list(itertools.product(all_pollinators, all_plants))

        outfile_name = "Site" + site_num + "_Adjacency.dat"
        with open(os.path.join('data', 'adjacency', outfile_name), 'w') as outfile:
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
    all_site_pairs = list(itertools.permutations(os.listdir(ADJ_DIR_LOC), 2))
    print "Number of ordered site pairs", len(all_site_pairs)
    col_names = ["Edge", "Pollinator", "Plant"] + ['L'+str(i) for i in range(1, 15)]

    for site_pair in all_site_pairs:
        train_site_num = re.findall(r'\d+', site_pair[0])[0]
        train_site = pd.read_table(os.path.join(ADJ_DIR_LOC, site_pair[0]),
                                   delim_whitespace=True, header=None,
                                   names=col_names, index_col=False)
        train_site = train_site[["Edge", "Pollinator", "Plant", "L"+train_site_num]]

        test_site_num = re.findall(r'\d+', site_pair[1])[0]
        test_site = pd.read_table(os.path.join(ADJ_DIR_LOC, site_pair[1]),
                                  delim_whitespace=True, header=None,
                                  names=col_names, index_col=False)
        test_site = test_site[["Edge", "Pollinator", "Plant", "L"+test_site_num]]

        # Select 20% of test for holdout and drop from test df
        test_holdout = test_site.sample(frac=0.2)
        test_site = test_site.drop(test_holdout.index)

        # Combine two layers into single adjacency matrix
        combined_adj_mat = pd.merge(train_site, test_site, how='outer',
                                    on=["Edge", "Pollinator", "Plant"])
        combined_adj_mat.fillna(value=0, inplace=True)

        outfile_name = "Sites_" + train_site_num + "_" + test_site_num + "_adjacency.dat"
        combined_adj_mat.to_csv(os.path.join("data", "two_layer_adjacency", outfile_name),
                                header=None, index=None, sep=" ")


#
if __name__ == "__main__":
    SITE_DIR_LOC = os.path.join("data", "sites")
    ADJ_DIR_LOC = os.path.join("data", "one_layer_adjacency")
    ALL_SITES_FILE_LOC = os.path.join("data", "all_sites", "AllSites.csv")

    # POLLINATOR_LOOKUP, PLANT_LOOKUP = create_node_names()
    # collapse_to_islands()
    # collaps_to_main_islands()
    # collapse_to_single_layer()
    # create_single_layer_adjacency()
    create_two_layer_adjacency()
