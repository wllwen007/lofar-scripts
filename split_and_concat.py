from __future__ import print_function

import numpy as np
import os
import pyrap.tables as pt
import sys

if __name__ == '__main__':
    
    import argparse
    parser = argparse.ArgumentParser(description='concat_and_split')
    parser.add_argument('--datacolumn', help='datacolumn', default='CORRECTED_DATA', type=str)
    parser.add_argument('--skipconcat', help='skipconcat', default=False, action='store_true')
    parser.add_argument('--skipsplit', help='skipsplit', default=False, action='store_true')
    parser.add_argument('--noclobber', help='clobber is off', default=False, action='store_true')
    parser.add_argument('outmsroot', help='Output MS root name', type=str)
    parser.add_argument('inmsfile', help='Measurement sets', nargs='+', type=str)
    args = parser.parse_args()
    
    inmsfiles = args.inmsfile
    outmsroot = args.outmsroot
    datacolumn = args.datacolumn
    
    
    nchan = None
    
    
    if not args.skipsplit:

        allms = []
        for inms in inmsfiles:
            ### split
            subnchan=40
            if nchan is None:
                t0_spw = pt.table(inms+'/SPECTRAL_WINDOW')
                nchan = t0_spw.getcol('NUM_CHAN')[0]
                fchan = t0_spw.getcol('CHAN_FREQ')[0]
                dchan = t0_spw.getcol('CHAN_WIDTH')[0]
                
            allmsi = []
            inmsroot = inms.split('.')[0]
            for ii,i in enumerate(range(0,nchan,subnchan)):
                inmsband = '{inmsroot}_BAND{ii:03d}.MS'.format(ii=ii, inmsroot=inmsroot)
                cmd= 'DPPP numthreads=32 msin={inms} msin.datacolumn={datacolumn} msout={inmsband} steps=[filter] filter.type=filter  filter.startchan={i:d} filter.nchan={subnchan:d}'.format(i=i,subnchan=subnchan, inms=inms, outmsroot=outmsroot, datacolumn=datacolumn, inmsband=inmsband)
                print(cmd)
                os.system(cmd)
                allmsi.append(inmsband)
                
            allms.append(allmsi)
        




    allms = np.array(allms)
    print(allms)
    #sys.exit()
    
    
 
    
    if not args.skipconcat:
        ### concatenate
        
        for bandi in range(allms.shape[1]):
        
            mergems = '{outmsroot}_BAND{ii:03d}.MS'.format(ii=bandi, outmsroot=outmsroot)
            
                    
            if os.path.isdir(mergems):
                if args.noclobber==False:
                    print ('removing existing ms: '+mergems )
                    os.system('rm -rf '+mergems)
                else:
                    print ('ms '+mergems+' exists and noclobber is set True')
                    sys.exit()
            
            
            
            print('concatenating')
            print(mergems, allms[:,bandi])
            t = pt.table(allms[:,bandi])
            t.sort('TIME,ANTENNA1,ANTENNA2').copy(mergems, deep=True)
            
            print('concatenating done')
        
                

            pt.addImagingColumns(mergems)
        
        
        
        
    
    ## Create time-chunks
    #print('Splitting in time...')
    #tc = 0
    
    #t = pt.table(mergems, ack=False)
    #starttime = t[0]['TIME']
    #endtime   = t[t.nrows()-1]['TIME']
    #hours = (endtime-starttime)/3600.
    #print(mergems+' has length of '+str(hours)+' h.')

    #for timerange in np.array_split(sorted(set(t.getcol('TIME'))), round(hours)):
        #print('%02i - Splitting freqrange %f %f' % (tc, timerange[0], timerange[-1]))
        #t1 = t.query('TIME >= ' + str(timerange[0]) + ' && TIME <= ' + str(timerange[-1]), sortlist='TIME,ANTENNA1,ANTENNA2')
        #splitms = groupname+'_TC%02i.MS' % tc
        ##lib_util.check_rm(splitms)
        #t1.copy(splitms, True)
        #t1.close()
        #tc += 1
    #t.close()
