#[macro_use]
extern crate bencher;
extern crate serde_json;
extern crate whatlang;

use bencher::Bencher;
use std::collections::HashMap;
use whatlang::{detect, detect_script};

fn bench_detect(bench: &mut Bencher) {
    let example_data = include_str!("../tests/examples.json");
    let examples: HashMap<String, String> = serde_json::from_str(example_data).unwrap();

    bench.iter(|| {
        for text in examples.values() {
            detect(text);
        }
    })
}

fn bench_detect_script(bench: &mut Bencher) {
    let example_data = include_str!("../tests/examples.json");
    let examples: HashMap<String, String> = serde_json::from_str(example_data).unwrap();

    bench.iter(|| {
        for text in examples.values() {
            detect_script(text);
        }
    })
}

benchmark_group!(benches, bench_detect, bench_detect_script);
benchmark_main!(benches);
