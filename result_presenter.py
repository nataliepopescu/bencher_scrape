# Python 3
#
# Natalie Popescu (Adapted from Ziyang Xu)
# Jan 22, 2021
#
# Present results in HTML

import argparse
import os
import json
import numpy as np
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import plotly.express as px
import math

# some setting for plot
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.config.suppress_callback_exceptions = True

graph_styles = {
    0: {
        "bar-name": "Vanilla Rustc",
        "bar-color": "#FF4500"
    },
    1: {
        "bar-name": "Rustc No Slice Bounds Checks",
        "bar-color": "#FFA500"
    },
    2: {
        "bar-name": "Speedup",
        "bar-color": "#FEA500"
    }
}

# geometric mean helper
def geomean_overflow(iterable):
    locarr = []
    for i in iterable:
        if i == 0:
            locarr.append(10**-100)
        else:
            locarr.append(i)
    # convert all elements to positive numbers
    a = np.log(locarr)
    return np.exp(a.sum() / len(a))

# arithmetic mean helper
#def arithmean_overflow(iterable):
#    rng_avg = 0
#    count = 1
#    for i in iterable:
#        rng_avg += (i - rng_avg) / count
#        count += 1
#    return rng_avg

# helper for checking if a datafile has no data
def is_empty_datafile(filepath):
    handle = open(filepath, 'r')
    for line in handle: 
        if line[:1] == '#':
            continue
        else:
            return False
    return True

class ResultProvider:

    # complete object has the following fields: 
    # - root
    # - datafile
    # - crates
    # - options
    # - better
    # - worse
    # - neither
    def __init__(self, root):
        self.root = root
        self.datafile = "crunched.data"

        # populate list of crates
        self.crates = []
        for name in os.listdir(self.root):
            if os.path.isdir(os.path.join(self.root, name)):
                self.crates.append(name)
        self.crates.sort()

        # populate options array for drop-down menu
        self.options = []
        for crate in self.crates:
            self.options.append({'label': crate, 'value': crate})

    def get_speedups(self):
        # clearly categorized benchmark results
        self.better = dict()
        self.worse = dict()
        self.neither = dict()
        self.better_ = dict()
        self.worse_ = dict()
        for c in self.crates: 
            # FIXME
            filepath = os.path.join(self.root, c, "results_o3_dbg2_embed=yes", self.datafile)
            if is_empty_datafile(filepath) or not os.path.exists(filepath):
                continue
            # open data file for reading
            handle = open(filepath)

            for line in handle: 
                if line[:1] == '#':
                    continue
                cols = line.split()
                # <crate_name>::<benchmark_name>
                name = c + "::" + cols[0]

                if not len(cols) == 5: 
                    exit("file at <" + filepath + "> is improperly formatted; "\
                    "expected 5 columns but got " + len(cols))

                unmod_time = cols[1]
                unmod_error = cols[2]
                bcrm_time = cols[3]
                bcrm_error = cols[4]

                # get speedup
                if math.isclose(float(unmod_time), float(bcrm_time), rel_tol=1e-6): 
                    speedup = 1
                elif math.isclose(float(bcrm_time), float(0), rel_tol=1e-6):
                    speedup = -1 # FIXME how does this show up?
                else: 
                    speedup = float(unmod_time) / float(bcrm_time)

                # categorize speedup: better, worse, neither
                if speedup < 0.97: 
                    self.worse[name] = speedup
                    # exlcude outliers
                    if speedup > 0.4:
                        self.worse_[name] = speedup
                elif speedup > 1.03: 
                    self.better[name] = speedup
                    # exclude outliers
                    if speedup < 1.6:
                        self.better_[name] = speedup
                else:
                    self.neither[name] = speedup

