#!/bin/bash

# *****DEFAULTS*****

# Don't scrape
scrape=0
# Don't bench
bench=0
# Don't pre-compile
comp=0
# Only one run
runs=1
# Names
name="sanity"
output="output"

# Optimization Level Management
OPTFLAGS_3="-C opt-level=3"
#OPTFLAGS_0="-C opt-level=0"
OPTFLAGS_NONE="-C no-prepopulate-passes -C passes=name-anon-globals" # NO OPTS at all, stricter than opt-level=0

# Debug Management
DBGFLAGS="-C debuginfo=2"

# LTO Flags
LTOFLAGS_A="-C embed-bitcode=no -C lto=off"

RUSTFLAGS_3=""$OPTFLAGS_3" "$DBGFLAGS" "$LTOFLAGS_A""
RUSTFLAGS_NONE=""$OPTFLAGS_NONE" "$DBGFLAGS" "$LTOFLAGS_A""

# Two Rustc Versions
#VERSION="nightly-2020-07-05"
TARGET="x86_64-unknown-linux-gnu"
#UNMOD="$VERSION-$TARGET"
#BCRMP="bcrm"
UNMOD="UNMOD"
BCRMP="BCRMP"

#EXPERIMENTS=( "$BCRMP" )
#EXPERIMENTS=( "$UNMOD" )
EXPERIMENTS=( "$UNMOD" "$BCRMP" )

# *****COMMAND-LINE ARGS*****

usage () {
	echo ""
	echo "Usage: $0 [-s] [-b] [-c] [r <num-runs>] [-n <outfile-label>] [-o <outdir-label>]"
	echo "   -s		Scrape crates.io for reverse dependencies of bencher [default = off]."
	echo "   -b		Bench crates with and without remove-bounds-check-pass [default = off]."
	echo "   -c		Compile benchmarks, without running, for crates with and without"
	echo "			  remove-bounds-check-pass; for large-scale experiments [default = off]."
	echo "   -r <num-runs>  How many runs to execute [default = 1]."
	echo "   -n <outfile-label>"
	echo "			How to label the output files of this invocation [default = 'sanity']."
	echo "   -o <outdir-label>"
	echo "			How to label the output directories of this invocation [default = 'output']."
	echo ""
}

# Parse args
while getopts "sbcr:n:o:h" opt
do
	case "$opt" in
	s)	scrape=1
		;;
	b)	bench=1
		;;
	c)	comp=1
		;;
	r)	runs="$(($OPTARG))"
		;;
	n)	name="$OPTARG"
		;;
	o)	output="$OPTARG"
		;;
	h)	usage
		exit 0
		;;
	*)	usage
		exit 1
		;;
	esac
done

ROOT="$PWD"
SUBDIRS="$ROOT/get-crates/*/"
DIRLIST="dirlist"
RAND_DIRLIST="rand-dirlist"
RAND_SCRIPT="randomize.py"

cp bash_profile_bcrm ~/.bash_profile
source ~/.bash_profile

# *****SCRAPE*****
if [ "$scrape" -eq 1 ]
then
        cd "get-crates/"
	scrapy crawl get-crates
	cd $ROOT
fi

# *****PRE-PROCESS*****
for i in $(seq 1 $runs)
do

# Get list of crates + randomize order
set -x

# Initial crate list (ordered alphabetically)
rm "$DIRLIST"
for d in ${SUBDIRS[@]}
do
	if [ "$d" == "/benchdata/rust/bencher_scrape/get-crates/spiders/" ]
	then
		continue
	fi
	echo "$d" >> "$DIRLIST"
done

# Randomize
python3 "$RAND_SCRIPT" "$DIRLIST" "$RAND_DIRLIST"

# Parse randomized list as array
RANDDIRS=()
while read -r line
do
	# Append each crate name to end of list
	RANDDIRS=( "${RANDDIRS[@]}" "$line" )
done < "$RAND_DIRLIST"

# Initialize output directory names depending on # runs
SUFFIX="$name"
if [ $runs -gt 1 -a $comp -eq 0 ]
then
	OUTPUT="$output-$i"
else
	OUTPUT="$output"
fi

# *****COMPILE BENCHMARKS*****

