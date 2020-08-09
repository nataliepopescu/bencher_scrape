import sys

def replace(
        infile,
     #   outfile,
        execlist):
#    o = open(outfile, 'w')
    i = open(infile, 'r')
    e = open(execlist, 'a')
    one_line = True
    args = []
    seen_o_flag = False
    # Read in one-line infile
    for line in i:
        if one_line == False:
            print("Check format of input file!")
            return
        args = line.split("\"")
        one = False
        # Write to outfile replacing any "-pie" instances
        for a in args: 
 #           if a == "-pie":
 #               o.write("-no-pie ")
                #print("WROTE -no-pie")
            if seen_o_flag and len(a.strip()) > 0:
                path = a.split("/")
                name = path[-1]
                e.write(name + "\n")
                #print("SHOULD HAVE WRITTEN TO EXECLIST")
            #    o.write(a + " ")
                #print("WROTE " + a)
                seen_o_flag = False
            elif a == "-o":
                seen_o_flag = True
             #   o.write(a + " ")
                #print("WROTE " + a)
            #else:
            #    o.write(a + " ")
                #print("WROTE " + a)
    # Cleanup
    e.close()
    i.close()
    #o.close()

if __name__ == "__main__":
    infile = sys.argv[1]
    #outfile = sys.argv[2]
    execlist = sys.argv[2]
    replace(
        infile,
     #   outfile,
        execlist
    )
