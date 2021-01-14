# Setting up Environment

## Requirements

make

python3

[cmake](https://cmake.org/download/) >= 3.13.4

scrapy >= 2.0.0

numpy >= 1.16.1

dash >= 0.42.0

## LLVM

Clone [this](https://github.com/nataliepopescu/llvm-project/tree/match-version-from-rust) 
LLVM repository and branch.

### Configure

Configure LLVM with your desired build system (we used Unix Makefiles) and these flags:

```sh
$ cmake -G "Unix Makefiles" \
	-DCMAKE_INSTALL_PREFIX="/path/you/have/read/write/access/to" \
	-DLLVM_ENABLE_PROJECTS="clang" \
	-DCMAKE_BUILD_TYPE=Release ../llvm
```

### Build and Install 

```sh
$ make install-llvm-headers && make -j$(nproc)
```

## Rust

Clone [this](https://github.com/nataliepopescu/rust) Rust repository.

### Configure

Make the following changes to you `config.toml`: 

```sh
[install]
...

prefix = "/another/path/you/have/read/write/access/to"

sysconfdir = "etc"
...

[target.*]
...

llvm-config = "path/to/local/llvm-config"
...
```

### Build and Install

```sh
$ ./x.py build && ./x.py install && ./x.py install cargo && ./x.py doc
```

```sh
cargo install cargo-edit
```

# Benchmarking

Clone this repository and run: 

```sh
$ python3 tool.py -h
```

## Example Workflow: Benchmarking Reverse Dependencies of [Criterion](https://crates.io/crates/criterion)

1. Scrape crates.io and download the latest set of Criterion reverse dependencies, by running the
following command from the top-level directory in this repository:

```sh
$ python3 tool.py --scrape 200
```

This will create and populate a directory called "criterion_rev_deps" with the 
200 most downloaded reverse dependencies of the `criterion` benchmarking crate. 

2. Now you can pre-compile the benchmarks with: 

```sh
$ python3 tool.py --compile
```

3. Finally, run the benchmarks by passing the number of rounds you want each benchmark to run for: 

```sh
$ python3 tool.py --bench 10
```

Note, you can also run steps 1-3 in a single command depending on how the 
benchmarks will be run: 

```sh
$ python3 tool.py --scrape 200 --compile --bench 10
```

4. If you would like to consolidate per-crate results from all runs on the current 
node, you can run this instead of the above step: 

```sh
$ python3 tool.py --scrape 200 --compile --bench 10 --local
```
or consolidate separately like: 

```sh
$ python3 tool.py --local
```

You will find the consolidated results in the "crunched.data" file in the results
directory, which can then be visualized (see command in [this](https://github.com/nataliepopescu/bencher_scrape#visualizing-results) section). 

5. If you would like to aggregate all results across one or more remote machines, 
run: 

```sh
$ ./post-run.sh -n $num_nodes -r $num_runs
```

Where $num_runs must be the same on every machine. The implementation for this step is still in 
progress, so you will likely have to customize the script yourself. 

# Visualizing Results

```sh
$ python3 result_presenter.py -p .
```
