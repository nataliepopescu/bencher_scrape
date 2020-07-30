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
crates = []

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
        "bar-name": "Rustc No Slice Bounds Checks + Safe memcpy",
        "bar-color": "#DDA0DD"
    },
    3: {
        "bar-name": "Rustc Safe memcpy",
        "bar-color": "#0571B0"
    }
}

lto_off_1 = "results-lto-off-1"
lto_off_2 = "results-lto-off-2"
lto_thin_1 = "results-lto-thin-1"
lto_thin_2 = "results-lto-thin-2"
no_inline = "results-no-inline-lto-off"
agg_inline = "results-agg-inline-lto-off"
bcrm_o0 = "results-bcrmpass-embedbitcode-no-lto-off"
bcrm_o0_many = "results-bcrmpass-embedbitcode-no-lto-off-many"
bcrm_o3 = "results-bcrmpass-embedbitcode-no-lto-off-o3"
bcrm_o3_many = "results-bcrmpass-embedbitcode-no-lto-off-many-o3"

switcher = {
    "lto-off-1": {
        "label": "1: -C embed-bitcode=no",
        "dir": lto_off_1
    },
    "lto-off-2": {
        "label": "2: -C embed-bitcode=no -C lto=off",
        "dir": lto_off_2
    },
    "lto-thin-1": {
        "label": "3: -C embed-bitcode=yes",
        "dir": lto_thin_1
    },
    "lto-thin-2": {
        "label": "4: -C embed-bitcode=yes =C lto=thin",
        "dir": lto_thin_2
    },
    "no-inline": {
        "label": "5: -C llvm-args=-inline-threshold=0 and -C lto=off",
        "dir": no_inline
    },
    "agg-inline": {
        "label": "6: -C llvm-args=-inline-threshold=300 and -C lto=off",
        "dir": agg_inline
    },
    "diff-ltos-1": {
        "label": "1 vs 3",
        "y-axis-label": "3 Time per Iteration Relative to 1 [%]",
        "dir1": lto_off_1, # baseline
        "dir2": lto_thin_1, # tocompare
    },
    "diff-ltos-2": {
        "label": "2 vs 4",
        "y-axis-label": "4 Time per Iteration Relative to 2 [%]",
        "dir1": lto_off_2, # baseline
        "dir2": lto_thin_2, # tocompare
    },
    "diff-off": {
        "label": "1 vs 2",
        "y-axis-label": "2 Time per Iteration Relative to 1 [%]",
        "dir1": lto_off_1, # baseline
        "dir2": lto_off_2, # tocompare
    },
    "diff-thin": {
        "label": "3 vs 4",
        "y-axis-label": "4 Time per Iteration Relative to 3 [%]",
        "dir1": lto_thin_1, # baseline
        "dir2": lto_thin_2, # tocompare
    },
    "diff-inline": {
        "label": "5 vs 6",
        "y-axis-label": "6 Time per Iteration Relative to 5 [%]",
        "dir1": no_inline, # baseline
        "dir2": agg_inline, # tocompare
    },
    "bcrm-o0": {
        "label": "1: -C embed-bitcode=no -C lto=off [average of 36 runs]",
        "dir": bcrm_o0
    },
    "bcrm-o3": {
        "label": "2: -C embed-bitcode=no -C lto=off && opt -o3 [average of 36 runs]",
        "dir": bcrm_o3
    },
    "bcrm-o0-many": {
        "label": "3: -C embed-bitcode=no -C lto=off [average of 180 runs]",
        "dir": bcrm_o0_many
    },
    "bcrm-o3-many": {
        "label": "4: -C embed-bitcode=no -C lto=off && opt -o3 [average of 180 runs]",
        "dir": bcrm_o3_many
    },
    "diff-bcrm": {
        "label": "1 vs 2",
        "y-axis-label": "2 Time per Iteration Relative to 1 [%]",
        "dir1": bcrm_o0,
        "dir2": bcrm_o3
    },
    "diff-bcrm-o0": {
        "label": "1 vs 3",
        "y-axis-label": "3 Time per Iteration Relative to 1 [%]",
        "dir1": bcrm_o0,
        "dir2": bcrm_o0_many
    },
    "diff-bcrm-many": {
        "label": "3 vs 4",
        "y-axis-label": "4 Time per Iteration Relative to 3 [%]",
        "dir1": bcrm_o0_many,
        "dir2": bcrm_o3_many
    },
    "diff-bcrm-o3": {
        "label": "2 vs 4",
        "y-axis-label": "4 Time per Iteration Relative to 2 [%]",
        "dir1": bcrm_o3,
        "dir2": bcrm_o3_many
    }
}


def get_crates():
    global crates
    for name in os.listdir(path_to_crates):
        crates.append(name)
    crates.sort()


