#!/usr/bin/env python

import os
import sys
import argparse
import platform
import random
import subprocess
import shutil
import numpy
from aggregate import dump_benchmark, path_wrangle, writerow
from crunch import crunch, stats
import datetime
import re

EXPLORE_OG = "explore"
EXPLORE_RX = "explore_regex"
RESULTS = "results"

COMPILE = os.path.join("/benchdata", "BoundsCheckExplorer", "make_onebc.sh")
RUN = os.path.join("/benchdata", "BoundsCheckExplorer", "gen_and_run_regex_exp.sh")
REGEX_PY = os.path.join("/benchdata", "BoundsCheckExplorer", "regexify.py")

UNMOD = "UNMOD"
REGEX = "REGEX"
exp_types = [UNMOD, REGEX]
headers = ['#', 'bench-name', 'unmod-time', 'unmod-error', 'bcrm-time', 'bcrm-error']

optval =    "3"
dbgval =    "2"
embdval =   "yes"
OPTFLAGS =  " -C opt-level={}".format(optval)
DBGFLAGS =  " -C debuginfo={}".format(dbgval)
EMBDFLAGS = " -C embed-bitcode={}".format(embdval)
RBCFLAGS =  " -Z remove-bc"
UNMODFLAGS = OPTFLAGS + DBGFLAGS + EMBDFLAGS
BCRMPFLAGS = OPTFLAGS + DBGFLAGS + EMBDFLAGS + RBCFLAGS

TESTS_OUT =     "tests.out"
TESTS_ERR =     "tests.err"
COMP_OUT =      "compile.out"
COMP_ERR =      "compile.err"
BENCH_DATA =    "bench.data"
CRUNCHED_DATA = "crunched.data"

category_map = {
    "criterion":    "criterion_rev_deps",
}

