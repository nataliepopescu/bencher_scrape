#!/bin/bash

cleanup=-1
bench=-1
tst=-1
ctgry="criterion_rev_deps"

ROOT=$PWD

OUTNAME="results-bcrmpass-embed-bitcode-yes-lto-thin"

# Usage message
usage () {
	echo ""
	echo "Usage: $0 [-c] [-b bench_arg] [-t test_arg] [-o outname] [-h]"
	echo "   -c		Run cleanup script."
	echo "   -b <bench_arg>	Compile or run benchmarks. If <bench_arg> is a positive integer, will run this many"
	echo "			rounds of benchmarks per node."
	echo "			   -b 0: compile benchmarks"
	echo "			   -b 4: run 4 rounds of benchmarks"
	echo "   -t <test_arg>	Compile or run tests."
	echo "			   -t 0: compile tests"
	echo "			   -t 1: run tests"
	echo "   -o <outname>	Specify new output directory name for this set of benchmarks."
	echo ""
}

# Parse args
while getopts "cb:t:o:h" opt
do
	case $opt in
	c)	cleanup=1
		;;
	b)	bench="$(($OPTARG))"
		# bench=c -> compile benchmarks
		# bench=num_runs -> run benchmarks
		;;
	t)	tst="$(($OPTARG))"
		# tst=c -> compile tests
		# tst=r -> run tests
		;;
	o)	OUTNAME="$(($OPTARG))"
		;;
	h)	usage
		exit 0
		;;
	*)	usage
		exit 1
		;;
	esac
done

# *****Comp Version #1*****

if [ $bench -eq 0 ]
then
	echo "COMPILING BENCHMARKS..."
	./pass-bench.sh -b 0 -o "$OUTNAME"

elif [ $bench -gt 0 ]
then
	echo "RUNNING BENCHMARKS..."
	./pass-bench.sh -b $bench -o "$OUTNAME"

elif [ $tst -eq 0 ]
then
	echo "COMPILING TESTS..."
	./pass-bench.sh -t 0 -o "$OUTNAME"

elif [ $tst -eq 1 ]
then
	echo "RUNNING TESTS..."
	./pass-bench.sh -t 1 -o "$OUTNAME"

elif [ $cleanup -eq 1 ]
then
	echo "CLEANING UP..."
	#cp bash_profile_bcrm ~/.bash_profile
	#source ~/.bash_profile

	#YES_FILE="bc_removed_scfg.crates"
	#NO_FILE="bc_unremoved_scfg.crates"
	#rm -f $YES_FILE && touch $YES_FILE
	#rm -f $NO_FILE && touch $NO_FILE

	cd "$ROOT/downloaded_$ctgry/"
	SUBDIRS="*"
	for d in ${SUBDIRS[@]}
	do
		echo $d
		cd $d
		#cargo clean
		#rm -rf $d/$OUTNAME
		#rm -rf BCRMP #/$OUTNAME
		#rm -rf UNMOD #/$OUTNAME
		#echo "DONE"
		cargo rm criterion --dev
		cargo add criterion@=0.3.2 --dev
		cd ..
		#if [ -f "recomp_tries" ]; then
		#	echo "$d" 
		#fi
		#bc_old=$(grep -rnwI '@_ZN4core9panicking18panic_bounds_check17h566454b12ba8f623E' $d/UNMOD/$OUTNAME/target/ | wc -l)
		#bc_new=$(grep -rnwI '@_ZN4core9panicking18panic_bounds_check17h566454b12ba8f623E' $d/BCRMP/$OUTNAME/target/ | wc -l)
		#if [ $bc_old -gt $bc_new ]; then
		#	echo "$d" >> $YES_FILE
		#else
		#	echo "$d" >> $NO_FILE
		#fi
		#cd $ROOT
	done
fi