def get_overview_layout(rp):
    rp.get_speedups()
    # for counting + average calc
    all_bmarks = {**rp.better, **rp.worse, **rp.neither}
    trimmed_bmarks = {**rp.better_, **rp.worse_, **rp.neither}
    # for maximum/potential speedup calc
    mock_all = list(rp.better.values()) + [1] * len(rp.worse) + list(rp.neither.values())
    mock_trimmed = list(rp.better_.values()) + [1] * len(rp.worse_) + list(rp.neither.values())

    trace = go.Histogram(x=list(all_bmarks.values()), nbinsx=100, autobinx=False)
    fig_hist = go.Figure({
        'data': trace,
        'layout': {
            'title': 'Histogram of Speedups',
            'xaxis': {
                'linecolor': 'black',
                'ticks': 'outside',
                'mirror': 'all',
                'showline': True, 
                'nticks': 100,
                'title': {'text': 'Speedup'},
            },
            'yaxis': {
                'linecolor': 'black',
                'ticks': 'outside',
                'mirror': 'all',
                'showline': True, 
                'gridcolor':'rgb(200,200,200)', 
                'nticks': 50,
                'title': {'text': 'Number of Benchmarks'},
            },
            'font': {'family': 'Helvetica', 'color': 'black', 'size': 16},
            'plot_bgcolor': 'white',
            'autosize': False,
            'bargap': 0.2,
            'width': 2000, 
            'height': 700}
        })

    def make_graph(d):
        trace = {'x': list(d.keys()), 'y': list(d.values()), 'type': 'bar', 
                'name': graph_styles.get(2).get('bar-name'), 
                'marker_color': graph_styles.get(2).get('bar-color')}
        return go.Figure({
            'data': trace,
            'layout': {
                'xaxis': {
                    'linecolor': 'black',
                    'showline': True, 
                    'linewidth': 2,
                    'mirror': 'all',
                    'nticks': 10,
                    'showticklabels': True,
                    'title': {'text': 'Benchmarks'},
                },
                'yaxis': {
                    'showline': True, 
                    'linewidth': 2,
                    'ticks': 'outside',
                    'mirror': 'all',
                    'linecolor': 'black',
                    'gridcolor': 'rgb(200,200,200)', 
                    'nticks': 20,
                    'title': {'text': 'Speedup'},
                },
                'font': {'family': 'Helvetica', 'color': 'black', 'size': 16},
                'plot_bgcolor': 'white',
                'autosize': False,
                'width': 2000, 
                'height': 700}
            })

    fig_better = make_graph(rp.better)
    fig_worse = make_graph(rp.worse)
    fig_neither = make_graph(rp.neither)

    layout = html.Div([
        # to calculate: 
        # - overall average speedup
        #   - with and without outliers
        # - max potential speedup
        #   - with and without outliers
        # - average speedup within selected category
        #   - with and without outliers
        # to visualize: 
        # - histogram
        # - bar chart per category
        html.Br(),
        html.H3('All benchmarks'),
        html.H5('Total number of benchmarks: {}'.format(len(all_bmarks))),
        html.H5('Total number of benchmarks (- outliers): {}'.format(len(trimmed_bmarks))),
        html.H5('Average speedup across all benchmarks: {}'.format(geomean_overflow(list(all_bmarks.values())))),
        html.H5('Average speedup across all benchmarks (- outliers): {}'.format(geomean_overflow(list(trimmed_bmarks.values())))),
        html.H5('Potential speedup across all benchmarks: {}'.format(geomean_overflow(mock_all))),
        html.H5('Potential speedup across all benchmarks (- outliers): {}'.format(geomean_overflow(mock_trimmed))),
        html.Br(),
        dcc.Graph(
            id='histogram',
            figure=fig_hist
        ),
        html.Br(),

        html.H3('Benchmarks where removing bounds checks IMPROVES performance'),
        html.H5('Total number of benchmarks in this category: {}'.format(len(rp.better))),
        html.H5('Total number of benchmarks in this category (- outliers): {}'.format(len(rp.better_))),
        html.H5('Average speedup across benchmarks in this category: {}'.format(geomean_overflow(list(rp.better.values())))),
        html.H5('Average speedup across benchmarks in this category (- outliers): {}'.format(geomean_overflow(list(rp.better_.values())))),
        html.Br(),
        dcc.Graph(
            id='better-graph',
            figure=fig_better
        ),
        html.Br(),

        html.H3('Benchmarks where removing bounds checks HURTS performance'),
        html.H5('Total number of benchmarks in this category: {}'.format(len(rp.worse))),
        html.H5('Total number of benchmarks in this category (- outliers): {}'.format(len(rp.worse_))),
        html.H5('Average speedup across benchmarks in this category: {}'.format(geomean_overflow(list(rp.worse.values())))),
        html.H5('Average speedup across benchmarks in this category (- outliers): {}'.format(geomean_overflow(list(rp.worse_.values())))),
        html.Br(),
        dcc.Graph(
            id='worse-graph',
            figure=fig_worse
        ),
        html.Br(),

        html.H3('Benchmarks where removing bounds checks trivially affects performance'),
        html.H5('Total number of benchmarks in this category: {}'.format(len(rp.neither))),
        html.H5('Average speedup across benchmarks in this category: {}'.format(geomean_overflow(list(rp.neither.values())))),
        html.Br(),
        dcc.Graph(
            id='neither-graph',
            figure=fig_neither
        ),
        html.Br(),
    ])

    return layout

