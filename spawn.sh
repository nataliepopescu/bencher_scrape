#!/bin/bash

#cp bashrc ~/.bashrc
#cp bash_profile ~/.bash_profile
#source ~/.bashrc

#rustup toolchain link nobc /benchdata/rust/rust-nobc/build/x86_64-unknown-linux-gnu/stage2
#rustup toolchain link nobc+sl /benchdata/rust/rust-nobc+sl/build/x86_64-unknown-linux-gnu/stage2
#rustup toolchain link safelib /benchdata/rust/rust-safelib/build/x86_64-unknown-linux-gnu/stage2

cleanup=0

while getopts "c" opt
do
	case $opt in
	c)	cleanup=1
		;;
	*)	exit 1
		;;
	esac
done

# *****Comp Version #1*****

OUTNAME="results-bcrmpass-embed-bitcode-yes-lto-thin-retry"

if [ $cleanup -eq 0 ]
then

# Pre-compile
#./bench.sh -c -o "$OUTNAME"
./pass-bench.sh -c 1 -o "$OUTNAME"
#./pass-bench.sh -t 4 -o "$OUTNAME"

# Run
#./bench.sh -b -r 2 -o "$OUTNAME"
#./pass-bench.sh -b -o "$OUTNAME"
#./pass-bench.sh -b -r 3 -o "$OUTNAME"


# *****Comp Version #2*****

#OUTNAME="results-bcrmpass-embedbitcode-no-lto-off-many-o3"

# Pre-compile
#./pass-bench.sh -c -p -m -o "$OUTNAME"

# Run
#./pass-bench.sh -b -r 10 -o "$OUTNAME"


# **************************

else
	SUBDIRS="./get-crates/*"
	
	for d in ${SUBDIRS[@]}
	do
		#cargo clean
		rm -rf $d/BCRMP
		rm -rf $d/UNMOD
	done
fi
