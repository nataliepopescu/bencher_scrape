#!/bin/bash

cp bashrc ~/.bashrc
cp bash_profile ~/.bash_profile
source ~/.bashrc

#rustup toolchain link nobc /benchdata/rust/rust-nobc/build/x86_64-unknown-linux-gnu/stage2
#rustup toolchain link nobc+sl /benchdata/rust/rust-nobc+sl/build/x86_64-unknown-linux-gnu/stage2
#rustup toolchain link safelib /benchdata/rust/rust-safelib/build/x86_64-unknown-linux-gnu/stage2

OUTNAME="results-bcrm-pass-lto-off"

#SUBDIRS="./crates/crates/*"
#
#for d in ${SUBDIRS[@]}
#do
#	rm -r "$d/$OUTNAME"
#done

# Pre-compile
#./bench.sh -c -o "$OUTNAME"

# Run
#./bench.sh -b -r 2 -o "$OUTNAME"
