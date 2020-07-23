import sys

def replace(
        infile,
        outfile):
    o = open(outfile, 'w')
    i = open(infile, 'r')
    one = True
    args = []
    # Read in one-line infile
    for line in i:
        if one == False:
            print("Check format of input file!")
        args = line.split("\"")
        one = False
        # Write to outfile replacing any "-pie" instances
        for a in args:
            if a == "-pie":
                o.write("-no-pie ")
                #print("WROTE -no-pie")
            else:
                o.write(a + " ")
                #print("WROTE " + a)
    # Cleanup
    i.close()
    o.close()

if __name__ == "__main__":
    infile = sys.argv[1]
    outfile = sys.argv[2]
    replace(
        infile,
        outfile
    )
