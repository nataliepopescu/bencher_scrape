#!/bin/bash

# *****DEFAULTS*****

# Don't scrape
scrape=0
# Don't bench
bench=0
# Don't pre-compile
comp=0
# Don't test
tst=0
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

RBCFLAG="-Z remove-bc"

RUSTFLAGS_3=""$OPTFLAGS_3" "$DBGFLAGS" "$LTOFLAGS_A""
RUSTFLAGS_3RBC=""$RBCFLAG" "$OPTFLAGS_3" "$DBGFLAGS" "$LTOFLAGS_A""
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
	echo "Usage: $0 [-s] [-b] [-c] [-t] [r <num-runs>] [-n <outfile-label>] [-o <outdir-label>]"
	echo "   -s		Scrape crates.io for reverse dependencies of bencher [default = off]."
	echo "   -b		Bench crates with and without remove-bounds-check-pass [default = off]."
	echo "   -c <comp-type>	Compile benchmarks, without running, for crates with and without"
	echo "			  remove-bounds-check-pass; for large-scale experiments [default = off]."
	echo "				-c 1: compile tests"
	echo "   -t <test-type>	Test crates with remove-bounds-check-pass [default = off]."
	echo "				-t 1: compile tests"
	echo "				-t 3: run tests"
	echo "   -r <num-runs>  How many runs to execute [default = 1]."
	echo "   -n <outfile-label>"
	echo "			How to label the output files of this invocation [default = 'sanity']."
	echo "   -o <outdir-label>"
	echo "			How to label the output directories of this invocation [default = 'output']."
	echo ""
}

# Parse args
while getopts "sbc:t:r:n:o:h" opt
do
	case "$opt" in
	s)	scrape=1
		;;
	b)	bench=1
		cmd="--bench"
		;;
	c)	comp="$(($OPTARG))"
		cmd="--bench"
		;;
	t)	tst="$(($OPTARG))"
		cmd="--test"
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
#rustup override set bcrm

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
	if [ "$d" == "$ROOT/get-crates/spiders/" -o "$d" == "$ROOT/get-crates/bex-0.1.4/" -o "$d" == "$ROOT/get-crates/__pycache__/" ]
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

# *****COMPILE BENCHMARKS/TESTS*****

#LLVM_HOME="/benchdata/llvm-project/build"
#RUSTUP_TOOLCHAIN_LIB="/benchdata/.rustup/toolchains/$UNMOD/lib/rustlib/$TARGET/lib"
NOPIE_SCRIPT=$ROOT/make_no_pie.py
SAVE_EXE_SCRIPT=$ROOT/save_execs.py
NAME_SCRIPT=$ROOT/process_benchnames.py
CONVERT_ARGS_SCRIPT=$ROOT/convert_rustc_to_opt_args.py

for exp in ${EXPERIMENTS[@]}
do

if [ $exp == $UNMOD ]
then
	RUSTFLAGS="-C opt-level=3 -C debuginfo=2 -C embed-bitcode=yes -C lto=thin"
else
	RUSTFLAGS="-C opt-level=3 -C debuginfo=2 -C embed-bitcode=yes -C lto=thin -Z remove-bc"
fi
export RUSTFLAGS

