#!/bin/bash

# Initial script taken from: https://medium.com/@squanderingtime/manually-linking-rust-binaries-to-support-out-of-tree-llvm-passes-8776b1d037a4

set -x

NAME="example"
DIR=`pwd`/$NAME
LLVM_HOME=/benchdata/llvm-project/build
RUSTUP_TOOLCHAIN_LIB=/benchdata/.rustup/toolchains/nightly-2020-05-07-x86_64-unknown-linux-gnu/lib/rustlib/x86_64-unknown-linux-gnu/lib

# Build main with temporary files preserved and emit LLVM-IR
cd $DIR
cargo clean
cargo rustc --verbose -- -Z print-link-args -v -C save-temps --emit=llvm-ir > "linked"
cd target/debug/deps

# Remove the unoptimized bc or we'll get duplicate symbols at link time
rm *no-opt*

# Get bitcode
find . -name '*.ll' | xargs -n 1 $LLVM_HOME/bin/llvm-as

# Run all the bitcode through our phantom pass
find . -name '*.bc' | rev | cut -c 3- | rev | xargs -n 1 -I {} $LLVM_HOME/bin/opt -o {}bc {}bc

# Compile the bitcode to object files
find . -name '*.bc' | xargs -n 1 $LLVM_HOME/bin/llc -filetype=obj

# Complete the linking to default a.out file
# Extra flags for removing C++ default libs, but link System, resolv, libc, and math.
# Also strip dead code so we don't have tons of rust std library code that isn't referenced.
# Use cargo's '-Z print-link-args' to get the exact set of .rlibs

#while read -r line
#do
#done < $OUTPUT_DIR/file-names

#clang -m64 *.o -Wl,--start-group $(find $RUSTUP_TOOLCHAIN_LIB -name '*rlib') -Wl,--end-group -lpthread -ldl

`cat /benchdata/rust/bencher_scrape/example/linked`
