#!/bin/bash

# Initial script taken from: https://medium.com/@squanderingtime/manually-linking-rust-binaries-to-support-out-of-tree-llvm-passes-8776b1d037a4

set -x

ROOT="$PWD"
LLVM_HOME=/benchdata/llvm-project/build
RUSTUP_TOOLCHAIN_LIB=/benchdata/.rustup/toolchains/nightly-2020-05-07-x86_64-unknown-linux-gnu/lib/rustlib/x86_64-unknown-linux-gnu/lib
NOPIE_SCRIPT="$ROOT/make_no_pie.py"
PASS="/benchdata/remove-bounds-check-pass/build/CAT.so"

DIR="$ROOT/example"
OUTDIR="$DIR/target/debug/deps"
LINKARGS="$DIR/link-args"

# Build main with temporary files preserved and emit LLVM-IR
# Also use cargo's '-Z print-link-args' to get the exact linker command
cd $DIR
cargo clean
cargo rustc --verbose -- -Z print-link-args -v -C save-temps --emit=llvm-ir > "$LINKARGS"

# Replace instances of "-pie" with "-no-pie", otherwise get 
# "relocation R_X86_64_32 against `.rodata' can not be used when 
# making a PIE object; recompile with -fPIE" error
OUT="tmp"
python3 "$NOPIE_SCRIPT" "$LINKARGS" "$OUT"
mv "$OUT" "$LINKARGS"

cd $OUTDIR

# Remove the unoptimized bc or we'll get duplicate symbols at link time
rm *no-opt*

# Get bitcode
find . -name '*.ll' | xargs -n 1 $LLVM_HOME/bin/llvm-as

# Run all the bitcode through our phantom pass
find . -name '*.bc' | rev | cut -c 3- | rev | xargs -n 1 -I {} $LLVM_HOME/bin/opt -load $PASS -remove-bc -simplifycfg -dce {}bc -o {}bc

# Compile the bitcode to object files
find . -name '*.bc' | xargs -n 1 $LLVM_HOME/bin/llc -filetype=obj

# Complete the linking with previously saved/process command
/bin/bash $LINKARGS

cd $ROOT
