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

system_name_map = {
    "Darwin": "apple-darwin"
}

category_map = {
    "bencher":      "downloaded_bencher_rev_deps",
    "criterion":    "downloaded_criterion_rev_deps",
}

def get_target():
    machine = platform.machine()
    os_name = platform.system()
    mapped_os = system_name_map.get(os_name)
    return machine + "-" + mapped_os

class State: 

    def __init__(self, action, ctgry, runs, scrape, top):
        self.action = action
        self.ctgry = ctgry
        self.runs = runs
        self.scrape = scrape
        self.top = top

        self.root = os.getcwd()
        self.scrape_dir = os.path.join(self.root, "get-crates")
        self.subdirs = os.path.join(self.root, category_map.get(self.ctgry))

        self.target = get_target()
        self.output = "output_" + action \
                + "_" + str(runs) \
                + "_o" + optval \
                + "_dbg" + dbgval \
                + "_embed=" + embdval

    def get_crates(self):
        os.chdir(self.scrape_dir)
        # TODO scrape...
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

    def run_tests(self):
        for e in exp_types:
            os.environ["RUSTFLAGS"] = UNMODFLAGS if e == unmod else BCRMPFLAGS

            for d in self.dirlist:
                os.chdir(d)
                outdir = os.path.join(d, e)
                subprocess.run(["mkdir", "-p", outdir])
                f_out = open(outdir + "/tests.out", "w")
                f_err = open(outdir + "/tests.err", "w")
                try: 
                    subprocess.run(["cargo", "test", "--verbose"], 
                            capture_output=True, text=True, timeout=600, 
                            stdout=f_out, stderr=f_err)
                except subprocess.TimeoutExpired as e: 
                    print(e)
                    fname = d + e + "/timedout"
                    subprocess.run(["touch", fname])
                finally: 
                    f.close()
                    os.chdir(self.root)

    def compile_benchmarks(self):
        for e in exp_types:
            os.environ["RUSTFLAGS"] = UNMODFLAGS if e == unmod else BCRMPFLAGS

            for d in self.dirlist:
                # TODO compile...
                os.chdir(d)
                os.chdir(self.root)

    def run_benchmarks(self):
        for r in self.runs: 
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
            help="category of crates on which to run the specified action")
    parser.add_argument("action",
            choices=["bench_compile", "bench_run", "test"],
            help="action to perform on the specified category of crates")
    parser.add_argument("--top",
            metavar="X",
            type=int,
            required=False,
            default=100,
            help="top X crates of specified category on which to perform action "\
            "(default is 100)")
    parser.add_argument("--runs",
            metavar="N",
            type=int,
            required=False,
            default=5,
            help="run benchmarks N times per node (default is 5); option is only "\
            "used if performing the -bench_run- action")
    parser.add_argument("--scrape",
            required=False,
            action="store_true",
            help="scrape crates.io for specified set of crates before performing "\
            "action")
    args = parser.parse_args()
    print(args)
    return args.action, args.ctgry, args.runs, args.scrape, args.top

if __name__ == "__main__":
    action, ctgry, runs, scrape, top = arg_parse()
    s = State(action, ctgry, runs, scrape, top)

    if s.scrape == True:
        s.get_crates()

    s.create_dirlist()

    if s.action == "test":
        s.run_tests()
    elif s.action == "bench_compile": 
        s.compile_benchmarks()
    else: 
        s.run_benchmarks()
