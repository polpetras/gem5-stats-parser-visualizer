#   This file is part of gem5-stats-parser-visualizer
# 
#   gem5-stats-parser-visualizer is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, version 3.
# 
#   gem5-stats-parser-visualizer is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#   GNU General Public License for more details.
# 
#   You should have received a copy of the GNU General Public License
#   along with gem5-stats-parser-visualizer. If not, see <http://www.gnu.org/licenses/>.

import re
import os
import csv
import sys
import numpy as np
from os import listdir
from os.path import isfile, join
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages
import traceback
#import glob

# Format of Stats we are interested in
# The user provides info about these stats using an input csv file
# An example can be:
# system.ruby.network.average_packet_vqueue_latency ,value,Queue Latency,500
#
# Also complex stats can be provided like the following:
# system.ruby.network.router_flit_queueing_latency / system.ruby.network.router_flits_received ,value,Queue Latency,500
#
# The input.csv should have 4 columns:
# 1) statname (or stat1 / stat2), that we want to chart.
#    If stat1/stat2 is defined then this stat is considered a complex stat
# 2) Second column (stat_type), should contain one of: value, percent, cumm_percent
#    (Currently only value is supported)
# 3) Third column: Title of the chart (description)
# 4) Fourth column (calculation): An int value X, The chart values are divided by X
#    This is basically used for graph units conversion, e.g:
#    - Convert bytes to GB
#    - Convert ticks (picoseconds) to cycles (by dividing with 500 for a 2GHz NoC clock)
#
class Stat:
    def __init__(self,name,type,description,calculation):
        if '/' in name:
            spl = name.split('/')
            self.name = spl[0]
            self.name2 = spl[1].lstrip()
            self.isComplex = True
        else:
            self.name = name
            self.name2 = ''
            self.isComplex = False
        self.type = type
        self.description = description

        if (calculation == ''):
            self.calculation = 0.0
        else:
            self.calculation = float(calculation)

    def print(self,idx):
        printd('Stat[%d] [isComplex=%s]: %s / %s -- %s  -- %s'
            %(idx, self.isComplex, self.name,
              self.name2, self.type, self.description))


# List directories found in the current directory,
# that contain string 'filter_str'
def get_dirs_current_path(path, filter_str):
    return [f for f in sorted(listdir(path))
            if (not isfile(join(path, f) ) and (filter_str in f) )]


# Returns roi files list for a given directory
# Skipping .short ROI files
def get_rois_list(path):
    return [f for f in sorted(listdir(path)) if ('roi' in f and 'short' not in f)]

# Returns roi files list for a given directory, with .short extension
def get_short_rois_list(path):
    return [f for f in sorted(listdir(path)) if 'short' in f]


# returns a list of Stat instances
def get_attr_from_csv(input_fname):

    # Attributes contained in the csv e.g: 'system.bigCluster0.cpu0.iq.rate'
    search_attributes = []

    # Graph type can be one of the: value, percent, cumm_percent
    graph_type_per_attr = []
    units_row = []
    stat_calculation = []
    pattern = r'^(.*)\[(\d+)-(\d+)\](.*)$'

    with open(input_fname) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            # Ignore Comments
            if '#' in row[0]:
                continue
            # Save attribute name
            #search_attributes.append(row[0].strip())
            stat_name = row[0]

            # if stat name contains a range e.g: cpus[0-15], expand that range to several single stats
            if '[' in stat_name:
                match = re.search(pattern, stat_name)
                if match:
                    before_text = match.group(1)
                    start = int(match.group(2))
                    end = int(match.group(3))
                    after_text = match.group(4)
                    assert(start < end)

                else:
                    print('WARNING: No match found for range expression')
                    assert(0)
            else:
                start = 0
                end = 0

            for counter in np.arange(0, end - start + 1):
                if (start == end) and (start == 0):
                    search_attributes.append(row[0])
                else:
                    newname = before_text+ str(start+counter) +after_text
                    search_attributes.append(newname)
                    #print('APPENDING: %s' % newname)

                # Save user's input regarding which stats column should be used
                # for graphs
                graph_type = row[1].strip()

                # Any of those 3 columns can be used in the graph
                # TODO: Currently only value is supported
                assert( graph_type == 'percent' or
                    graph_type == 'value' or
                    graph_type == 'cumm_percent')

                graph_type_per_attr.append(graph_type)

                # The 3rd column of the csv, will be put in units_row,
                # and will be used as a Y-axis label.
                units_row.append(row[2].strip())

                stat_calculation.append(row[3].strip())

    #Check input.csv for duplicates
    for i in np.arange(0, len(search_attributes), 1):
        for j in np.arange(0, len(search_attributes), 1):
            if i == j:
                continue
            else:
                if search_attributes[i] == search_attributes[j]:
                    print('ERROR: Your input file contains duplicate search attributes: %s'
                          % search_attributes[i])
                    sys.exit()

    retlist = []
    for i in np.arange(0, len(search_attributes)):
        retlist.append(Stat(search_attributes[i], graph_type_per_attr[i], units_row[i], stat_calculation[i]))

    return retlist