# Geometric mean helper
def geo_mean_overflow(iterable):
    a = np.log(iterable)
    return np.exp(a.sum() / len(a))


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


def setting_options(version):
    options = []
    global switcher
    keys = switcher.keys()
    for k in keys:
        if version == 0 and "bcrm" in k: #k.startswith("bcrm"):
            label = switcher.get(k).get("label")
            options.append({'label': label, 'value': k})
        elif version == 1 and not "bcrm" in k:
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
            options=setting_options(1),
            value="diff-inline"
        ),

        html.Br(),
        html.Label('Lower is better!'),
        html.Div(id='crate-content')
    ])

    return layout


def getPerfPassLayout():

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
            options=setting_options(0),
            value="bcrm-o0"
        ),

        html.Br(),
        html.Label('Lower is better!'),
        html.Div(id='crate-content')
    ])

    return layout


@app.callback(dash.dependencies.Output('crate-content', 'children'),
              [dash.dependencies.Input('crate_name', 'value'),
               dash.dependencies.Input('crate_opt', 'value')])
def display_crate_info(crate_name, crate_opt):

    #y_axis_txt = switcher.get(crate_opt).get("y-axis-label")

    if crate_opt.startswith("diff"):
        return display_diff(crate_name, crate_opt) #, dir_lto_thin, dir_lto_thin_rerun, y_axis_txt)
    else:
        return display_relative(crate_name, crate_opt)


def display_diff(crate_name, crate_opt): #, dir_baseline, dir_tocompare, graph_text):

#    unexp_unmod = []
#    unexp_nobc = []
#    unexp_both = []
#    unexp_safelib = []

    if "bcrm" in crate_opt:
        file_baseline = path_to_crates + "/" + crate_name + "/" + switcher.get(crate_opt).get("dir1") + "/" + data_file_new
        file_tocompare = path_to_crates + "/" + crate_name + "/" + switcher.get(crate_opt).get("dir2") + "/" + data_file_new
    else:
        file_baseline = path_to_crates + "/" + crate_name + "/" + switcher.get(crate_opt).get("dir1") + "/" + data_file
        file_tocompare = path_to_crates + "/" + crate_name + "/" + switcher.get(crate_opt).get("dir2") + "/" + data_file

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

            # get stats for expectation #2
#            if perc_time > 0:
#                switcher_local = {
#                    0: unexp_unmod,
#                    1: unexp_nobc, 
#                    2: unexp_both,
#                    3: unexp_safelib
#                }
#                arr = switcher_local.get(rustc_type)
#                arr.append(perc_time)

        handle_baseline.close()
        handle_tocompare.close()

        bar_one = {'x': one_bmark_list, 'y': one_perf_list, 'error_y': {'type': 'data', 'array': one_y_error_list},
                   'type': 'bar', 'name': bar_name, 'marker_color': color}
        return bar_one


    bar_list = []
    if "bcrm" in crate_opt:
        bar_unmod = get_one_bar(0, graph_styles.get(0).get("bar-name"), graph_styles.get(0).get("bar-color"))
        bar_nobc = get_one_bar(1, graph_styles.get(1).get("bar-name"), graph_styles.get(1).get("bar-color"))

        bar_list = [bar_unmod, bar_nobc]
    else:
        bar_unmod = get_one_bar(0, graph_styles.get(0).get("bar-name"), graph_styles.get(0).get("bar-color"))
        bar_nobc = get_one_bar(1, graph_styles.get(1).get("bar-name"), graph_styles.get(1).get("bar-color"))
        bar_both = get_one_bar(2, graph_styles.get(2).get("bar-name"), graph_styles.get(2).get("bar-color"))
        bar_safelib = get_one_bar(3, graph_styles.get(3).get("bar-name"), graph_styles.get(3).get("bar-color"))

        bar_list = [bar_unmod, bar_nobc, bar_both, bar_safelib]

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

