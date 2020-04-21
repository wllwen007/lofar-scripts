#!/usr/bin/env python3

import os
import sys
import glob
from datetime import datetime
import numpy as np
import astropy.units as u
import argparse

def getlast(lines, i):
    try:
        tlast = datetime.strptime(lines[-i][0:19], '%Y-%m-%d %H:%M:%S')
        return tlast
    except:
        return False
    return tlast

def readlog(log, tignore=5., tasksdone=[]):
    print('reading {:s}'.format(log))
    with open(log,'r') as f:
        lines = f.readlines()
    Blines = []
    steps = []
    kinds = []
    kind = None
    # extract the lines with 'Begin step' 
    for l in lines:
        if 'Begin' in l:
            Blines.append(l.strip())
            if len(Blines) > 1:
                kinds.append(kind)
            kind = None
        if 'executable_args' in l:
            kind = 'execargs'
    kinds.append(kind)
            
    ts = [datetime.strptime(s[0:19], '%Y-%m-%d %H:%M:%S') for s in Blines]
    steps = [s.split()[-1] for s in Blines]
    t0 = datetime.strptime(lines[0][0:19], '%Y-%m-%d %H:%M:%S')
    
    # deal with the case where the pipeline has stopped mid output... look back for the last line with a timestamp in the right place
    ## hopefully 200 is sufficient lines to scroll back...
    i = 1
    found = False
    while (not found) and (i < 200):
        tlast = getlast(lines, i)
        if isinstance(tlast, datetime):
            found = True
        i += 1
    if not found:
        print('could not find last timestamp ')
        tlast = t0
    finished = False
    success = True
    if 'completed' in lines[-1]:
        finished = True
        if 'completed with errors' in lines[-1]:
            success = False
    ts.append(tlast)
    
    #tdiffs = [(ts[0] - t0).total_seconds()]
    tdiffs = []
    for i in range(0, len(ts)-1):
        tdiffs.append((ts[i+1]-ts[i]).total_seconds())
    
    stdiffs = [in_units(td)  for td in tdiffs]
    
    
    # print the formatted output
    for t, k, step, tdiff, stdiff in zip(ts, kinds, steps, tdiffs, stdiffs):
        trep = ''
        if step in tasksdone:
            trep = '*'
        if tdiff > tignore:  # ignore very short running steps
            print('{:20s} {:8s} {:8.0f} {:5.1f}{:s} {:s}{:s}'.format(str(t), str(k), tdiff, stdiff.value, stdiff.unit, trep, step))
    ttotal = (ts[-1]-ts[0]).total_seconds()
    sttotal = in_units(ttotal)
    if not finished:
        print('incomplete run, last step may still be executing')
    else:
        if success:
            print('finished successfully')
        else:
            print('finished unsuccessfully')
    print('total time {:8.0f}s {:5.1f}{:s} '.format(ttotal,sttotal.value, sttotal.unit))
    
    return tdiffs, steps

def in_units(td):
    unit = u.s
    if td >= 60.:
        td = td/60.
        unit = u.m
        if td >= 60.:
            td = td/60.
            unit = u.h
            if td >= 24.:
                td = td/24.
                unit = u.day
    q = td * unit
    return q

def get_config_rundir(config):
    if not os.path.exists(config):
        print('config file {:s} does not exist'.format(config))
        sys.exit(1)
    with open(config, 'r') as f:
        lines = f.readlines()
        for l in lines:
            if 'runtime_directory' in l:
                rundir = l.strip().split('=')[1]
                print('found runtime directory: {:s}'.format(rundir))
                break
    
    return rundir


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Read step times from genericpipeline logs")
    parser.add_argument('parset', help='The pipeline parset')
    parser.add_argument('-r','--rundir', help='The pipeline runtime directory file', default=None)
    parser.add_argument('-c','--config', help='The pipeline configuration file', default=None)
    parser.add_argument('-t','--tignore', help='Ignore steps shorter than tignore in seconds', type=float, default=-1)
    args = parser.parse_args()
    

    if len(sys.argv) < 2:
        print('give parset name')
        sys.exit(1)
        
    parset = args.parset
    config = args.config
    rundir = args.rundir
    
    if (config is None) and (rundir is None):
        print('please specify either a config file or runtime directory')
        sys.exit(1)
    
    if config is not None:
        crundir = get_config_rundir(config)
        if (rundir is not None):
            if crundir != rundir:
                print('conflict: runtime directory from config ({:s}) does not match runtime directory specified ({:s})'.format(crundir, rundir))
                sys.exit(1)
            else:
                # rundirs match, all ok
                pass
        else:
            # use the config rundir
            rundir = crundir
        
    
    if not os.path.exists(rundir):
        print('runtime directory does not exist')
        sys.exit(1)
            
    pipedir = '{:s}/{:s}'.format(rundir, parset.replace('.parset','').split('/')[-1])
    
    print('checking {dir:s}'.format(dir=pipedir))

    if not os.path.isdir(pipedir):
        print('no such pipeline run')
        sys.exit(1)

    rundirs = glob.glob(pipedir+'/logs/*')
    rundirs.sort()

    if len(rundirs) > 1:
        print('we have multiple pipeline runs, printing info from all')



    steps = []
    for t in rundirs:
        print(t)
        tdiffs, steps = readlog(t+'/pipeline.log', tignore=args.tignore, tasksdone=steps)

