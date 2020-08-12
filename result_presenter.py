# Python 3
#
# Natalie Popescu (Adapted from Ziyang Xu)
# July 1, 2020
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


path_to_crates = "./crates/crates"
data_file = "bench-sanity-CRUNCHED.data"
data_file_new = "bench-CRUNCHED.data"
data_file_geo = "bench-GEOMEAN.data"
crates = []

graph_styles = {
    0: {
        "bar-name": "Vanilla Rustc",
        "bar-color": "#FF4500"
    },
    1: {
        "bar-name": "Rustc No Slice Bounds Checks",
        "bar-color": "#FFA500"
    } #,
#    2: {
#        "bar-name": "Rustc No Slice Bounds Checks + Safe memcpy",
#        "bar-color": "#DDA0DD"
#    },
#    3: {
#        "bar-name": "Rustc Safe memcpy",
#        "bar-color": "#0571B0"
#    }
}

# rustc stuff
lto_off_1 = "results-lto-off-1"
lto_off_2 = "results-lto-off-2"
lto_thin_1 = "results-lto-thin-1"
lto_thin_2 = "results-lto-thin-2"
no_inline = "results-no-inline-lto-off"
agg_inline = "results-agg-inline-lto-off"
# out-of-tree llvm stuff
bcrm_o0 = "results-bcrmpass-embedbitcode-no-lto-off"
bcrm_o0_many = "results-bcrmpass-embedbitcode-no-lto-off-many"
bcrm_o3 = "results-bcrmpass-embedbitcode-no-lto-off-o3"
bcrm_o3_many = "results-bcrmpass-embedbitcode-no-lto-off-many-o3"
bcrm_o0_o3 = "results-bcrmpass-o0-embedbitcode-no-lto-off-o3"
# in-tree llvm stuff
bcrm_fpm = "results-bcrmpass-first"
bcrm_mpm = "results-bcrmpass-mpm"

