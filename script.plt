#!/usr/bin/gnuplot -persist

set title "Crate Performance when using Vanilla vs Modified Rustc"
set xlabel "Benchmarks"
set ylabel "Time [ns/iter]"
#set xrange [0:800]
#set logscale xy
set logscale y
set style line 1 lw 1
set style line 2 lw 1
set style fill solid
set termoption noenhanced
set xtics rotate

#plot "bench.data" u 1 smooth cumulative t "Vanilla" w lines, \
#    "bench.data" u 3 smooth cumulative t "Modified" w lines

plot "bench.data" u 2:xtic(1) t "Vanilla" with histogram, \
    "bench.data" u 4 t "Modified" with histogram