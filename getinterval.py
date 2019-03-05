from __future__ import print_function
import sys

if len(sys.argv)>1:
    f = open(sys.argv[1], 'r')
    leading_space = True
    for line in f:
         data = line.split(' ')
         if leading_space:
             if 'space' in data[0]:
                 continue
             elif 'pulse' in data[0]:
                 leading_space = False
         if  'space' in data[0] or 'pulse' in data[0]:
             print(data[1].strip(), end=' ')
         elif 'timeout' in data[0]:
             break
    f.close()
    print()
else:
    print('python getduration.py filename')