switcher = {
    "lto-off-1": {
        "label": "1: [MIR modification] -C embed-bitcode=no -C opt-level=3",
        "dir": lto_off_1
    },
    "lto-off-2": {
        "label": "2: [MIR modification] -C embed-bitcode=no -C lto=off -C opt-level=3",
        "dir": lto_off_2
    },
    "lto-thin-1": {
        "label": "3: [MIR modification] -C embed-bitcode=yes -C opt-level=3",
        "dir": lto_thin_1
    },
    "lto-thin-2": {
        "label": "4: [MIR modification] -C embed-bitcode=yes =C lto=thin -C opt-level=3",
        "dir": lto_thin_2
    },
    "no-inline": {
        "label": "5: [MIR modification] -C llvm-args=-inline-threshold=0 -C lto=off -C opt-level=3",
        "dir": no_inline
    },
    "agg-inline": {
        "label": "6: [MIR modification] -C llvm-args=-inline-threshold=300 -C lto=off -C opt-level=3",
        "dir": agg_inline
    },
    "diff-ltos-1": {
        "label": "1 vs 3",
        "y-axis-label": "3 Time per Iteration Relative to 1 [%]",
        "dir-baseline": lto_off_1,
        "dir-tocompare": lto_thin_1,
    },
    "diff-ltos-2": {
        "label": "2 vs 4",
        "y-axis-label": "4 Time per Iteration Relative to 2 [%]",
        "dir-baseline": lto_off_2,
        "dir-tocompare": lto_thin_2,
    },
    "diff-off": {
        "label": "1 vs 2",
        "y-axis-label": "2 Time per Iteration Relative to 1 [%]",
        "dir-baseline": lto_off_1,
        "dir-tocompare": lto_off_2,
    },
    "diff-thin": {
        "label": "3 vs 4",
        "y-axis-label": "4 Time per Iteration Relative to 3 [%]",
        "dir-baseline": lto_thin_1,
        "dir-tocompare": lto_thin_2,
    },
    "diff-inline": {
        "label": "5 vs 6",
        "y-axis-label": "6 Time per Iteration Relative to 5 [%]",
        "dir-baseline": no_inline,
        "dir-tocompare": agg_inline,
    },
    "bcrm-o0": {
        "label": "7: [Out-of-Tree LLVM Pass] cargo rustc -C embed-bitcode=no -C lto=off -C opt-level=3 && opt -O0 [average of 36 runs]",
        "dir": bcrm_o0
    },
    "bcrm-o3": {
        "label": "8: [Out-of-Tree LLVM Pass] cargo rustc -C embed-bitcode=no -C lto=off -C opt-level=3 && opt -O3 [average of 36 runs]",
        "dir": bcrm_o3
    },
    "bcrm-o0-many": {
        "label": "9: [Out-of-Tree LLVM Pass] cargo rustc -C embed-bitcode=no -C lto=off -C opt-level=3 && opt -O0 [average of 180 runs]",
        "dir": bcrm_o0_many
    },
    "bcrm-o3-many": {
        "label": "10: [Out-of-Tree LLVM Pass] cargo rustc -C embed-bitcode=no -C lto=off -C opt-level=3 && opt -O3 [average of 180 runs]",
        "dir": bcrm_o3_many
    },
    "diff-bcrm": {
        "label": "7 vs 8",
        "y-axis-label": "8 Time per Iteration Relative to 7 [%]",
        "dir-baseline": bcrm_o0,
        "dir-tocompare": bcrm_o3
    },
    "diff-bcrm-o0": {
        "label": "7 vs 9",
        "y-axis-label": "9 Time per Iteration Relative to 7 [%]",
        "dir-baseline": bcrm_o0,
        "dir-tocompare": bcrm_o0_many
    },
    "diff-bcrm-many": {
        "label": "9 vs 10",
        "y-axis-label": "10 Time per Iteration Relative to 9 [%]",
        "dir-baseline": bcrm_o0_many,
        "dir-tocompare": bcrm_o3_many
    },
    "diff-bcrm-o3": {
        "label": "8 vs 10",
        "y-axis-label": "10 Time per Iteration Relative to 8 [%]",
        "dir-baseline": bcrm_o3,
        "dir-tocompare": bcrm_o3_many
    },
    "bcrm-o0-o3": {
        "label": "11: [Out-of-Tree LLVM Pass] cargo rustc -C no-prepopulate-passes -C passes=name-anon-globals -C embed-bitcode=no -C lto=off && opt -O3 [average of 36 runs]",
        "dir": bcrm_o0_o3
    },
    "diff-mir-v-out": {
        "label": "2 vs 11",
        "y-axis-label": "11 Time per Iteration Relative to 2 [%]",
        "dir-baseline": lto_off_2,
        "dir-tocompare": bcrm_o0_o3,
    },
    "diff-bcrm-o0-o3": {
        "label": "8 vs 11",
        "y-axis-label": "11 Time per Iteration Relative to 8 [%]",
        "dir-baseline": bcrm_o3,
        "dir-tocompare": bcrm_o0_o3,
    },
    "bcrm-fpm": {
        "label": "12: [In-Tree LLVM Pass] cargo rustc -C opt-level=3 -C embed-bitcode=no -C lto=off -- -Z remove-bc (called from LLVM's FunctionPass Manager) [average of 42 runs]",
        "dir": bcrm_fpm
    },
    "bcrm-mpm": {
        "label": "13: [In-Tree LLVM Pass] cargo rustc -C opt-level=3 -C embed-bitcode=no -C lto=off -- -Z remove-bc (called from LLVM's ModulePass Manager) [average of 42 runs]",
        "dir": bcrm_mpm
    },
    "diff-bcrm-fpm-o0-o3": {
        "label": "11 vs 12",
        "y-axis-label": "11 Time per Iteration Relative to 12 [%]",
        "dir-baseline": bcrm_fpm,
        "dir-tocompare": bcrm_o0_o3,
    },
    "diff-bcrm-mpm-o0-o3": {
        "label": "11 vs 13",
        "y-axis-label": "11 Time per Iteration Relative to 13 [%]",
        "dir-baseline": bcrm_mpm,
        "dir-tocompare": bcrm_o0_o3,
    },
    "diff-mir-v-in": {
        "label": "2 vs 13",
        "y-axis-label": "13 Time per Iteration Relative to 2 [%]",
        "dir-baseline": lto_off_2,
        "dir-tocompare": bcrm_mpm,
    },
    "diff-bcrm-fpm-mpm": {
        "label": "12 vs 13",
        "y-axis-label": "12 Time per Iteration Relative to 13 [%]",
        "dir-baseline": bcrm_mpm,
        "dir-tocompare": bcrm_fpm,
    }
}


