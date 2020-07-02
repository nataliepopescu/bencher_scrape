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
        options.append({'label': crate, 'value': crate})
    return options


def getPerfRustcsLayout(): #resultProvider):

    layout = html.Div([
#        html.Br(),
#        html.Div(children='''
#            Crate Performance when built with four Rustc Variants (Average of at least 36 runs)
#        '''),

        html.Br(),
        html.Label('Pick a crate:'),
        dcc.Dropdown(id='crate_name',
            options=create_options(),
            value='KDFs',
            style={'width': '50%'}
        ),

        html.Br(),
        html.Div([
            html.Label('Pick an optimization setting:'),
            dcc.RadioItems(id='crate_opt',
                options=[
                    {'label': 'LTO=thin', 'value': 'cloudlab-output'},
                    {'label': 'LTO=fat', 'value': 'cloudlab-output-lto'},
                ],
                value='cloudlab-output',
                labelStyle={'display': 'inline-block'}
            ),

            html.Label('Pick a view:'),
            dcc.RadioItems(id='crate_view',
                options=[
                    {'label': 'Absolute', 'value': 'abs'},
                    {'label': 'Relative', 'value': 'rel'},
                ],
                value='abs',
                labelStyle={'display': 'inline-block'}
            ),
        ], style={'columnCount': 2, 'width': '33%'}),

        html.Br(),
        html.Label('Lower is better!'),
        html.Div(id='crate-content')
    ])

    return layout


@app.callback(dash.dependencies.Output('crate-content', 'children'),
              [dash.dependencies.Input('crate_name', 'value'),
               dash.dependencies.Input('crate_opt', 'value'),
               dash.dependencies.Input('crate_view', 'value')])
def display_crate_info(crate_name, crate_opt, crate_view):

    if crate_view == 'rel':
        return display_rel(crate_name, crate_opt)
    elif crate_view == 'abs':
        return display_abs(crate_name, crate_opt)


def display_rel(crate_name, crate_opt):

    def get_one_bar_rel(rustc_type, bar_name, color):
        one_bmark_list = []
        one_perf_list = []

        filepath = path_to_crates + "/" + crate_name + "/" + crate_opt + "/bench-sanity-CRUNCHED.data"

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
            perc_time = ((float(time) - float(vanilla)) / float(vanilla)) * 100
            one_perf_list.append(perc_time)


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

    return html.Div(
        dcc.Graph(
            id='rustc-compare-graph-rel',
            figure=fig
        )
    )


def display_abs(crate_name, crate_opt):

    def get_one_bar_abs(rustc_type, bar_name, color):
        one_bmark_list = []
        one_perf_list = []

        filepath = path_to_crates + "/" + crate_name + "/" + crate_opt + "/bench-sanity-CRUNCHED.data"

        # open file for reading
        handle = open(filepath, 'r')

        for line in handle:
            if line[:1] == '#':
                continue
            cols = line.split()

            # get benchmark names for this crate
            name = cols[0]
            one_bmark_list.append(name)

            # get the times from the specified (column * 2 + 1)
            col = rustc_type * 2 + 1
            time = cols[col]
            one_perf_list.append(time)


        bar_one = {'x': one_bmark_list, 'y': one_perf_list, 
                   'type': 'bar', 'name': bar_name, 'marker_color': color}
        return bar_one

    bar_unmod = get_one_bar_abs(0, "Vanilla Rustc", '#ca0020')
    bar_nobc = get_one_bar_abs(1, "Rustc No Slice Bounds Checks", '#f4a582')
    bar_both = get_one_bar_abs(2, "Rustc No Slice Bounds Checks + Safe memcpy", '#0571b0')
    bar_safelib = get_one_bar_abs(3, "Rustc Safe memcpy", '#abd9e9')

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
                            'title': {'text': " Performance [ns/iter]"},
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

    fig.update_yaxes(type="log")

    return html.Div(
        dcc.Graph(
            id='rustc-compare-graph-abs',
            figure=fig
        )
    )


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
