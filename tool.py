#!/usr/bin/env python

import os
import sys
import argparse
import platform
import random
import subprocess
import shutil
import numpy
from aggregate import dump_benchmark
from crunch import crunch, path_wrangle, writerow, stats

UNMOD = "UNMOD"
BCRMP = "BCRMP"
exp_types = [UNMOD, BCRMP]
headers = ['#', 'bench-name', 'unmod-time', 'unmod-error', 'bcrm-time', 'bcrm-error']

optval =    "3"
dbgval =    "2"
embdval =   "yes"
OPTFLAGS =  " -C opt-level=" + optval
DBGFLAGS =  " -C debuginfo=" + dbgval
EMBDFLAGS = " -C embed-bitcode=" + embdval
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

    def __init__(self, scrape, test, cmpl, bench, clean):
        self.ctgry = 'criterion'
        self.ctgrydir = category_map.get(self.ctgry)
        self.scrape = scrape
        self.test = test
        self.cmpl = cmpl
        self.bench = bench
        self.clean = clean

        self.root = os.getcwd()
        self.scrapedir = os.path.join(self.root, "get-crates")
        self.subdirs = os.path.join(self.root, self.ctgrydir)
        self.resname = "results_o" + optval \
                + "_dbg" + dbgval \
                + "_embed=" + embdval

    def scrape_crates(self):
        os.chdir(self.scrapedir)
        subprocess.run(["scrapy", "crawl", "-a", "category=" + self.ctgry, "-a", 
                "x=" + str(self.scrape), "get-crates"])
        os.chdir(self.root)

    def create_dirlist(self):
        if os.path.exists(self.subdirs):
            self.dirlist = []
            for dir in os.listdir(self.subdirs):
                self.dirlist.append(os.path.join(self.subdirs, dir))
        else: 
            exit("directory <" + self.subdirs + "> does not exist, need to run "\
            "scraper for the -" + self.ctgry + "- category of crates")

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

            for d in self.dirlist:
                os.chdir(d)
                outdir = os.path.join(d, e, self.resname)
                print(outdir)
                subprocess.run(["mkdir", "-p", outdir])
                f_out = open(os.path.join(outdir, TESTS_OUT), "w")
                f_err = open(os.path.join(outdir, TESTS_ERR), "w")
                try: 
                    subprocess.run(["cargo", "test", "--verbose"], 
                            text=True, timeout=600, stdout=f_out, stderr=f_err)
                except subprocess.TimeoutExpired as err: 
                    print(err)
                    fname = os.path.join(outdir, "test-timedout")
                    subprocess.run(["touch", fname])
                finally: 
                    f_out.close()
                    f_err.close()
                    os.chdir(self.root)

    def aggregate_test_results(self):
        for d in self.dirlist: 
            os.chdir(d)
            unmod_res = os.path.join(d, UNMOD, self.resname, TESTS_OUT)
            unmod_oks = subprocess.run(["grep", "-cw", "ok", unmod_res],
                    capture_output=True, text=True)
            bcrmp_res = os.path.join(d, BCRMP, self.resname, TESTS_OUT)
            bcrmp_oks = subprocess.run(["grep", "-cw", "ok", bcrmp_res],
                    capture_output=True, text=True)
            if not int(unmod_oks.stdout) == int(bcrmp_oks.stdout): 
                print("Mismatch in number of passed tests for: " + d.split("/")[-1])
                fname = os.path.join(d, "test-mismatch")
                subprocess.run(["touch", fname])
            os.chdir(self.root)

    def compile_benchmarks(self):
        for e in exp_types:
            os.environ["RUSTFLAGS"] = UNMODFLAGS if e == UNMOD else BCRMPFLAGS

            for d in self.dirlist:
                os.chdir(d)
                outdir = os.path.join(d, e, self.resname)
                print(outdir)
                subprocess.run(["mkdir", "-p", outdir])
                f_out = open(os.path.join(outdir, COMP_OUT), "w")
                f_err = open(os.path.join(outdir, COMP_ERR), "w")
                try: # TODO make lightweight
                    subprocess.run(["cargo", "bench", "--no-run", "--verbose",
                            "--target-dir", os.path.join(outdir, "target")], 
                            text=True, timeout=600, stdout=f_out, stderr=f_err)
                except subprocess.TimeoutExpired as err: 
                    print(err)
                    fname = os.path.join(outdir, "compile-timedout")
                    subprocess.run(["touch", fname])
                finally: 
                    f_out.close()
                    f_err.close()
                    os.chdir(self.root)

    def run_benchmarks(self):
        for r in range(self.bench): 
            self.randomize_dirlist()
            for e in exp_types: 
                os.environ["RUSTFLAGS"] = UNMODFLAGS if e == UNMOD else BCRMPFLAGS

                for d in self.dirlist:
                    os.chdir(d)
                    targetdir = os.path.join(d, e, self.resname, "target")
                    outdir = os.path.join(d, self.resname, str(r))
                    print(outdir)
                    subprocess.run(["mkdir", "-p", outdir]) # TODO if exists, differentiate
                    f_out = open(os.path.join(outdir, e + ".out"), "w")
                    f_err = open(os.path.join(outdir, e + ".err"), "w")
                    try:
                        subprocess.run(["cargo", "bench", "--verbose",
                                "--target-dir", targetdir], 
                                text=True, timeout=1200, stdout=f_out, stderr=f_err)
                    except subprocess.TimeoutExpired as err: 
                        print(err)
                        fname = os.path.join(outdir, "bench-timedout")
                        subprocess.run(["touch", fname])
                    finally: 
                        f_out.close()
                        f_err.close()
                        os.chdir(self.root)

    # summarize data for each run of each crate
    def aggregate_bench_results(self):
        for r in range(self.bench):
            for d in self.dirlist:
                os.chdir(d)
                unmodres = os.path.join(d, self.resname, str(r), UNMOD + ".out")
                bcrmpres = os.path.join(d, self.resname, str(r), BCRMP + ".out")
                outfile = os.path.join(d, self.resname, str(r), BENCH_DATA)
                dump_benchmark(outfile, unmodres, bcrmpres, 1)
                os.chdir(self.root)

    # summarize data for all runs of each crate on current node 
    # (assuming all data is on this node)
    def crunch_local(self):
        for d in self.dirlist: 
            os.chdir(d)
            aggdir = os.path.join(d, self.resname)
            outfile = os.path.join(d, self.resname, CRUNCHED_DATA)
            path_wrangle(outfile, headers)

            sample_file = os.path.join(d, self.resname, "0", BENCH_DATA)
            # count number of distinctly captured benchmarks
            rows = len(open(sample_file).readlines()) - 1
            cols = 2
            matrix = numpy.zeros((rows, cols, self.bench))
            bench_names = []
            for r in range(self.bench):
                infile = os.path.join(d, self.resname, str(r), BENCH_DATA)
                infd = open(infile)
                row = 0
                for line in infd: 
                    # skip comments (i.e. header)
                    if line[:1] == '#': 
                        continue
                    columns = line.split()
                    for col in range(len(columns)): 
                        # only get the benchmark names from one file
                        if r == 0 and col == 0: 
                            bench_names.append(columns[col])
                        # collect <time> only (not <error>)
                        if col % 2 == 1: 
                            mcol_idx = int((col - 1) / 2)
                            matrix[row][mcol_idx][r] = columns[col]
                    row += 1

            # crunch matrix numbers
            outfd = open(outfile, 'a')
            for row in range(rows):
                cur = []
                bench_name = bench_names[row]
                cur.append(bench_name)
                for col in range(cols):
                    avg, stdev = stats(matrix[row][col])
                    cur.append(str(avg))
                    cur.append(str(stdev))
                writerow(outfd, cur)
            os.chdir(self.root)

    def cleanup(self):
        if self.clean == "c":
            for d in self.dirlist: 
                for e in exp_types: 
                    os.chdir(d)
                    subprocess.run(["cargo", "clean"])
                    dirname = os.path.join(d, e, self.resname, "target")
                    print("deleting directory: " + dirname + "...")
                    try: 
                        shutil.rmtree(dirname)
                    except OSError as err: 
                        print("Error: %s : %s" % (dirname, err.strerror))
                    finally: 
                        os.chdir(self.root)
        if self.clean == "a":
            for d in self.dirlist: 
                for e in exp_types: 
                    os.chdir(d)
                    dirname = os.path.join(d, e)
                    print("deleting directory: " + dirname + "...")
                    try: 
                        shutil.rmtree(dirname)
                    except OSError as err: 
                        print("Error: %s : %s" % (dirname, err.strerror))
                    finally:
                        os.chdir(self.root)
        if self.clean == "a" or self.clean == "b":
            for d in self.dirlist: 
                os.chdir(d)
                subprocess.run(["cargo", "clean"])
                dirname = os.path.join(d, self.resname)
                print("deleting directory: " + dirname + "...")
                try:
                    shutil.rmtree(dirname)
                except OSError as err:
                    print("Error: %s : %s" % (dirname, err.strerror))
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
    return args.scrape, args.test, args.compile, args.bench, args.clean

if __name__ == "__main__":
    scrape, test, cmpl, bench, clean = arg_parse()
    s = State(scrape, test, cmpl, bench, clean)

    if s.scrape:
        s.scrape_crates()

    s.create_dirlist()
    if s.clean: 
        s.cleanup()
    if s.test == True or s.cmpl == True or s.bench:
        s.revert_criterion_version()
    if s.test == True:
        s.run_tests()
        s.aggregate_test_results()
    if s.cmpl == True:
        s.compile_benchmarks()
    if s.bench: 
        s.run_benchmarks()
        s.aggregate_bench_results()
        s.crunch_local()

