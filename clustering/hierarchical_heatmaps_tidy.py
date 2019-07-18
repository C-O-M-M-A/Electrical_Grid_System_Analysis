# coding: utf-8
"""This script performs a cluster analysis on day ahead price profiles"""
########################################################################################################################
# Import required tools
########################################################################################################################

# import off-the-shelf scripting modules
from __future__ import division     # Without this, rounding errors occur in python 2.7, but apparently not in 3.4
import numpy as np
import pandas as pd
import tkinter as _tkinter
from scipy.cluster.hierarchy import dendrogram, linkage, is_monotonic    # For cluster analysis
from scipy.cluster.hierarchy import fcluster   # For cluster membership
from matplotlib import pyplot as plt
import math

# import raw temporal data
raw_data = pd.read_csv('N2EX_hourly_2017_2019_calendar_year.csv', encoding='ISO-8859-1')
raw_price = raw_data.ix[:, 'price_sterling']
# Tidy up price data (remove commas from as-downloaded CSV)
price = []
for raw in raw_price:
    stripped = ''
    for c in str(raw):
        if c == ',':
            continue
        else:
            stripped = stripped + c
    price = price + [float(stripped) / 100]

# Get 24h profile in list format, then stack in array.
arrays = []
for i in range(int(len(price)/24)):
    price_profile = np.array(price[i*24:(i+1)*24])
    arrays = arrays + [price_profile]
input_array = np.stack(arrays, axis=0)
#print(input_array)

# generate linkage matrix (this does all work, after this it's just a case of defining cluster cut-off points)
Z = linkage(input_array, 'ward')

# define cutoff point for intercluster distance
cutoff = 1500
# calculate full dendrogram
plt.figure(figsize=(25, 10))
plt.title('Hierarchical Clustering Dendrogram')
plt.xlabel('Sample index')
plt.ylabel('Distance')


def fancy_dendrogram(*args, **kwargs):
    max_d = kwargs.pop('max_d', None)
    if max_d and 'color_threshold' not in kwargs:
        kwargs['color_threshold'] = max_d
    annotate_above = kwargs.pop('annotate_above', 0)

    ddata = dendrogram(*args, **kwargs)

    if not kwargs.get('no_plot', False):
        plt.title('Hierarchical Clustering Dendrogram')
        plt.xlabel('Sample index')
        plt.ylabel('Distance £/MWh')
        for i, d, c in zip(ddata['icoord'], ddata['dcoord'], ddata['color_list']):
            x = 0.5 * sum(i[1:3])
            y = d[1]
            if y > annotate_above:
                plt.plot(x, y, 'o', c=c)
                plt.annotate("%.3g" % y, (x, y), xytext=(0, -5),
                             textcoords='offset points',
                             va='top', ha='center')
        if max_d:
            plt.axhline(y=max_d, c='k')
    return ddata

fancy_dendrogram(
    Z,
    leaf_rotation=90.,  # rotates the x axis labels
    leaf_font_size=8.,  # font size for the x axis labels
    no_labels=True, 	# Suppress singleton cluster labels that clog up x -axis
    annotate_above=cutoff, # Prevent excessive annotation of merge distances
    max_d=cutoff
)
plt.show(block=False)

# Elbow plot, for guidance on where to truncate dendrogram

last = Z[-100:, 2]
last_rev = last[::-1]
idxs = np.arange(1, len(last) + 1)

plt.figure(figsize=(25, 10))
plt.title('Elbow plot')
plt.xlabel('Clusters identified')
plt.ylabel('Distance travelled to join clusters')
plt.plot(idxs, last_rev, label="Dist", marker='D')

acceleration = np.diff(last, 2)  # 2nd derivative of the distances
acceleration_rev = acceleration[::-1]
plt.plot(idxs[:-2] + 1, acceleration_rev, label="2nd Deriv Dist", marker='.')
plt.legend()
plt.show(block=False)

print("idxs", idxs)
print("last_rev", last_rev)
print("accel_rev", acceleration_rev)

# retrieve cluster membership for each vector
cluster_membership = fcluster(Z, cutoff, criterion='distance')

# retrieve the number of clusters
cluster_list = []
for i in cluster_membership:
    if i not in cluster_list:
        cluster_list = cluster_list + [i]
n = len(cluster_list)
print ("number of clusters = ", n)

# Generate a CSV for Excel plotting, where each price datum is indexed by hour then day then cluster membership
hour_index =[]
day_index = []
cluster_index =[]
price_data = []
for i in range(int(len(price)/24)):
    hour_index = hour_index + [x+1 for x in range(len(input_array[i, :]))]
    day = [i for x in input_array[i, :]]
    day_index = day_index + day
    cluster = [cluster_membership[i] for x in input_array[i, :]]
    cluster_index = cluster_index + cluster
    price_profile = price[i*24:(i+1)*24]
    price_data = price_data + price_profile

