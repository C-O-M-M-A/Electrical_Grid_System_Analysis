# coding: utf-8
"""This script takes various exogenous variables and parses them to hourly resolution and common time index (GMT).
Diarmid Roberts 2019/07/17."""
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
import datetime

#####################################################
# Import and clean day-ahead electricity price data #
#####################################################

# import day_ahead price data
price_data = pd.read_csv('N2EX_hourly_2017_2019_calendar_year.csv', encoding='ISO-8859-1')
raw_price = price_data.ix[:, 'price_sterling']
date = price_data.ix[:, 'date']
hour_start_CET = [int(x[5:7]) for x in price_data.ix[:, 'hour']]

# Generate date-time indices
# Create year index
yyyy = [int(x[6:10]) for x in date]

# Create month index
mm = [int(x[3:5]) for x in date]

# Create day (of month) index
dd = [int(x[0:2]) for x in date]

# Create day of week index
day_of_week = []
for i in range(len(date)):
    day_name = datetime.datetime(yyyy[i], mm[i], dd[i]).strftime("%A")  # Get day name
    day_of_week = day_of_week + [day_name]

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
print(len(yyyy))

##################################
# Import UK wholsesale gas price #
##################################

# Create monthly wholesale gas price dictionary
gas_price_key = pd.read_csv('wholesale_gas_price_monthly.csv', encoding='ISO-8859-1')
gas_price_dict = {(gas_price_key.ix[:, 'year'][i], gas_price_key.ix[:, 'month'][i]):
                      gas_price_key.ix[:, 'price'][i]
                      for i in range(len(gas_price_key))
                      }

# For every hour, add current monthly average gas price using above dictionary
gas_price = []
for i in range(len(price)):
    gas_price = gas_price + [gas_price_dict[yyyy[i], mm[i]]]





# Export in CSV format

GP_data_set = pd.DataFrame({"YYYY": yyyy,
                            "MM": mm,
                            "DD": dd,
                            "Day of Week": day_of_week,
                            "Hour start CET": hour_start_CET,
                            "Month Average Gas Price": gas_price,
                            "Day Ahead Electricity Price": price
})

GP_data_set.to_csv('hourly_grid_data_set_output.csv', sep=',')