def get_crates():
    global crates
    for name in os.listdir(path_to_crates):
        crates.append(name)
    crates.sort()


# Geometric mean helper
def geo_mean_overflow(iterable):
    locarr = []
    for i in iterable:
        if i == 0:
            locarr.append(10**-100)
        else:
            locarr.append(i)
    # Convert all elements to positive numbers
    a = np.log(np.absolute(locarr))
    return np.exp(a.sum() / len(a))


def arith_mean_overflow(iterable):
    rng_avg = 0
    count = 1
    for i in iterable:
        rng_avg += (i - rng_avg) / count
        count += 1
    return rng_avg


#class ResultProvider:
#
#    def __init__(self, path):
#        self._path = path


def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--root_path", type=str, required=True,
                        help="Root path of CPF benchmark directory")
    parser.add_argument("--port", type=str, default="8050",
                        help="Port for Dash server to run, 8050 or 8060 on AWS")
    args = parser.parse_args()
    return args.root_path, args.port


# some setting for plot
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.config.suppress_callback_exceptions = True


def crate_options():
    options = []
    global crates
    for crate in crates:
        options.append({'label': crate, 'value': crate})
    return options


def setting_options(): 
    options = []
    global switcher
    keys = switcher.keys()
    for k in keys:
        label = switcher.get(k).get("label")
        options.append({'label': label, 'value': k})
    return options


def is_empty_datafile(filepath):
    handle = open(filepath, 'r')
    for line in handle: 
        if line[:1] == '#':
            continue
        else:
            return False
    return True


def getPerfRustcsLayout():

    layout = html.Div([
        html.Br(),
        html.Label('Pick a crate:'),
        dcc.Dropdown(id='crate_name',
            options=crate_options(),
            value='KDFs',
            style={'width': '50%'}
        ),

        html.Br(),
        html.Label('Pick a setting:'),
        dcc.RadioItems(id='crate_opt',
            options=setting_options(),
            value="bcrm-fpm"
        ),

        html.Br(),
        html.Label('Statistic:'),
        dcc.RadioItems(id='crate_stat',
            options=[{'label': 'Arithmetic Mean', 'value': 'am'},
                    {'label': 'Geometric Mean', 'value': 'gm'}],
            value="am"
        ),

        html.Br(),
        html.Label('Lower is better!'),
        html.Div(id='crate-content')
    ])

    return layout


def getPerfPassLayout():

    layout = html.Div([
        html.Br(),
        html.Label('Across all crates, choose which result you would like to view:'),
        dcc.RadioItems(id='result_type',
            options=[
                    {'label': 'Benchmarks where removal of bounds checks performs BETTER', 'value': 'intuitive'},
                    {'label': 'Benchmarks where removal of bounds checks performs WORSE', 'value': 'unintuitive'}
            ],
            value='intuitive',
            style={'width': '70%'}
        ),

        html.Br(),
        html.Label('Pick a statistic:'),
        dcc.RadioItems(id='stat_type',
            options=[{'label': 'Arithmetic Mean', 'value': 'am'},
                    {'label': 'Geometric Mean', 'value': 'gm'}],
            value='gm'
        ),

        html.Br(),
        html.Label('Lower is better!'),
        html.Div(id='crate-content-front')
    ])

    return layout


@app.callback(dash.dependencies.Output('crate-content', 'children'),
               [dash.dependencies.Input('crate_name', 'value'),
                dash.dependencies.Input('crate_opt', 'value'),
                dash.dependencies.Input('crate_stat', 'value')])
def display_crate_info(crate_name, crate_opt, crate_stat):

    if 'diff' in crate_opt:
        return display_diff(crate_name, crate_opt)
    else:
        return display_relative(crate_name, crate_opt, crate_stat)


