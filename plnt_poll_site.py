"""Check which plants and pollinators have interactions at each site"""
import os

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

import utils


def pp_histogram():
    """Histograms of number of sites each plant and pollinator is present in"""
    # Pollinators are rows and plants are columns
    pollinators = {}
    plants = {}
    sites = []

    for file_name in os.listdir("data"):
        site = file_name.split('.')[0]
        sites.append(site)
        df = pd.read_csv("data/" + file_name, header=0, index_col=0)
        for col_name in df.columns:
            if col_name in plants:
                plants[col_name].append(site)
            else:
                plants[col_name] = [site]

        for row_name in df.index:
            if row_name in pollinators:
                pollinators[row_name].append(site)
            else:
                pollinators[row_name] = [site]

    cols = list(set(plants.keys()))
    cols.sort()
    rows = list(set(pollinators.keys()))
    rows.sort()
    sites.sort()

    plant_df = pd.DataFrame(index=sites, columns=cols)
    poll_df = pd.DataFrame(index=sites, columns=rows)

    for k, v in plants.iteritems():
        for site in v:
            plant_df.loc[site, k] = 1

    for k, v in pollinators.iteritems():
        for site in v:
            poll_df.loc[site, k] = 1

    plant_sum = plant_df.sum(axis=0)
    pollntr_sum = poll_df.sum(axis=0)

    fig = plt.figure()
    ax = plant_sum.plot.hist()
    ax = fig.add_subplot(ax)
    plt.title("Histogram of # of Sites that Recorded Plant Species\nMax is 14")
    fig.savefig("viz/plant_histo.png")
    plt.show()

    fig = plt.figure()
    ax = pollntr_sum.plot.hist()
    ax = fig.add_subplot(ax)
    plt.title("Histogram of # of Sites that Recorded Pollinator Species\nMax is 14")
    plt.savefig("viz/pollinator_histo.png")
    plt.show()

#
def check_superset():
    species_list = []

    for site_file in os.listdir(SITE_DIR):
        site_df = pd.read_csv(os.path.join(SITE_DIR, site_file), index_col=0, header=0)

        for idx_name in site_df.index:
            try:
                species = POLLINATOR_LOOKUP[idx_name]
            except KeyError:
                print("Pollinator not found: ", idx_name)
                species = idx_name
            if species not in species_list:
                species_list.append(species)

        for col_name in site_df.columns:
            try:
                species = PLANT_LOOKUP[col_name]
            except KeyError:
                print("Plant not found: ", col_name)
                species = col_name
            if species not in species_list:
                species_list.append(species)

    all_species_df_cols = ["Site"+str(l) for l in range(1, 15)]
    species_list.sort()
    all_species_df = pd.DataFrame({sn:[0]*len(species_list) for sn in all_species_df_cols},
                                  index=species_list)

    for site_file in os.listdir(SITE_DIR):
        site_df = pd.read_csv(os.path.join(SITE_DIR, site_file), index_col=0, header=0)
        site_num = site_file.split('_')[0]
        for idx_name in site_df.index:
            try:
                species = POLLINATOR_LOOKUP[idx_name]
            except KeyError:
                print("Pollinator not found: ", idx_name)
                species = idx_name
            all_species_df.loc[species, site_num] = 1

        for col_name in site_df.columns:
            try:
                species = PLANT_LOOKUP[col_name]
            except KeyError:
                print("Plant not found: ", col_name)
                species = col_name
            all_species_df.loc[species, site_num] = 1

    all_species_df = all_species_df[["Site1", "Site2", "Site3", "Site4", "Site5", "Site6", "Site7",
                                     "Site8", "Site9", "Site10", "Site11", "Site12", "Site13", "Site14"]]
    all_species_df.to_csv("all.csv")
    ax = sns.heatmap(all_species_df, cmap="Blues",
                     yticklabels=False, cbar=False,
                     vmin=0, vmax=1, center=0.5)

    plt.title("Species Presence by Site")
    sns.plt.show()
            


if __name__ == "__main__":
    SITE_DIR = os.path.join("data", "sites")
    POLLINATOR_LOOKUP, PLANT_LOOKUP = utils.create_node_names(SITE_DIR)
    check_superset()
