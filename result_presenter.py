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
import plotly.express as px


path_to_crates = "./downloaded_bencher_rev_deps"
path_to_top = "./downloaded_top_200"
data_file = "bench-sanity-CRUNCHED.data"
data_file_new = "bench-CRUNCHED.data"
bencher_rev_dep_crates = []
top_crates = []

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
bcrm_mod_rustc_only = "results-bcrmpass-mod-rustc-only"
bcrm_rescrape = "results-bcrmpass-rescrape"
bcrm_rustflags = "results-bcrmpass-in-rustflags"
#bcrm_rustflags_thin_retry = "results-bcrmpass-embed-bitcode-yes-lto-thin-retry"
bcrm_rustflags_thin_retry_again = "results-bcrmpass-embed-bitcode-yes-lto-thin-retry-again"
bcrm_rustflags_off_retry = "results-bcrmpass-embed-bitcode-no-lto-off-retry"
bcrm_rustflags_unspec_retry = "results-bcrmpass-embed-bitcode-no-lto-unspec-retry"
bcrm_rustflags_thin_append_simplifycfg = "results-bcrmpass-embed-bitcode-yes-lto-thin-append-simplifycfg"
bcrm_rustflags_thin_append_simplifycfg_cargobench = "results-bcrmpass-embed-bitcode-yes-lto-thin-append-simplifycfg-cargobench"
irce_rustflags_thin_append_simplifycfg_cargobench = "results-ircepass-embed-bitcode-yes-lto-thin-append-simplifycfg-cargobench"
# post segfault fix
bcrm_rustflags_thin = "results-bcrmpass-embed-bitcode-yes-lto-thin"

