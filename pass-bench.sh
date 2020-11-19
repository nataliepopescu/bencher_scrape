#!/bin/bash

# *****DEFAULTS*****

# Don't scrape
scrape=0
# Don't bench
bench=-1
# Don't test
tst=-1
# Only one run
runs=1
# Names
name="sanity"
output="results-bcrmpass-embed-bitcode-yes-lto-thin" #output"
rustc=1
#ctgry="top_200"
#ctgry="bencher_rev_deps"
ctgry="criterion_rev_deps"
b_type=0
#agg=1

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
	echo "Usage: $0 [-s] [-b <benchnum>] [-t <testnum>] [-c <category>] [-n <outfile>] [-o <outdir>]"
	echo "   -s		Scrape crates.io for some set of crates TBD by the [-c] flag. [default = off]."
	echo "   -b <benchnum>	Bench crates with and without remove-bounds-check-pass [default = off]."
	echo "				-b 0: compile benchmarks"
	echo "				-b n: run benchmarks n times"
	echo "   -t <testnum>	Test crates with remove-bounds-check-pass [default = off]."
	echo "				-t 0: compile tests"
	echo "				-t 1: run tests"
	echo "   -c <category>	Category of crates for which to download code and/or run benchmarks/tests."
	echo "			[default = 'top_200']."
	echo "				-c 'bencher_rev_deps'	: reverse dependencies of the bencher crate"
	echo "				-c 'criterion_rev_deps'	: reverse dependencies of the criterion crate"
	echo "				-c 'top_200'		: top 200 most downloaded crates on crates.io"
	echo "				-c 'top_500'		: top 500 most downloaded crates on crates.io"
	echo "   -n <outfile>	How to label the output files of this invocation [default = 'sanity']."
	echo "   -o <outdir>	How to label the output directories of this invocation [default = 'output']."
	echo ""
}

# Parse args
while getopts "sb:t:c:n:o:h" opt
do
	case "$opt" in
	s)	scrape=1
		;;
	b)	bench="$(($OPTARG))"
		cmd="bench"
		;;
	t)	tst="$(($OPTARG))"
		cmd="test"
		;;
	c)	ctgry="$(($OPTARG))"
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

if [ ctgry == "criterion_rev_deps" ]
then
	b_type=1
fi

ROOT="$PWD"
SPIDERDIR="$ROOT/get-crates/"
SUBDIRS="$ROOT/downloaded_$ctgry/*/"
DIRLIST="dirlist"
RAND_DIRLIST="rand-dirlist"
RAND_SCRIPT="randomize.py"

#cp bash_profile_bcrm ~/.bash_profile
source bash_profile
#rustup override set bcrm

# *****SCRAPE*****
if [ "$scrape" -eq 1 ]
then
        cd $SPIDERDIR
	scrapy crawl get-crates -a category=$ctgry
	cd $ROOT
fi

# *****PRE-PROCESS*****
if [ $bench -gt 0 ]
then
	runs=$bench
fi

for i in $(seq 1 $runs)
do

# Get list of crates + randomize order
set -x

# Initial crate list (ordered alphabetically)
rm "$DIRLIST"
for d in ${SUBDIRS[@]}
do
	#if [ "$d" == "$ROOT/downloaded_$ctgry/bex-0.1.4/" ]
	#then
	#	continue
	#fi
	#if [ "$d" == "$ROOT/downloaded_$ctgry/sluice-0.5.3/" ]
	#then
	#	continue
	#fi
	#if [ "$d" == "$ROOT/downloaded_$ctgry/schnorrkel-0.9.1/" ]
	#then
	#	continue
	#fi
	#if [ "$d" == "$ROOT/downloaded_$ctgry/rdrand-0.7.0/" ]
	#then
	#	continue
	#fi
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
if [ $bench -gt 0 ]
then
	OUTPUT="$output-$i"
else
	OUTPUT="$output"
fi

# *****COMPILE BENCHMARKS/TESTS*****

NOPIE_SCRIPT=$ROOT/make_no_pie.py
SAVE_EXE_SCRIPT=$ROOT/save_execs.py
NAME_SCRIPT=$ROOT/process_benchnames.py
CONVERT_ARGS_SCRIPT=$ROOT/convert_rustc_to_opt_args.py
TIMEOUT_SCRIPT=$ROOT/timeout.py

