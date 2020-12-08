import os
import sys
import pandas as pd

infile = sys.argv[1]
fname = os.path.join(infile)
data = pd.read_csv(fname)
print(len(data.iloc[0:400, 1].value_counts()))
