"""Check which plants and pollinators have interactions at each site"""
import os
import pandas as pd
import matplotlib.pyplot as plt


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

# plant_df.to_csv("plants.csv")
# poll_df.to_csv("polls.csv")
