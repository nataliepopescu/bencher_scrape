import os
import sys
import argparse
import platform
import random
import subprocess
import shutil

UNMOD = "UNMOD"
BCRMP = "BCRMP"
exp_types = [UNMOD, BCRMP]

optval =    "3"
dbgval =    "2"
embdval =   "yes"
OPTFLAGS =  " -C opt-level=" + optval
DBGFLAGS =  " -C debuginfo=" + dbgval
EMBDFLAGS = " -C embed-bitcode=" + embdval
RBCFLAGS =  " -Z remove-bc"
UNMODFLAGS = OPTFLAGS + DBGFLAGS + EMBDFLAGS
BCRMPFLAGS = OPTFLAGS + DBGFLAGS + EMBDFLAGS + RBCFLAGS

TESTS_OUT = "tests.out"
TESTS_ERR = "tests.err"
COMP_OUT =  "compile.out"
COMP_ERR =  "compile.err"
BENCH_OUT = "bench.out"
BENCH_ERR = "bench.err"

category_map = {
    #"bencher":      "bencher_rev_deps",
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
                try: 
                    subprocess.run(["cargo", "bench", "--no-run", "--verbose"], 
                            text=True, timeout=600, stdout=f_out, stderr=f_err)
                except subprocess.TimeoutExpired as err: 
                    print(err)
                    fname = os.path.join(outdir, "bench-timedout")
                    subprocess.run(["touch", fname])
                finally: 
                    f_out.close()
                    f_err.close()
                    os.chdir(self.root)

    def run_benchmarks(self):
        for r in self.bench: 
            self.randomize_dirlist()
            for e in exp_types: 
                os.environ["RUSTFLAGS"] = UNMODFLAGS if e == UNMOD else BCRMPFLAGS

                for d in self.dirlist:
                    # TODO bench...
                    os.chdir(d)
                    os.chdir(self.root)

    def aggregate_bench_results(self):
        # TODO
        print("aggregating...")

    def cleanup(self):
        for d in self.dirlist: 
            for e in exp_types: 
                dirname = os.path.join(d, e)
                print("deleting directory: " + dirname + "...")
                try: 
                    shutil.rmtree(dirname)
                except OSError as err: 
                    print("Error: %s : %s" % (dirname, err.strerror))

def arg_parse():
    parser = argparse.ArgumentParser()
    #parser.add_argument("ctgry",
    #        choices=["bencher", "criterion"],
    #        help="category of crates on which to run the specified action(s)")
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
            action="store_true",
            help="remove compilation output and/or result artifacts from "\
            "prior use")
    args = parser.parse_args()
    return args.scrape, args.test, args.compile, args.bench, args.clean

if __name__ == "__main__":
    scrape, test, cmpl, bench, clean = arg_parse()
    s = State(scrape, test, cmpl, bench, clean)
    s.create_dirlist()
    s.aggregate_test_results()

    #if s.scrape:
    #    s.scrape_crates()
    #if not s.clean: 
    #    s.create_dirlist()
    #    s.revert_criterion_version()
    #    if s.test == True:
    #        s.run_tests()
    #        s.aggregate_test_results()
    #    if s.cmpl == True:
    #        s.compile_benchmarks()
    #    if s.bench: 
    #        s.run_benchmarks()
    #        s.aggregate_bench_results()
    #else:
    #    s.cleanup()