class State: 

    def __init__(self, scrape, test, cmpl, bench, local, remote, clean):
        self.ctgry = 'criterion'
        self.ctgrydir = category_map.get(self.ctgry)
        self.scrape = scrape
        self.test = test
        self.cmpl = cmpl
        self.bench = bench
        self.local = local
        self.remote = remote
        self.clean = clean

        self.root = os.getcwd()
        self.scrapedir = os.path.join(self.root, "get-crates")
        self.subdirs = os.path.join(self.root, self.ctgrydir)

    def scrape_crates(self):
        os.chdir(self.scrapedir)
        subprocess.run(["scrapy", "crawl", "-a", "category={}".format(self.ctgry), "-a", 
                "x={}".format(self.scrape), "get-crates"])
        os.chdir(self.root)

    def create_dirlist(self, remote=False):
        self.dirlist = []
        if remote == True: 
            for path in os.listdir(RESULTS):
                full_path = os.path.join(RESULTS, path)
                if os.path.isdir(full_path): 
                    self.dirlist.append(full_path)
        elif os.path.exists(self.subdirs):
            for path in os.listdir(self.subdirs):
                full_path = os.path.join(self.subdirs, path)
                if os.path.isdir(full_path): 
                    self.dirlist.append(full_path)
        else: 
            exit("directory <{}> or directory <{}> "\
            "do not exist, need to run "\
            "scraper for the -{}- category of crates OR "\
            "crunch remote results".format(self.subdirs, RESULTS, self.ctgry))

    def randomize_dirlist(self):
        random.shuffle(self.dirlist)

    def revert_criterion_version(self):
        subprocess.run(["cargo", "install", "cargo-edit"])
        for d in self.dirlist: 
            os.chdir(d)
            subprocess.run(["cargo", "rm", "criterion", "--dev"])
            subprocess.run(["cargo", "add", "criterion@=0.3.2", "--dev"])
            os.chdir(self.root)

    def run_tests(self):
        for e in exp_types:
            os.environ["RUSTFLAGS"] = UNMODFLAGS if e == UNMOD else BCRMPFLAGS
            curnum = 0
            totalnum = len(self.dirlist)

            for d in self.dirlist:
                os.chdir(d)
                outdir = os.path.join(d, e, RESULTS)
                curnum += 1
                print("Testing {}/{} crates...".format(curnum, totalnum))
                print(outdir)
                subprocess.run(["mkdir", "-p", outdir])
                f_out = open(os.path.join(outdir, TESTS_OUT), "w")
                f_err = open(os.path.join(outdir, TESTS_ERR), "w")
                try: 
                    subprocess.run(["cargo", "test", "--verbose"], 
                            text=True, timeout=600, stdout=f_out, stderr=f_err)
                except subprocess.TimeoutExpired as err: 
                    print(err)
                    fname = os.path.join(outdir, "test-timedout-{}".format(e))
                    subprocess.run(["touch", fname])
                finally: 
                    f_out.close()
                    f_err.close()
                    os.chdir(self.root)

    def crunch_test_results(self):
        for d in self.dirlist: 
            os.chdir(d)
            unmod_res = os.path.join(d, UNMOD, RESULTS, TESTS_OUT)
            unmod_oks = subprocess.run(["grep", "-cw", "ok", unmod_res],
                    capture_output=True, text=True)
            bcrmp_res = os.path.join(d, BCRMP, RESULTS, TESTS_OUT)
            bcrmp_oks = subprocess.run(["grep", "-cw", "ok", bcrmp_res],
                    capture_output=True, text=True)
            if not int(unmod_oks.stdout) == int(bcrmp_oks.stdout): 
                print("Mismatch in number of passed tests for: {}".format(d.split("/")[-1]))
                fname = os.path.join(d, "test-mismatch")
                subprocess.run(["touch", fname])
            os.chdir(self.root)

    def get_bmark_names(self):
        self.bnames = dict()
        for d in self.dirlist: 
            names = []
            ctoml = open(os.path.join(d, "Cargo.toml"))
            ctoml_data = ctoml.read()
            ctoml.close()
            # well-spaced
            matches = re.findall(r'(?<=\[\[bench\]\][\s]name[\s]=[\s]\")[a-zA-Z_][a-zA-Z0-9_-]*', ctoml_data)
            for m in matches: 
                names.append(m)
            # no spaces
            matches = re.findall(r'(?<=\[\[bench\]\][\s]name=\")[a-zA-Z_][a-zA-Z0-9_-]*', ctoml_data)
            for m in matches: 
                names.append(m)
            # off spaces
            matches = re.findall(r'(?<=\[\[bench\]\][\s]name=[\s]\")[a-zA-Z_][a-zA-Z0-9_-]*', ctoml_data)
            for m in matches: 
                names.append(m)
            matches = re.findall(r'(?<=\[\[bench\]\][\s]name[\s]=\")[a-zA-Z_][a-zA-Z0-9_-]*', ctoml_data)
            for m in matches: 
                names.append(m)
            self.bnames.update({d: names})

    def compile_benchmarks(self, regex=False):
        self.get_bmark_names()
        curnum = 0
        totalnum = len(self.dirlist)
        EXPLORE = EXPLORE_RX if regex else EXPLORE_OG
        if EXPLORE == EXPLORE_OG: 
            print("Compiling original crates")
        else: 
            print("Compiling regexified crates")

        for d in self.dirlist:
            curnum += 1
            os.chdir(d)
            outdir = os.path.join(d, EXPLORE)
            print("Compiling {}/{} crates...".format(curnum, totalnum))
            print(outdir)
            subprocess.run(["mkdir", "-p", outdir])
            for b in self.bnames.get(d): 
                print("\tBenchmark: {}".format(b))
                f_out = open(os.path.join(outdir, "{}_{}".format(b, COMP_OUT)), "w")
                f_err = open(os.path.join(outdir, "{}_{}".format(b, COMP_ERR)), "w")
                try:
                    subprocess.run(["cargo", "clean"])
                    subprocess.run([COMPILE, b, EXPLORE], text=True, timeout=600,
                            stdout=f_out, stderr=f_err)
                except subprocess.TimeoutExpired as err: 
                    print(err)
                    fname = os.path.join(outdir, "compile-timedout-{}".format(e))
                    subprocess.run(["touch", fname])
                finally: 
                    f_out.close()
                    f_err.close()
            os.chdir(self.root)

    def run_benchmarks(self):
        self.get_bmark_names()
        for r in range(self.bench): 
            self.randomize_dirlist()
            curnum = 0
            totalnum = len(self.dirlist)
            for d in self.dirlist:
                os.chdir(d)
                outdir = os.path.join(d, RESULTS, str(r))
                curnum += 1
                print("Benchmarking {}/{} crates...".format(curnum, totalnum))
                print(outdir)
                subprocess.run(["mkdir", "-p", outdir])
                for e in exp_types:
                    print(e)
                    EXPLORE = EXPLORE_RX if e == REGEX else EXPLORE_OG
                    for b in self.bnames.get(d):
                        print("\tBenchmark: {}".format(b))
                        f_out = open(os.path.join(outdir, "{}_{}.out".format(b, e)), "w")
                        f_err = open(os.path.join(outdir, "{}_{}.err".format(b, e)), "w")
                        try:
                            subprocess.run([RUN, b, EXPLORE], text=True, timeout=1200, 
                                    stdout=f_out, stderr=f_err)
                        except subprocess.TimeoutExpired as err: 
                            print(err)
                            fname = os.path.join(outdir, "bench-timedout-{}".format(e))
                            subprocess.run(["touch", fname])
                        finally: 
                            f_out.close()
                            f_err.close()
                os.chdir(self.root)

    # summarize data for each run of each crate
    def crunch_per_run(self):
        self.get_bmark_names()
        for r in range(self.bench):
            for d in self.dirlist:
                os.chdir(d)
                for b in self.bnames.get(d):
                    unmodres = os.path.join(d, RESULTS, str(r), "{}_{}.out".format(b, UNMOD))
                    bcrmpres = os.path.join(d, RESULTS, str(r), "{}_{}.out".format(b, REGEX))
                    outfile = os.path.join(d, RESULTS, str(r), BENCH_DATA)
                    dump_benchmark(outfile, unmodres, bcrmpres, 1)
                os.chdir(self.root)

    # summarize data for all runs of each crate on current node 
    # (assuming all data is on this node)
    def crunch_local(self, from_remote=False):
        for d in self.dirlist: 
            aggdir = os.path.join(d, RESULTS)
            outfile = os.path.join(aggdir, CRUNCHED_DATA)
            path_wrangle(outfile, headers)

            if from_remote == True: 
                sample_file = os.path.join(aggdir, "0", 
                        "{}_{}".format(BENCH_DATA, self.nodes[0]))
            else: 
                sample_file = os.path.join(aggdir, "0", BENCH_DATA)

            # count number of distinctly captured benchmarks
            runs = self.bench if self.bench else sum(os.path.isdir(os.path.join(aggdir, i)) for i in os.listdir(aggdir))
            sf = open(sample_file)
            rows = len(sf.readlines()) - 1
            sf.close()
            cols = 2
            if from_remote == True: 
                matrix = numpy.zeros((rows, cols, runs, len(self.nodes)))
            else: 
                matrix = numpy.zeros((rows, cols, runs))

            bench_names = []
            for run in range(runs):
                if from_remote == True: 
                    for nidx, node in enumerate(self.nodes): 
                        infd = open(os.path.join(aggdir, str(run), 
                                "{}_{}".format(BENCH_DATA, node)))
                        for row, line in enumerate(infd): 
                            if row == 0: continue # skip header
                            columns = line.split()
                            for col in range(len(columns)): 
                                # only get the benchmark names from one file
                                if run == 0 and col == 0: 
                                    bench_names.append(columns[col])
                                # collect <time> columns only (not <error>)
                                if col % 2 == 1:
                                    mcol_idx = int((col - 1) / 2)
                                    matrix[row-1][mcol_idx][run][nidx] = columns[col]
                        infd.close()
                else: 
                    infd = open(os.path.join(aggdir, str(run), BENCH_DATA))
                    for row, line in enumerate(infd): 
                        if row == 0: continue # skip header
                        columns = line.split()
                        for col in range(len(columns)): 
                            # only get the benchmark names from one file
                            if run == 0 and col == 0: 
                                bench_names.append(columns[col])
                            # collect <time> columns only (not <error>)
                            if col % 2 == 1: 
                                mcol_idx = int((col - 1) / 2)
                                matrix[row-1][mcol_idx][run] = columns[col]
                    infd.close()

            # crunch matrix numbers
            outfd = open(outfile, 'a')
            for row in range(rows):
                cur = []
                bench_name = bench_names[row]
                cur.append(bench_name)
                for col in range(cols):
                    if from_remote == True:
                        flat = []
                        for run in range(runs):
                            for node in range(len(self.nodes)):
                                flat.append(matrix[row][col][run][node])
                        avg, stdev = stats(flat) 
                    else: 
                        avg, stdev = stats(matrix[row][col])
                    cur.append(str(avg))
                    cur.append(str(stdev))
                writerow(outfd, cur)
            outfd.close()

    def get_crates_on_node(self, rt_path):
        contents = subprocess.run(["ssh", self.nodes[0], "ls", "-l", rt_path],
                capture_output=True, text=True)
        lines = contents.stdout.split("\n")
        crates = []
        for line in lines: 
            # skip the count of files in dir (first line)
            if line == lines[0]: 
                continue
            parts = line.split()
            if len(parts) > 0:
                crate = parts[-1]
                crates.append(crate)
        return crates

    def get_num_runs(self, rt_path, crate):
        # FIXME RESULTS not necessarily correct
        path = os.path.join(rt_path, crate, RESULTS)
        contents = subprocess.run(["ssh", self.nodes[0], "ls", "-l", path],
                capture_output=True, text=True)
        lines = contents.stdout.split("\n")
        numruns = 0
        for line in lines: 
            numruns += 1
        # account for 1) "total _" line and 2) blank line
        numruns -= 2
        return numruns

    def crunch_remote(self):
        # parse input file
        fd = open(self.remote)
        rt_paths = []
        self.nodes = []
        for line in fd: 
            if line[:1] == "/":
                rt_paths.append(line.strip())
            elif line[:1] == "#":
                continue
            else:
                self.nodes.append(line.strip())
        fd.close()
        # single path case
        if len(rt_paths) == 1:
            # get list of crates from one of the nodes
            rt_path = os.path.join(rt_paths[0], self.ctgrydir)
            crates = self.get_crates_on_node(rt_path)
            # get number of runs from one of the nodes
            runs = self.get_num_runs(rt_path, crates[0])
            # create dir to store results
            subprocess.run(["mkdir", "-p", RESULTS])
            for crate in crates: 
                name = os.path.join(RESULTS, crate)
                subprocess.run(["mkdir", "-p", name])
                resdir = os.path.join(name, RESULTS)
                subprocess.run(["mkdir", "-p", resdir])
                for run in range(runs):
                    rundir = os.path.join(resdir, str(run))
                    subprocess.run(["mkdir", "-p", rundir])
            # start copying
            for node in self.nodes: 
                for crate in crates: 
                    print("-----Copying from {} on {}-----".format(crate, node))
                    for run in range(runs): 
                        rem_path = os.path.join(rt_paths[0], self.ctgrydir, crate, 
                                RESULTS, str(run), BENCH_DATA)
                        loc_path = os.path.join(RESULTS, crate, RESULTS, 
                                str(run), "{}_{}".format(BENCH_DATA, node))
                        subprocess.run(["scp", "{}:{}".format(node, rem_path), loc_path])
            # crunch_local relies on the construction of dirlist attribute
            self.create_dirlist(remote=True)
            self.crunch_local(from_remote=True)
        # multiple paths case
        elif len(rt_paths) == len(self.nodes):
            exit("not implemented")
        # input file is incorrect
        else:
            exit("cannot parse <{}>, please see "\
            "<remote_same.example> and/or <remote.example> files for how "\
            "to format input file".format(self.remote))

    def cleanup(self):
        # remove compile directories
        if self.clean == "a" or self.clean == "c":
            for d in self.dirlist: 
                for EXPLORE in [EXPLORE_OG, EXPLORE_RX]:
                    os.chdir(d)
                    subprocess.run(["cargo", "clean"])
                    dirname = os.path.join(d, EXPLORE)
                    print("deleting directory: {}...".format(dirname))
                    try: 
                        shutil.rmtree(dirname)
                    except OSError as err: 
                        print("Error: {} : {}".format(dirname, err.strerror))
                    finally: 
                        os.chdir(self.root)
        # remove benchmark directories
        if self.clean == "a" or self.clean == "b":
            for d in self.dirlist: 
                os.chdir(d)
                print("deleting directory: {}...".format(RESULTS))
                try: 
                    shutil.rmtree(RESULTS)
                except OSError as err: 
                    print("Error: {} : {}".format(RESULTS, err.strerror))
                finally:
                    os.chdir(self.root)