top_switcher = {
    "top-200": {
        "label": "1: [In-Tree LLVM Pass] RUSTFLAGS='-C opt-level=3 -C embed-bitcode=yes -C lto=thin -Z remove-bc' vs RUSTFLAGS='-C opt-level=3 -C embed-bitcode=yes -C lto=thin' [average of 40 runs]",
        "dir": bcrm_rustflags_thin_retry_again
    }
}

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
    "diff-mir-ltos-1": {
        "label": "1 vs 3",
        "y-axis-label": "3 Time per Iteration Relative to 1 [%]",
        "dir-baseline": lto_off_1,
        "dir-tocompare": lto_thin_1,
    },
    "diff-mir-ltos-2": {
        "label": "2 vs 4",
        "y-axis-label": "4 Time per Iteration Relative to 2 [%]",
        "dir-baseline": lto_off_2,
        "dir-tocompare": lto_thin_2,
    },
    "diff-mir-off": {
        "label": "1 vs 2",
        "y-axis-label": "2 Time per Iteration Relative to 1 [%]",
        "dir-baseline": lto_off_1,
        "dir-tocompare": lto_off_2,
    },
    "diff-mir-off": {
        "label": "1 vs 4",
        "y-axis-label": "4 Time per Iteration Relative to 1 [%]",
        "dir-baseline": lto_off_1,
        "dir-tocompare": lto_thin_2,
    },
    "diff-mir-thin": {
        "label": "3 vs 4",
        "y-axis-label": "4 Time per Iteration Relative to 3 [%]",
        "dir-baseline": lto_thin_1,
        "dir-tocompare": lto_thin_2,
    },
    "diff-mir-inline": {
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
    "diff-bcrm-out-opt": {
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
    "diff-bcrm-out-opt-many": {
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
    "diff-mir-v-bcrm-out": {
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
        "label": "13: [In-Tree LLVM Pass] cargo rustc -C opt-level=3 -C embed-bitcode=no -C lto=off -- -Z remove-bc (called from LLVM's ModulePass Manager) vs using nightly rustc (with rustc/LLVM versions matched) [average of 42 runs]",
        "dir": bcrm_mpm
    },
    "bcrm-mod-rustc-only": {
        "label": "14: [In-Tree LLVM Pass] cargo rustc -C opt-level=3 -C embed-bitcode=no -C lto=off -- -Z remove-bc (called from LLVM's ModulePass Manager) vs our modified rustc withOUT '-Z remove-bc' [average of 42 runs]",
        "dir": bcrm_mod_rustc_only
    },
    "bcrm-rescrape": {
        "label": "15: [In-Tree LLVM Pass] cargo rustc -C opt-level=3 -C embed-bitcode=no -C lto=off -- -Z remove-bc (called from LLVM's ModulePass Manager) vs our modified rustc withOUT '-Z remove-bc' [average of 42 runs, after scraping crates.io again for updated crate list]",
        "dir": bcrm_rescrape
    },
    "bcrm-rustflags": {
        "label": "16: [In-Tree LLVM Pass] RUSTFLAGS='-C opt-level=3 -C embed-bitcode=no -Z remove-bc' vs RUSTFLAGS='-C opt-level=3 -C embed-bitcode=no' [average of 42 runs]",
        "dir": bcrm_rustflags
    },
    "bcrm-rustflags-lto-off": {
        "label": "17: [In-Tree LLVM Pass] RUSTFLAGS='-C opt-level=3 -C embed-bitcode=no -C lto=off -Z remove-bc' vs RUSTFLAGS='-C opt-level=3 -C embed-bitcode=no -C lto=off' [average of 42 runs]",
        "dir": bcrm_rustflags_off_retry
    },
    "bcrm-rustflags-lto-unspec": {
        "label": "18: [In-Tree LLVM Pass] RUSTFLAGS='-C opt-level=3 -C embed-bitcode=no -Z remove-bc' vs RUSTFLAGS='-C opt-level=3 -C embed-bitcode=no' [average of 42 runs]",
        "dir": bcrm_rustflags_unspec_retry
    },
    #"bcrm-rustflags-thin": {
    #    "label": "17: [In-Tree LLVM Pass] RUSTFLAGS='-C opt-level=3 -C embed-bitcode=yes -C lto=thin -Z remove-bc' vs RUSTFLAGS='-C opt-level=3 -C embed-bitcode=yes -C lto=thin' [average of 42 runs]",
    #    "dir": bcrm_rustflags_thin
    #},
    #"bcrm-rustflags-thin-retry": {
    #    "label": "18: [In-Tree LLVM Pass] RUSTFLAGS='-C opt-level=3 -C embed-bitcode=yes -C lto=thin -Z remove-bc' vs RUSTFLAGS='-C opt-level=3 -C embed-bitcode=yes -C lto=thin' [average of 36 runs]",
    #    "dir": bcrm_rustflags_thin_retry
    #},
    "bcrm-rustflags-thin-retry-again": {
        "label": "19: [In-Tree LLVM Pass] RUSTFLAGS='-C opt-level=3 -C embed-bitcode=yes -C lto=thin -Z remove-bc' vs RUSTFLAGS='-C opt-level=3 -C embed-bitcode=yes -C lto=thin' [average of 36 runs]",
        "dir": bcrm_rustflags_thin_retry_again
    },
    "bcrm-rustflags-thin-append-simplifycfg": {
        "label": "20: [In-Tree LLVM Pass] RUSTFLAGS='-C opt-level=3 -C embed-bitcode=yes -C lto=thin -Z remove-bc' vs RUSTFLAGS='-C opt-level=3 -C embed-bitcode=yes -C lto=thin' [average of 40 runs]; extra SimplifyCFG before RemoveBC",
        "dir": bcrm_rustflags_thin_append_simplifycfg
    },
    "bcrm-rustflags-thin-append-simplifycfg-cargobench": {
        "label": "21: [In-Tree LLVM Pass] RUSTFLAGS='-C opt-level=3 -C embed-bitcode=yes -C lto=thin -Z remove-bc' vs RUSTFLAGS='-C opt-level=3 -C embed-bitcode=yes -C lto=thin' [average of 35 runs]; extra SimplifyCFG before RemoveBC + ran with cargo bench (recovery)",
        "dir": bcrm_rustflags_thin_append_simplifycfg_cargobench
    },
    "irce-rustflags-thin-append-simplifycfg-cargobench": {
        "label": "22: [In-Tree LLVM Pass] RUSTFLAGS='-C opt-level=3 -C embed-bitcode=yes -C lto=thin -Z remove-bc' vs RUSTFLAGS='-C opt-level=3 -C embed-bitcode=yes -C lto=thin' [average of 40 runs]; extra SimplifyCFG before IRCE + ran with cargo bench (recovery)",
        "dir": irce_rustflags_thin_append_simplifycfg_cargobench
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
    "diff-mir-v-bcrm-fpm": {
        "label": "2 vs 13",
        "y-axis-label": "13 Time per Iteration Relative to 2 [%]",
        "dir-baseline": lto_off_2,
        "dir-tocompare": bcrm_mpm,
    },
    "diff-mir-v-bcrm-mpm": {
        "label": "2 vs 14",
        "y-axis-label": "14 Time per Iteration Relative to 2 [%]",
        "dir-baseline": lto_off_2,
        "dir-tocompare": bcrm_mpm,
    },
    "diff-bcrm-fpm-mpm": {
        "label": "12 vs 13",
        "y-axis-label": "12 Time per Iteration Relative to 13 [%]",
        "dir-baseline": bcrm_mpm,
        "dir-tocompare": bcrm_fpm,
    },
    "diff-bcrm-night-v-mod": {
        "label": "13 vs 14",
        "y-axis-label": "13 Time per Iteration Relative to 14 [%]",
        "dir-baseline": bcrm_mod_rustc_only,
        "dir-tocompare": bcrm_mpm,
    },
    "diff-bcrm-more-bmarks": {
        "label": "14 vs 15",
        "y-axis-label": "14 Time per Iteration Relative to 15 [%]",
        "dir-baseline": bcrm_rescrape,
        "dir-tocompare": bcrm_mod_rustc_only,
    },
    "diff-bcrm-in-out-rustflags": {
        "label": "15 vs 16",
        "y-axis-label": "16 Time per Iteration Relative to 15 [%]",
        "dir-baseline": bcrm_rescrape,
        "dir-tocompare": bcrm_rustflags,
    },
    "diff-bcrm-mir-coverage": {
        "label": "16 vs 1",
        "y-axis-label": "16 Time per Iteration Relative to 1 [%]",
        "dir-baseline": lto_off_1,
        "dir-tocompare": bcrm_rustflags,
    },
    "diff-bcrm-unspecs": { # should be roughly equal
        "label": "18 vs 16",
        "y-axis-label": "18 Time per Iteration Relative to 16 [%]",
        "dir-baseline": bcrm_rustflags,
        "dir-tocompare": bcrm_rustflags_unspec_retry,
    },
    "diff-bcrm-embed-bitcode-nos": {
        "label": "18 vs 17",
        "y-axis-label": "18 Time per Iteration Relative to 17 [%]",
        "dir-baseline": bcrm_rustflags_off_retry,
        "dir-tocompare": bcrm_rustflags_unspec_retry,
    },
    "diff-bcrm-off-to-thin": {
        "label": "19 vs 17",
        "y-axis-label": "19 Time per Iteration Relative to 17 [%]",
        "dir-baseline": bcrm_rustflags_off_retry,
        "dir-tocompare": bcrm_rustflags_thin_retry_again,
    },
    "diff-bcrm-unspec-to-thin": {
        "label": "19 vs 18",
        "y-axis-label": "19 Time per Iteration Relative to 18 [%]",
        "dir-baseline": bcrm_rustflags_unspec_retry,
        "dir-tocompare": bcrm_rustflags_thin_retry_again,
    },
    "diff-bcrm-thin-to-simplifycfg": {
        "label": "20 vs 19",
        "y-axis-label": "20 Time per Iteration Relative to 19 [%]",
        "dir-baseline": bcrm_rustflags_thin_retry_again,
        "dir-tocompare": bcrm_rustflags_thin_append_simplifycfg,
    },
    "diff-bcrm-simplifycfg-cargorustc-vs-cargobench": {
        "label": "21 vs 20",
        "y-axis-label": "21 Time per Iteration Relative to 20 [%]",
        "dir-baseline": bcrm_rustflags_thin_append_simplifycfg,
        "dir-tocompare": bcrm_rustflags_thin_append_simplifycfg_cargobench,
    },
    "diff-bcrm-cargobench-w-a-wout-simplifycfg": {
        "label": "21 vs 19",
        "y-axis-label": "21 Time per Iteration Relative to 19 [%]",
        "dir-baseline": bcrm_rustflags_thin_retry_again,
        "dir-tocompare": bcrm_rustflags_thin_append_simplifycfg_cargobench,
    },
    "diff-bcrm-cargobench-w-a-wout-simplifycfg": {
        "label": "22 vs 21",
        "y-axis-label": "22 Time per Iteration Relative to 21 [%]",
        "dir-baseline": bcrm_rustflags_thin_append_simplifycfg_cargobench,
        "dir-tocompare": irce_rustflags_thin_append_simplifycfg_cargobench,
    },
    "bcrm-rustflags-thin": {
        "label": "23: [Fixed SegFault] RUSTFLAGS='-C opt-level=3 -C embed-bitcode=yes -C lto=thin -Z remove-bc' vs RUSTFLAGS='-C opt-level=3 -C embed-bitcode=yes -C lto=thin' [average of 36 runs]",
        "dir": bcrm_rustflags_thin
    },
    "diff-bcrm-segfault": {
        "label": "23 vs 19",
        "y-axis-label": "23 Time per Iteration Relative to 19 [%]",
        "dir-baseline": bcrm_rustflags_thin_retry_again,
        "dir-tocompare": bcrm_rustflags_thin,
    },
}


def get_crates():
    global bencher_rev_dep_crates
    for name in os.listdir(path_to_crates):
        if os.path.isdir(os.path.join(path_to_crates, name)):
            bencher_rev_dep_crates.append(name)
    bencher_rev_dep_crates.sort()


def get_top_crates():
    global top_crates
    for name in os.listdir(path_to_top):
        if os.path.isdir(os.path.join(path_to_top, name)):
            top_crates.append(name)
    top_crates.sort()


# Geometric mean helper
def geo_mean_overflow(iterable):
    locarr = []
    for i in iterable:
        if i == 0:
            locarr.append(10**-100)
        else:
            locarr.append(i)
        #print("value = " + str(i))
    # Convert all elements to positive numbers
    a = np.log(locarr)
    #print(a)
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



# some setting for plot
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.config.suppress_callback_exceptions = True


def crate_options():
    options = []
    global bencher_rev_dep_crates
    for crate in bencher_rev_dep_crates:
        options.append({'label': crate, 'value': crate})
    return options


def top_crate_options():
    options = []
    global top_crates
    for crate in top_crates:
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


def top_setting_options():
    options = []
    global top_switcher
    keys = top_switcher.keys()
    for k in keys:
        label = top_switcher.get(k).get("label")
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


def getPerfTopLayout():

    layout = html.Div([
        html.Br(),
        html.Label('Pick a crate:'),
        dcc.Dropdown(id='crate_name',
            options=top_crate_options(),
            value='adler32-1.2.0', #aerospike-0.5.0',
            style={'width': '50%'}
        ),

        html.Br(),
        html.Label('Pick a setting:'),
        dcc.RadioItems(id='crate_opt',
            options=top_setting_options(),
            value="top-200" #diff-bcrm-thin-to-simplifycfg"
        ),

        html.Br(),
        html.Label('Lower is better!'),
        html.Div(id='crate-content')
    ])

    return layout


def getPerfRustcsLayout():

    layout = html.Div([
        html.Br(),
        html.Label('Pick a crate:'),
        dcc.Dropdown(id='crate_name',
            options=crate_options(),
            value='aerospike-0.5.0',
            style={'width': '50%'}
        ),

        html.Br(),
        html.Label('Pick a setting:'),
        dcc.RadioItems(id='crate_opt',
            options=setting_options(),
            value="diff-bcrm-thin-to-simplifycfg"
        ),

        html.Br(),
        html.Label('Lower is better!'),
        html.Div(id='crate-content')
    ])

    return layout


def getPerfPassLayout():

    layout = html.Div([
        #html.Br(),
        #html.H1(children='Testing..?', style={'textAlign': 'center'}),

        html.Br(),
        html.Label('Across all crates, choose which result you would like to view:'),
        dcc.RadioItems(id='result_type',
            options=[
                    {'label': 'Benchmarks where removal of bounds checks performs BETTER', 'value': 'intuitive'},
                    {'label': 'Benchmarks where removal of bounds checks performs WORSE', 'value': 'unintuitive'},
                    {'label': 'Benchmarks where removal of bounds checks performs trivially (i.e. everything else)', 'value': 'other'},
            ],
            value='intuitive',
            style={'width': '70%'}
        ),

        html.Br(),
        html.Label('Lower is better!'),
        html.Div(id='crate-content-front')
    ])

    return layout


@app.callback(dash.dependencies.Output('crate-content', 'children'),
               [dash.dependencies.Input('crate_name', 'value'),
                dash.dependencies.Input('crate_opt', 'value')])
def display_crate_info(crate_name, crate_opt):

    if 'diff' in crate_opt:
        return display_diff(crate_name, crate_opt)
    else:
        return display_relative(crate_name, crate_opt)


@app.callback(dash.dependencies.Output('crate-content-front', 'children'),
              [dash.dependencies.Input('result_type', 'value')])
def display_crate_info(result_type):

    return display_significant(result_type)


def display_diff(crate_name, crate_opt):

    if "bcrm" in crate_opt and not "mir" in crate_opt:
        file_baseline = path_to_crates + "/" + crate_name + "/" + switcher.get(crate_opt).get("dir-baseline") + "/" + data_file_new
        file_tocompare = path_to_crates + "/" + crate_name + "/" + switcher.get(crate_opt).get("dir-tocompare") + "/" + data_file_new
    elif "bcrm" in crate_opt and "mir" in crate_opt:
        file_baseline = path_to_crates + "/" + crate_name + "/" + switcher.get(crate_opt).get("dir-baseline") + "/" + data_file
        file_tocompare = path_to_crates + "/" + crate_name + "/" + switcher.get(crate_opt).get("dir-tocompare") + "/" + data_file_new
    else:
        file_baseline = path_to_crates + "/" + crate_name + "/" + switcher.get(crate_opt).get("dir-baseline") + "/" + data_file
        file_tocompare = path_to_crates + "/" + crate_name + "/" + switcher.get(crate_opt).get("dir-tocompare") + "/" + data_file

    #if ((not os.path.exists(file_baseline)) or is_empty_datafile(file_baseline)) or ((not os.path.exists(file_tocompare)) or is_empty_datafile(file_tocompare)):
    #    return "\n\nNo diff data for [" + str(crate_name) + "] with these settings."

    no_baseline = 0
    no_tocompare = 0

    if (not os.path.exists(file_baseline)) or is_empty_datafile(file_baseline): 
        no_baseline = 1
    if (not os.path.exists(file_tocompare)) or is_empty_datafile(file_tocompare):
        no_tocompare = 1
    if no_baseline == 1 and no_tocompare == 1: 
        return "\n\nNo diff data for [" + str(crate_name) + "] with these settings."
    elif no_baseline == 0 and no_tocompare == 1: 
        return "\n\nMISMATCH: No diff data for [" + str(crate_name) + "] with the ~to compare~ setting."
    elif no_baseline == 1 and no_tocompare == 0: 
        return "\n\nMISMATCH: No diff data for [" + str(crate_name) + "] with the ~baseline~ setting."

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


def display_relative(crate_name, crate_opt): 

    if "top" in crate_opt:
        filepath = path_to_top + "/" + crate_name + "/" + top_switcher.get(crate_opt).get("dir") + "/" + data_file_new
    elif "bcrm" in crate_opt:
        filepath = path_to_crates + "/" + crate_name + "/" + switcher.get(crate_opt).get("dir") + "/" + data_file_new
    else: 
        filepath = path_to_crates + "/" + crate_name + "/" + switcher.get(crate_opt).get("dir") + "/" + data_file

    if (not os.path.exists(filepath)) or is_empty_datafile(filepath):
        return "\n\nNo relative data for [" + str(crate_name) + "] with these settings."

    speedup_arr = []

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

            # calculate actual speedup
            speedup_div = 1 + (perc_time / 100)
            speedup = 1 if speedup_div == 0 else 1 / speedup_div
            #speedup = 1 / (1 + (perc_time / 100))
            speedup_arr.append(speedup)

            one_perf_list.append(perc_time)
            one_y_error_list.append(perc_e)

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

    geo_speedup = geo_mean_overflow(speedup_arr)

    return html.Div([
        html.Br(),
        html.Label('Average Speedup for [' + crate_name + ']: ' + str(geo_speedup)),
        html.Br(),
        html.Label(str(len(speedup_arr)) + ' Benchmarks'),
        dcc.Graph(
            id='rustc-compare-graph-rel',
            figure=fig
        )
    ])


def display_significant(result_type):

    one_bmark_list = []
    one_perf_list = []
    one_yerror_list = []

    # array for just tracking the speedup in the BETTER, WORSE, or neither "setting"
    speedup_arr_setting = dict() # make dictionary: speedup -> name
    # all speedup (for histogram)
    speedup_arr = []
    max_benefit = []
    histo_arr = []

    def get_one_bar(bar_name, bar_color):

        global bencher_rev_dep_crates
        bmark_ctr = 0

        for c in bencher_rev_dep_crates: 

            #filepath = path_to_crates + "/" + c + "/" + switcher.get('bcrm-rustflags-thin-retry-again').get("dir") + "/" + data_file_new
            filepath = path_to_crates + "/" + c + "/" + switcher.get('bcrm-rustflags-thin').get("dir") + "/" + data_file_new

            if (not os.path.exists(filepath)) or is_empty_datafile(filepath):
                continue

            # open data file for reading
            handle = open(filepath, 'r')

            for line in handle: 
                if line[:1] == '#':
                    continue
                cols = line.split()

                name = c + "::" + cols[0]
                bmark_ctr += 1

                vanilla_time = cols[1]
                vanilla_error = cols[2]
                nobc_time = cols[3]
                nobc_error = cols[4]

                div = float(vanilla_time) if float(vanilla_time) != 0 else 1
                perc_time = ((float(nobc_time) - float(vanilla_time)) / div) * 100

                speedup_div = 1 + (perc_time / 100)
                speedup = 1 if speedup_div == 0 else 1 / speedup_div
                if result_type == 'unintuitive' and speedup < 1: 
                    speedup_arr_setting[speedup] = name
                elif result_type == 'intuitive' and speedup >= 1 and speedup < 1.6:
                    speedup_arr_setting[speedup] = name

                if speedup < 1.6:
                    speedup_arr.append(speedup)
                if speedup >= 1 and speedup < 1.6: 
                    max_benefit.append(speedup)
                else: 
                    max_benefit.append(1)
                #if speedup < 350:
                histo_arr.append(speedup)

                div_e = float(nobc_time) if float(nobc_time) != 0 else 1
                perc_error = (float(nobc_error) / div_e) * 100
                vanilla_perc_error = (float(vanilla_error) / div) * 100

                # if positive and unintuitive
                if result_type == 'unintuitive' and perc_time > 0:
                    # perc_time is within vanilla stdev
                    if perc_time < float(vanilla_perc_error): 
                        #print("bmark = " + c + "::" + name)
                        #print("perc_time = " + str(perc_time))
                        #print("vanilla_error = " + str(vanilla_error))
                        #print("vanilla_perc_error = " + str(vanilla_perc_error))
                        continue
                    # stdev magnitude is larger than perc_time magnitude
                    elif perc_time < float(perc_error):
                        continue
                    # perc_time magnitude is less than 3%
                    elif perc_time < 3:
                        continue
                    else:
                        one_bmark_list.append(name)
                        one_perf_list.append(perc_time)
                        one_yerror_list.append(perc_error)
                # if negative and intuitive
                elif result_type == 'intuitive' and perc_time < 0:
                    # perc_time is within vanilla stdev
                    if abs(perc_time) < float(vanilla_perc_error): 
                        #print("bmark = " + c + "::" + name)
                        #print("perc_time = " + str(perc_time))
                        #print("vanilla_error = " + str(vanilla_error))
                        #print("vanilla_perc_error = " + str(vanilla_perc_error))
                        continue
                    # stdev magnitude is larger than perc_time magnitude
                    elif abs(perc_time) < float(perc_error):
                        continue
                    # perc_time magnitude is less than 3%
                    elif abs(perc_time) < 3:
                        continue
                    else:
                        one_bmark_list.append(name)
                        one_perf_list.append(perc_time)
                        one_yerror_list.append(perc_error)
                # add all other benchmarks to this graph
                elif result_type == 'other': # and perc_time < 0:
                    if abs(perc_time) < float(vanilla_perc_error) or abs(perc_time) < float(perc_error) or abs(perc_time) < 3:
                        one_bmark_list.append(name)
                        one_perf_list.append(perc_time)
                        one_yerror_list.append(perc_error)


            handle.close()

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

    if result_type == 'other':
        avg_speedup_setting = "Not calculated"
    else: 
        avg_speedup_setting = geo_mean_overflow(list(speedup_arr_setting))
    avg_speedup = geo_mean_overflow(speedup_arr)
    max_ben = geo_mean_overflow(max_benefit)
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
    parser.add_argument("-p", "--root_path", type=str, required=True,
                        help="Root path of CPF benchmark directory")
    parser.add_argument("--port", type=str, default="8050",
                        help="Port for Dash server to run, 8050 or 8060 on AWS")
    args = parser.parse_args()
    return args.root_path, args.port


@app.callback(dash.dependencies.Output('page-content', 'children'),
              [dash.dependencies.Input('url', 'pathname')])
def display_page(pathname):
    if not pathname:
        return 404

    if pathname == '/':
        pathname = '/comparePass'

    if pathname == '/compareBencherRevDeps':
        layout = getPerfRustcsLayout() #app._resultProvider)
        return layout
    if pathname == '/compareTop200':
        layout = getPerfTopLayout()
        return layout
    if pathname == '/comparePass':
        layout = getPerfPassLayout() #app._resultProvider)
        return layout
    else:
        return 404


if __name__ == '__main__':
    cpf_root, port = parseArgs()
    # I'm not actually using this...
    #result_path = os.path.join(cpf_root, "./crates/crates")
    #app._resultProvider = ResultProvider(result_path)

    get_crates()
    get_top_crates()

    app.layout = html.Div([
        dcc.Location(id='url', refresh=False),
        dcc.Link('All Techniques on Bencher Reverse Dependencies', href='/compareBencherRevDeps'),
        html.Br(),
        dcc.Link('All Techniques on Top 200 Most Downloaded Crates', href='/compareTop200'),
        html.Br(),
        dcc.Link('In-Tree LLVM Pass', href='/comparePass'),
        html.Br(),
        html.Div(id='page-content')
    ])

    app.run_server(debug=False, host='0.0.0.0', port=port)