@app.callback(dash.dependencies.Output('crate-content-front', 'children'),
              [dash.dependencies.Input('result_type', 'value'),
               dash.dependencies.Input('stat_type', 'value')])
def display_crate_info(result_type, stat_type):

    return display_significant(result_type, stat_type)


def display_diff(crate_name, crate_opt):

    if "bcrm" in crate_opt:
        file_baseline = path_to_crates + "/" + crate_name + "/" + switcher.get(crate_opt).get("dir-baseline") + "/" + data_file_new
        file_tocompare = path_to_crates + "/" + crate_name + "/" + switcher.get(crate_opt).get("dir-tocompare") + "/" + data_file_new
    elif "mir" in crate_opt:
        file_baseline = path_to_crates + "/" + crate_name + "/" + switcher.get(crate_opt).get("dir-baseline") + "/" + data_file
        file_tocompare = path_to_crates + "/" + crate_name + "/" + switcher.get(crate_opt).get("dir-tocompare") + "/" + data_file_new
    else:
        file_baseline = path_to_crates + "/" + crate_name + "/" + switcher.get(crate_opt).get("dir-baseline") + "/" + data_file
        file_tocompare = path_to_crates + "/" + crate_name + "/" + switcher.get(crate_opt).get("dir-tocompare") + "/" + data_file

    if ((not os.path.exists(file_baseline)) or is_empty_datafile(file_baseline)) or ((not os.path.exists(file_tocompare)) or is_empty_datafile(file_tocompare)):
        return "\nNo diff data for crate " + str(crate_name) + " with these settings."

    def get_one_bar(rustc_type, bar_name, color):
        one_bmark_list = []
        one_perf_list = []
        one_y_error_list = []

        # open files for reading
        handle_baseline = open(file_baseline, 'r')
        handle_tocompare = open(file_tocompare, 'r')

        col = rustc_type * 2 + 1

        for line_baseline, line_tocompare in zip(handle_baseline, handle_tocompare):
            if line_baseline[:1] == '#':
                continue

            # get columns from files
            cols_baseline = line_baseline.split()
            cols_tocompare = line_tocompare.split()

            # get benchmark names for this crate
            name = cols_baseline[0]
            one_bmark_list.append(name)

            # get times from specified (column * 2 + 1)
            time_baseline = cols_baseline[col]
            time_tocompare = cols_tocompare[col]
            error = cols_tocompare[col + 1]

            # calculate the percent speedup or slowdown
            div = float(time_baseline) if float(time_baseline) != 0 else 1
            perc_time = ((float(time_tocompare) - float(time_baseline)) / div) * 100
            one_perf_list.append(perc_time)

            div = float(time_tocompare) if float(time_tocompare) != 0 else 1
            perc_e = (float(error) / div) * 100
            one_y_error_list.append(perc_e)


        handle_baseline.close()
        handle_tocompare.close()

        bar_one = {'x': one_bmark_list, 'y': one_perf_list, 'error_y': {'type': 'data', 'array': one_y_error_list},
                   'type': 'bar', 'name': bar_name, 'marker_color': color}
        return bar_one


    bar_list = []
    #if ("bcrm" in crate_opt) or ("mir" in crate_opt):
    bar_unmod = get_one_bar(0, graph_styles.get(0).get("bar-name"), graph_styles.get(0).get("bar-color"))
    bar_nobc = get_one_bar(1, graph_styles.get(1).get("bar-name"), graph_styles.get(1).get("bar-color"))

    bar_list = [bar_unmod, bar_nobc]
    #else:
    #    bar_unmod = get_one_bar(0, graph_styles.get(0).get("bar-name"), graph_styles.get(0).get("bar-color"))
    #    bar_nobc = get_one_bar(1, graph_styles.get(1).get("bar-name"), graph_styles.get(1).get("bar-color"))
    #    bar_both = get_one_bar(2, graph_styles.get(2).get("bar-name"), graph_styles.get(2).get("bar-color"))
    #    bar_safelib = get_one_bar(3, graph_styles.get(3).get("bar-name"), graph_styles.get(3).get("bar-color"))

    #    bar_list = [bar_unmod, bar_nobc, bar_both, bar_safelib]

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
                            'title': {'text': switcher.get(crate_opt).get("y-axis-label")},
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
                        'width': 1450, 
                        'height': 700}
                    })

        
    return html.Div([
        dcc.Graph(
            id='rustc-compare-ltos',
            figure=fig
        )
    ])


