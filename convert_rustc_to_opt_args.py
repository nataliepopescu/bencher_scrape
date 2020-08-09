import sys

def get_args(
        infile,
        outfile):
    o = open(outfile, 'w')
    i = open(infile, 'r')
    # Read infile
    for line in i:
        stripped = line.strip()
        if stripped.startswith("Pass Arguments:"):
            if "-phi-node-elimination" in stripped:
                continue
            elif "-write-thinlto-bitcode" in stripped:
                continue
            elif "-lower-constant-intrinsics" in stripped:
                continue
            elif len(stripped) < 200:
                continue
            split = stripped.split()
            j = 0
            for s in split:
                if j > 1:
                    o.write(s + " ")
                j += 1
    # Close files
    i.close()
    o.close()

if __name__ == "__main__":
    infile = sys.argv[1]
    outfile = sys.argv[2]
    get_args(
        infile,
        outfile
    )