for exp in ${EXPERIMENTS[@]}
do

if [ $exp == $UNMOD ]
then
	RUSTFLAGS="-C opt-level=3 -C debuginfo=2 -C embed-bitcode=yes"
	#RUSTFLAGS="-C opt-level=3 -C debuginfo=2 -C embed-bitcode=yes -C lto=thin"
else
	RUSTFLAGS="-C opt-level=3 -C debuginfo=2 -C embed-bitcode=yes -Z remove-bc"
	#RUSTFLAGS="-C opt-level=3 -C debuginfo=2 -C embed-bitcode=yes -C lto=thin -Z remove-bc"
fi
export RUSTFLAGS

# Compile benchmarks or tests using rustc
#RANDDIRS=( "/benchdata/rust/bencher_scrape/downloaded_top_200/arrayvec-0.5.1/" )
#RANDDIRS=( "/benchdata/rust/bencher_scrape/downloaded_criterion_rev_deps/pem-0.8.1/" )
#RANDDIRS=( "/benchdata/rust/bencher_scrape/downloaded_criterion_rev_deps/rdrand-0.7.0/" )
#RANDDIRS=( "/benchdata/rust/assume_true/iterator_bench/" )
#RANDDIRS=( "/benchdata/rust/assume_true/example/" )
if [ $rustc -eq 1 ] && [ $bench -eq 0 -o $tst -eq 0 ]
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
		cargo rustc --verbose --release --$cmd 2> $ERRMSG
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
			COMP_PASSLIST="$PRECOMPDIR/$n-rustc-pass-list"
			LINKARGS="$PRECOMPDIR/$n-link-args"
			REMARKS="$PRECOMPDIR/$n-remarks"
			EXECLIST="$PRECOMPDIR/exec-list"
			rm -f $REMARKS && touch $REMARKS
			rm -f $EXECLIST && touch $EXECLIST
			rm -f $LINKARGS && touch $LINKARGS
			rm -f $COMP_PASSLIST && touch $COMP_PASSLIST
			tries=0

			# Spawn timeout script to kill hanging cargo rustc
			python3 $TIMEOUT_SCRIPT $$ &
			# Rerun until no more segfault occurs
			cargo rustc --verbose --release --$cmd $n -- -Z print-link-args -v -C save-temps --emit=llvm-ir 2> $COMP_PASSLIST > $LINKARGS
			#while [ $(grep -c 'SIGSEGV: invalid memory reference' "$COMP_PASSLIST") -gt 0 ]; do
			#	cp $COMP_PASSLIST $COMP_PASSLIST-$tries
			#	tries=$((tries+1))
			#	echo "try #: $tries"
			#	echo "total tries: $tries" > "recomp_tries"
			#	cargo rustc --verbose --release --$cmd $n -- -Z print-link-args -v -C save-temps --emit=llvm-ir 2> $COMP_PASSLIST > $LINKARGS
			#	if [ $tries -gt 7 ]; then
			#		break
			#	fi
			#done
			python3 $SAVE_EXE_SCRIPT $LINKARGS $EXECLIST
		done
		cd $ROOT
		mv $DEFAULT_TGT $PRECOMPDIR
	done
fi

# Compile benchmarks or tests NOT using rustc
if [ $rustc -eq 0 ] && [ $bench -eq 0 -o $tst -eq 0 ]
then
	for d in ${RANDDIRS[@]}
	do
		PRECOMPDIR="$d$exp/$output"
		DEFAULT_TGT=$d"target"
		if [ -d $PRECOMPDIR ]
		then
			rm -rf $PRECOMPDIR/target
		fi
		mkdir -p $PRECOMPDIR

		cd $d

		# Pre-process: list of benchmark/test names
		cargo clean
		COMP_PASSLIST="$PRECOMPDIR/cargo-pass-list"
		REMARKS="$PRECOMPDIR/remarks"
		rm -f $REMARKS && touch $REMARKS
		rm -f $COMP_PASSLIST && touch $COMP_PASSLIST
		tries=0

		# Rerun until no more segfault occurs
		cargo $cmd --no-run --verbose 2> $COMP_PASSLIST
		#while [ $(grep -c 'SIGSEGV: invalid memory reference' "$COMP_PASSLIST") -gt 0 ]; do
		#	tries=$((tries+1))
		#	echo "try #: $tries"
		#	cargo $cmd --no-run --verbose 2> $COMP_PASSLIST
		#done
		cd $ROOT
		mv $DEFAULT_TGT $PRECOMPDIR
	done
