#!/usr/bin/env python

import argparse
import os
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

def arg_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", 
            metavar="path/to/deps/",
            type=str,
            required=True,
            help="path to the directory containing the dependencies to convert")
    args = parser.parse_args()
    return args.root

if __name__ == "__main__":
    root = arg_parse()
    convert(root)
    subprocess.run(["python3", "../BoundsCheckExplorer/regexify.py", "--root", root])
