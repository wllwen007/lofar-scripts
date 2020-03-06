#!/usr/bin/env python2.7
from __future__ import print_function

import numpy as np
import os
import pyrap.tables as pt
import sys

if __name__ == '__main__':
    
    import argparse
    parser = argparse.ArgumentParser(description='concat_and_split')
    parser.add_argument('--nchan', help='number of channels per band', type=int, default=40)
    parser.add_argument('--fc', help='starting band index', type=int, default=0)
    parser.add_argument('--datacolumn', help='datacolumn to read', type=str, default='DATA')
    parser.add_argument('outmsroot', help='Output MS root name', type=str)
    parser.add_argument('inmsfile', help='Measurement set', type=str)
    args = parser.parse_args()
    
    
    # Create time-chunks
    print('Splitting in frequency bands...')
    fc = 0
    
    
    
    
    
    ms = args.inmsfile
    root = args.outmsroot
    nchan = args.nchan
    datacolumn = args.datacolumn

    msextend = ms.split('.')[-1]
    
    if not os.path.exists(ms): 
        print ('input ms does not exist')
        sys.exit(1)
        
    for ii,i in enumerate(range(0,976,nchan)):
        cmd="DPPP numthreads=32 msin={ms} msin.datacolumn={datacolumn} msout={root}_BAND{ii:02d}.{msextend} steps=[filter] filter.type=filter filter.startchan={i:d} filter.nchan={nchan:d}".format(i=i,nchan=nchan,ii=ii,ms=ms,root=root, datacolumn=datacolumn, msextend=msextend)
        print (cmd)
        os.system(cmd)
        #pt.addImagingColumns('{root}_BAND{ii:03d}.ms'.format(root=root,ii=ii))

    
    
    
    #t = pt.table(ms, ack=False)
    #starttime = t[0]['TIME']
    #endtime   = t[t.nrows()-1]['TIME']
    #hours = (endtime-starttime)/3600.
    #print(ms+' has length of '+str(hours)+' h.')

    #for timerange in np.array_split(sorted(set(t.getcol('TIME'))), round(hours)):
        #print('%02i - Splitting timerange %f %f' % (tc, timerange[0], timerange[-1]))
        #t1 = t.query('TIME >= ' + str(timerange[0]) + ' && TIME <= ' + str(timerange[-1]), sortlist='TIME,ANTENNA1,ANTENNA2')
        #splitms = groupname+'_TC%02i.MS' % tc
        ##lib_util.check_rm(splitms)
        #t1.copy(splitms, True)
        #t1.close()
        #tc += 1
    #t.close()

