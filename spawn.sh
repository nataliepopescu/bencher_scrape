#!/bin/bash

#cp bashrc ~/.bashrc
#cp bash_profile ~/.bash_profile
#source ~/.bashrc

#rustup toolchain link nobc /benchdata/rust/rust-nobc/build/x86_64-unknown-linux-gnu/stage2
#rustup toolchain link nobc+sl /benchdata/rust/rust-nobc+sl/build/x86_64-unknown-linux-gnu/stage2
#rustup toolchain link safelib /benchdata/rust/rust-safelib/build/x86_64-unknown-linux-gnu/stage2


# *****Comp Version #1*****

OUTNAME="results-bcrmpass-first"

# Pre-compile
#./bench.sh -c -o "$OUTNAME"
./pass-bench.sh -c -p -m -o "$OUTNAME"

# Run
#./bench.sh -b -r 2 -o "$OUTNAME"
#./pass-bench.sh -b -r 3 -o "$OUTNAME"


# *****Comp Version #2*****

#OUTNAME="results-bcrmpass-embedbitcode-no-lto-off-many-o3"

# Pre-compile
#./pass-bench.sh -c -p -m -o "$OUTNAME"

# Run
#./pass-bench.sh -b -r 10 -o "$OUTNAME"


# **************************

#OUTNAME="results-bcrmpass-remarks"
#SUBDIRS="./crates/crates/*"
#
#for d in ${SUBDIRS[@]}
#do
#	rm -r $d/BCRMP/$OUTNAME
#	rm -r $d/UNMOD/$OUTNAME
#done

