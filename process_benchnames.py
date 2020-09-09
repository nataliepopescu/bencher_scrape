import sys

def get_names(
        infile,
        outfile):
    o = open(outfile, 'w')
    i = open(infile, 'r')
    start = False
    # Read infile
    for line in i:
        stripped = line.strip()
        if start == True and len(stripped) > 0:
            print("WRITING " + stripped)
            o.write(stripped + "\n")
        if stripped.startswith("Available"): # benches:":
            start = True
    # Close files
    i.close()
    o.close()

if __name__ == "__main__":
    infile = sys.argv[1]
    outfile = sys.argv[2]
    get_names(
        infile,
        outfile
    )