dataframe_output = pd.DataFrame({"hour": hour_index,
                                "day": day_index,
                                "cluster":cluster_index,
                                "price": price_data
                                })

dataframe_output.to_csv("hierarchical_clustering_cutoff=" + str(cutoff) + "_n="+ str(n) + ".csv", sep=',')

# Plot clusters by making price v period set for each then doing 2d histogram
fig = plt.figure(figsize=(10, 10))
ax = fig.add_subplot(111)       # This empty subplot is just for the common axes.
ax.set_xlabel("Hour of Day", labelpad=10)
ax.set_ylabel("Electrical Price £/MWh", labelpad=10)
ax.spines['top'].set_color('none')
ax.spines['bottom'].set_color('none')
ax.spines['left'].set_color('none')
ax.spines['right'].set_color('none')
ax.tick_params(labelcolor='w', top='off', bottom='off', left='off', right='off')

for i in [i+1 for i in range(n)]:
    n_list_period = []  # Receptacle for period data where cluster = n
    n_list_price = []   # Receptacle for price data where cluster = n
    for h in range(len(hour_index)):
        if cluster_index[h] == i:
            n_list_period = n_list_period + [hour_index[h]]
            n_list_price = n_list_price + [price_data[h]]
            
    # next two lines insert an  hour of price = zero, so that histograms all have the same bottom
    n_list_period_normalised = n_list_period + [1]
    n_list_price_normalised = n_list_price + [0]

    # And an hour of price = 125 so they have same top.
    n_list_period_normalised = n_list_period_normalised + [1]
    n_list_price_normalised = n_list_price_normalised + [125]

    # Code that defines grid array for cluster histograms
    if n > 3:
        fig.add_subplot(math.floor(math.sqrt(n)), math.ceil(n/2),i) # Define array and index for subplots.
    else:
        fig.add_subplot(2, 2, i)  # Define array and index for subplots.

    # Stack outliers so histograms have same max y value
    n_list_price_stacked = []
    for j in n_list_price_normalised:
        if j >125:
            n_list_price_stacked = n_list_price_stacked + [125]
        else:
            n_list_price_stacked = n_list_price_stacked + [j]
            
    plt.title('Cluster '+str(i))
    plt.hist2d(n_list_period_normalised, n_list_price_stacked, bins=24)

plt.show()
plt.show(block=False)

# CSV for plotting average profile for each cluster
price_data = pd.DataFrame(input_array)
clusters = pd.DataFrame(cluster_membership)
clusters_for_means = pd.concat([clusters, price_data], axis=1)

clusters_for_means.to_csv("clusters_for_means=" + str(cutoff) + "_n="+ str(n) + ".csv", sep=',')

# CSV for clusters organised into calandar layout
days_of_week = ["mon", "tue", "wed", "thur", "fri", "sat", "sun"]
start_day = "sun"
d_0 = days_of_week.index(start_day) # Get number of start day

calendar_output = pd.DataFrame()   #Start output table
calendar_output = calendar_output.append([days_of_week]) # Insert days of week as header

# Add spacer at start of data to get clusters lined up on right day of week
spacer_start = []     
if d_0 > 0:
    for i in range(d_0):
        spacer_start = spacer_start + ["NaN"]

cluster_membership = spacer_start + cluster_membership.tolist()
print(len(cluster_membership))

# Add enough spacers at end to make total length of cluster_membership list a multiple of 7 (avoid index error below)
round_up = len(cluster_membership) % 7
print(round_up)
spacer_end = []
for i in range(7-round_up):             # For every spacer at start,
    spacer_end = spacer_end + ["NaN"]

cluster_membership = cluster_membership + spacer_end

# Go through cluster membership list and arrange in 7 day rows
day=1
while day < len(cluster_membership):
    counter = 0
    remaining_data = cluster_membership[day-1:]
    week_list = []
    while counter <= 6:
        week_list= week_list + [remaining_data[counter]]
        counter = counter + 1
    print(week_list)
    calendar_output = calendar_output.append([week_list])
    day = day + counter

calendar_output.to_csv("calendar_view=" + str(cutoff) + "_n="+ str(n) + ".csv", sep=',')

print("Have you entered the correct day of week for the start point?")

# Elbow and acceleration plot to CSV

# Pad acceleration plot so it fits in CSV with others
acceleration_rev_pad = [1000000]
for i in range(len(acceleration_rev)):
    acceleration_rev_pad = acceleration_rev_pad + [acceleration_rev[i]]
acceleration_rev_pad = acceleration_rev_pad + [1000000]

elbow_plot = pd.DataFrame({"Index": idxs, "Distance to Merge": last_rev, "Acceleration": acceleration_rev_pad})
elbow_plot.to_csv("elbow_plot_cutoff=" + str(cutoff) + "_n="+ str(n) + ".csv", sep=',')
