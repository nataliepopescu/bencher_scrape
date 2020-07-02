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

### Dash/Plotly

The easiest way to visualize our results would be: 

1. Clone this repository

2. Install `numpy >= 1.16.1`, `dash >= 0.42.0`, and any other required dependencies

3. Run: 

```sh
$ python3 result_presenter.py -p .
```

4. Visit `http://0.0.0.0:8050/`

### Gnuplot

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

We are looking into the effects of: 

1. Removing bounds checks when indexing into slices [branch: master]

2. Using safe implementations of library functions like memcpy [branch: version2_safe-lib]

3. Both [1] and [2] together [branch: version2_no-bounds-check+safe-lib]

### Building the Modified Rustc Locally

Clone the [repo](https://github.com/nataliepopescu/rust) and largely follow the instructions listed there.
This includes double checking all of your dependencies. You may also want to change the default "prefix" 
directory (install location of this rustc) and the "sysconfdir" to something you have write access to. Normally, running
`which rustc` lands me in `~/.cargo/bin/rustc`, so I just created an analogous directory `~/.cargo-nobc/` 
and changed my config.toml respectively:

```
[install]

...

prefix = "/Users/np/.cargo-nobc"

sysconfdir = "etc" # Note this is a *relative* path

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

If you want to create your own pre-populated data set, see the "Creating and Populating
your Dataset" subsection. 

Once your experiment is ready, the `/mydata` directory should be set up with all the
necessities, so all you should need to do is enter that directory and start. 

Unfortunately, commands in the the profile that use the "execute" service on the RSpec 
cannot modify files in the file system home directory, due to the privileges of the 
special user that executes these commands on node bootup. This affects how much we
can automate initializing the benchmark environment. Specificially, the system
won't know where `rustup` is if `~/.bash_profile` (or some alternative file) doesn't
point it to the right location, and will think `rustup` is not installed at all. 
To solve this I've written a simple `spawn.sh` script that copies over and sources such 
files. The script also starts the benchmarks, so once configured to your needs it can 
enable you to only run a single command per node. 

Note that since the `spawn.sh` script itself contains a `source` command, it needs to 
be run as:

```sh
$ source spawn.sh
```

Once the benchmarks have completed on the remote nodes, you can use the `post-run.sh`
script to copy over the many [ data ] files to process locally (or you can process remotely
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

### Creating and Populating your Dataset

Create a long term dataset [Storage > Create Dataset] in Cloudlab. The size of 3 individually-built rustcs and the
bencher_scrape repository is about 80GB, so I'd recommend creating your dataset with at
least that much space. 

You can use the above [profile](https://www.cloudlab.us/p/Praxis/setup-bench-lt) to spin
up an experiment and initialize the dataset, making sure to replace the current URN with
that of your specific dataset. You will also only need a single node rather than the default 
of 10.

Once you have an experiment for initializing the dataset, if 
using the Ubuntu20-STD disk image, you will probably have to build cmake and rustup. 
Note also that any modifications to your home directory will not be saved, so keep that 
in mind when installing the various projects. I've customized the modified-rustcs to 
install in a subdirectory of the dataset's filesystem root, and copy over the `~/.bashrc` 
and `~/.bash_profile` files into the dataset with the intent of copying them back when I 
instantiate a new experiment. 

When you've finished initializing your dataset, you can just terminate your experiment and
start a new one that uses the dataset, and your data should just be there. However, I have been
having trouble with this step (my dataset initialization does not persist), so be aware that 
that may also happen to you, and maybe take appropriate precautions (like snapshotting the
underlying filesystem so you don't have to build everything all over again). I am still working 
on getting the kinks out of this step. 

## End Goals

Upon completion, this tool will be able to do the following:

1. [done] Download and install crates
2. [done] Run the benchmarks normally
3. [done] Run the tests normally
3. [done] Run the benchmarks with Rust bounds checks turned off
3. [done] Run the test with Rust bounds checks turned off
4. [done] Generate a compact form of comparison between the two sets of benchmarks
4. [done] Generate a compact form of comparison between the two sets of tests