# Debug prints
def printd(s):
    if Debug:
        print(s)

# Generate smaller stats files
# that contain only the stats we are interested in
# These files will have .short extension
def generate_short_ROIs(simdirs, selected_attrs):

    number_of_rois = 0

    for dir in simdirs:
        printd('--- Directory: %s ---'%dir)
        roi_cnt = 0
        for f in get_rois_list(dir):
            roifile = dir+'/'+ f
            printd('--- ROI file: %s --- '%roifile)
            roi_cnt += 1
            fl = open(roifile)
            keep_stat_lines = []

            for ln in fl:
                for attr in selected_attrs:
                    if (attr.name in ln) or (attr.isComplex and attr.name2 in ln):
                        if ' nan ' in ln:
                            ln = ln.replace(' nan ', ' 0 ')
                        keep_stat_lines.append(ln)
                        #print('Keeping: %s' % ln[:-1])
                        break

            # The following adds missing stats we are interested in
            for attr in selected_attrs:
                nameFound = False
                name2Found = False
                for ln in keep_stat_lines:
                    if (attr.name in ln):
                        nameFound = True
                    if (attr.isComplex and attr.name2 in ln):
                        name2Found = True
                if not nameFound:
                    keep_stat_lines.append('%s 0 # Missing stat\n' % attr.name)
                if (attr.isComplex and (not name2Found)):
                    keep_stat_lines.append('%s 0 # Missing stat\n' % attr.name2)
            keep_stat_lines.sort()

            ## Keeping a smaller roi stats file with only the stats we are interested in
            fl2 = open(roifile+'.short', 'w')
            for ln in keep_stat_lines:
                fl2.write('%s'%ln)

        if( number_of_rois == 0):
            number_of_rois = roi_cnt
        else:
            assert(number_of_rois == roi_cnt)

    return number_of_rois

# Parses stat name and values from a stat line
# Returns a list where
# First element is the stat_name
# Second element is a list with the values of this stat
def parse_stat(ln):
    ret = ln.split('#')[0]
    ret = ret.split(' ')
    ret2 = [f for f in ret if (f!='' and f!='|' and '(' not in f)]
    # Characters to remove
    chars_to_remove = "|%"

    # Removing the specified characters from each string in the list
    values = [s.replace('|', '').replace('%', '') for s in ret2[1:]]
    return [ret2[0], values]

def add_stats_in_dataframe(simdirs, selected_attrs):

    sim_cnt = 0
    df = pd.DataFrame(columns = df_cols)

    for dir in simdirs:
        roi_cnt = 0
        printd('--- Directory: %s ---'%dir)
        short_roi_list = get_short_rois_list(dir)

        # [:-1] to ignore last ROI
        if ignore_last_roi:
            short_roi_list = short_roi_list[:-1]

        for f in short_roi_list:
            roifile = dir+'/'+ f
            printd('--- Working on ROI file: %s --- '%roifile)
            fl = open(roifile)

            for ln in fl:
                ret = parse_stat(ln)
                new_row_df = pd.DataFrame([ [ sim_cnt, roi_cnt, ret[0], ret[1] ] ], columns=df_cols)
                df = pd.concat([df, new_row_df], ignore_index=True)

            roi_cnt += 1
        sim_cnt += 1

    return df


# Filter a given Data frame accorind to a stat string (or substring)
# We are stripping the filter_str because sometimes the selected attrs contain spaces in purpose
# E.g. If we want to get busUtil stat, but not busUtilRead or busUtilWrite
#
def filter_dataframe(df, filter_str):
    filtered_df = df[df['stat_name'].str.contains(filter_str.strip())]
    return filtered_df

