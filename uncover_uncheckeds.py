#!/usr/bin/env python3.8

import argparse
import os
import re
import subprocess
import shutil
import numpy

VENDOR = "vendor"
DIRECT_DEF = "direct_loc_def.txt"
INDIRECT_DEF = "indirect_loc_def.txt"
DIRECT_USES = "direct_uses.txt"
INDIRECT_USES = "indirect_uses.txt"
CHANGES = "changes.txt"
V_CHANGES = "vendored_changes.txt"
SUMM_DIRECT_USES = "summary_direct_num_uses.txt"
SUMM_INDIRECT_DEPS = "summary_indirect_num_deps.txt"
SUMM_INDIRECT_USES = "summary_indirect_num_uses.txt"
SUMM_TOTAL = "summary_total_uses.txt"

class State:

    def __init__(self, root, regexify):
        self.root = root
        self.regexify = regexify
        self.loc_def = []
        self.num_deps = dict()
        self.direct_uses = dict()
        self.indirect_deps = dict()
        self.indirect_uses = dict()
        self.vendor_dir = VENDOR
        self.app_dirs = dict()
        for app in os.listdir(self.root):
            path = os.path.join(self.root, app)
            if os.path.isdir(path): 
                if "flatbuffers" in app: 
                    app_dir = os.path.join(path, "rust", "flatbuffers")
                elif "flux" in app: 
                    app_dir = os.path.join(path, "libflux", "flux")
                elif "splinter" in app:
                    app_dir = os.path.join(path, "splinter")
                else: 
                    app_dir = path
                self.app_dirs.update({app: {"top-dir": path, "cargo-dir": app_dir}})

    def get_loc_def_gu(self, indirect=False):
        for app in self.app_dirs: 
            any_gu = subprocess.run(["grep", "-rn", "fn get_unchecked", 
                    self.app_dirs.get(app).get("top-dir")], 
                    capture_output=True, text=True)
            num_gu = len(any_gu.stdout.split())
            # record any crates with locally-defined get_unchecked[_mut]s
            if num_gu > 0: 
                self.loc_def.append(app)
        if indirect == True: 
            loc_def_crates = open(os.path.join(self.root, INDIRECT_DEF), "w")
        else:
            loc_def_crates = open(os.path.join(self.root, DIRECT_DEF), "w")
        for c in self.loc_def: 
            loc_def_crates.write("{}\n".format(c))

    def convert(self):
        for app in self.app_dirs:
            os.chdir(self.app_dirs.get(app).get("top-dir"))
            subprocess.run(["python3.8", self.regexify, "--root", "."])
            directs = open(DIRECT_USES, "w")
            changes = open(CHANGES, "r")

            temp = []
            for line in changes.readlines():
                changed_file = line.split()[2]
                crate = changed_file.split("/")[0]
                temp.append(crate)
            arr = numpy.array(temp)
            crates, counts = numpy.unique(arr, return_counts=True)
            crate_counts = zip(crates, counts)
            for c, i in crate_counts: 
                directs.write("{}:\t{}\n".format(c, i))
            os.chdir(self.root)

    def filter(self):
        # get list of all vendored crates
        all_deps = []
        contents = os.listdir(self.vendor_dir)
        for c in contents:
            if os.path.isdir(os.path.join(self.vendor_dir, c)):
                all_deps.append(c)
        # get list of all non-dev dependencies
        no_dev_dep_tree = subprocess.run(["cargo", "tree", "-e", "no-dev", 
                "--prefix", "none"], capture_output=True, text=True)
        lines = no_dev_dep_tree.stdout.split("\n")
        non_dev_deps = []
        for line in lines:
            non_dev_deps.append(line.replace(" v", "-"))
        # delete any vendored crates that are not in the non-dev dep list
        # (i.e. delete anything that is _only_ a dev dep)
        to_delete = [x for x in all_deps if x not in non_dev_deps]
        for d in to_delete:
            path = os.path.join(self.vendor_dir, d)
            print("deleting {}".format(d))
            try: 
                shutil.rmtree(path)
            except OSError as err: 
                print("Error: {} : {}".format(path, err.strerror))

    def vendor(self):
        # count the number of crates that have indirectly been converted
        for app in self.app_dirs:
            app_dir = self.app_dirs.get(app).get("cargo-dir")
            os.chdir(app_dir)
            print()
            print("***** current app: {} *****".format(app))
            print("  vendor dir: {}".format(self.vendor_dir))
            print()

            # vendor crates for this app
            subprocess.run(["rustup", "override", "set", "nightly-2021-02-11"])
            subprocess.run(["cargo", "vendor", "--versioned-dirs"])
            num_vendored = subprocess.run(["ls", self.vendor_dir], 
                    capture_output=True, text=True)
            if len(num_vendored.stdout) == 0:
                os.chdir(self.root)
                continue

            # filter out dev deps
            print("filtering out dev deps not otherwise used")
            self.filter()
            os.chdir(self.root)

    def convert_vendor(self):
        for app in self.app_dirs:
            app_dir = self.app_dirs.get(app).get("cargo-dir")
            os.chdir(app_dir)
            # convert vendored crates
            print("converting vendored crates for {}".format(app))
            subprocess.run(["python3.8", self.regexify, "--root", self.vendor_dir])
            v_changes_file = os.path.join(self.vendor_dir, CHANGES)
            v_changes = open(v_changes_file, "r")
            indirects = open(INDIRECT_USES, "w")
            temp = []
            for line in v_changes.readlines():
                v_changed_file = line.split()[2]
                v_crate = v_changed_file.split("/")[0]
                temp.append(v_crate)
            v_arr = numpy.array(temp)
            v_crates, v_counts = numpy.unique(v_arr, return_counts=True)
            v_crate_counts = zip(v_crates, v_counts)
            for v, i in v_crate_counts: 
                # log indirect conversions to a file
                indirects.write("{}:\t{}\n".format(v, i))

            ## delete vendor dir
            #subprocess.run(["mv", v_changes_file, V_CHANGES])
            #print("deleting vendor dir for space")
            #try: 
            #    shutil.rmtree(self.vendor_dir)
            #except OSError as err: 
            #    print("Error: {} : {}".format(self.vendor_dir, err.strerror))
            os.chdir(self.root)

    def get_direct_gus(self):
        for app in self.app_dirs:
            app_dir = self.app_dirs.get(app).get("top-dir")
            directs = open(os.path.join(app_dir, DIRECT_USES), "r").read()
            lines = directs.split("\n")
            count = 0
            for line in lines:
                if len(line) == 0:
                    break
                parts = line.split()
                count += int(parts[1])
            self.direct_uses.update({app: count})

        # write all direct gu uses to file
        summary_directs = open(os.path.join(self.root, SUMM_DIRECT_USES), "w")
        sorted_directs = {k: v for k, v in 
                sorted(self.direct_uses.items(), key=lambda item: item[1])}
        for app, count in sorted_directs.items(): 
            summary_directs.write("{}: {}\n".format(app, count))

    def get_num_deps(self):
        for app in self.app_dirs:
            app_dir = self.app_dirs.get(app).get("cargo-dir")
            os.chdir(app_dir)
            # get list of all non-dev dependencies
            num_deps = subprocess.run(["cargo", "tree", "-e", "no-dev", 
                    "--prefix", "none"], capture_output=True, text=True)
            deps = num_deps.stdout.split("\n")
            dedup_deps = []
            for d in deps: 
                if "(*)" not in d: 
                    dedup_deps.append(d)
            num_deps = len(dedup_deps)
            self.num_deps.update({app: num_deps})
            os.chdir(self.root)

    def get_indirect_deps(self): 
        for app in self.app_dirs:
            app_dir = self.app_dirs.get(app).get("cargo-dir")
            indirects = open(os.path.join(app_dir, INDIRECT_USES), "r").read()
            lines = indirects.split("\n")
            count = 0
            for line in lines:
                if len(line) == 0:
                    break
                count += 1
            self.indirect_deps.update({app: count})

        # write indirect gu deps per app to file
        summ_indirect_deps = open(os.path.join(self.root, SUMM_INDIRECT_DEPS), "w")
        sorted_indirect_deps = {k: v for k, v in
                sorted(self.indirect_deps.items(), key=lambda item: item[1])}
        for app, count in sorted_indirect_deps.items():
            summ_indirect_deps.write("{}: {}\n".format(app, count))

    def get_indirect_uses(self): 
        for app in self.app_dirs:
            app_dir = self.app_dirs.get(app).get("cargo-dir")
            indirects = open(os.path.join(app_dir, INDIRECT_USES), "r").read()
            lines = indirects.split("\n")
            count = 0
            for line in lines:
                if len(line) == 0:
                    break
                parts = line.split()
                count += int(parts[1])
            self.indirect_uses.update({app: count})

        # write indirect gu num per app to file
        summ_indirect_uses = open(os.path.join(self.root, SUMM_INDIRECT_USES), "w")
        sorted_indirect_uses = {k: v for k, v in
                sorted(self.indirect_uses.items(), key=lambda item: item[1])}
        for app, count in sorted_indirect_uses.items():
            summ_indirect_uses.write("{}: {}\n".format(app, count))

    def get_total_uses(self):
        summ_total_uses = open(os.path.join(self.root, SUMM_TOTAL), "w")
        sorted_indirects = {k: v for k, v in 
            sorted(self.indirect_uses.items(), key=lambda item: item[1])}
        for app, indirect in sorted_indirects.items():
            direct = self.direct_uses.get(app)
            all_deps = self.num_deps.get(app)
            unchecked_deps = self.indirect_deps.get(app)
            summ_total_uses.write("{} & {} & {} & {} & {}\n" 
                    .format(app, direct, indirect, all_deps, unchecked_deps))

