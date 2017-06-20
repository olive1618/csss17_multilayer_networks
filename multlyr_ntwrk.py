import os
import pandas as pd

import pymnet

import utils


def build_site_network_layers():
    for file_name in os.listdir(SITE_DIR_LOC):
        df = pd.read_csv(os.path.join(SITE_DIR_LOC, file_name), header=0, index_col=0)

        # New site so add new layer with site #
        layer_name = file_name.split('_')[0]
        MNET.add_layer(layer_name)

        # Iterate through every plant/pollinator interaction and add the edge weights
        #   between those nodes. Note: The node is created implicitly if it does not exist.
        for row_name in df.index:
            # Pollinators are rows and plants are columns
            # Access the summary name from the correct lookup table
            try:
                pollinator = POLLINATOR_LOOKUP[row_name]
            except:
                print("Pollinator not found: ", row_name)
                pollinator = row_name

            for col_name in df.columns:
                try:
                    plant = PLANT_LOOKUP[col_name]
                except:
                    print("Plant not found: ", col_name)
                    plant = col_name
                
                MNET[pollinator, plant, layer_name, layer_name] = df.loc[row_name, col_name]


def add_inter_layer_edges():
    pass


if __name__ == "__main__":
    # Run function in utils.py to create plant/pollinator lookup tables for summary names
    SITE_DIR_LOC = "data"
    POLLINATOR_LOOKUP, PLANT_LOOKUP = utils.create_node_names(SITE_DIR_LOC)

    # Initialize the multilayer network
    MNET = pymnet.MultilayerNetwork(aspects=1)

    # Add site layers to networks. Edge weights are the observation counts from the data set
    build_site_network_layers()
