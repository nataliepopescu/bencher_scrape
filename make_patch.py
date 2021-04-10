#!/usr/bin/env python

import argparse
import os
import re
import subprocess
import shutil

def convert(root):
    if os.path.exists(root): 
        for dep in os.listdir(root):
            full_path = os.path.join(root, dep)
            if os.path.isdir(full_path): 
                any_gu = subprocess.run(["grep", "-rn", "fn get_unchecked", 
                        full_path], capture_output=True, text=True)
                num_gu = len(any_gu.stdout.split())
                # if any locally-defined get_unchecked[_mut]s, 
                # remove from the set of crates to convert
                if num_gu > 0: 
                    print("deleting {}".format(dep))
                    try: 
                        shutil.rmtree(full_path)
                    except OSError as err: 
                        print("Error: {} : {}".format(full_path, err.strerror))

def patch(toml_dir, rel_root, root):
    toml = open(os.path.join(toml_dir, "Cargo.toml"), "a")
    patches = dict()

    if os.path.exists(root): 
        for dep in os.listdir(root):
            full_path = os.path.join(root, dep)
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
                        "path": os.path.join(rel_root, dep), 
                        "package": dep
                    }
                patches.update({dep: new_patch})

    for dep in patches.keys(): 
        toml.write("[patch.crates-io.{}]\npath = \"{}\"\npackage = \"{}\"\n\n"
                .format(dep, os.path.join(rel_root, dep), dep))

def arg_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("--toml", "-t",
            metavar="path/to/toml/",
            type=str,
            required=True,
            help="path to the directory containing the Cargo.toml file to "\
                    "append to")
    parser.add_argument("--rel_root", "-r",
            metavar="path/to/deps/",
            type=str,
            required=True,
            help="path to the directory containing the dependencies to convert, "\
                    "relative to the specified toml directory")
    args = parser.parse_args()
    return args.toml, args.rel_root

if __name__ == "__main__":
    toml, rel_root = arg_parse()
    root = os.path.join(toml, rel_root)
    convert(root)
    subprocess.run(["python3", 
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "regexify.py"), 
            "--root", root])
    patch(toml, rel_root, root)
