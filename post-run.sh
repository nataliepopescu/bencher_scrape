#!/bin/bash

SSH_NODES=(
"npopescu@c220g5-111316.wisc.cloudlab.us"
"npopescu@c220g5-111031.wisc.cloudlab.us"
"npopescu@c220g5-111028.wisc.cloudlab.us"
"npopescu@c220g5-120132.wisc.cloudlab.us"
"npopescu@c220g5-120123.wisc.cloudlab.us"
"npopescu@c220g5-120120.wisc.cloudlab.us"
"npopescu@c220g5-111324.wisc.cloudlab.us"
"npopescu@c220g5-110513.wisc.cloudlab.us"
"npopescu@c220g5-120109.wisc.cloudlab.us"
"npopescu@c220g5-110504.wisc.cloudlab.us"
"npopescu@c220g5-110501.wisc.cloudlab.us"
"npopescu@c220g5-120105.wisc.cloudlab.us"
"npopescu@c220g5-120118.wisc.cloudlab.us"
"npopescu@c220g5-111015.wisc.cloudlab.us"
"npopescu@c220g5-120117.wisc.cloudlab.us"
"npopescu@c220g5-120113.wisc.cloudlab.us"
"npopescu@c220g5-111011.wisc.cloudlab.us"
"npopescu@c220g5-120125.wisc.cloudlab.us"
)

numnodes=18
runs=2
output="results-bcrmpass-embedbitcode-no-lto-off-o3"

usage () {
    echo ""
    echo "Usage: $0 [-n <num-nodes>] [-o <dir-label>] [-r <num-runs>]"
    echo "   -n <num-nodes>   How many nodes were used [default = 13]."
    echo "   -o <dir-label>   How to label the output directory of this invocation."
    echo "   -r <num-runs>    How many runs were executed [default = 3]."
    echo ""
}

while getopts "n:o:r:h" opt
do
    case "$opt" in
    n)
        numnodes="$(($OPTARG))"
        ;;
    r)
        runs="$(($OPTARG))"
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

# Parse paths to get concise crate names
ROOT="$PWD"
SUBDIRS="$ROOT/crates/crates/*/"
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
LOCAL_PATH="$ROOT/crates/crates"
REMOTE_PATH="/benchdata/rust/bencher_scrape/crates/crates"

i=0
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

        if [ $i -eq 0 ]
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

python3 "$CRUNCH" "$crate" "$FNAME" "$OUTPUT" "$numnodes" "$runs"

done