#@app.callback(dash.dependencies.Output('crate-content', 'children'),
#              [dash.dependencies.Input('result_type', 'value')])
#def display_crate_info(result_type):
#    print("right here")
#    print(rp)
#    return display_overview(rp)
#
#def display_overview(rp):

#def display_diff(crate_name, crate_opt):
#
#    no_baseline = 0
#    no_tocompare = 0
#
#    if (not os.path.exists(file_baseline)) or is_empty_datafile(file_baseline): 
#        no_baseline = 1
#    if (not os.path.exists(file_tocompare)) or is_empty_datafile(file_tocompare):
#        no_tocompare = 1
#    if no_baseline == 1 and no_tocompare == 1: 
#        return "\n\nNo diff data for [" + str(crate_name) + "] with these settings."
#    elif no_baseline == 0 and no_tocompare == 1: 
#        return "\n\nMISMATCH: No diff data for [" + str(crate_name) + "] with the ~to compare~ setting."
#    elif no_baseline == 1 and no_tocompare == 0: 
#        return "\n\nMISMATCH: No diff data for [" + str(crate_name) + "] with the ~baseline~ setting."
#
#    def get_one_bar(rustc_type, bar_name, color):
#        one_bmark_list = []
#        one_perf_list = []
#        one_y_error_list = []
#
#        # open files for reading
#        handle_baseline = open(file_baseline, 'r')
#        handle_tocompare = open(file_tocompare, 'r')
#
#        col = rustc_type * 2 + 1
#
#        for line_baseline, line_tocompare in zip(handle_baseline, handle_tocompare):
#            if line_baseline[:1] == '#':
#                continue
#
#            # get columns from files
#            cols_baseline = line_baseline.split()
#            cols_tocompare = line_tocompare.split()
#
#            # get benchmark names for this crate
#            name = cols_baseline[0]
#            one_bmark_list.append(name)
#
#            # get times from specified (column * 2 + 1)
#            time_baseline = cols_baseline[col]
#            time_tocompare = cols_tocompare[col]
#            error = cols_tocompare[col + 1]
#
#            # calculate the percent speedup or slowdown
#            div = float(time_baseline) if float(time_baseline) != 0 else 1
#            perc_time = ((float(time_tocompare) - float(time_baseline)) / div) * 100
#            one_perf_list.append(perc_time)
#
#            div = float(time_tocompare) if float(time_tocompare) != 0 else 1
#            perc_e = (float(error) / div) * 100
#            one_y_error_list.append(perc_e)
#
#
#        handle_baseline.close()
#        handle_tocompare.close()
#
#        bar_one = {'x': one_bmark_list, 'y': one_perf_list, 'error_y': {'type': 'data', 'array': one_y_error_list},
#                   'type': 'bar', 'name': bar_name, 'marker_color': color}
#        return bar_one
#
#
#    bar_list = []
#    #if ("bcrm" in crate_opt) or ("mir" in crate_opt):
#    bar_unmod = get_one_bar(0, graph_styles.get(0).get("bar-name"), graph_styles.get(0).get("bar-color"))
#    bar_bcrm = get_one_bar(1, graph_styles.get(1).get("bar-name"), graph_styles.get(1).get("bar-color"))
#
#    bar_list = [bar_unmod, bar_bcrm]
#    #else:
#    #    bar_unmod = get_one_bar(0, graph_styles.get(0).get("bar-name"), graph_styles.get(0).get("bar-color"))
#    #    bar_bcrm = get_one_bar(1, graph_styles.get(1).get("bar-name"), graph_styles.get(1).get("bar-color"))
#    #    bar_both = get_one_bar(2, graph_styles.get(2).get("bar-name"), graph_styles.get(2).get("bar-color"))
#    #    bar_safelib = get_one_bar(3, graph_styles.get(3).get("bar-name"), graph_styles.get(3).get("bar-color"))
#
#    #    bar_list = [bar_unmod, bar_bcrm, bar_both, bar_safelib]
#
#    fig = go.Figure({
#                    'data': bar_list,
#                    'layout': {
#                        'legend': {'orientation': 'h', 'x': 0.2, 'y': 1.3},
#                        'yaxis': {
#                            'showline': True, 
#                            'linewidth': 2,
#                            'ticks': "outside",
#                            'mirror': 'all',
#                            'linecolor': 'black',
#                            'gridcolor':'rgb(200,200,200)', 
#                            'nticks': 20,
#                            'title': {'text': bencher_switcher.get(crate_opt).get("y-axis-label")},
#                        },
#                        'xaxis': {
#                            'linecolor': 'black',
#                            'showline': True, 
#                            'linewidth': 2,
#                            'mirror': 'all',
#                            'nticks': 10,
#                            'showticklabels': True,
#                            'title': {'text': "Benchmarks"},
#                        },
#                        'font': {'family': 'Helvetica', 'color': "Black"},
#                        'plot_bgcolor': 'white',
#                        'autosize': False,
#                        'width': 1450, 
#                        'height': 700}
#                    })
#
#        
#    return html.Div([
#        dcc.Graph(
#            id='rustc-compare-ltos',
#            figure=fig
#        )
#    ])
#
#
#def display_relative(crate_name, crate_opt): 
#
#    if "crit" in crate_opt:
#        filepath = path_to_criterion + "/" + crate_name + "/" + criterion_switcher.get(crate_opt).get("dir") + "/" + data_file_new
#    elif "bcrm" in crate_opt:
#        filepath = path_to_bencher + "/" + crate_name + "/" + bencher_switcher.get(crate_opt).get("dir") + "/" + data_file_new
#    else: 
#        filepath = path_to_bencher + "/" + crate_name + "/" + bencher_switcher.get(crate_opt).get("dir") + "/" + data_file
#
#    if (not os.path.exists(filepath)) or is_empty_datafile(filepath):
#        return "\n\nNo relative data for [" + str(crate_name) + "] with these settings."
#
#    speedup_arr = []
#
#    def get_one_bar_rel(rustc_type, bar_name, color):
#        one_bmark_list = []
#        one_perf_list = []
#        one_y_error_list = []
#
#        # open file for reading
#        handle = open(filepath, 'r')
#
#        for line in handle:
#            if line[:1] == '#':
#                continue
#            cols = line.split()
#
#            # get benchmark names for this crate
#            name = cols[0]
#            one_bmark_list.append(name)
#
#            # get baseline (unmod times) to compare this version againt
#            unmod = cols[1]
#            unmod_error = cols[2]
#
#            # get the times from the specified (column * 2 + 1)
#            col = rustc_type * 2 + 1
#            time = cols[col]
#            error = cols[col + 1]
#
#            # calculate the percent speedup or slowdown
#            div = float(unmod) if float(unmod) != 0 else 1
#            perc_time = ((float(time) - float(unmod)) / div) * 100
#            div_e = float(time) if float(time) != 0 else 1
#            perc_e = (float(error) / div_e) * 100
#
#            # calculate actual speedup
#            speedup_div = 1 + (perc_time / 100)
#            speedup = 1 if speedup_div == 0 else 1 / speedup_div
#            #speedup = 1 / (1 + (perc_time / 100))
#            speedup_arr.append(speedup)
#
#            one_perf_list.append(perc_time)
#            one_y_error_list.append(perc_e)
#
#        handle.close()
#
#        color_e = 'black' if rustc_type != 0 else color
#
#        bar_one = {'x': one_bmark_list, 'y': one_perf_list, 'error_y': {'type': 'data', 'array': one_y_error_list, 'color': color_e},
#                   'type': 'bar', 'name': bar_name, 'marker_color': color}
#
#        return bar_one
#
#    
#    bar_list = []
#    #if "bcrm" in crate_opt: #.startswith("bcrm"):
#    #bar_unmod = get_one_bar_rel(0, graph_styles.get(0).get("bar-name"), graph_styles.get(0).get("bar-color"))
#    bar_bcrm = get_one_bar_rel(1, graph_styles.get(1).get("bar-name"), graph_styles.get(1).get("bar-color"))
#
#    bar_list = [bar_bcrm]
#    #bar_list = [bar_unmod, bar_bcrm]
#
#    #else: 
#    #    bar_unmod = get_one_bar_rel(0, graph_styles.get(0).get("bar-name"), graph_styles.get(0).get("bar-color"))
#    #    bar_nobc = get_one_bar_rel(1, graph_styles.get(1).get("bar-name"), graph_styles.get(1).get("bar-color"))
#    #    bar_both = get_one_bar_rel(2, graph_styles.get(2).get("bar-name"), graph_styles.get(2).get("bar-color"))
#    #    bar_safelib = get_one_bar_rel(3, graph_styles.get(3).get("bar-name"), graph_styles.get(3).get("bar-color"))
#
#    #    bar_list = [bar_unmod, bar_nobc, bar_both, bar_safelib]
#
#    fig = go.Figure({
#                    'data': bar_list,
#                    'layout': {
#                        'legend': {'orientation': 'h', 'x': 0.2, 'y': 1.3},
#                        'yaxis': {
#                            'showline': True, 
#                            'linewidth': 2,
#                            'ticks': "outside",
#                            'mirror': 'all',
#                            'linecolor': 'black',
#                            'gridcolor':'rgb(200,200,200)', 
#                            'nticks': 20,
#                            'title': {'text': " Performance Relative to Vanilla [%]"},
#                        },
#                        'xaxis': {
#                            'linecolor': 'black',
#                            'showline': True, 
#                            'linewidth': 2,
#                            'mirror': 'all',
#                            'nticks': 10,
#                            'showticklabels': True,
#                            'title': {'text': "Benchmarks"},
#                        },
#                        'font': {'family': 'Helvetica', 'color': "Black"},
#                        'plot_bgcolor': 'white',
#                        'autosize': False,
#                        'width': 1450, 
#                        'height': 700}
#                    })
#
#    geo_speedup = geomean_overflow(speedup_arr)
#
#    return html.Div([
#        html.Br(),
#        html.Label('Average Speedup for [' + crate_name + ']: ' + str(geo_speedup)),
#        html.Br(),
#        html.Label(str(len(speedup_arr)) + ' Benchmarks'),
#        dcc.Graph(
#            id='rustc-compare-graph-rel',
#            figure=fig
#        )
#    ])


