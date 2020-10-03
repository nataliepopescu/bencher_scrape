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

Configure LLVM with your desired build system (we used Unix Makefiles) as follows:

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

Clone [this](https://github.com/nataliepopescu/rust) repository.

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

# Benchmarking

Clone our [framework](https://github.com/nataliepopescu/bencher_scrape) for downloading and benchmarking 
crates from `crates.io`. Run: 

```sh
$ ./pass-bench.sh -h
```

to see your options for benchmarking. 

# Visualizing Results

```sh
$ python3 result_presenter.py -p .
```
