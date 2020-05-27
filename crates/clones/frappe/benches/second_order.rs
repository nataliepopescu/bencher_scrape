//! FRP benchmarks from https://github.com/aepsil0n/carboxyl

use bencher::{benchmark_group, benchmark_main, Bencher};
use frappe::Sink;
use rand::prelude::*;

/// Second-order benchmark.
///
/// Generate `n_sinks` `Stream<()>`, then for each stream create a `Signal<i32>`
/// that counts the number of firings. Create a `Stream<Signal<i32>>` that every
/// 10 network steps sequentially moves to the next signal. Create a
/// `Signal<i32>` from this stream. At each network step, fire 10 `Stream<()>`
/// at random, then print the current value of the `Signal<i32>`.
///
/// Benchmark the time required for `n_steps` steps.
fn second_order(n_sinks: usize, n_steps: usize, b: &mut Bencher) {
    // Setup network
    let stepper = Sink::<usize>::new();
    let sinks: Vec<_> = (0..n_sinks).map(|_| Sink::new()).collect();
    let counters: Vec<_> = sinks
        .iter()
        .map(|sink| sink.stream().fold(0, |n, _| n + 1))
        .collect();
    let walker = {
        let counters = counters.clone();
        stepper.stream().map(move |k| counters[*k / 10].clone())
    };
    let signal = walker.hold(counters[0].clone()).switch();

    // Feed events
    let mut rng = rand::thread_rng();
    b.iter(|| {
        let mut res = 0;
        for i in 0..n_steps {
            stepper.send(i);
            for sink in sinks.choose_multiple(&mut rng, 10) {
                sink.send(());
            }
            res += signal.sample();
        }
        res
    });
}

fn second_order_100(b: &mut Bencher) {
    second_order(1_000, 100, b);
}

fn second_order_1k(b: &mut Bencher) {
    second_order(1_000, 1_000, b);
}

fn second_order_10k(b: &mut Bencher) {
    second_order(1_000, 10_000, b);
}

benchmark_group!(
    second_order_,
    second_order_100,
    second_order_1k,
    second_order_10k
);
benchmark_main!(second_order_);
