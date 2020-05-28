#[macro_use]
extern crate bencher;

extern crate exr;
use exr::image::{full, read_options};

use bencher::Bencher;
use std::fs;

/// Read uncompressed (always single core)
fn read_single_image_uncompressed(bench: &mut Bencher) {
    bench.iter(||{
        let path = "tests/images/valid/custom/crowskull/crow_uncompressed.exr";

        let image = full::Image::read_from_file(path, read_options::high()).unwrap();
        bencher::black_box(image);
    })
}

/// Read from in-memory in parallel
fn read_single_image_uncompressed_from_buffer(bench: &mut Bencher) {
    let file = fs::read("tests/images/valid/custom/crowskull/crow_uncompressed.exr").unwrap();

    bench.iter(||{
        let image = full::Image::read_from_buffered(file.as_slice(), read_options::high()).unwrap();
        bencher::black_box(image);
    })
}

/// Read with multi-core zip decompression
fn read_single_image_zips(bench: &mut Bencher) {
    bench.iter(||{
        let path = "tests/images/valid/custom/crowskull/crow_zips.exr";
        let image = full::Image::read_from_file(path, read_options::low()).unwrap();
        bencher::black_box(image);
    })
}

/// Read with multi-core RLE decompression
fn read_single_image_rle(bench: &mut Bencher) {
    bench.iter(||{
        let path = "tests/images/valid/custom/crowskull/crow_rle.exr";
        let image = full::Image::read_from_file(path, read_options::high()).unwrap();
        bencher::black_box(image);
    })
}

/// Read without multi-core ZIP decompression
fn read_single_image_non_parallel_zips(bench: &mut Bencher) {
    bench.iter(||{
        let path = "tests/images/valid/custom/crowskull/crow_zips.exr";
        let image = full::Image::read_from_file(path, read_options::low()).unwrap();
        bencher::black_box(image);
    })
}


benchmark_group!(read,
    read_single_image_uncompressed_from_buffer,
    // write_single_image_parallel_zip,
    read_single_image_uncompressed,
    read_single_image_zips,
    read_single_image_rle,
    read_single_image_non_parallel_zips
);

benchmark_main!(read);