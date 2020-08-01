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
            split = stripped.split()
            j = 0
            for s in split:
                if j > 1:
                    if s == "-machinemoduleinfo":
                        o.write("-machinedomtree ")
                    elif s == "-collector-metadata":
                        o.write("-evaluate-aa-metadata ")
                    elif s == "-gc-lowering":
                        o.write("-coro-elide ")
                    elif s == "-shadow-stack-gc-lowering":
                        o.write("-safe-stack-coloring ")
                    elif s == "-stack-protector":
                        o.write("-stack-safety ")
                    elif s == "-finalize-isel":
                        o.write("-fast-isel ")
                    elif s == "-localstackalloc":
                        o.write("-vp-static-alloc ")
                    elif s == "-evaluate-aa-metadata-machine-branch-prob":
                        o.write("-evaluate-aa-metadata ")
                    elif s == "-coro-elide-safe-stack-coloring-unreachableblockelim":
                        o.write("-unreachableblockelim ")
                    elif s == "-stack-safety-verify":
                        o.write("-stack-safety-local ")
                    elif s == "-fast-isel-vp-static-alloc-x86-slh":
                        o.write("-vp-static-alloc ")
                    elif s == "-phi-node-elimination":
                        continue
                    else: 
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
