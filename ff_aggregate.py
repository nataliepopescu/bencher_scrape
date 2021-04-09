#!/usr/bin/env python

import argparse
import os
import subprocess
import shutil
import json
from result_presenter import geomean_overflow

def process(root):
    # each subdirectory in this root dir should be a different set of 
    # tests, w each having its own JSON organization so handle each separately 
    if os.path.exists(root): 
        # a11yr
        bname = "a11yr_keep"
        full_path = os.path.join(root, bname)
        print()
        print("BENCHMARK: {}\t".format(bname))
        if os.path.isdir(full_path): 
            unmod_vals = []
            regex_vals = []
            for r in range(32):
                output = open(os.path.join(full_path, "bench_{}.data".format(r)), 'w')
                unmod = open(os.path.join(full_path, "unmod_{}.json".format(r)), 'r').read()
                regex = open(os.path.join(full_path, "regex_{}.json".format(r)), 'r').read()
                json_unmod = json.loads(unmod)
                json_regex = json.loads(regex)
                unmod_val = json_unmod.get("suites")[0].get("subtests")[0].get("value")
                regex_val = json_regex.get("suites")[0].get("subtests")[0].get("value")
                unmod_vals.append(unmod_val)
                regex_vals.append(regex_val)
            unmod_geomean = geomean_overflow(unmod_vals)
            regex_geomean = geomean_overflow(regex_vals)
            print("UNMOD geomean: {}".format(unmod_geomean))
            print("REGEX geomean: {}".format(regex_geomean))
            print("REGEX vs UNMOD speedup: {}".format(unmod_geomean/regex_geomean))

        # about_newtab_with_snippets
        bname = "about_newtab_with_snippets"
        full_path = os.path.join(root, bname)
        print()
        print("BENCHMARK: {}\t".format(bname))
        if os.path.isdir(full_path): 
            unmod_vals_1 = []
            regex_vals_1 = []
            unmod_vals_2 = []
            regex_vals_2 = []
            for r in range(32):
                output = open(os.path.join(full_path, "bench_{}.data".format(r)), 'w')
                unmod = open(os.path.join(full_path, "unmod_{}.json".format(r)), 'r').read()
                regex = open(os.path.join(full_path, "regex_{}.json".format(r)), 'r').read()
                json_unmod = json.loads(unmod)
                json_regex = json.loads(regex)

                # bench 1
                unmod_val_1 = json_unmod.get("suites")[0].get("value")
                regex_val_1 = json_regex.get("suites")[0].get("value")
                unmod_vals_1.append(unmod_val_1)
                regex_vals_1.append(regex_val_1)

                # bench 2
                unmod_val_2 = json_unmod.get("suites")[1].get("subtests")[0].get("value")
                regex_val_2 = json_regex.get("suites")[1].get("subtests")[0].get("value")
                unmod_vals_2.append(unmod_val_2)
                regex_vals_2.append(regex_val_2)

            unmod_geomean_1 = geomean_overflow(unmod_vals_1)
            regex_geomean_1 = geomean_overflow(regex_vals_1)
            print("UNMOD geomean bench #1: {}".format(unmod_geomean_1))
            print("REGEX geomean bench #1: {}".format(regex_geomean_1))
            print("REGEX vs UNMOD speedup: {}".format(unmod_geomean_1/regex_geomean_1))

            unmod_geomean_2 = geomean_overflow(unmod_vals_2)
            regex_geomean_2 = geomean_overflow(regex_vals_2)
            print("UNMOD geomean bench #2: {}".format(unmod_geomean_2))
            print("REGEX geomean bench #2: {}".format(regex_geomean_2))
            print("REGEX vs UNMOD speedup: {}".format(unmod_geomean_2/regex_geomean_2))

        # about_preferences_basic
        bname = "about_preferences_basic"
        full_path = os.path.join(root, bname)
        print()
        print("BENCHMARK: {}\t".format(bname))
        if os.path.isdir(full_path): 
            unmod_vals = []
            regex_vals = []
            for r in range(32):
                output = open(os.path.join(full_path, "bench_{}.data".format(r)), 'w')
                unmod = open(os.path.join(full_path, "unmod_{}.json".format(r)), 'r').read()
                regex = open(os.path.join(full_path, "regex_{}.json".format(r)), 'r').read()
                json_unmod = json.loads(unmod)
                json_regex = json.loads(regex)

                unmod_val = json_unmod.get("suites")[0].get("value")
                regex_val = json_regex.get("suites")[0].get("value")
                unmod_vals.append(unmod_val)
                regex_vals.append(regex_val)
            unmod_geomean = geomean_overflow(unmod_vals)
            regex_geomean = geomean_overflow(regex_vals)
            print("UNMOD geomean: {}".format(unmod_geomean))
            print("REGEX geomean: {}".format(regex_geomean))
            print("REGEX vs UNMOD speedup: {}".format(unmod_geomean/regex_geomean))

def arg_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", 
            metavar="path/to/deps/",
            type=str,
            required=True,
            help="path to the directory containing Firefox results")
    args = parser.parse_args()
    return args.root

if __name__ == "__main__":
    root = arg_parse()
    process(root)
