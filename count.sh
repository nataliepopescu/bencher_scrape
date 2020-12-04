#!/bin/bash

ROOT=$PWD
source $ROOT/bash_profile

SUBDIRS="$ROOT/downloaded_bencher_rev_deps/*/"

for d in ${SUBDIRS[@]}
do
	cd $d
	echo $d
	cargo count -l rs --separator , --unsafe-statistics | head -n 4 | tail -n 3
	echo ""
	cd $ROOT
done
