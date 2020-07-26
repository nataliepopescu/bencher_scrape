import os
import sys
import shutil

cwd = os.getcwd()
root = cwd + "/crates/crates"

def rewrite(infile):
    i = open(infile, 'r')
    tmp = "tmp"
    t = open(tmp, 'w')
    # Read infile
    for line in i:
        # Write to tmp file replacing any "iter(" instances with "bench_n(10000000, "
        if "iter(" in line:
            new_line = line.replace("iter(", "bench_n(10000000, ")
            t.write(new_line)
        else:
            t.write(line)
    # Move rewritten tmp file back to original infile
    shutil.move(tmp, infile)
    # Cleanup
    t.close()
    i.close()

if __name__ == "__main__":
    for sd, d, f in os.walk(root):
        if sd.endswith("benches"):
            print("SD == " + sd)
            for benchfile in f:
                rewrite(sd + "/" + benchfile)