# prints a dataframe row by row
def print_dataframe(df):
    print('Index\t\t: sim_cnt -- roi_cnt -- stat_name -- stat_value')
    for index, row in df.iterrows():
        print('%d\t\t: %s -- %s -- \'%s\' -- %s' % (index, row[0], row[1], row[2], row[3]))


# Checks if a specific stat is multi-value or not
# Meaning that in the stats.txt it has multiple columns with values
# E.g. 1 value per VNET, or value and cummulative percentage etc.
# For example system.ruby.network.average_packet_vnet_latency | 3341.883113 | 1765.707927 | 3238.996918 | 3599.744934
# is multi value stat
def isMultiValueStat(stat_name, stat_df):
    #fdf = filter_dataframe(stat_df, stat_name)
    if len(stat_df['stat_value'].iloc[0]) > 1:
        return True
    else:
        return False

def autolabel(rects, ax):
    """
    Attach a text label above each bar displaying its height.
    """
    max = 0
    for rect in rects:
        for bar in rect:
            height = bar.get_height()
            if height > max:
                max = height
                plt.ylim([1, height*2])

            ax.annotate('{:,.2f}'.format(height),
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', rotation=90)

def get_plot_data(selected_attrs, df):

    if Create_pdf:
        pp = PdfPages(graph_pdf_fname)

    plot_num = 0
    barwidth = 0.2

    for attr in selected_attrs:

        if not attr.isComplex:
            printd('Plotting : \'%s\'' % attr.name)
        else:
            printd('Plotting : \'%s\' / \'%s\'' % (attr.name, attr.name2))

        fdf = filter_dataframe(df, attr.name)
        fdf = fdf.copy()

        if attr.isComplex:
            fdf2 = filter_dataframe(df, attr.name2)
            fdf2 = fdf2.copy()

        number_of_rois = fdf[fdf['sim_cnt'] == 0].shape[0]

        # make sure that all the simulations have the same number of ROIs
        # as the first simulation
        for i in np.arange(1, number_of_sims):
           assert(number_of_rois == fdf[fdf['sim_cnt'] == i].shape[0])

        if fdf.empty:
            print(f'WARNING:{attr.name} dataframe is empty')
            continue

        try:

            # Convert the stat_values to floats
            fdf['stat_value'] = fdf['stat_value'].apply(lambda lst: [float(x) for x in lst])
            if attr.isComplex:
                fdf2['stat_value'] = fdf2['stat_value'].apply(lambda lst: [float(x) for x in lst])

            # Count the number of values in value list
            # This is usually 1, 4 or 12
            value_len =  len(fdf['stat_value'].iloc[0])

            if attr.isComplex:
                value_len2 = len(fdf2['stat_value'].iloc[0])

            if(value_len == 12):
                # Keep first of every 3 values
                # TODO: if percent is specified keep second value of every 3 values
                # TODO: if cumm_percent is specified keep third value of every 3 values
                #
                fdf['stat_value'] = fdf['stat_value'].apply(lambda x: [x[i] for i in [0, 3, 6, 9]])
                value_len = 4
            if attr.isComplex and value_len2 == 12:
                fdf2['stat_value'] = fdf2['stat_value'].apply(lambda x: [x[i] for i in [0, 3, 6, 9]])
                value_len2 = 4

            if (value_len == 1) or (value_len == 4):

                # If there are many columns in values list
                # then we need to create a separate figure for each of the columns
                # Usually each column represents a single VNET (VNETs 0 to 3)
                for stat_column in np.arange(0, value_len):
                    rects = []
                    pltfig = plt.figure(plot_num, figsize=(12, 6))
                    plot_num += 1
                    ax = plt.subplot()
                    ax.grid(True)
                    plt.grid(True)

                    for i in np.arange(0, number_of_sims):

                        # Simple case where attr is not complex and we only plot 1 stat
                        # If attr.calculation is specified in input file just divide stat values by attr.calculation
                        if not attr.isComplex:
                            if attr.calculation > 0:
                                rect = ax.bar( range(i, number_of_rois*number_of_sims, number_of_sims),
                                                fdf[fdf['sim_cnt'] == i]['stat_value'].apply(lambda x: x[stat_column]).div(attr.calculation),
                                        color = g_colors[i%len(g_colors)], width=barwidth, label=labels[i])
                            else:
                                rect = ax.bar( range(i, number_of_rois*number_of_sims, number_of_sims),
                                            fdf[fdf['sim_cnt'] == i]['stat_value'].apply(lambda x: x[stat_column]),
                                    color = g_colors[i%len(g_colors)], width=barwidth, label=labels[i])
                        #
                        # More complex case, where we plot a stat divided by a second stat
                        #
                        else:
                            assert(not fdf2.empty)
                            df_vals = fdf[fdf['sim_cnt'] == i]['stat_value'].apply(lambda x: x[0]).reset_index(drop=True)
                            df2_vals = fdf2[fdf2['sim_cnt'] == i]['stat_value'].apply(lambda x: x[0]).reset_index(drop=True)

                            # if df2_vals contain zeros then we cannot plot these simulations
                            if 0.0 in df2_vals.values:
                                print(f'Cannot plot sim_cnt {i}, for stat {attr.name2}: division with 0 value')
                                continue

                            if attr.calculation > 0:
                                rect = ax.bar( range(i, number_of_rois*number_of_sims, number_of_sims),
                                                df_vals.div(df2_vals).div(attr.calculation),
                                        color = g_colors[i%len(g_colors)], width=barwidth, label=labels[i])
                            else:
                                rect = ax.bar( range(i, number_of_rois*number_of_sims, number_of_sims),
                                                df_vals.div(df2_vals),
                                        color = g_colors[i%len(g_colors)], width=barwidth, label=labels[i])

                        rects.append(rect)

                    # Generate a value label for each bar on the plot
                    autolabel(rects, ax)

                    plt.gca().set_ylim(bottom=0)

                    plt.xlabel('ROI #')
                    plt.ylabel(attr.description)
                    plt.legend(title='sim_cnt')

                    if (value_len == 4):
                        suffix = ' - VNET: %s'% VNETS[stat_column]
                    else:
                        suffix = ''

                    if not attr.isComplex:
                        plt.title('%s%s' % (attr.name, suffix), pad = 10)
                    else:
                        plt.title('%s / %s%s' % (attr.name, attr.name2,suffix), pad = 10)

                    plt.xticks([r*number_of_sims for r in range(number_of_rois)], np.arange(0,number_of_rois))
                    pp.savefig(pltfig, dpi=300, bbox_inches='tight')

        except Exception as e:
            print('Could not plot attribute: %s' % attr.name)
            print(e)
            print(traceback.format_exc())
            print('%s' % fdf)
            if attr.isComplex:
                print('%s' % fdf2)
            #exit(-1)

    pp.close()
    return 0


##### MAIN ####

# AMBA CHI VNETs
VNETS = ['REQ', 'SNP', 'RESP', 'DAT']

# You can adjust these labels according to your simulations
labels = ['sim_0001', 'sim_0002', 'sim_0003', 'sim_0004' ]

# The last ROI starts when our benchmark kernel finishes
# and until the simulator shuts down. Usually we don't need this ROI
# so we ignore it.
ignore_last_roi = True

plt.rcParams.update({'figure.max_open_warning': 0})

linestyles = ['-','--',':','-','--','-.', '-','--','-.','-','--','-.']
markers = ['.', '^', 'x' ]
g_colors = ['blue', 'orange', 'green', 'red', 'purple', 'darkorange', 'cornflowerblue']

graph_pdf_fname = 'graphs_out.pdf'

Create_pdf = True

Debug = True

filter_str_list = [ 'sim' ]

mypath = os.getcwd()

df_cols = ['sim_cnt', 'roi_cnt', 'stat_name', 'stat_value']

for filter_str in filter_str_list:
    simdirs = get_dirs_current_path(mypath, filter_str)

number_of_sims = len(simdirs)

printd('INFO: Number of sims: %d' % number_of_sims);

selected_attrs = get_attr_from_csv('./input/input.csv')

for idx, element in enumerate(selected_attrs):
    #print('Stat # %d' % idx)
    element.print(idx)

# Could skip this step if already generated
# This needs to be called everytime we adjust the input.csv file
generate_short_ROIs(simdirs, selected_attrs)

df = add_stats_in_dataframe(simdirs, selected_attrs)

get_plot_data(selected_attrs, df)

