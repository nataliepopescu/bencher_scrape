#!/bin/bash

SSH_NODES=(
#"npopescu@clnode104.clemson.cloudlab.us"
#"npopescu@clnode126.clemson.cloudlab.us"
#"npopescu@clnode124.clemson.cloudlab.us"
#"npopescu@clnode097.clemson.cloudlab.us"
#"npopescu@clnode119.clemson.cloudlab.us"
#"npopescu@clnode103.clemson.cloudlab.us"
#"npopescu@clnode131.clemson.cloudlab.us"
)

numnodes=7
runs=5
output="results-bcrmpass-embed-bitcode-yes-lto-thin-append-simplifycfg-cargobench"
cpy=$numnodes

usage () {
    echo ""
    echo "Usage: $0 [-c] [-n <num-nodes>] [-o <dir-label>] [-r <num-runs>]"
    echo "   -c		      Copy file listing transformation passes run [default = off]."
    echo "   -n <num-nodes>   How many nodes were used [default = 13]."
    echo "   -o <dir-label>   How to label the output directory of this invocation."
    echo "   -r <num-runs>    How many runs were executed [default = 3]."
    echo ""
}

while getopts "cn:o:r:h" opt
do
    case "$opt" in
    c)
	cpy=0
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
SUBDIRS="$ROOT/get-crates/*/"
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
    if [ "$d" == "/disk/scratch2/npopescu/hack/bencher_scrape/get-crates/spiders/" ]
    then
        continue
    fi
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
LOCAL_PATH="$ROOT/get-crates"
REMOTE_PATH="/benchdata/rust/bencher_scrape/get-crates"

i=0
#CRATES=( "wireguard-vanity-address-0.4.0" "woodpecker-0.4.0" "xoroshiro-0.3.0" "xoshiro-0.0.5" "zip-0.5.6" "zip-0.5.7" )
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
python3 "$CRUNCH" "$crate" "$FNAME" "$OUTPUT" "$numnodes" "$runs"

done