LLVM_HOME="/benchdata/llvm-project/build"
RUSTUP_TOOLCHAIN_LIB="/benchdata/.rustup/toolchains/$UNMOD/lib/rustlib/$TARGET/lib"
NOPIE_SCRIPT=$ROOT/make_no_pie.py
SAVE_EXE_SCRIPT=$ROOT/save_execs.py
BNAME_SCRIPT=$ROOT/process_benchnames.py
CONVERT_ARGS_SCRIPT=$ROOT/convert_rustc_to_opt_args.py
#PASS="/benchdata/remove-bounds-check-pass/build/CAT.so"

for exp in ${EXPERIMENTS[@]}
do

# Get list of benchmark names and
# the list of llvm passes rustc -O3 runs
if [ $comp -eq 1 ]
then
	for d in ${RANDDIRS[@]}
	do
		ERRMSG=$d"err-msg"
		rm -f $ERRMSG && touch $ERRMSG
		NAMELIST=$d"name-list"
		rm -f $NAMELIST && touch $NAMELIST
		DEFAULT_TGT=$d"target/release/deps"
		PRECOMPDIR=$d$exp/$output
		if [ -d $PRECOMPDIR ]
		then
			rm -r $PRECOMPDIR
		fi
		mkdir -p $PRECOMPDIR

		cd $d

		# Pre-process: list of benchmark names
		cargo clean
		# No optimizations because just want to capture error msg
		RUSTFLAGS=$RUSTFLAGS_NONE cargo rustc --verbose --release --bench -- --emit=llvm-bc 2> $ERRMSG
		python3 $BNAME_SCRIPT $ERRMSG $NAMELIST

		# Pre-process: list of rustc optimization args to LLVM (per benchmark)
		cargo clean
		BENCHES=()
		while read -r name
		do
			BENCHES=( "${BENCHES[@]}" "$name" )
		done < "$NAMELIST"

		for b in ${BENCHES[@]}
		do
			RUSTC_PASSLIST="$PRECOMPDIR/$b-rustc-pass-list"
			rm -f $RUSTC_PASSLIST && touch $RUSTC_PASSLIST
			REMARKS="$PRECOMPDIR/$b-remarks"
			rm -f $REMARKS && touch $REMARKS
			LINKARGS="$PRECOMPDIR/$b-link-args"
			rm -f $LINKARGS && touch $LINKARGS
			EXECLIST="$PRECOMPDIR/exec-list"
			rm -f $EXECLIST && touch $EXECLIST

			# Running with opt-level = O3
			if [ $exp == $UNMOD ]
			then
				RUSTFLAGS=$RUSTFLAGS_3 cargo rustc --verbose --release --bench "$b" -- -Z print-link-args -C "remark=all" -v -C save-temps --emit=llvm-ir -C llvm-args=-debug-pass=Structure 2> $RUSTC_PASSLIST > $LINKARGS
			else
				RUSTFLAGS=$RUSTFLAGS_3 cargo rustc --verbose --release --bench "$b" -- -Z remove-bc -Z print-link-args -C "remark=all" -v -C save-temps --emit=llvm-ir -C llvm-args=-debug-pass=Structure 2> $RUSTC_PASSLIST > $LINKARGS
			fi
			python3 $SAVE_EXE_SCRIPT $LINKARGS $EXECLIST
		done
		cd $ROOT
		mv $DEFAULT_TGT $PRECOMPDIR
	done
fi

if [ $bench -eq 1 ] # -o $comp -eq 1 ]
then
	for d in ${RANDDIRS[@]}
	do
		DEFAULT_TGT=$d"target/release/deps"
		PRECOMPDIR=$d$exp/$output
		# Save a list of the executables to run later
		EXECLIST="$PRECOMPDIR/exec-list"
		cd $d

		# Compile executables
