#!/bin/bash

# *****DEFAULTS*****

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
#OPTFLAGS="-C opt-level=3"
#OPTFLAGS="-C opt-level=0"
OPTFLAGS="-C no-prepopulate-passes -C passes=name-anon-globals" # NO OPTS at all, stricter than opt-level=0

# Debug Management
DBGFLAGS="-C debuginfo=2"

# LTO Flags
LTOFLAGS_A="-C embed-bitcode=no -C lto=off"

RUSTFLAGS=""$OPTFLAGS" "$DBGFLAGS" "$LTOFLAGS_A""

# LLVM Print Passes Flag
PRNTFLAG=""

# LLVM O3 Flag
O3=""

EXPERIMENTS=( "UNMOD" "BCRMP" )

# *****COMMAND-LINE ARGS*****

usage () {
	echo ""
	echo "Usage: $0 [-b] [-c] [-p] [r <num-runs>] [-n <outfile-label>] [-o <outdir-label>]"
	echo "   -b		Bench crates with and without remove-bounds-check-pass [default = off]."
	echo "   -c		Compile benchmarks, without running, for crates with and without"
	echo "			  remove-bounds-check-pass; for large-scale experiments [default = off]."
	echo "   -p		Print list of passes that were run during compilation [default = off]."
	echo "   -m		optiMize using O3 after removing bounds checks [default = off]."
	echo "   -r <num-runs>  How many runs to execute [default = 1]."
	echo "   -n <outfile-label>"
	echo "			How to label the output files of this invocation [default = 'sanity']."
	echo "   -o <outdir-label>"
	echo "			How to label the output directories of this invocation [default = 'output']."
	echo ""
}

# Parse args
while getopts "bcpmr:n:o:h" opt
do
	case "$opt" in
	b)
		bench=1
		;;
	c)
		comp=1
		;;
	p)
		PRNTFLAG="--debug-pass=Structure"
		;;
	m)
		O3="--O3"
		;;
	r)
		runs="$(($OPTARG))"
		;;
	n)
		name="$OPTARG"
		;;
	o)
		output="$OPTARG"
		;;
	h)
		usage
		exit 0
		;;
	*)
		usage
		exit 1
		;;
	esac
done

# *****PRE-PROCESS*****
for i in $(seq 1 $runs)
do

# Get list of crates + randomize order
set -x

ROOT="$PWD"
SUBDIRS="$ROOT/crates/crates/*/"
DIRLIST="dirlist"
RAND_DIRLIST="rand-dirlist"
RAND_SCRIPT="randomize.py"

# Initial crate list (ordered alphabetically)
rm "$DIRLIST"
for d in ${SUBDIRS[@]}
do
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

# *****COMPILE BENCHMARKS _WITH_ PASS*****

LLVM_HOME="/benchdata/llvm-project/build"
RUSTUP_TOOLCHAIN_LIB="/benchdata/.rustup/toolchains/nightly-2020-05-07-x86_64-unknown-linux-gnu/lib/rustlib/x86_64-unknown-linux-gnu/lib"
NOPIE_SCRIPT=$ROOT/make_no_pie.py
BNAME_SCRIPT=$ROOT/process_benchnames.py
PASS="/benchdata/remove-bounds-check-pass/build/CAT.so"

for exp in ${EXPERIMENTS[@]}
do

# Get list of benchmark names
if [ $comp -eq 1 ]
then
	for d in ${RANDDIRS[@]}
	do
		ERRMSG=$d"err-msg"
		rm -f $ERRMSG && touch $ERRMSG
		NAMELIST=$d"name-list"
		rm -f $NAMELIST && touch $NAMELIST
		cd $d
		cargo clean
		RUSTFLAGS=$RUSTFLAGS cargo rustc --verbose --release --bench -- -Z print-link-args -v -C save-temps --emit=llvm-ir 2> $ERRMSG
		python3 $BNAME_SCRIPT $ERRMSG $NAMELIST
		cd $ROOT
	done
fi

