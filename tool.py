import os
import sys
import argparse
import platform
import random
import subprocess

unmod = "UNMOD"
bcrmp = "BCRMP"
exp_types = [unmod, bcrmp]

optval =    "3"
dbgval =    "2"
embdval =   "yes"
OPTFLAGS =  " -C opt-level=" + optval
DBGFLAGS =  " -C debuginfo=" + dbgval
EMBDFLAGS = " -C embed-bitcode=" + embdval
RBCFLAGS =  " -Z remove-bc"
UNMODFLAGS = OPTFLAGS + DBGFLAGS + EMBDFLAGS
BCRMPFLAGS = OPTFLAGS + DBGFLAGS + EMBDFLAGS + RBCFLAGS

category_map = {
    "bencher":      "bencher_rev_deps",
    "criterion":    "criterion_rev_deps",
}

class State: 

    def __init__(self, ctgry, scrape, test, cmpl, bench):
        self.ctgry = ctgry
        self.ctgrydir = category_map.get(ctgry)
        self.scrape = scrape
        self.test = test
        self.cmpl = cmpl
        self.bench = bench

        self.root = os.getcwd()
        self.scrapedir = os.path.join(self.root, "get-crates")
        self.subdirs = os.path.join(self.root, self.ctgrydir)
        self.output = "output_o" + optval \
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
            os.environ["RUSTFLAGS"] = UNMODFLAGS if e == unmod else BCRMPFLAGS

            for d in self.dirlist:
                os.chdir(d)
                outdir = os.path.join(d, e)
                print(outdir)
                subprocess.run(["mkdir", "-p", outdir])
                f_out = open(outdir + "/tests.out", "w")
                f_err = open(outdir + "/tests.err", "w")
                try: 
                    subprocess.run(["cargo", "test", "--verbose"], 
                            text=True, timeout=600, stdout=f_out, stderr=f_err)
                except subprocess.TimeoutExpired as e: 
                    print(e)
                    fname = d + e + "/timedout"
                    subprocess.run(["touch", fname])
                finally: 
                    f_out.close()
                    f_err.close()
                    os.chdir(self.root)

    def compile_benchmarks(self):
        for e in exp_types:
            os.environ["RUSTFLAGS"] = UNMODFLAGS if e == unmod else BCRMPFLAGS

            for d in self.dirlist:
                # TODO compile...
                os.chdir(d)
                os.chdir(self.root)

    def run_benchmarks(self):
        for r in self.bench: 
            self.randomize_dirlist()
            for e in exp_types: 
                os.environ["RUSTFLAGS"] = UNMODFLAGS if e == unmod else BCRMPFLAGS

                for d in self.dirlist:
                    # TODO bench...
                    os.chdir(d)
                    os.chdir(self.root)

def arg_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("ctgry",
            choices=["bencher", "criterion"],
            help="category of crates on which to run the specified action(s)")
    parser.add_argument("--scrape",
            metavar="X",
            nargs="?",
            type=int,
            required=False,
            const=100,
            help="scrape top X crates of specified category from crates.io, "\
            "where X is rounded up to a multiple of 10 (default is 100 if this "\
            "option is specified).")
    parser.add_argument("--test",
            required=False,
            action="store_true",
            help="")
    parser.add_argument("--compile",
            required=False,
            action="store_true",
            help="")
    parser.add_argument("--bench",
            metavar="N",
            nargs="?",
            type=int,
            required=False,
            const=5,
            help="run each benchmark N times per node (default is 5 if this "\
            "option is specified)")
    args = parser.parse_args()
    print(args)
    return args.ctgry, args.scrape, args.test, args.compile, args.bench

if __name__ == "__main__":
    ctgry, scrape, test, cmpl, bench = arg_parse()
    s = State(ctgry, scrape, test, cmpl, bench)

    if s.scrape:
        s.scrape_crates()
    s.create_dirlist()
    if ctgry == "criterion":
        s.revert_criterion_version()
    if s.test == True:
        s.run_tests()
    if s.cmpl == True:
        s.compile_benchmarks()
    if s.bench: 
        s.run_benchmarks()