#		if [ $comp -eq 1 ]
#		then
#			cargo clean
#			# Recurse through benchmark names
#			NAMELIST=$d"name-list"
#			BENCHES=()
#			while read -r name
#			do
#				BENCHES=( "${BENCHES[@]}" "$name" )
#			done < "$NAMELIST"
#			
#			LINKARGS=$d"link-args"
#			rm -f $LINKARGS && touch $LINKARGS
#			rm -f $EXECLIST && touch $EXECLIST
#
#			for b in ${BENCHES[@]}
#			do
#				# From previous loop
#				RUSTC_PASSLIST="$PRECOMPDIR/$b-rustc-pass-list"
#
#				# New files
#				OPT_PASSLIST="$PRECOMPDIR/$b-opt-pass-list"
#				REMARKS="$PRECOMPDIR/$b-remarks"
#				rm -f $OPT_PASSLIST && touch $OPT_PASSLIST
#				rm -f $REMARKS && touch $REMARKS
#
#				# Build with no opts, with temporary files preserved, and emit LLVM-BC
#				# Also use cargo's '-Z print-link-args' to get the exact linker command
#				RUSTFLAGS=$RUSTFLAGS_NONE cargo rustc --verbose --release --bench "$b" -- -Z mir-opt-level=1 -Z print-link-args -v -C save-temps --emit=llvm-bc > $LINKARGS
#
#				# Replace instances of "-pie" with "-no-pie", otherwise get 
#				# "relocation R_X86_64_32 against `.rodata' can not be used when 
#				# making a PIE object; recompile with -fPIE" error
#				OUT=$d"tmp"
#				python3 $NOPIE_SCRIPT $LINKARGS $OUT $EXECLIST
#				mv $OUT $LINKARGS
#
#				# Use the saved LLVM opts from the previous rustc -O3 command
#				# and pass to LLVM's 'opt' tool explicitly, so we can insert our
#				# custom pass first
#				OPT_ARGS="$PRECOMPDIR/$b-opt-args"
#				python3 $CONVERT_ARGS_SCRIPT $RUSTC_PASSLIST $OPT_ARGS
#				
#				cd $DEFAULT_TGT
#				
#				# Remove the unoptimized bc or we'll get duplicate symbols at link time
#				rm *no-opt*
#				
#				# Run all the bitcode through our pass (phantom if UNMOD)
#				# If [-p] was specified, also save the list of passes that were run
#				# ***** UNMOD version *****
#				if [ $exp == $UNMOD ]
#				then
#					find . -name '*.bc' | rev | cut -c 3- | rev | xargs -n 1 -I {} $LLVM_HOME/bin/opt $(cat $OPT_ARGS) -pass-remarks-output=$REMARKS $PRNTFLAG $O3 -o {}bc {}bc 2> $OPT_PASSLIST
#				# ***** BCRMP version *****
#				else
#					find . -name '*.bc' | rev | cut -c 3- | rev | xargs -n 1 -I {} $LLVM_HOME/bin/opt -load $PASS -remove-bc -simplifycfg -dce $(cat $OPT_ARGS) -pass-remarks-output=$REMARKS $PRNTFLAG $O3 -o {}bc {}bc 2> $OPT_PASSLIST
#				fi
#				
#				# Compile the bitcode to object files
#				find . -name '*.bc' | xargs -n 1 $LLVM_HOME/bin/llc -filetype=obj
#				
#				# Complete the linking with previously saved/process command
#				/bin/bash $LINKARGS
#
#			done
#			cd $d
#			mv $DEFAULT_TGT $PRECOMPDIR
#		# Run executables
#		else
			# Read in executable names from the list we saved during compilation step
			EXECS=()
			while read -r name
			do
				EXECS=( ${EXECS[@]} $name )
			done < $EXECLIST

			OUTDIR=$d$OUTPUT
			mkdir -p $OUTDIR
			BENCH_RES="$OUTDIR/$exp.bench"
			rm -f $BENCH_RES && touch $BENCH_RES

			# Run
			cd $PRECOMPDIR/deps
			for e in ${EXECS[@]}
			do
				./$e >> $BENCH_RES
			done
		#fi
		cd $ROOT
	done
fi

# *****AGGREGATE RESULTS*****

AGGLOC="$ROOT/aggregate_bench.py"

if [ $bench -eq 1 ]
then
	for d in ${RANDDIRS[@]}
	do
		unmod_res="$d$OUTPUT/${EXPERIMENTS[0]}.bench"
		bcrmp_res="$d$OUTPUT/${EXPERIMENTS[1]}.bench"
		cd $d
		DATA_FILE="$PWD/$OUTPUT/bench.data"
		touch $DATA_FILE
		python3 $AGGLOC $DATA_FILE $unmod_res $bcrmp_res
		cd $ROOT
	done
fi
done
done