def arg_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scrape", "-s",
            metavar="X",
            nargs="?",
            type=int,
            const=100,
            help="scrape top X crates of specified category from crates.io, "\
            "where X is rounded up to a multiple of 10 (default is 100)")
    parser.add_argument("--test", "-t",
            action="store_true",
            help="run tests for all scraped crates")
    parser.add_argument("--compile", "-c",
            action="store_true",
            help="compile benchmarks (intended as a precursor for eventually "\
            "running the benchmarks multiple times on multiple machines)")
    parser.add_argument("--bench", "-b",
            metavar="N",
            nargs="?",
            type=int,
            const=5,
            help="run each benchmark N times per node (default is 5)")
    parser.add_argument("--local", "-l",
            action="store_true",
            help="consolidate benchmark results across all runs on the current "\
            "node")
    parser.add_argument("--remote", "-r", 
            metavar="filename",
            type=str,
            help="consolidate benchmark results across all runs across one or "\
            "more remote nodes--specify with a file containing the list of "\
            "ssh destination nodes and the absolute path to this repository "\
            "on those nodes (see <remote.example> and <remote_same.example>)")
    parser.add_argument("--clean",
            metavar="S",
            nargs="?",
            type=str,
            const="c",
            help="remove compilation output and/or result artifacts from "\
            "prior use (default just removes compilation dirs, can use option "\
            "'a' to additionally remove benchmark result dirs or 'b' to only "\
            "remove benchmark result dirs and not compilation dirs)")
    args = parser.parse_args()
    return args.scrape, args.test, args.compile, args.bench, args.local, args.remote, args.clean

