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
crates = []

dir_lto_off = "cloudlab-output"
dir_lto_off_rerun = "cloudlab-output-lto-off"
dir_lto_thin = "cloudlab-output-lto"
dir_lto_thin_rerun = "cloudlab-output-lto-thin"

data_file = "bench-sanity-CRUNCHED.data"


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


def create_options():
    global crates
    options = []
    for crate in crates:
        # only display crates that have this data
        #filepath = path_to_crates + "/" + crate + "/" + dir_lto_off + "/" + data_file
        #if os.path.exists(filepath): # and (not is_empty_datafile(filepath)):
        options.append({'label': crate, 'value': crate})
    return options


def is_empty_datafile(filepath):
    handle = open(filepath, 'r')
    for line in handle: 
        if line[:1] == '#':
            continue
        else:
            return False
    return True


def getPerfRustcsLayout(): #resultProvider):

    layout = html.Div([
        html.Br(),
        html.Label('Pick a crate:'),
        dcc.Dropdown(id='crate_name',
            options=create_options(),
            value='KDFs',
            style={'width': '50%'}
        ),

        html.Br(),
        html.Div([
            html.Label('Pick a setting:'),
            dcc.RadioItems(id='crate_opt',
                options=[
                    {'label': 'LTO=off [Run 1]', 'value': dir_lto_off},
                    {'label': 'LTO=off [Run 2]', 'value': dir_lto_off_rerun},
                    {'label': 'LTO=thin [Run 1]', 'value': dir_lto_thin},
                    {'label': 'LTO=thin [Run 2]', 'value': dir_lto_thin_rerun},
                    {'label': 'LTO=off -vs- LTO=thin [Run 1]', 'value': 'diff'},
                    {'label': 'LTO=off -vs- LTO=thin [Run 2]', 'value': 'diff_rerun'},
                    {'label': 'Run 1 -vs- Run 2 [LTO=off]', 'value': 'diff_off'},
                    {'label': 'Run 1 -vs- Run 2 [LTO=thin]', 'value': 'diff_thin'},
                ],
                value=dir_lto_off #,
                #labelStyle={'display': 'inline-block'}
            ),

#            html.Label('Pick a view:'),
#            dcc.RadioItems(id='crate_view',
#                options=[
#                    {'label': 'Absolute', 'value': 'abs'},
#                    {'label': 'Relative', 'value': 'rel'},
#                ],
#                value='abs',
#                labelStyle={'display': 'inline-block'}
#            ),
        ]), #style={'columnCount': 2, 'width': '33%'}),

        html.Br(),
        html.Label('Lower is better!'),
        html.Div(id='crate-content')
    ])

    return layout


@app.callback(dash.dependencies.Output('crate-content', 'children'),
              [dash.dependencies.Input('crate_name', 'value'),
               dash.dependencies.Input('crate_opt', 'value')])
               #dash.dependencies.Input('crate_view', 'value')])
def display_crate_info(crate_name, crate_opt): #, crate_view):

    if crate_opt == 'diff':
        return display_diff(crate_name, dir_lto_off, dir_lto_thin, "Performance Change Relative to LTO=off [%]")
    elif crate_opt == 'diff_rerun':
        return display_diff(crate_name, dir_lto_off_rerun, dir_lto_thin_rerun, "Performance Change Relative to LTO=off [%]")
    elif crate_opt == 'diff_off':
        return display_diff(crate_name, dir_lto_off, dir_lto_off_rerun, "LTO=off Performance Comparison across Runs [%]")
    elif crate_opt == 'diff_thin':
        return display_diff(crate_name, dir_lto_thin, dir_lto_thin_rerun, "LTO=thin Performance Comparison across Runs [%]")
    else:
        return display_relative(crate_name, crate_opt)
#    elif crate_view == 'abs':
#        return display_absolute(crate_name, crate_opt)


def display_diff(crate_name, dir_baseline, dir_tocompare, graph_text):

