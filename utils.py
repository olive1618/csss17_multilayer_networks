import os
import string

import pandas as pd
import numpy as np


def create_node_names():
    pollinator_key = {}
    plant_key = {}

    for file_name in os.listdir(SITE_DIR_LOC):
        df = pd.read_csv(os.path.join(SITE_DIR_LOC, file_name), header=0, index_col=0)

        # Pollinators are rows and plants are columns
        for poll in df.index:
            if poll not in pollinator_key:
                # Remove punctuation and create list of strings
                temp = poll.translate(None, string.punctuation).split(' ')
                # If species provided, shorten to genus first initial & whole species
                # If not provided, shorten to whole genus
                # If gender or count provided, add to end
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
def collapse_to_islands():
    """Each island has two site files. Collapse both sites on each island to a single file"""
    collapsed_islands = []
    site_list = os.listdir(SITE_DIR_LOC)

    for file_name in site_list:
        base_df = pd.read_csv(os.path.join(SITE_DIR_LOC, file_name), header=0, index_col=0)
        site_name = file_name.split('_')[1].split('.')[0][:-1]

        if site_name not in collapsed_islands:
            collapsed_islands.append(site_name)
            print("File name: ", file_name,)
            for site_file in site_list:
                # Find other site on island and confirm it isn't the same site
                if site_name in site_file and site_file != file_name:
                    add_df = pd.read_csv(os.path.join(SITE_DIR_LOC, site_file), header=0, index_col=0)
                    print("Match: ", site_file, '\n')

                    for row_name in add_df.index:
                        for col_name in add_df.columns:
                            try:
                                # Add count if that plant/pollinator pair already exists
                                base_df.loc[row_name, col_name] += add_df.loc[row_name, col_name]
                            except KeyError:
                                # If column does not exist, add it
                                if col_name not in base_df.columns:
                                    base_df[col_name] = 0
                                # If row does not exist, add it
                                if row_name not in base_df.index:
                                    temp_array = np.array([0]*len(base_df.columns))
                                    row_data = np.reshape(temp_array, (1, len(base_df.columns)))
                                    ndf = pd.DataFrame(data=row_data, columns=base_df.columns, index=[row_name])
                                    base_df = pd.concat([base_df, ndf])
                                try:
                                    base_df.loc[row_name, col_name] += add_df.loc[row_name, col_name]
                                except KeyError:
                                    print('WTF! Row: {}  Col: {}'.format(row_name, col_name))
                    base_df.to_csv('data/islands/'+site_name+'.csv')
                    break



if __name__ == "__main__":
    SITE_DIR_LOC = "data/sites"
    # pollinator_lookup, plant_lookup = create_node_names()
    collapse_to_islands()