if __name__ == "__main__":
    scrape, test, cmpl, bench, local, remote, clean = arg_parse()
    s = State(scrape, test, cmpl, bench, local, remote, clean)

    start = datetime.datetime.now()

    if s.scrape:
        s.scrape_crates()
        s.revert_criterion_version()

    if not s.remote: 
        s.create_dirlist()
    if s.clean: 
        s.cleanup()
    if s.test == True:
        s.run_tests()
        s.crunch_test_results()
    if s.cmpl == True:
        s.compile_benchmarks()
        print("Converting source code with regexify.py")
        subprocess.run(["python3", REGEX_PY, "--root", s.ctgrydir])
        s.compile_benchmarks(regex=True)
    if s.bench: 
        s.run_benchmarks()
        s.crunch_per_run()
    if s.local:
        s.crunch_local()
    if s.remote: 
        s.crunch_remote()

    end = datetime.datetime.now()
    duration = end - start

    # log duration of command
    cmdfile = "{}_{}_{}_{}_{}_{}_{}.time".format(scrape, test, cmpl, bench, local, remote, clean)
    cmdfd = open(cmdfile, "w")
    cmdfd.write("start:\t\t{}\n".format(start))
    cmdfd.write("end:\t\t{}\n".format(end))
    cmdfd.write("duration:\t{}\n".format(duration))
    cmdfd.close()

