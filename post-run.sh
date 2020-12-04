#!/bin/bash

SSH_NODES=(
#"npopescu@clnode157.clemson.cloudlab.us"
#"npopescu@clnode154.clemson.cloudlab.us"
"npopescu@clnode115.clemson.cloudlab.us"
)

numnodes=1
runs=3
output="results-bcrmpass-embed-bitcode-yes-lto-thin"
cpy=$numnodes
ctgry="criterion_rev_deps" #"top_200"
lcl=0

usage () {
    echo ""
    echo "Usage: $0 [-c] [-n <num-nodes>] [-o <dir-label>] [-r <num-runs>]"
    echo "   -c <category>    Category of crates to download [default = 'criterion_rev_deps']."
    echo "				-c 'bencher_rev_deps'	: reverse dependencies of the bencher crate"
    echo "				-c 'criterion_rev_deps'	: reverse dependencies of the criterion crate"
    echo "				-c 'top_200'		: top 200 most downloaded crates on crates.io"
    echo "				-c 'top_500'		: top 500 most downloaded crates on crates.io"
    echo "   -n <num-nodes>   How many nodes were used [default = 13]."
    echo "   -o <dir-label>   How to label the output directory of this invocation."
    echo "   -r <num-runs>    How many runs were executed [default = 3]."
    echo "   -l               Don't copy between two different machine, just aggregate locally."
    echo ""
}

while getopts "c:n:o:r:lh" opt
do
    case "$opt" in
    c)
	ctgry="$(($OPTARG))"
	;;
    n)
        numnodes="$(($OPTARG))"
        ;;
    r)
        runs="$(($OPTARG))"
        ;;
    o)
        output="$OPTARG"
        ;;
    l)
	lcl=1
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

# Parse paths to get concise crate names
ROOT="$PWD"
SUBDIRS="$ROOT/downloaded_$ctgry/*/"
DIRLIST="dirlist"
CRATELIST="cratelist"
ISO_SCRIPT="isolate_crate_names.py"

if [ -f "$DIRLIST" ]
then
    rm "$DIRLIST"
fi
touch "$DIRLIST"

for d in ${SUBDIRS[@]}
do
    echo "$d" >> "$DIRLIST"
done

if [ -f "$CRATELIST" ]
then
    rm "$CRATELIST"
fi
touch "$CRATELIST"

python3 "$ISO_SCRIPT" "$DIRLIST" "$CRATELIST"

CRATES=()
while read -r line
do
    CRATES=( "${CRATES[@]}" "$line" )
done < "$CRATELIST"

# Copy actual benchmark data over

OUTPUT="$output"
FNAME="bench"
LOCAL_PATH="$ROOT/downloaded_$ctgry"
REMOTE_PATH="/benchdata/rust/bencher_scrape/downloaded_$ctgry"
CRATES=( "atoi-0.4.0" )

i=0

if [ $lcl -eq 0 ]
then
for node in ${SSH_NODES[@]}
do
    for crate in ${CRATES[@]}
    do
        loc_dir="$LOCAL_PATH/$crate/$OUTPUT"
        loc_names="$LOCAL_PATH/$crate/name-list"
        rem_dir="$REMOTE_PATH/$crate/$OUTPUT"
        name_file="$REMOTE_PATH/$crate/name-list"
        rem_unmod="$REMOTE_PATH/$crate/UNMOD/$OUTPUT"
        rem_bcrmp="$REMOTE_PATH/$crate/BCRMP/$OUTPUT"
        mkdir -p "$loc_dir"

        if [ $i -eq $cpy ]
        then
            scp "$node:$name_file" "$loc_names"

            BENCHES=()
            while read -r name
            do
                BENCHES=( "${BENCHES[@]}" "$name" )
            done < $loc_names

            for b in ${BENCHES[@]}
            do
                scp "$node:$rem_unmod/$b-pass-list" "$loc_dir/UNMOD-$b-pass-list"
                scp "$node:$rem_bcrmp/$b-pass-list" "$loc_dir/BCRMP-$b-pass-list"
            done
        fi

        for r in $(seq 1 $runs)
        do
            scp "$node:$rem_dir-$r/$FNAME.data" "$loc_dir/$FNAME-$i-$r.data"
        done
    done
    i=$((i+1))
done
fi

if [ $lcl -eq 1 ]
then
    for crate in ${CRATES[@]}
    do
        agg_dir="$LOCAL_PATH/$crate/$OUTPUT"
        iso_dir="$LOCAL_PATH/$crate/$OUTPUT"
	mkdir -p $agg_dir
        for r in $(seq 1 $runs)
        do
            cp "$iso_dir-$r/$FNAME.data" "$agg_dir/$FNAME-$i-$r.data"
        done

    done
fi

# Read out benchmark names from one file and create arrays
#   One array = 1 crate, 1 benchmark (function), 1 rustc version (out of the four)
#
# Note: bench names are kept for graph readability, but they correspond to each 
# of the rows in the bench data file (which is how we will ultimately iterate through 
# the data).

for crate in ${CRATES[@]}
do

# Now that we have the benchmark data locally, transfer control to python (read + number crunch)

CRUNCH="crunch.py"

echo "$crate"
python3 "$CRUNCH" "$crate" "$FNAME" "$OUTPUT" "$numnodes" "$runs" "$ctgry"

done
