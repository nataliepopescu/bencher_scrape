import re
import sys
import time
import subprocess
import os
from multiprocessing import Process

def stall():
    while True:
        time.sleep(60)

if __name__ == "__main__":
    pid = sys.argv[1]
    d = sys.argv[2]
    timeout = sys.argv[3]
    bname = ""
    if len(sys.argv) == 5:
        bname = sys.argv[4]

    p = Process(target=stall, name='process_stall')
    p.start()
    # in seconds
    p.join(timeout=float(timeout))
    p.terminate()

cur = os.getpid()
pid1 = cur + 1
child2 = subprocess.run(["pgrep", "-P", str(pid1)], stdout=subprocess.PIPE, text=True)
pid2 = child2.stdout[:-1]

if bname == "":
    fname = d + "/timedout"
else:
    fname = d + "/timedout-" + bname

if not pid2 == "":
    subprocess.run(["kill", "-15", pid2])
    subprocess.run(["touch", fname])
