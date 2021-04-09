#!/bin/bash

# $1 == benchmark name as it would be passed on the 
#   commandline to `./mach talos-test --activeTests $1`
# $2 == number of times to run the benchmark

script_path=`realpath $0`
root_path=`dirname $script_path`

ffdir="ff_results"
mkdir -p $ffdir
mkdir -p $ffdir/$1
outfile="testing/mozharness/build/local.json"

rounds=$(($2-1))
echo $rounds

# run each unmod/regex benchmark multiple times
for num in $(seq 0 $rounds)
do
# if run is even run regex version first
if [ $(($num%2)) -eq 0 ]; then

	echo ""
	echo "even!"
	echo "running regex first"
	echo ""
	# run regex
	cd ../gecko_regex
	unshare -rn xvfb-run ./mach talos-test --activeTests $1
	cp $outfile $root_path/$ffdir/$1/regex_$num.json
	rm $outfile
	# run unmod
	echo ""
	echo "running unmod second"
	echo ""
	cd ../gecko
	unshare -rn xvfb-run ./mach talos-test --activeTests $1
	cp $outfile $root_path/$ffdir/$1/unmod_$num.json
	rm $outfile

# if run is odd run unmod version first
else

	echo ""
	echo "odd!"
	echo "running unmod first"
	echo ""
	# run unmod
	cd ../gecko
	unshare -rn xvfb-run ./mach talos-test --activeTests $1
	cp $outfile $root_path/$ffdir/$1/unmod_$num.json
	rm $outfile
	# run regex
	echo ""
	echo "running regex second"
	echo ""
	cd ../gecko_regex
	unshare -rn xvfb-run ./mach talos-test --activeTests $1
	cp $outfile $root_path/$ffdir/$1/regex_$num.json
	rm $outfile

fi
cd $root_path
done
