#!/usr/bin/env python

import argparse
import os
import subprocess
import shutil
import json
from result_presenter import geomean_overflow
from statistics import median

def process(root):
    subdir = ["a11yr", 
            "about_newtab_with_snippets", 
            "about_preferences_basic", 
            "cpstartup",
            "displaylist_mutate",
            "glterrain",
            "pdfpaint",
            "perf_reftest",
            "perf_reftest_singletons",
            "rasterflood_gradient",
            "rasterflood_svg",
            "sessionrestore"]
    # each subdirectory in this root dir should be a different set of 
    # tests, w each having its own JSON organization so handle each separately 
    for bname in subdir: 
        full_path = os.path.join(root, bname)
        print("\n*****BENCHMARK: {}*****".format(bname))
        if os.path.isdir(full_path): 
            if bname == "a11yr" or \
                    bname == "cpstartup" or \
                    bname == "pdfpaint" or \
                    bname == "perf_reftest_singletons" or \
                    bname == "rasterflood_gradient" or \
                    bname == "rasterflood_svg" or \
                    bname == "sessionrestore": 
                unmod_vals = []
                regex_vals = []
                speedups = []
                for r in range(32):
                    unmod_path = os.path.join(full_path, "unmod_{}.json".format(r))
                    regex_path = os.path.join(full_path, "regex_{}.json".format(r))
                    json_unmod = json.loads(open(unmod_path).read())
                    json_regex = json.loads(open(regex_path).read())
                    unmod_val = json_unmod.get("suites")[0].get("subtests")[0].get("value")
                    regex_val = json_regex.get("suites")[0].get("subtests")[0].get("value")
                    unmod_vals.append(unmod_val)
                    regex_vals.append(regex_val)
                    speedups.append(unmod_val/regex_val)
                unmod_med = median(unmod_vals)
                regex_med = median(regex_vals)
                print("speedup of medians: {}".format(unmod_med/regex_med))
                print("speedup geomean: {}".format(geomean_overflow(speedups)))

            if bname == "about_newtab_with_snippets": 
                unmod_vals_1 = []
                regex_vals_1 = []
                unmod_vals_2 = []
                regex_vals_2 = []
                speedups_1 = []
                speedups_2 = []
                for r in range(32):
                    unmod_path = os.path.join(full_path, "unmod_{}.json".format(r))
                    regex_path = os.path.join(full_path, "regex_{}.json".format(r))
                    json_unmod = json.loads(open(unmod_path).read())
                    json_regex = json.loads(open(regex_path).read())
                    # bench 1
                    unmod_val_1 = json_unmod.get("suites")[0].get("value")
                    regex_val_1 = json_regex.get("suites")[0].get("value")
                    unmod_vals_1.append(unmod_val_1)
                    regex_vals_1.append(regex_val_1)
                    speedups_1.append(unmod_val_1/regex_val_1)
                    # bench 2
                    unmod_val_2 = json_unmod.get("suites")[1].get("subtests")[0].get("value")
                    regex_val_2 = json_regex.get("suites")[1].get("subtests")[0].get("value")
                    unmod_vals_2.append(unmod_val_2)
                    regex_vals_2.append(regex_val_2)
                    speedups_2.append(unmod_val_2/regex_val_2)
                unmod_med_1 = median(unmod_vals_1)
                regex_med_1 = median(regex_vals_1)
                print("speedup of medians: {}".format(unmod_med_1/regex_med_1))
                print("speedup geomean: {}".format(geomean_overflow(speedups_1)))
                unmod_med_2 = median(unmod_vals_2)
                regex_med_2 = median(regex_vals_2)
                print("speedup of medians: {}".format(unmod_med_2/regex_med_2))
                print("speedup geomean: {}".format(geomean_overflow(speedups_2)))

            if bname == "about_preferences_basic" or \
                    bname == "displaylist_mutate" or \
                    bname == "glterrain" or\
                    bname == "perf_reftest":
                unmod_vals = []
                regex_vals = []
                speedups = []
                for r in range(22):
                    unmod_path = os.path.join(full_path, "unmod_{}.json".format(r))
                    regex_path = os.path.join(full_path, "regex_{}.json".format(r))
                    json_unmod = json.loads(open(unmod_path).read())
                    json_regex = json.loads(open(regex_path).read())
                    unmod_val = json_unmod.get("suites")[0].get("value")
                    regex_val = json_regex.get("suites")[0].get("value")
                    unmod_vals.append(unmod_val)
                    regex_vals.append(regex_val)
                    speedups.append(unmod_val/regex_val)
                print("unmod_vals...")
                for uv in unmod_vals:
                    print(uv)
                print("regex_vals...")
                for rv in regex_vals:
                    print(rv)
                # remove top and bottom two in each
                print("removing from unmod...")
                print("removing:\t{}".format(max(unmod_vals)))
                unmod_vals.remove(max(unmod_vals))
                print("removing:\t{}".format(max(unmod_vals)))
                unmod_vals.remove(max(unmod_vals))
                print("removing:\t{}".format(min(unmod_vals)))
                unmod_vals.remove(min(unmod_vals))
                print("removing:\t{}".format(min(unmod_vals)))
                unmod_vals.remove(min(unmod_vals))
                print("removing from regex...")
                print("removing:\t{}".format(max(regex_vals)))
                regex_vals.remove(max(regex_vals))
                print("removing:\t{}".format(max(regex_vals)))
                regex_vals.remove(max(regex_vals))
                print("removing:\t{}".format(min(regex_vals)))
                regex_vals.remove(min(regex_vals))
                print("removing:\t{}".format(min(regex_vals)))
                regex_vals.remove(min(regex_vals))

                unmod_med = median(unmod_vals)
                regex_med = median(regex_vals)
                print("speedup of medians: {}".format(unmod_med/regex_med))
                print("speedup geomean: {}".format(geomean_overflow(speedups)))

def arg_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", "-r", 
            metavar="path/to/results/",
            type=str,
            required=True,
            help="path to the directory containing Firefox results")
    args = parser.parse_args()
    return args.root

if __name__ == "__main__":
    root = arg_parse()
    process(root)
