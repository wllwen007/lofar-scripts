import numpy as np
import losoto.h5parm as h5
import matplotlib.pyplot as plt
import os
import glob

#solsname = 'DDS3_full_smoothed'
#solsname = 'DDS3_full_5044842001.00278_smoothed'
#solsname = 'DDS3_full_5044842001.00278_merged'
#solsname = 'DDS3_full_slow_5044842001.00278_merged'
#solsname = 'DDS3_full_5045702401.00278_smoothed'
#solsname = 'DDS3_full_5045702401.00278_merged'
#solsname = 'DDS3_full_slow_5045702401.00278_merged'
#solsname = 'DDS3_full_5045702401.00278_smoothed'
##solsname = 'DDS2_full_5046393601.00278_smoothed'
#solsname = 'killMS.DDS2_full.sols'

for sols in glob.glob('*merged.npz'):
#for sols in glob.glob('*smoothed.npz'):
    solsname = sols.replace('.npz','')
    os.system('killMS2H5parm.py {s}.h5 {s}.npz'.format(s=solsname))
    #tt = h5.h5parm('SOLSDIR/killMS.DDS0.sols.h5')
    #tt = h5.h5parm('SOLSDIR/killMS.DDS3_full.sols.h5')
    #tt = h5.h5parm('SOLSDIR/killMS.{s}.sols.h5'.format(s=solsname))
    tt = h5.h5parm('{s}.h5'.format(s=solsname))

    ss = tt.getSolset('sol000')

    stph0 = ss.getSoltab('phase000')
    stamp0 = ss.getSoltab('amplitude000')
    #['pol', 'dir', 'ant', 'freq', 'time']

    ph0, aph = stph0.getValues()
    amp0, aamp = stamp0.getValues()
    #In [32]: ph0.shape
    #Out[32]: (4, 15, 34, 19, 480)

    nant = len(aph['ant'])
    dirs = aph['dir']
    ants = aph['ant']
    pols = aph['pol']
    freqs = aph['freq'] /1e6  # MHz
    times = aph['time']
    times = (times -times[0])/3600.   # in hours

    ipol = 3 
    idir = 0
    for idir in range(len(dirs)):
            
        # phase
        figgrid, axa = plt.subplots(6, 6, sharex=True, sharey=True, figsize=(18,8))
        axs = axa.flatten()
        for iant in range(nant):
            ax = axs[iant]
            #ax.imshow(ph0[ipol,idir,iant,ifreq,itime], cmap=plt.cm.viridis)
            c=ax.imshow(ph0[ipol,idir,iant,:,:], vmin=-np.pi, vmax=np.pi, cmap=plt.cm.hsv, origin='lower', extent=[times.min(), times.max(), freqs.min(), freqs.max()], aspect='auto')
            #c=ax.imshow(amp0[ipol,idir,iant,:,:], vmin=0.5, vmax=2., cmap=plt.cm.viridis, origin='lower', extent=[times.min(), times.max(), freqs.min(), freqs.max()], aspect='auto')
            ax.text(.5, .85, ants[iant], horizontalalignment='center', fontsize=14, transform=ax.transAxes)

        figgrid.suptitle('Direction:'+str(dirs[idir]))
        figgrid.subplots_adjust(right=0.9,left=0.05,bottom=0.1,top=0.9,hspace=0, wspace=0)
        cbar_ax = figgrid.add_axes([0.925, 0.1, 0.025, 0.8])
        cbar = figgrid.colorbar(c, cax=cbar_ax)
        figgrid.savefig('SOLSDIR/killMS.{s}.sols.phase.{p}.{d}.png'.format(s=solsname,d=dirs[idir],p=pols[ipol]))

        # amp
        figgrid, axa = plt.subplots(6, 6, sharex=True, sharey=True, figsize=(18,8))
        axs = axa.flatten()
        for iant in range(nant):
            ax = axs[iant]
            #ax.imshow(ph0[ipol,idir,iant,ifreq,itime], cmap=plt.cm.viridis)
            #c=ax.imshow(ph0[ipol,idir,iant,:,:], vmin=-np.pi, vmax=np.pi, cmap=plt.cm.hsv, origin='lower', extent=[times.min(), times.max(), freqs.min(), freqs.max()], aspect='auto')
            c=ax.imshow(amp0[ipol,idir,iant,:,:], vmin=0.5, vmax=2., cmap=plt.cm.viridis, origin='lower', extent=[times.min(), times.max(), freqs.min(), freqs.max()], aspect='auto')
            ax.text(.5, .85, ants[iant], horizontalalignment='center', fontsize=14, transform=ax.transAxes)

        figgrid.suptitle('Direction:'+str(dirs[idir]))
        figgrid.subplots_adjust(right=0.9,left=0.05,bottom=0.1,top=0.9,hspace=0, wspace=0)
        cbar_ax = figgrid.add_axes([0.925, 0.1, 0.025, 0.8])
        cbar = figgrid.colorbar(c, cax=cbar_ax)
        figgrid.savefig('SOLSDIR/killMS.{s}.sols.amp.{p}.{d}.png'.format(s=solsname,d=dirs[idir],p=pols[ipol]))
        
        plt.close('all')

