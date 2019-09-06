from __future__ import print_function

import numpy as np
import os
import pyrap.tables as pt
import sys

if __name__ == '__main__':
    
    import argparse
    parser = argparse.ArgumentParser(description='concat_and_split')
    parser.add_argument('--tc', help='set starting time index', type=int, default=0)
    parser.add_argument('outmsroot', help='Output MS root name', type=str)
    parser.add_argument('inmsfile', help='Measurement sets', type=str)
    args = parser.parse_args()
    
    
    # Create time-chunks
    print('Splitting in time...')
    tc = 0
    
    ms = args.inmsfile
    groupname = args.outmsroot
    
    if not os.path.exists(ms): 
        print ('input ms does not exist')
        sys.exit(1)
    
    t = pt.table(ms, ack=False)
    starttime = t[0]['TIME']
    endtime   = t[t.nrows()-1]['TIME']
    hours = (endtime-starttime)/3600.
    print(ms+' has length of '+str(hours)+' h.')

    for timerange in np.array_split(sorted(set(t.getcol('TIME'))), round(hours)):
        print('%02i - Splitting timerange %f %f' % (tc, timerange[0], timerange[-1]))
        t1 = t.query('TIME >= ' + str(timerange[0]) + ' && TIME <= ' + str(timerange[-1]), sortlist='TIME,ANTENNA1,ANTENNA2')
        splitms = groupname+'_TC%02i.MS' % tc
        if os.path.exists(splitms):
            print('output ms',splitms,'already exists, not overwriting')
            continue
        t1.copy(splitms, True)
        t1.close()
        tc += 1
    t.close()