def display_significant(result_type):
    one_bmark_list = []
    one_perf_list = []
    one_yerror_list = []

    # array for just tracking the speedup in the BETTER, WORSE, or neither
    speedup_arr_setting = dict() # make dictionary: speedup -> name
    # all speedup (for histogram)
    speedup_arr = []
    max_benefit = []
    histo_arr = []

    def get_one_bar(bar_name, bar_color):
        #if speedup < 1.6 and speedup > 0.4:
        #    speedup_arr.append(speedup)
        #if speedup >= 1 and speedup < 1.6: 
        #    max_benefit.append(speedup)
        #else: 
        #    max_benefit.append(1)
        ##if speedup < 350:
        #histo_arr.append(speedup)

        div_e = float(bcrm_time) if float(bcrm_time) != 0 else 1
        perc_error = (float(bcrm_error) / div_e) * 100
        unmod_perc_error = (float(unmod_error) / div) * 100

        # if positive and worse
        #if result_type == 'worse' and perc_time > 0:
        #    # perc_time is within unmod stdev
        #    # stdev magnitude is larger than perc_time magnitude
        #    # perc_time magnitude is less than 3%
        #    if not (perc_time < float(unmod_perc_error) or perc_time < float(perc_error) or perc_time < 3):
        #    #if speedup < 1 and speedup > 0.4:
        #    #    speedup_arr_setting[speedup] = name
        #    #else:
        #    one_bmark_list.append(name)
        #    one_perf_list.append(perc_time)
        #    one_yerror_list.append(perc_error)
        ## if negative and better
        #elif result_type == 'better' and perc_time < 0:
        #    # perc_time is within unmod stdev
        #    # stdev magnitude is larger than perc_time magnitude
        #    # perc_time magnitude is less than 3%
        #    if not (abs(perc_time) < float(unmod_perc_error) or abs(perc_time) < float(perc_error) or abs(perc_time) < 3):
        #    #if speedup > 1 and speedup < 1.6:
        #    #    speedup_arr_setting[speedup] = name
        #    #else:
        #    one_bmark_list.append(name)
        #    one_perf_list.append(perc_time)
        #    one_yerror_list.append(perc_error)
        ## add rest of benchmarks to this graph
        #elif result_type == 'neither': # and perc_time < 0:
        #    if abs(perc_time) < float(unmod_perc_error) or abs(perc_time) < float(perc_error) or abs(perc_time) < 3:
        #        one_bmark_list.append(name)
        #        one_perf_list.append(perc_time)
        #        one_yerror_list.append(perc_error)
        #        speedup_arr_setting[speedup] = name

        color_e = 'black'
        bar_one = {'x': one_bmark_list, 'y': one_perf_list, 'error_y': {'type': 'data', 'array': one_yerror_list, 'color': color_e},
                    'type': 'bar', 'name': bar_name, 'marker_color': bar_color}        
        return {0: bar_one, 1: len(one_bmark_list), 2: bmark_ctr}

    results = get_one_bar(graph_styles.get(1).get("bar-name"), graph_styles.get(1).get("bar-color"))
    bar_list = results.get(0)
    num_bmarks = results.get(1)
    total_num_bmarks = results.get(2)

    fig = go.Figure({
                    'data': bar_list,
                    'layout': {
                        'legend': {'orientation': 'h', 'x': 0.2, 'y': 1.3},
                        'yaxis': {
                            'showline': True, 
                            'linewidth': 2,
                            'ticks': "outside",
                            'mirror': 'all',
                            'linecolor': 'black',
                            'gridcolor':'rgb(200,200,200)', 
                            'nticks': 20,
                            'title': {'text': " Performance Relative to Vanilla [%]"},
                        },
                        'xaxis': {
                            'linecolor': 'black',
                            'showline': True, 
                            'linewidth': 2,
                            'mirror': 'all',
                            'nticks': 10,
                            'showticklabels': True,
                            'title': {'text': "Benchmarks"},
                        },
                        'font': {'family': 'Helvetica', 'color': "Black"},
                        'plot_bgcolor': 'white',
                        'autosize': False,
                        'width': 2450, 
                        'height': 1000}
                    })

    trace = go.Histogram(x=histo_arr, nbinsx=100, autobinx=False)
    fig_hist = go.Figure({
                    'data': trace, #, cumulative_enabled=True),
                    'layout': {
                        'title': "Histogram of Benchmark Speedups",
                        'xaxis': {
                            'linecolor': 'black',
                            'showline': True, 
                            'nticks': 100,
                            'title': {'text': "Speedup"},
                            #'autobinx': False,
                        },
                        'yaxis': {
                            'linecolor': 'black',
                            'ticks': "outside",
                            'showline': True, 
                            'gridcolor':'rgb(200,200,200)', 
                            'nticks': 50,
                            'type': "log",
                            'title': {'text': "Number of Benchmarks"},
                        },
                        'font': {'family': 'Helvetica', 'color': "Black"},
                        'plot_bgcolor': 'white',
                        'autosize': False,
                        'bargap': 0.2,
                        'width': 4000, 
                        'height': 1000}
                    })
    
    # add vertical line designating slowdown => speedup shift
    #fig_hist.add_shape(
    #    dict(
    #        type="line",
    #        x0=1,
    #        x1=1,
    #        y0=0,
    #        y1=500,
    #        line=dict(
    #            color="OrangeRed",
    #            width=4,
    #            dash="dot",
    #        )
    #    )
    #)

    if result_type == 'neither':
        avg_speedup_setting = "Not calculated"
    else: 
        avg_speedup_setting = geomean_overflow(list(speedup_arr_setting))
    avg_speedup = geomean_overflow(speedup_arr)
    max_ben = geomean_overflow(max_benefit)
    num_bmarks_considered = len(speedup_arr)

    def ordered_benchmarks(dic): 
        for i in sorted(dic):
            print((str(i), dic[i]), flush=True)
        
    return html.Div([
        html.Br(),
        html.Label('Number of Benchmarks in this graph: ' + str(num_bmarks)),
        html.Label('Total Number of Benchmarks: ' + str(total_num_bmarks)),
        html.Br(),
        html.Label('Average Speedup [of benchmarks in graph where speedup < 1.6] = ' + str(avg_speedup_setting)),
        html.Label('Average Speedup [total of ' + str(num_bmarks_considered) + ' benchmarks where speedup < 1.6] = ' + str(avg_speedup)),
        html.Label('Potential Speedup [total of benchmarks where speedup < 1.6] = ' + str(max_ben)),
        html.Br(),
        dcc.Graph(
            id='significant-res-graph',
            figure=fig
        ),
        html.Br(),
        html.Label(ordered_benchmarks(speedup_arr_setting)),
        html.Br(),
        dcc.Graph(
            id='histogram',
            figure=fig_hist
        )
    ])

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--root_path",
            type=str,
            required=False,
            default="./criterion_rev_deps/",
            help="root path of scraped crates directory with benchmark results; "\
            "default is ./criterion_rev_deps/")
    parser.add_argument("-p", "--port",
            type=str,
            required=False,
            default="8050",
            help="port for Dash server to run; 8050 or 8060 on AWS")
    args = parser.parse_args()
    return args.root_path, args.port

@app.callback(dash.dependencies.Output('page-content', 'children'),
              [dash.dependencies.Input('url', 'pathname')])
def display_page(pathname):
    if not pathname:
        return 404
    if pathname == '/':
        pathname = '/passOverview'
    if pathname == '/passOverview':
        layout = get_overview_layout(app._result_provider)
        return layout
    else:
        return 404

if __name__ == '__main__':
    root_path, port = parseArgs()
    app._result_provider = ResultProvider(root_path)

    app.layout = html.Div([
        dcc.Location(id='url', refresh=False),
        dcc.Link('Results Overview', href='/passOverview'),
        html.Br(),
        html.Div(id='page-content')
    ])

    app.run_server(debug=False, host='0.0.0.0', port=port)

