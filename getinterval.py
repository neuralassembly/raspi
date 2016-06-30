from __future__ import print_function
import sys

if len(sys.argv)>1:
    f = open(sys.argv[1], 'r')
    line = f.readline()  # Discard the first line
    for line in f:
         data = line.split(' ')
         print(data[1].strip(), end=' ')
    f.close()
    print()
else:
    print('python getduration.py filename')
