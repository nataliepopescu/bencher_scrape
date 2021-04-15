#!/bin/bash

#CRATES=(
#"combine-4.5.2"
#"bytecount-0.6.2"
#"string-interner-0.12.2"
#"prost-0.7.0"
#"glam-0.14.0"
#"primal-sieve-0.3.1"
#"euc-0.5.3"
#"roaring-0.6.5"
#)

#for crate in ${CRATES[@]}
#do
#done

startpath="http://crates.io/api/v1/crates/"
endpath="/download"

DIR="criterion_rev_deps"
mkdir -p $DIR
cd $DIR

wget $startpath"combine/4.5.2"$endpath
tar -xf download
rm download
wget $startpath"bytecount/0.6.2"$endpath
tar -xf download
rm download
wget $startpath"string-interner/0.12.2"$endpath
tar -xf download
rm download
wget $startpath"prost/0.7.0"$endpath
tar -xf download
rm download
wget $startpath"glam/0.14.0"$endpath
tar -xf download
rm download
wget $startpath"primal-sieve/0.3.1"$endpath
tar -xf download
rm download
wget $startpath"euc/0.5.3"$endpath
tar -xf download
rm download
wget $startpath"roaring/0.6.5"$endpath
tar -xf download
rm download

cd ..
