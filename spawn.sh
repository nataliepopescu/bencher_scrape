#!/bin/bash

cleanup=0
bench=0
tst=0

OUTNAME="results-bcrmpass-embed-bitcode-yes-lto-thin-append-simplifycfg"

# Usage message
usage () {
	echo ""
	echo "Usage: $0 [-c] [-b bench_arg] [-t test_arg]"
	echo "   -c			Run cleanup script."
	echo "   -b <bench_arg>	Compile or run benchmarks. If <bench_arg> is an integer, will run this many"
	echo "			rounds of benchmarks per node."
	echo "			   -b c: compile benchmarks"
	echo "			   -b 4: run 4 rounds of benchmarks"
	echo "   -t <test_arg>	Compile or run tests."
	echo "			   -t c: compile tests"
	echo "			   -t r: run tests"
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

if [ $bench == "c" ]
then
	./pass-bench.sh -c 1 -o "$OUTNAME"

elif [ $bench -gt 0 ]
then
	./pass-bench.sh -b -r $bench -o "$OUTNAME"

elif [ $tst == "c" ]
then
	./pass-bench.sh -t 1 -o "$OUTNAME"

elif [ $tst == "r" ]
then
	./pass-bench.sh -t 3 -o "$OUTNAME"

elif [ $cleanup -eq 1 ]
then
	cp bash_profile_bcrm ~/.bash_profile
	source ~/.bash_profile

	SUBDIRS="./get-crates/*"
	#YES_FILE="bc_removed.crates"
	#NO_FILE="bc_unremoved.crates"
	#rm -f $YES_FILE && touch $YES_FILE
	#rm -f $NO_FILE && touch $NO_FILE

	for d in ${SUBDIRS[@]}
	do
		cargo clean
		rm -rf $d/$OUTNAME
		rm -rf $d/$OUTNAME-1
		#rm -rf $d/BCRMP
		#rm -rf $d/UNMOD
		#bc_old=$(grep -rnwI '@_ZN4core9panicking18panic_bounds_check17h566454b12ba8f623E' $d/UNMOD/$OUTNAME/target/ | wc -l)
		#bc_new=$(grep -rnwI '@_ZN4core9panicking18panic_bounds_check17h566454b12ba8f623E' $d/BCRMP/$OUTNAME/target/ | wc -l)
		#if [ $bc_old -gt $bc_new ]; then
		#	echo "$d" >> $YES_FILE
		#else
		#	echo "$d" >> $NO_FILE
		#fi
	done
fi