#    unexp_unmod = []
#    unexp_nobc = []
#    unexp_both = []
#    unexp_safelib = []

    file_baseline = path_to_crates + "/" + crate_name + "/" + dir_baseline + "/" + data_file
    file_tocompare = path_to_crates + "/" + crate_name + "/" + dir_tocompare + "/" + data_file

    if ((not os.path.exists(file_baseline)) or is_empty_datafile(file_baseline)) or ((not os.path.exists(file_tocompare)) or is_empty_datafile(file_tocompare)):
        return "\nNo data for crate " + str(crate_name) + " with these settings."

    def get_one_bar(rustc_type, bar_name, color):
        one_bmark_list = []
        one_perf_list = []

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

            # calculate the percent speedup or slowdown
            div = float(time_baseline) if float(time_baseline) != 0 else 1
            perc_time = ((float(time_tocompare) - float(time_baseline)) / div) * 100
            one_perf_list.append(perc_time)

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

        bar_one = {'x': one_bmark_list, 'y': one_perf_list, 
                   'type': 'bar', 'name': bar_name, 'marker_color': color}
        return bar_one


    bar_unmod = get_one_bar(0, "Vanilla Rustc", '#ca0020')
    bar_nobc = get_one_bar(1, "Rustc No Slice Bounds Checks", '#f4a582')
    bar_both = get_one_bar(2, "Rustc No Slice Bounds Checks + Safe memcpy", '#0571b0')
    bar_safelib = get_one_bar(3, "Rustc Safe memcpy", '#abd9e9')

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
                            'title': {'text': graph_text},
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

    filepath = path_to_crates + "/" + crate_name + "/" + crate_opt + "/" + data_file

    if (not os.path.exists(filepath)) or is_empty_datafile(filepath):
        return "\nNo data for crate " + str(crate_name) + " with these settings."

    def get_one_bar_rel(rustc_type, bar_name, color):
        one_bmark_list = []
        one_perf_list = []

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

            # get the times from the specified (column * 2 + 1)
            col = rustc_type * 2 + 1
            time = cols[col]

            # calculate the percent speedup or slowdown
            div = float(vanilla) if float(vanilla) != 0 else 1
            perc_time = ((float(time) - float(vanilla)) / div) * 100
            one_perf_list.append(perc_time)

            # get stats for expectation #1 and #3
 #           if rustc_type == 1 and perc_time > 0:
 #               unexp_1.append(perc_time)
 #           elif rustc_type == 3 and perc_time < 0:
 #               unexp_3.append(perc_time)

        handle.close()

        bar_one = {'x': one_bmark_list, 'y': one_perf_list, 
                   'type': 'bar', 'name': bar_name, 'marker_color': color}
        return bar_one

    
    bar_nobc = get_one_bar_rel(1, "Rustc No Slice Bounds Checks", '#ca0020')
    bar_both = get_one_bar_rel(2, "Rustc No Slice Bounds Checks + Safe memcpy", '#D8BFD8')
    bar_safelib = get_one_bar_rel(3, "Rustc Safe memcpy", '#0571b0')

    bar_list = [bar_nobc, bar_both, bar_safelib]

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
                            'title': {'text': " Performance Change Relative to Vanilla [%]"},
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


#def display_absolute(crate_name, crate_opt):
#
#    def get_one_bar_abs(rustc_type, bar_name, color):
#        one_bmark_list = []
#        one_perf_list = []
#
#        filepath = path_to_crates + "/" + crate_name + "/" + crate_opt + "/" + data_file
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
#            # get the times from the specified (column * 2 + 1)
#            col = rustc_type * 2 + 1
#            time = cols[col]
#            one_perf_list.append(time)
#
#
#        bar_one = {'x': one_bmark_list, 'y': one_perf_list, 
#                   'type': 'bar', 'name': bar_name, 'marker_color': color}
#        return bar_one
#
#    bar_unmod = get_one_bar_abs(0, "Vanilla Rustc", '#ca0020')
#    bar_nobc = get_one_bar_abs(1, "Rustc No Slice Bounds Checks", '#f4a582')
#    bar_both = get_one_bar_abs(2, "Rustc No Slice Bounds Checks + Safe memcpy", '#0571b0')
#    bar_safelib = get_one_bar_abs(3, "Rustc Safe memcpy", '#abd9e9')
#
#    bar_list = [bar_unmod, bar_nobc, bar_both, bar_safelib]
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
#                            'title': {'text': " Performance [ns/iter]"},
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
#    fig.update_yaxes(type="log")
#
#    return html.Div(
#        dcc.Graph(
#            id='rustc-compare-graph-abs',
#            figure=fig
#        )
#    )


@app.callback(dash.dependencies.Output('page-content', 'children'),
              [dash.dependencies.Input('url', 'pathname')])
def display_page(pathname):
    if not pathname:
        return 404

    if pathname == '/':
        pathname = '/compareRustcs'

    if pathname == '/compareRustcs':
        layout = getPerfRustcsLayout() #app._resultProvider)
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
        #dcc.Link('Performance Comparisons', href='/compareRustcs'),
        #html.Br(),
        html.Div(id='page-content')
    ])

    app.run_server(debug=False, host='0.0.0.0', port=port)
