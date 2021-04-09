#!/usr/bin/env python

import argparse
import os
import re

def patch(toml_dir, dep_root):
    toml = os.path.join(toml_dir, "Cargo.toml")
    toml = open(toml, "a")

    patches = dict()

    dep_root_full = os.path.join(toml_dir, dep_root)
    if os.path.exists(dep_root_full): 
        for dep in os.listdir(dep_root_full):
            full_path = os.path.join(dep_root_full, dep)
            if os.path.isdir(full_path): 
                # are there any keys already in the dictionary that are 
                # a substring of this key (and the non-matching characters 
                # are not alphabetical, i.e. a version number is appended)
                versioned = False
                for old_patch in patches.keys():
                    if old_patch in dep: 
                        unmatched = dep.replace(old_patch, "")
                        if re.search('[a-zA-Z]', unmatched) == None: 
                            # this crate is versioned, need some different logic
                            # FIXME not catching everything
                            versioned = True
                            print(dep)
                if versioned: 
                    continue
                new_patch = {
                        "path": os.path.join(dep_root, dep), 
                        "package": dep
                    }
                patches.update({dep: new_patch})

    for dep in patches.keys(): 
        toml.write("[patch.crates-io.{}]\npath = \"{}\"\npackage = \"{}\"\n\n"
                .format(dep, os.path.join(dep_root, dep), dep))

def arg_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("--toml_dir", "-t",
            metavar="path/to/toml/",
            type=str,
            required=True,
            help="path to the directory containing the Cargo.toml file to "\
                    "append to")
    parser.add_argument("--dep_root", 
            metavar="path/to/deps/",
            type=str,
            required=True,
            help="path to the directory containing the patched version of "\
                    "the dependency relative to the location of the previously "\
                    "indicated Cargo.toml")
    args = parser.parse_args()
    return args.toml_dir, args.dep_root

if __name__ == "__main__":
    toml_dir, dep_root = arg_parse()
    patch(toml_dir, dep_root)