def display_relative(crate_name, crate_opt, crate_stat):

    if ("bcrm" in crate_opt) and ("gm" in crate_stat): 
        filepath = path_to_crates + "/" + crate_name + "/" + switcher.get(crate_opt).get("dir") + "/" + data_file_geo
    elif ("bcrm" in crate_opt) and ("am" in crate_stat):
        filepath = path_to_crates + "/" + crate_name + "/" + switcher.get(crate_opt).get("dir") + "/" + data_file_new
    else: 
        filepath = path_to_crates + "/" + crate_name + "/" + switcher.get(crate_opt).get("dir") + "/" + data_file

    if (not os.path.exists(filepath)) or is_empty_datafile(filepath):
        return "\nNo relative data for crate " + str(crate_name) + " with these settings."

    def get_one_bar_rel(rustc_type, bar_name, color):
        one_bmark_list = []
        one_perf_list = []
        one_y_error_list = []

        # open file for reading
        handle = open(filepath, 'r')

        for line in handle:
            if line[:1] == '#':
                continue
            cols = line.split()

            # get benchmark names for this crate
            name = cols[0]
            one_bmark_list.append(name)

            # get baseline (vanilla times) to compare this version againt
            vanilla = cols[1]
            vanilla_error = cols[2]

            # get the times from the specified (column * 2 + 1)
            col = rustc_type * 2 + 1
            time = cols[col]
            error = cols[col + 1]

            # calculate the percent speedup or slowdown
            div = float(vanilla) if float(vanilla) != 0 else 1
            perc_time = ((float(time) - float(vanilla)) / div) * 100
            div_e = float(time) if float(time) != 0 else 1
            perc_e = (float(error) / div_e) * 100

            if perc_time > 0:
                if perc_time + perc_e >= float(vanilla_error):
                    one_perf_list.append(perc_time)
                    one_y_error_list.append(perc_e)
                else:
                    one_perf_list.append(0)
                    one_y_error_list.append(0)
            else:
                if perc_time - perc_e <= (0 - float(vanilla_error)):
                    one_perf_list.append(perc_time)
                    one_y_error_list.append(perc_e)
                else:
                    one_perf_list.append(0)
                    one_y_error_list.append(0)

        handle.close()

        color_e = 'black' if rustc_type != 0 else color

        bar_one = {'x': one_bmark_list, 'y': one_perf_list, 'error_y': {'type': 'data', 'array': one_y_error_list, 'color': color_e},
                   'type': 'bar', 'name': bar_name, 'marker_color': color}

        return bar_one

    
    bar_list = []
    #if "bcrm" in crate_opt: #.startswith("bcrm"):
    #bar_unmod = get_one_bar_rel(0, graph_styles.get(0).get("bar-name"), graph_styles.get(0).get("bar-color"))
    bar_nobc = get_one_bar_rel(1, graph_styles.get(1).get("bar-name"), graph_styles.get(1).get("bar-color"))

    bar_list = [bar_nobc]
    #bar_list = [bar_unmod, bar_nobc]

    #else: 
    #    bar_unmod = get_one_bar_rel(0, graph_styles.get(0).get("bar-name"), graph_styles.get(0).get("bar-color"))
    #    bar_nobc = get_one_bar_rel(1, graph_styles.get(1).get("bar-name"), graph_styles.get(1).get("bar-color"))
    #    bar_both = get_one_bar_rel(2, graph_styles.get(2).get("bar-name"), graph_styles.get(2).get("bar-color"))
    #    bar_safelib = get_one_bar_rel(3, graph_styles.get(3).get("bar-name"), graph_styles.get(3).get("bar-color"))

    #    bar_list = [bar_unmod, bar_nobc, bar_both, bar_safelib]

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
                        'width': 1450, 
                        'height': 700}
                    })

        
    return html.Div([
        dcc.Graph(
            id='rustc-compare-graph-rel',
            figure=fig
        )
    ])


