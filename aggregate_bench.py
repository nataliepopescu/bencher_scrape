#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A wrapper for cargo bench
Its numeric output is parsed and dumped to a csv
Pass an an optional independent variable from the command line
And also any other static keys and values

USAGE: python aggregate_bench.py [independent variable]
Writes to measurements.csv in the cwd by default, pass a different filepath to alter this
any other keyword arguments will be written as a header row and value. Be careful with that.

(C) Stephan Hügel 2016
License: MIT

Original: https://github.com/urschrei/lonlat_bng/blob/master/aggregate_bench.py
Adapted by: Natalie Popescu 2020
"""
import os
import sys
from subprocess import check_output
import re

pattern = "bench:\s+([0-9,]*)\D+([0-9,]*)"
name_pattern = "(?<=test\s).*(?=\s+[.]{3}\s+bench)"

default_file = "./bench.data"

default_unmod = "./UNMOD.bench"
default_bcrmp = "./BCRMP.bench"

# default == criterion
default_type = 1

def dump_benchmark(
    #pattern,
    filepath=default_file,
    unmod,
    bcrmp,
    bench_type,
    headers=['#','bench-name','unmod-time', 'unmod-error','bcrmp-time','bcrmp-error'],
    **kwargs):
    """
    Customise with your own output path and header row.
    idep_var is an optional independent variable.
    """
    # capture benchmark output
    unmod_names = re.findall(name_pattern, check_output(["cat", unmod]).decode('utf-8'))
    unmod_result = re.findall(pattern, check_output(["cat", unmod]).decode('utf-8'))
    bcrmp_result = re.findall(pattern, check_output(["cat", bcrmp]).decode('utf-8'))
    # get rid of nasty commas
    output = []
    unmod_len = len(unmod_result)
    bcrmp_len = len(bcrmp_result)
    length = unmod_len if unmod_len < bcrmp_len else bcrmp_len
    for i in range(length):
        line = []
        # grab and append benchmark name to line
        bname = unmod_names[i]
        line.append(bname)
        # grab each matched line
        unmod_line = unmod_result[i]
        bcrmp_line = bcrmp_result[i]
        # grab each of the two numbers per line
        for num in unmod_line:
            tnum = num.translate({ord(','): None})
            line.append(tnum)
        for num in bcrmp_line:
            tnum = num.translate({ord(','): None})
            line.append(tnum)
        output.append(line)
    # any other kwargs will be written as a CSV header row and value
    # nothing prevents you from writing rows that don't have a header
    for k, v in kwargs.items():
        headers.append(k),
        output.append(v)
    # check that path and file exist, or create them
    path_wrangle(filepath, headers)
    # write data to the file
    with open(filepath, 'a') as handle:
        for elem in output:
            writerow(handle, elem)

def path_wrangle(filepath, headers):
    """ Check for or create path and output file
    There's no error handling, because noisy failure's probably a good thing
    """
    # check for or create directory path
    directory = os.path.split(filepath)[0]
    if not os.path.exists(directory):
            os.makedirs(directory)
    # regardless if file itself exists or not, want blank slate so:
    # create new or overwrite existing data
    with open(filepath, 'w') as newhandle:
        writerow(newhandle, headers)

def writerow(filehandle, array):
    """ Write the contents of the array as a white-space
    delimited row in the file
    """
    for elem in array:
        filehandle.write(elem)
        filehandle.write("\t")
    filehandle.write("\n")

if __name__ == "__main__":
    # So brittle. Shhh.
    filepath = default_file
    unmod = default_unmod
    bcrmp = default_bcrmp
    # 0 == bencher; 1 == criterion
    bench_type = default_type
    if len(sys.argv) == 5:
        filepath = sys.argv[1]
        unmod = sys.argv[2]
        bcrmp = sys.argv[3]
        bench_type = sys.argv[4]
    else: 
        print("Wrong number of arguments")
        quit()

    dump_benchmark(
            #pattern,
            filepath=filepath,
            unmod=unmod,
            bcrmp=bcrmp,
            bench_type=bench_type
            )