if [ $bench -eq 1 -o $comp -eq 1 ]
then
	for d in ${RANDDIRS[@]}
	do
		DEFAULT_TGT=$d"target/release/deps"
		PRECOMPDIR=$d$exp/$output

		# Save a list of the executables to run later
		EXECLIST=$d"exec-list"
		cd $d

		# Compile executables
		if [ $comp -eq 1 ]
		then
			
			cargo clean
			
			if [ -d $PRECOMPDIR ]
			then
				rm -r $PRECOMPDIR
			fi
			mkdir -p $PRECOMPDIR

			# Recurse through benchmark names
			NAMELIST=$d"name-list"
			BENCHES=()
			while read -r name
			do
				BENCHES=( "${BENCHES[@]}" "$name" )
			done < "$NAMELIST"
			
			LINKARGS=$d"link-args"
			rm -f $LINKARGS && touch $LINKARGS
			rm -f $EXECLIST && touch $EXECLIST

			for b in ${BENCHES[@]}
			do
				PASSLIST="$PRECOMPDIR/$b-pass-list"
				REMARKS="$PRECOMPDIR/$b-remarks"
				rm -f $PASSLIST && touch $PASSLIST
				rm -f $REMARKS && touch $REMARKS

				# Build main with temporary files preserved and emit LLVM-IR
				# Also use cargo's '-Z print-link-args' to get the exact linker command
				RUSTFLAGS=$RUSTFLAGS cargo rustc --verbose --release --bench "$b" -- -Z print-link-args -v -C save-temps --emit=llvm-ir > $LINKARGS

				# Replace instances of "-pie" with "-no-pie", otherwise get 
				# "relocation R_X86_64_32 against `.rodata' can not be used when 
				# making a PIE object; recompile with -fPIE" error
				OUT=$d"tmp"
				python3 $NOPIE_SCRIPT $LINKARGS $OUT $EXECLIST
				mv $OUT $LINKARGS
				
				cd $DEFAULT_TGT
				
				# Remove the unoptimized bc or we'll get duplicate symbols at link time
				rm *no-opt*
				
				# Get bitcode
				find . -name '*.ll' | xargs -n 1 $LLVM_HOME/bin/llvm-as
				
				# Run all the bitcode through our pass (phantom if UNMOD)
				# If [-p] was specified, also save the list of passes that were run
				if [ $exp == "UNMOD" ]
				then
					find . -name '*.bc' | rev | cut -c 3- | rev | xargs -n 1 -I {} $LLVM_HOME/bin/opt -pass-remarks-output=$REMARKS $PRNTFLAG $O3 -o {}bc {}bc 2> $PASSLIST
				else
					find . -name '*.bc' | rev | cut -c 3- | rev | xargs -n 1 -I {} $LLVM_HOME/bin/opt -load $PASS -remove-bc -simplifycfg -dce -pass-remarks-output=$REMARKS $PRNTFLAG $O3 -o {}bc {}bc 2> $PASSLIST
				fi
				
				# Compile the bitcode to object files
				find . -name '*.bc' | xargs -n 1 $LLVM_HOME/bin/llc -filetype=obj
				
				# Complete the linking with previously saved/process command
				/bin/bash $LINKARGS

			done
			
			cd $d
			mv $DEFAULT_TGT $PRECOMPDIR

		# Run executables
		else
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
		fi
		cd $ROOT
	done
fi

# *****AGGREGATE RESULTS*****

AGGLOC="$ROOT/aggregate_bench.py"

if [ $bench -eq 1 ]
then
	for d in ${RANDDIRS[@]}
	do
		unmod_res="$d$OUTPUT/UNMOD.bench"
		bcrmp_res="$d$OUTPUT/BCRMP.bench"
		cd $d
		DATA_FILE="$PWD/$OUTPUT/bench.data"
		touch $DATA_FILE
		python3 $AGGLOC $DATA_FILE $unmod_res $bcrmp_res
		cd $ROOT
	done
fi
done
done