#    sum_unexp_0 = 0
#    len_unexp_0 = len(unexp_unmod)
#    avg_0 = "None"
#
#    if len_unexp_0 > 0: 
#        for e in unexp_unmod: 
#            sum_unexp_0 += e
#        avg_0 = str(sum_unexp_0 / len_unexp_0)
#
#    sum_unexp_1 = 0
#    len_unexp_1 = len(unexp_nobc)
#    avg_1 = "None"
#
#    if len_unexp_1 > 0: 
#        for e in unexp_nobc: 
#            sum_unexp_1 += e
#        avg_1 = str(sum_unexp_1 / len_unexp_1)
#        
#    sum_unexp_2 = 0
#    len_unexp_2 = len(unexp_both)
#    avg_2 = "None"
#
#    if len_unexp_2 > 0: 
#        for e in unexp_both: 
#            sum_unexp_2 += e
#        avg_2 = str(sum_unexp_2 / len_unexp_2)
#        
#    sum_unexp_3 = 0
#    len_unexp_3 = len(unexp_safelib)
#    avg_3 = "None"
#
#    if len_unexp_3 > 0: 
#        for e in unexp_safelib: 
#            sum_unexp_3 += e
#        avg_3 = str(sum_unexp_3 / len_unexp_3)
        
    return html.Div([
#        html.Br(),
#        html.Label('Expectation 2 [unmod]: ' + avg_0),
#        html.Br(),
#        html.Label('Expectation 2 [nobc]: ' + avg_1),
#        html.Br(),
#        html.Label('Expectation 2 [both]: ' + avg_2),
#        html.Br(),
#        html.Label('Expectation 2 [safelib]: ' + avg_3),
#        html.Br(),
        dcc.Graph(
            id='rustc-compare-ltos',
            figure=fig
        )
    ])


def display_relative(crate_name, crate_opt):

   # unexp_1 = []
   # unexp_3 = []

    if "bcrm" in crate_opt: #.startswith("bcrm"):
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
#            one_y_error_list.append(error)

            # calculate the percent speedup or slowdown
            div = float(vanilla) if float(vanilla) != 0 else 1
            perc_time = ((float(time) - float(vanilla)) / div) * 100
            one_perf_list.append(perc_time)

            #div_e = float(vanilla_error) if float(vanilla_error) != 0 else 1
            #perc_error = ((float(error) - float(vanilla_er
            div_e = float(time) if float(time) != 0 else 1
            perc_e = (float(error) / div_e) * 100
            #perc_error = perc_e if perc_e > 0 else (0 - perc_e)
            one_y_error_list.append(perc_e)

            # get stats for expectation #1 and #3
 #           if rustc_type == 1 and perc_time > 0:
 #               unexp_1.append(perc_time)
 #           elif rustc_type == 3 and perc_time < 0:
 #               unexp_3.append(perc_time)

        handle.close()

        color_e = 'black' if rustc_type != 0 else color

        bar_one = {'x': one_bmark_list, 'y': one_perf_list, 'error_y': {'type': 'data', 'array': one_y_error_list, 'color': color_e},
                   'type': 'bar', 'name': bar_name, 'marker_color': color}
        return bar_one

    
    bar_list = []
    if "bcrm" in crate_opt: #.startswith("bcrm"):
        bar_unmod = get_one_bar_rel(0, graph_styles.get(0).get("bar-name"), graph_styles.get(0).get("bar-color"))
        bar_nobc = get_one_bar_rel(1, graph_styles.get(1).get("bar-name"), graph_styles.get(1).get("bar-color"))

        bar_list = [bar_unmod, bar_nobc]
    else: 
        bar_unmod = get_one_bar_rel(0, graph_styles.get(0).get("bar-name"), graph_styles.get(0).get("bar-color"))
        bar_nobc = get_one_bar_rel(1, graph_styles.get(1).get("bar-name"), graph_styles.get(1).get("bar-color"))
        bar_both = get_one_bar_rel(2, graph_styles.get(2).get("bar-name"), graph_styles.get(2).get("bar-color"))
        bar_safelib = get_one_bar_rel(3, graph_styles.get(3).get("bar-name"), graph_styles.get(3).get("bar-color"))

        bar_list = [bar_unmod, bar_nobc, bar_both, bar_safelib]

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

#    sum_unexp_1 = 0
#    len_unexp_1 = len(unexp_1)
#    avg_1 = "None"
#
#    if len_unexp_1 > 0: 
#        for e in unexp_1: 
#            sum_unexp_1 += e
#        avg_1 = str(sum_unexp_1 / len_unexp_1)
#        
#    sum_unexp_3 = 0
#    len_unexp_3 = len(unexp_3)
#    avg_3 = "None"
#
#    if len_unexp_3 > 0: 
#        for e in unexp_3: 
#            sum_unexp_3 += e
#        avg_3 = str(sum_unexp_3 / len_unexp_3)
        
    return html.Div([
#        html.Br(),
#        html.Label('Expectation 1: ' + avg_1),
#        html.Br(),
#        html.Label('Expectation 3: ' + avg_3),
#        html.Br(),
        dcc.Graph(
            id='rustc-compare-graph-rel',
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

    if pathname == '/compareRustcs':
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
        dcc.Link('Modified Rustc', href='/compareRustcs'),
        html.Br(),
        dcc.Link('Out of Tree LLVM Pass', href='/comparePass'),
        html.Br(),
        html.Div(id='page-content')
    ])

    app.run_server(debug=False, host='0.0.0.0', port=port)
