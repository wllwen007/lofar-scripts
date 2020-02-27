import numpy as np
import pyregion
import sys

def makeClusterCat(regfile, clusterfile):

    print 'reading',regfile
    regions = pyregion.open(regfile)

    centers = np.zeros(len(regions[:]), dtype=([('Name', 'S200'), ('ra', '<f8'), ('dec', '<f8'), ('SumI', '<f8'), ('Cluster', '<i8')]))

    print 'Number of directions', len(regions[:])

    for region_id,regions in enumerate(regions[:]):

      #print region_id
      ra  = np.pi*regions.coord_list[0]/180.
      dec = np.pi*regions.coord_list[1]/180.

      centers[region_id][0] = ''
      centers[region_id][1] = ra
      centers[region_id][2] = dec
      centers[region_id][3] = 0.
      centers[region_id][4] = region_id

      #print centers[region_id]
      #sys.exit()

    print centers
    np.save(clusterfile,centers)
    print 'saving',clusterfile
    
if __name__ == '__main__':
    
    if len(sys.argv) == 1:
        print 'usage: ds9Reg2ClusterCat.py regionfile clustercatfile'
        sys.exit(1)
    
    reg = sys.argv[1]
    cluster = sys.argv[2]
    
    makeClusterCat(reg,cluster)
