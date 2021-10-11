#!/usr/bin/env python3

import subprocess
import os

ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
cratedir = "criterion_rev_deps"

crates = [
"actix-service-1.0.6",
"adler-1.0.1",
"adler32-1.2.0",
"ahash-0.6.1",
"annotate-snippets-0.9.0",
"askama_escape-0.10.1",
"atoi-0.4.0",
"base64-0.13.0",
"bitvec-0.19.4",
"bs58-0.4.0",
"bumpalo-3.4.0",
"bytecount-0.6.2",
"chrono-0.4.19",
"chunked_transfer-1.3.0",
"combine-4.4.0",
"curve25519-dalek-3.0.0",
"ed25519-dalek-1.0.1",
"enumflags2-0.6.4",
"ethbloom-0.9.2",
"fancy-regex-0.4.1",
"fixed-hash-0.6.1",
"fluent-syntax-0.10.0",
"generational-arena-0.2.8",
"geo-0.16.0",
"geojson-0.20.1",
"gif-0.11.1",
"glam-0.11.1",
"glyph_brush-0.7.0",
"half-1.6.0",
"handlebars-3.5.1",
"hash256-std-hasher-0.15.2",
"hex-0.4.2",
"html5ever-0.25.1",
"image-0.23.12",
"impl-serde-0.3.1",
"intl_pluralrules-7.0.0",
"ipnetwork-0.17.0",
"itertools-0.9.0",
"jpeg-decoder-0.1.20",
"kvdb-rocksdb-0.9.1",
"lexical-5.2.0",
"libp2p-mplex-0.25.0",
"libp2p-secio-0.25.0",
"maxminddb-0.15.0",
"memory-db-0.24.1",
"metrics-0.12.1",
"metrics-runtime-0.13.1",
"metrics-util-0.3.2",
"mime_guess-2.0.3",
"multibase-0.9.1",
"multihash-0.13.2",
"nibble_vec-0.1.0",
"nom-6.0.1",
"parity-scale-codec-1.3.5",
"pem-0.8.2",
"phf_generator-0.8.0",
"plotters-0.3.0",
"png-0.16.7",
"postgres-0.18.1",
"pretty-0.10.0",
"primal-0.3.0",
"primal-sieve-0.3.1",
"prometheus-0.11.0",
"proptest-derive-0.2.0",
"prost-0.6.1",
"pulldown-cmark-0.8.0",
"quanta-0.6.5",
"radix_trie-0.2.1",
"rdrand-0.7.0",
"redis-0.18.0",
"rle-decode-fast-1.0.1",
"rlp-0.4.6",
"rlua-0.17.0",
"rustls-0.19.0",
"schnorrkel-0.9.1",
"sharded-slab-0.1.0",
"sized-chunks-0.6.2",
"sluice-0.5.3",
"snow-0.7.2",
"specs-0.16.1",
"sqlformat-0.1.5",
"statrs-0.13.0",
"string-interner-0.12.1",
"syntect-4.4.0",
"tiff-0.6.0",
"tinytemplate-1.1.0",
"tinyvec-1.1.0",
"tokio-postgres-0.6.0",
"tracing-0.1.22",
"tracing-subscriber-0.2.15",
"trie-db-0.22.1",
"typed-arena-2.0.1",
"uint-0.8.5",
"unsigned-varint-0.5.1",
"walrus-0.18.0",
"wasmparser-0.69.1",
"x25519-dalek-1.1.0",
"xml5ever-0.16.1",
"yamux-0.8.0",
"zxcvbn-2.0.1",
]

def rreplace(s, old, new):
  pieces = s.rsplit(old, 1)
  return new.join(pieces)

if __name__ == "__main__":
  subprocess.run(["mkdir", "-p", cratedir])
  os.chdir(os.path.join(ROOT_PATH, cratedir))

  for crate in crates: 
    crate = rreplace(crate, "-", "/")
    subprocess.run(["wget", "https://crates.io/api/v1/crates/{}/download".format(crate)])
    subprocess.run(["tar", "-xf", "download"])
    subprocess.run(["rm", "-f", "download"])
