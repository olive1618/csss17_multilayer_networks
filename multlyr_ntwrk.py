"""
Create the multilayer network object with pymnet library
"""
import os
import pandas as pd

import pymnet

import utils


def build_site_network_layers(dir_loc):
    """Create layers and add edges that are within the layer"""
    # Create lookup for site numbers and names for between layer processing
    site_lookup_tbl = {}
    node_color = {}

    for file_name in os.listdir(dir_loc):
        df = pd.read_csv(os.path.join(dir_loc, file_name), header=0, index_col=0)

        # Add new layer with site #
        site_num = file_name.split('_')[0]

        # Add site name/number to lookup table
        site_name = file_name.split('_')[1].split('.')[0]
        site_lookup_tbl[site_name] = site_num

        MNET.add_layer(site_num)

        # Iterate through every plant/pollinator interaction and add the edge weights
        #   between those nodes. Note: The node is created implicitly if it does not exist.
        for row_name in df.index:
            # Pollinators are rows and plants are columns
            # Access the summary name from the correct lookup table
            try:
                pollinator = POLLINATOR_LOOKUP[row_name]
            except KeyError:
                print("Pollinator not found: ", row_name)
                pollinator = row_name

            for col_name in df.columns:
                try:
                    plant = PLANT_LOOKUP[col_name]
                except KeyError:
                    print("Plant not found: ", col_name)
                    plant = col_name

                MNET[pollinator, plant, site_num, site_num] = df.loc[row_name, col_name]
                node_color[(plant, site_num)] = "forestgreen"
                node_color[(pollinator, site_num)] = "gold"

    return site_lookup_tbl, node_color

#
def add_inter_layer_edges():
    """Add the edges between layers"""
    df = pd.read_csv(DIST_DIR_FILE, header=0)
    for row in df.itertuples():
        from_site_name = row[1].split('_')[0] + row[1].split('_')[1]
        to_site_name = row[2].split('_')[0] + row[2].split('_')[1]

        # Access site number from site lookup table
        try:
            from_site_num = SITE_LOOKUP[from_site_name]
        except KeyError:
            print("From site not found: ", from_site_name)
            break

        try:
            to_site_num = SITE_LOOKUP[to_site_name]
        except KeyError:
            print("To site not found: ", to_site_name)
            break

        # Add between layer edge if the node has edges within both layers
        for node in list(MNET):
            if MNET[node, from_site_num].deg() > 0 and MNET[node, to_site_num].deg() > 0:
                MNET[node, node, from_site_num, to_site_num] = row[3]

#
if __name__ == "__main__":
    # Run function in utils.py to create plant/pollinator lookup tables for summary names
    SITE_DIR_LOC = "data/sites"
    SUBSET_SITE_DIR = os.path.join("data", "site_subset")
    POLLINATOR_LOOKUP, PLANT_LOOKUP = utils.create_node_names(SUBSET_SITE_DIR)

    # Initialize the multilayer network
    MNET = pymnet.MultilayerNetwork(aspects=1)

    # Add site layers to networks. Edge weights are the observation counts from the data set
    SITE_LOOKUP, PP_NODE_COLOR = build_site_network_layers(SUBSET_SITE_DIR)

    # Confirm all 14 network layers creates
    print("\nNetwork layers for each site added")
    print("Layers:", MNET.get_layers())

    # Add between layer edges. Weights are the distances in meters from the data set
    # DIST_DIR_FILE = "data/distances/Distance_between_sites_Dryad.csv"
    # add_inter_layer_edges()
    # print("\nBetween layer edges added")

    fig = pymnet.draw(MNET,
                      show=True,
                      layout="spring",
                      layershape="rectangle",
                      alignedNodes=True,
                      nodeLabelRule={},
                      nodeColorDict=PP_NODE_COLOR,
                      nodeSizeRule={"rule":"degree", "propscale":0.05},
                      defaultLayerColor="lightgray",
                      defaultEdgeColor='white',
                      layerLabelRule={})
