import os
import string

import pandas as pd


def create_node_names(dir_loc):
    pollinator_key = {}
    plant_key = {}

    for file_name in os.listdir(dir_loc):
        df = pd.read_csv(os.path.join(dir_loc, file_name), header=0, index_col=0)

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


if __name__ == "__main__":
    pollinator_lookup, plant_lookup = create_node_names("data")