fi

# *****RUN BENCHMARKS/TESTS*****

# Run executables compiled by 'cargo rustc'
if [ $rustc -eq 1 ] && [ $bench -gt 0 -o $tst -eq 1 ]
then
	for d in ${RANDDIRS[@]}
	do
		DEFAULT_TGT=$d"target"
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

		if [ $tst -eq 1 ]; then OUTDIR=$PRECOMPDIR; else OUTDIR=$d$OUTPUT; fi
		mkdir -p $OUTDIR

		BENCH_RES="$OUTDIR/$exp.bench"
		rm -f $BENCH_RES
		TEST_RES="$OUTDIR/$exp.test"
		rm -f $TEST_RES
		COMP_OUT="$OUTDIR/rustc-pass-list-$exp"
		rm -f $COMP_OUT && touch $COMP_OUT
		
		if [ $tst -eq 1 ]; then RESULTS=$TEST_RES; else RESULTS=$BENCH_RES; fi
		rm -f $RESULTS && touch $RESULTS

		# Run
		cd $PRECOMPDIR/target/release/deps
		for e in ${EXECS[@]}
		do
			./$e >> $RESULTS 2>> $COMP_OUT
		done
		cd $ROOT
	done
fi

# Run benchmarks/tests directly through cargo (no rustc)
if [ $rustc -eq 0 ] && [ $bench -gt 0 -o $tst -eq 1 ]
then
	for d in ${RANDDIRS[@]}
	do
		DEFAULT_TGT=$d"target"
		PRECOMPDIR=$d$exp/$output
		cd $d
		if [ $tst -eq 1 ]; then OUTDIR=$PRECOMPDIR; else OUTDIR=$d$OUTPUT; fi
		mkdir -p $OUTDIR

		BENCH_RES="$OUTDIR/$exp.bench"
		rm -f $BENCH_RES && touch $BENCH_RES
		TEST_RES="$OUTDIR/$exp.test"
		rm -f $TEST_RES && touch $TEST_RES
		COMP_OUT="$OUTDIR/cargo-pass-list-$exp"
		rm -f $COMP_OUT && touch $COMP_OUT
		
		if [ $tst -eq 1 ]; then RESULTS=$TEST_RES; else RESULTS=$BENCH_RES; fi
		rm -f $RESULTS && touch $RESULTS

		# Run
		cargo clean
		mv $PRECOMPDIR/target $DEFAULT_TGT
		cargo $cmd >> $RESULTS 2>> $COMP_OUT
		mv $DEFAULT_TGT $PRECOMPDIR/target
		cd $ROOT
	done
fi

# *****AGGREGATE RESULTS*****

AGGLOC="$ROOT/aggregate_bench.py"

if [ $bench -gt 0 ] # -o $agg -eq 1 ]
then
	for d in ${RANDDIRS[@]}
	do
		unmod_res="$d$OUTPUT/${EXPERIMENTS[0]}.bench"
		bcrmp_res="$d$OUTPUT/${EXPERIMENTS[1]}.bench"
		cd $d
		DATA_FILE="$PWD/$OUTPUT/bench.data"
		touch $DATA_FILE
		python3 $AGGLOC $DATA_FILE $unmod_res $bcrmp_res $b_type
		cd $ROOT
	done
fi
done

if [ $tst -eq 1 ]
then
	for d in ${RANDDIRS[@]}
	do
		cd $d
		DATA_FILE="$PWD/test.data"
		touch $DATA_FILE
		UNMOD_RES="$PWD/UNMOD/$output/UNMOD.test"
		BCRMP_RES="$PWD/BCRMP/$output/BCRMP.test"

		unmod_oks=$(grep -cw 'ok' "$UNMOD_RES")
		bcrmp_oks=$(grep -cw 'ok' "$BCRMP_RES")
		diff -s "$UNMOD_RES" "$BCRMP_RES" > $DATA_FILE
		
		OKS_DIFF="$PWD/oks_diff"
		rm -f $OKS_DIFF
		if [ $unmod_oks -ne $bcrmp_oks ]
		then
			touch $OKS_DIFF
		fi
		cd $ROOT
	done
fi
done
