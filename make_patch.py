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
        versioned = []
        unversioned = []
        for dep in os.listdir(root):
            full_path = os.path.join(root, dep)
            if os.path.isdir(full_path): 
                # if crate is versioned, come back to it later
                if re.search('[-][0-9]+[.][0-9]+[.][0-9]+', dep): 
                    versioned.append(dep)
                else: 
                    unversioned.append(dep)
        for v_crate in versioned: 
            m = re.search('[-][0-9]+[.][0-9]+[.][0-9]+', v_crate)
            end = m.span()[0]
            name = v_crate[:end]
            for u_crate in unversioned: 
                if u_crate == name:
                    unversioned.remove(u_crate)
                    u_patch = {
                        "path": os.path.join(rel_root, u_crate),
                    }
                    patches.update({u_crate: u_patch})
                    vname = "{}01".format(name)
                    v_patch = {
                        "path": os.path.join(rel_root, v_crate),
                        "package": name
                    }
                    patches.update({vname: v_patch})
        for u_crate in unversioned: 
            patch = {
                    "path": os.path.join(rel_root, u_crate),
                    "package": u_crate
                }
            patches.update({u_crate: patch})
        for patch in patches: 
            patch_str = []
            patch_str.append("[patch.crates-io.{}]\n".format(patch))
            info = patches.get(patch)
            for field in info: 
                value = info.get(field)
                patch_str.append("{} = \"{}\"\n".format(field, value))
            patch_str.append("\n")
            toml.write("".join(patch_str))

def arg_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("--toml", "-t",
            metavar="path/to/root/toml/",
            type=str,
            required=True,
            help="path to the directory containing the root Cargo.toml file to "\
                    "append to")
    parser.add_argument("--rel_root", "-r",
            metavar="path/to/deps/",
            type=str,
            required=True,
            help="path to the directory containing the dependencies to convert, "\
                    "relative to the root Cargo.toml")
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