def display_significant(result_type, stat_type):

    one_bmark_list = []
    one_perf_list = []
    one_yerror_list= []

    def get_one_bar(bar_name, bar_color):

        global crates

        for c in crates: 

            if stat_type == 'am':
                filepath = path_to_crates + "/" + c + "/" + switcher.get('bcrm-mpm').get("dir") + "/" + data_file_new
            else: 
                filepath = path_to_crates + "/" + c + "/" + switcher.get('bcrm-mpm').get("dir") + "/" + data_file_geo

            if (not os.path.exists(filepath)) or is_empty_datafile(filepath):
                continue

            # open data file for reading
            handle = open(filepath, 'r')

            for line in handle: 
                if line[:1] == '#':
                    continue
                cols = line.split()

                name = cols[0]

                vanilla_time = cols[1]
                vanilla_error = cols[2]
                nobc_time = cols[3]
                nobc_error = cols[4]

                div = float(vanilla_time) if float(vanilla_time) != 0 else 1
                perc_time = ((float(nobc_time) - float(vanilla_time)) / div) * 100

                div_e = float(nobc_time) if float(nobc_time) != 0 else 1
                perc_error = (float(nobc_error) / div_e) * 100

                if (result_type == 'unintuitive' and perc_time > 0 and (perc_time + perc_error >= float(vanilla_error))) or (result_type == 'intuitive' and perc_time < 0 and (perc_time - perc_error <= 0 - float(vanilla_error))):
                    one_bmark_list.append(c + "::" + name)
                    one_perf_list.append(perc_time)
                    one_yerror_list.append(perc_error)

            handle.close()

        color_e = 'black'
        bar_one = {'x': one_bmark_list, 'y': one_perf_list, 'error_y': {'type': 'data', 'array': one_yerror_list, 'color': color_e},
                    'type': 'bar', 'name': bar_name, 'marker_color': bar_color}
        return bar_one


    bar_list = [get_one_bar(graph_styles.get(1).get("bar-name"), graph_styles.get(1).get("bar-color"))]

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

    if stat_type == 'am' and result_type == 'intuitive': 
        # Make negative number
        mean_of_mean = 0 - arith_mean_overflow(one_perf_list)
    elif stat_type == 'am' and result_type == 'unintuitive': 
        # Keep as a positive number
        mean_of_mean = arith_mean_overflow(one_perf_list)
    elif stat_type == 'gm' and result_type == 'intuitive': 
        # Make negative number
        mean_of_mean = 0 - geo_mean_overflow(one_perf_list)
    else:
        # Keep as a positive number
        mean_of_mean = geo_mean_overflow(one_perf_list)
        
    return html.Div([
        html.Label('Mean of the means: ' + str(mean_of_mean)),
        html.Br(),
        dcc.Graph(
            id='significant-res-graph',
            figure=fig
        )
    ])


@app.callback(dash.dependencies.Output('page-content', 'children'),
              [dash.dependencies.Input('url', 'pathname')])
def display_page(pathname):
    if not pathname:
        return 404

    if pathname == '/':
        pathname = '/comparePass'

    if pathname == '/compareAll':
        layout = getPerfRustcsLayout() #app._resultProvider)
        return layout
    if pathname == '/comparePass':
        layout = getPerfPassLayout() #app._resultProvider)
        return layout
    else:
        return 404


if __name__ == '__main__':
    cpf_root, port = parseArgs()
    # I'm not actually using this...
    result_path = os.path.join(cpf_root, "./crates/crates")
    #app._resultProvider = ResultProvider(result_path)

    get_crates()

    app.layout = html.Div([
        dcc.Location(id='url', refresh=False),
        dcc.Link('All Techniques', href='/compareAll'),
        html.Br(),
        dcc.Link('In-Tree LLVM Pass', href='/comparePass'),
        html.Br(),
        html.Div(id='page-content')
    ])

    app.run_server(debug=False, host='0.0.0.0', port=port)