def arg_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", "-r",
            metavar="path/to/deps/",
            type=str,
            required=True,
            help="path to the directory containing the source code to convert")
    parser.add_argument("--single", "-s",
            action="store_true",
            help="script assumes that root contains many projects to iterate "\
                    "through - pass this flag if your root path only points to "\
                    "a single project")
    args = parser.parse_args()
    return args.root, args.single

if __name__ == "__main__":
    root, single = arg_parse()
    if single: 
        exit("not implemented")
    #regexify = os.path.join(os.path.dirname(os.path.abspath(__file__)), "regexify.py")
    regexify = os.path.join(os.getcwd(), "../", "nader", "scripts", "regexify.py")
    root = os.path.join(os.getcwd(), root)
    s = State(root, regexify)
    print("check for locally-defined get_unchecked")
    s.get_loc_def_gu()
    print("convert")
    s.convert()
    print("vendoring dependencies")
    s.vendor()
    print("check for locally-defined get_unchecked in deps")
    s.get_loc_def_gu(indirect=True)
    s.convert_vendor()
    print("get all direct get_unchecked usage from top-level apps")
    s.get_direct_gus()
    print("get total num of dependencies")
    s.get_num_deps()
    print("get num of dependencies with indirect get_unchecked per top-level app")
    s.get_indirect_deps()
    print("get num of indirect get_unchecked uses per top-level app")
    s.get_indirect_uses()
    print("get total uses")
    s.get_total_uses()
