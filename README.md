# Setting up Environment

## Requirements

make

python3

[cmake](https://cmake.org/download/) >= 3.13.4

scrapy >= 2.0.0

numpy >= 1.16.1

dash >= 0.42.0

## LLVM

Clone [this](https://github.com/nataliepopescu/llvm-project/tree/match-version-from-rust) LLVM repository.

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

Clone our [framework](https://github.com/nataliepopescu/bencher_scrape) for downloading and benchmarking 
crates from `crates.io`. Run: 

```sh
$ ./pass-bench.sh -h
```

to see your options for benchmarking. 

## Example Workflow for Benchmarking Reverse Dependencies of [Criterion](https://crates.io/crates/criterion)

1. Scrape crates.io and download the latest set of Criterion reverse dependencies, by running the
following command from the top-level directory in this repository:

```sh
./pass-bench.sh -s -c "criterion_rev_deps"
```

This will create and populate a directory called "downloaded_criterion_rev_deps". 

2. Revert the criterion dependency versions to v0.3.2 (for some reason, v0.3.3 hangs). Also run 
this from the repository's root directory: 

```sh
./spawn -c
```

3. Now you can pre-compile the benchmarks with: 

```sh
./spawn -b 0
```

4. Finally, run the benchmarks by passing the number of rounds you want each benchmark to run for: 

```sh
./spawn -b $num_runs
```

5. If you would like to aggregate all the crate-specific results that you ran on a single machine, 
run:

```sh
./post-run.sh -l -r $num_runs
```

You will find the aggregated results in the "bench-CRUNCHED.data" file in the newly-generated
directory. This file can be easily visualized (see command in the next section). 

6. If you would like to aggregate all the crate-specific results that you ran of various machines, 
run: 

```sh
./post-run.sh -n $num_nodes -r $num_runs
```

Where $num_runs must be the same on every machine. The implementation for this step is still in 
progress, so you will likely have to customize the script yourself. 

# Visualizing Results

```sh
$ python3 result_presenter.py -p .
```