# Compile benchmarks or tests
#RANDDIRS=( "/benchdata/rust/bencher_scrape/get-crates/outils-0.2.0/" )
if [ $comp -eq 1 -o $tst -eq 1 ]
then
	for d in ${RANDDIRS[@]}
	do
		PRECOMPDIR="$d$exp/$output"
		ERRMSG=$d"err-msg"
		NAMELIST=$d"name-list"
		rm -f $NAMELIST && touch $NAMELIST
		DEFAULT_TGT=$d"target"
		if [ -d $PRECOMPDIR ]
		then
			rm -rf $PRECOMPDIR/target
		fi
		mkdir -p $PRECOMPDIR

		cd $d

		# Pre-process: list of benchmark/test names
		cargo clean
		# Capture error msg to get list of bench/test names
		cargo rustc --verbose --release $cmd 2> $ERRMSG
		python3 $NAME_SCRIPT $ERRMSG $NAMELIST

		# Pre-process: list of rustc optimization args to LLVM (per benchmark/test)
		cargo clean
		NAMES=()
		while read -r name
		do
			NAMES=( "${NAMES[@]}" "$name" )
		done < "$NAMELIST"

		for n in ${NAMES[@]}
		do
			echo "compiling benchmark: $n"
			RUSTC_PASSLIST="$PRECOMPDIR/$n-rustc-pass-list"
			LINKARGS="$PRECOMPDIR/$n-link-args"
			REMARKS="$PRECOMPDIR/$n-remarks"
			EXECLIST="$PRECOMPDIR/exec-list"
			rm -f $REMARKS && touch $REMARKS
			rm -f $EXECLIST && touch $EXECLIST
			rm -f $LINKARGS && touch $LINKARGS
			rm -f $RUSTC_PASSLIST && touch $RUSTC_PASSLIST
			tries=0

			# Rerun until no more segfault occurs
			cargo rustc --verbose --release $cmd $n -- -Z print-link-args -v -C save-temps --emit=llvm-ir 2> $RUSTC_PASSLIST > $LINKARGS
			while [ $(grep -c 'SIGSEGV: invalid memory reference' "$RUSTC_PASSLIST") -gt 0 ]; do
				tries=$((tries+1))
				echo "try #: $tries"
				cargo rustc --verbose --release $cmd $n -- -Z print-link-args -v -C save-temps --emit=llvm-ir 2> $RUSTC_PASSLIST > $LINKARGS
			done
			python3 $SAVE_EXE_SCRIPT $LINKARGS $EXECLIST
		done
		cd $ROOT
		mv $DEFAULT_TGT $PRECOMPDIR
	done
fi

if [ $bench -eq 1 -o $tst -eq 3 ]
then
	for d in ${RANDDIRS[@]}
	do
		DEFAULT_TGT=$d"target" #/release/deps"
		PRECOMPDIR=$d$exp/$output
		# Use previously saved list of executables
		EXECLIST="$PRECOMPDIR/exec-list"
		cd $d

		# Read in executable names
		EXECS=()
		while read -r name
		do
			EXECS=( ${EXECS[@]} $name )
		done < $EXECLIST

		if [ $bench -eq 1 ]; then OUTDIR=$d$OUTPUT; else OUTDIR=$PRECOMPDIR; fi
		mkdir -p $OUTDIR

		BENCH_RES="$OUTDIR/$exp.bench"
		rm -f $BENCH_RES && touch $BENCH_RES
		TEST_RES="$OUTDIR/$exp.test"
		rm -f $TEST_RES && touch $TEST_RES
		COMP_OUT="$OUTDIR/rustc-pass-list-$exp"
		rm -f $COMP_OUT && touch $COMP_OUT
		
		if [ $bench -eq 1 ]; then RESULTS=$BENCH_RES; else RESULTS=$TEST_RES; fi

		# Run
		#mv $PRECOMPDIR/target $DEFAULT_TGT
		#cargo $cmd > $RESULTS 2> $COMP_OUT
		#mv $DEFAULT_TGT $PRECOMPDIR/target
		cd $PRECOMPDIR/target/release/deps
		for e in ${EXECS[@]}
		do
			./$e >> $RESULTS 2>> $COMP_OUT
		done
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

if [ $tst -eq 3 ]
then
	for d in ${RANDDIRS[@]}
	do
		cd $d
		DATA_FILE="$PWD/test.data"
		touch $DATA_FILE
		diff -s "$PWD/UNMOD/$output/UNMOD.test" "$PWD/BCRMP/$output/BCRMP.test" > $DATA_FILE
		cd $ROOT
	done
fi
done
