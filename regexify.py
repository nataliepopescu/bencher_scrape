#!/usr/bin/env python3
import re
import fileinput
import os
import subprocess

root = os.path.join(os.getcwd(), "criterion_rev_deps")
logfile = "changes.txt"
out = open(logfile, 'w')

mutregex_in = r'([a-zA-Z_][a-zA-Z0-9_\.]*)\.get_unchecked_mut[(]([a-zA-Z_][a-zA-Z0-9_\.]*)[)]'
mutregex_out = r'(&mut \1[\2])'
regex_in = r'([a-zA-Z_][a-zA-Z0-9_\.]*)\.get_unchecked[(]([a-zA-Z_][a-zA-Z0-9_\.]*)[)]'
regex_out = r'(&\1[\2])'
left_brack = r'\['

for dir in os.listdir(root): 
    os.chdir(os.path.join(root, dir))

    rs_files = subprocess.run(["find", ".", "-name", "*.rs", "-type", "f"], 
            capture_output=True, text=True)
    filelist = rs_files.stdout.split()

    with fileinput.input(files=filelist, inplace=True) as f: 
        for line in f: 
            # convert all instances per line one at a time
            while (match := re.search(mutregex_in, line.strip())): 
                line = re.sub(mutregex_in, mutregex_out, line.strip(), count=1)
                start = match.span()[0]
                end = match.span()[1]
                # create temp string whose start is "start"
                # find location of '[' in tmp string
                # then add value of "start" to this location to get col
                tmp = line[start:]
                brack = re.search(left_brack, tmp)
                if not brack: 
                    exit("SHOULD HAVE FOUND A BRACKET [mut]")
                bloc = brack.span()[0]
                col = bloc + start + 1
                if col > end: 
                    exit("Column calculation is off!! [mut]")
                fname = os.path.join(os.getcwd(), fileinput.filename())
                out.write(str(fileinput.filelineno()) + " " + 
                        str(col) + " " + 
                        fname + "\n")
            while (match := re.search(regex_in, line.strip())): 
                line = re.sub(regex_in, regex_out, line.strip(), count=1)
                start = match.span()[0]
                end = match.span()[1]
                # create temp string whose start is "start"
                # find location of '[' in tmp string
                # then add value of "start" to this location to get col
                tmp = line[start:]
                brack = re.search(left_brack, tmp)
                if not brack: 
                    exit("SHOULD HAVE FOUND A BRACKET [immut]")
                bloc = brack.span()[0]
                col = bloc + start + 1
                if col > end: 
                    exit("Column calculation is off!! [immut]")
                fname = os.path.join(os.getcwd(), fileinput.filename())
                out.write(str(fileinput.filelineno()) + " " + 
                        str(col) + " " + 
                        fname + "\n")
            print(line.strip())
