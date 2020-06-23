# Scraping Benchmarks on cargo.io

We use the [reverse dependencies](https://crates.io/crates/bencher/reverse_dependencies) of the [bencher](https://crates.io/crates/bencher) crate to get a list of crates with benchmarks that we can use.

Using the python tool, [scrapy](https://docs.scrapy.org/en/latest/index.html#), we scrape this reverse-dependency list to get a list of crates that use the bencher crate to run benchmarks, and leverage those benchmarks to evaluate the performance impact of Rust bounds checks.

## Running the Tool

After setting up your python and [scrapy](https://docs.scrapy.org/en/latest/intro/install.html) environments,
you can just run the tool with the default configuration by simply running: 

```sh
$ ./bench.sh
```

The default configuration runs neither the benchmarks nor the tests. 
For customizing options, run:

```sh
$ ./bench.sh -h
```

### Output Files

Note that this script generates and aggregates the data as:

 1) [ diff ] files whose contents are the output of `diff`ing the 
two sets of benchmarks, and

 2) [ data ] files that contain the parsed output of these benchmarks,
useful for generating graphs with gnuplot.

The `diff` output is meant for manual inspection
of specific benchmark numbers, whereas the parsed data file/the plot 
generated from it is more useful in conveying the 
overall performance characteristic(s) of the crate.

## Generating Graphs

The `gnuplot-script` reads from the respective `bench-sanity.data` files, so (in the current state of the tool)
the script should be invoked from the same directory as the data you want to visualize. 

Therefore: 

1. Install [gnuplot](http://www.gnuplot.info/) either by way of your system package manager or by following one of 
[these](http://www.gnuplot.info/download.html). On MacOS (10.15.2), I am using version 5.2 (installed with homebrew), 
and the default terminal type is 'qt'. On Ubuntu (14.04.6 LTS), I am using version 4.6 with default terminal type 'jpeg'.

2. If you ran the `bench.sh` script for both the unmodified _and_ modified versions, then the
`gnuplot-script` will be automatically copied into the same directory as the individual crate data.
If not, you will have to copy the script there manually.

3. Navigate into the directory for the crate whose data you want to visualize.

4. Start up gnuplot by simply typing: `gnuplot`.

5. In gnuplot's REPL, type: 

```sh
$ gnuplot> filename="bench-sanity.data"; load "gnuplot-script"
```

If you passed a label/name to `bench.sh` like:

```sh
$ ./bench.sh -n "just-for-kicks"
```

then in the REPL you will need to change the filename value as such: 

```sh
$ gnuplot> filename="bench-just-for-kicks.data"; load "gnuplot-script"
```

## What Changes are we Measuring?

See them [here](https://github.com/nataliepopescu/rust).

### Building the Modified Rustc Locally

Clone the [repo](https://github.com/nataliepopescu/rust) and largely follow the instructions listed there.
This includes double checking all of your dependencies. You may also want to change the default "prefix" 
directory (install location of this rustc) and the "sysconfdir" to something you have write access to. Normally, running
`which rustc` lands me in `~/.cargo/bin/rustc`, so I just created an analogous directory `~/.cargo-mod/` 
and changed my config.toml respectively:

```
[install]

...

prefix = "/Users/np/.cargo-mod"

sysconfdir = "$prefix/sysconf"

...
```

When you are ready to build and install, run:

```sh
$ ./x.py build && ./x.py install && ./x.py install cargo && ./x.py doc
```

Note that this will take a while. Once the modified rustc is installed and you are ready to build with it,
you should create a rust toolchain for the stage2 build of the modified version. 

```sh
$ rustup toolchain link nobc build/<host-triple>/stage2
```

The easiest way to toggle between toolchains is by changing the rustup environment:

```sh
$ rustup override set nobc
```

But you can also run directly with the modified rustc like:

```sh
$ rustc +nobc <cmd>
```

Or:

```sh
$ cargo +nobc <cmd>
```

The `bench.sh` script toggles between toolchains using the first method. 

## Running on Cloudlab

On [Cloudlab](https://www.cloudlab.us/), create an experiment by instantiating
[this](https://www.cloudlab.us/p/Praxis/setup-bench-lt) profile. The
profile allows you to customize the number of nodes and the hardware type upon
instantiation, so you can change those according to cluster availability. 

Once your experiment is ready, the `/mydata` directory should be set up with all the
necessities, so all you should need to do is enter that directory and start. 

Once the benchmarks have completed on the remote nodes, you can use the `post-run.sh`
script to copy over the many [.data] files to process locally (or you can process remotely
and then copy over the condensed files). However, the script expects to be used as the 
former, so you will have to modify it should you choose to do the latter. 

One thing you will have to do whenever you run a new experiment is, in the `post-run.sh`
script, you will have to manually update the `SSH_NODES` field to match up with the
nodes you actually ran the benchmarks on (I haven't figured out a good way to do this
automatically yet). 

The `post-run.sh` script also has a couple options you can configure when you run it. 
Find these out by running: 

```sh
$ ./post-run.sh -h
```

## End Goals

Upon completion, this tool will be able to do the following:

1. [done] Download and install crates
2. [done] Run the benchmarks normally
3. [done] Run the tests normally
3. [done] Run the benchmarks with Rust bounds checks turned off
3. [done] Run the test with Rust bounds checks turned off
4. [done] Generate a compact form of comparison between the two sets of benchmarks
4. [done] Generate a compact form of comparison between the two sets of tests
