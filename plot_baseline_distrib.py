import numpy as np
import casacore.tables as pt
import matplotlib.pyplot as plt

t = pt.table('mss/L667906_BAND22.ms', ack=False)
tant = pt.table('mss/L667906_BAND22.ms::ANTENNA', ack=False)
tspw = pt.table('mss/L667906_BAND22.ms::SPECTRAL_WINDOW', ack=False)

freq = tspw.getcol('CHAN_FREQ')
lam = 2.998e8 / freq

print freq/1e6

ants = tant.getcol('NAME')

time = t.getcol('TIME')   
timeu = np.unique(time)
ant1 = t.getcol('ANTENNA1')   
ant2 = t.getcol('ANTENNA2')   
uvw = t.getcol('UVW')   # in m
u = uvw[:,0]
v = uvw[:,1]
w = uvw[:,2]

uvdist = np.sqrt(u**2.+ v**2.)
uvlam = uvdist[:,np.newaxis] / lam

#select time 0
sel1 = (time == timeu[0])
sel2 = (time == timeu[len(timeu)/2])
sel3 = (time == timeu[-1])

print 't0', uvlam[sel1,:].min(), uvlam[sel1,:].max()
print 't1', uvlam[sel2,:].min(), uvlam[sel2,:].max()
print 't2', uvlam[sel3,:].min(), uvlam[sel3,:].max()

print 't0', uvdist[sel1].min(), uvdist[sel1].max()
print 't1', uvdist[sel2].min(), uvdist[sel2].max()
print 't2', uvdist[sel3].min(), uvdist[sel3].max()
ns = np.zeros((len(timeu), 200))
ns0 = np.zeros(len(timeu))
ns1 = np.zeros(len(timeu))
ns2 = np.zeros(len(timeu))
for t in range(len(timeu)):
    sel = (time == timeu[t])
    #ns[t],b = np.histogram(uvdist[sel]/1e3, range=(0,10),bins=200)
    ns1[t] = np.sum(uvdist[sel]/1e3 > 0.1)
    ns2[t] = np.sum(uvdist[sel]/1e3 > 0.2)
    ns0[t] = np.sum(uvdist[sel]/1e3 > 0.)
    
t0 = timeu.min()
plt.figure()
plt.plot(timeu-t0, ns0, label='all')
plt.plot(timeu-t0, ns1, label='100m')
plt.plot(timeu-t0, ns2, label='200m')
plt.legend()
#plt.figure()
#for iant in range(len(ants)):
    #sel = (time == timeu[0]) & (ant1==iant)
    #plt.hist(uvlam[sel,:].flatten(), bins=200, range=(0,15000))
