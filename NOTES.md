# Setting up Environment

## Rust

Make sure your rust version in rustup is nightly-1.45. 
This will serve as our baseline for comparison. 

Then download, build, and install our modified version [location]. 
When finished, create a rustup toolchain for it from the repository's
roo directory: 

```sh
$ rustup toolchain link bcrm build/<target>/stage2
```

The above creates a toolchain called `bcrm`. 

## LLVM

Download, configure, and build the LLVM version 9 from source. 
See the LLVM documentation for more specific instructions. 

## Remove-bounds-check Pass

Clone [this](https://github.com/vgene/remove-bounds-check-pass) repository, and
follow the directions listed there to build it. 

## Benchmarks

You should now be ready to start benchmarking. You can see what configuration 
options you have by running: 

```sh
$ ./pass-bench.sh -h
```
