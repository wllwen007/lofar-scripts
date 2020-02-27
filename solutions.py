import os
import sys
import glob

def MergeSols(solsname, keepnpz=False):

    solsin = 'SOLSDIR/L*_BAND*.MS/killMS.{solsname}.sols.npz'.format(solsname=solsname)
    tlist = glob.glob(solsin)
    tlist.sort()
    if len(tlist) == 0:
        print 'No solutions to combine'
        print solsin
        sys.exit(1)
    print 'Solutions to combine: '+','.join(tlist)
    solsmerge = 'SOLSDIR/killMS.{solsname}.sols.npz'.format(solsname=solsname)
    solsh5= 'SOLSDIR/killMS.{solsname}.sols.h5'.format(solsname=solsname)
    cmd = 'MergeSols.py --SolsFilesIn={solsin} --SolFileOut={solsmerge}'.format(solsin=solsin, solsmerge=solsmerge)
    os.system(cmd)
    cmd = 'killMS2H5parm.py {solsh5} {solsmerge}'.format(solsmerge=solsmerge, solsh5=solsh5)
    os.system(cmd)
    if not keepnpz:
        os.system('rm -rf '+solsmerge)


if __name__ == '__main__':
    
    
    import argparse
    parser = argparse.ArgumentParser(description='combine solutions to h5')
    parser.add_argument('solsname', help='name of kMS solutions to combine', type=str)
    args = parser.parse_args()

    
    MergeSols(args.solsname)
