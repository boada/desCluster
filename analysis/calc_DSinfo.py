import numpy as np
import h5py as hdf
from addHaloInfo import find_indices
from dstest import DStest
from multiprocessing import Pool, cpu_count, current_process
from itertools import izip, repeat

def mp_worker((h, data)):
    if len(h) < 10:
        return -1.
    else:
        cluster = np.column_stack([data['RA'][h],
            data['DEC'][h], data['Z'][h]])
        try:
            s = DStest(cluster, data['LOSV'][h],
                    data['LOSVD'][h][0], shuffles=1000)
            del cluster
            return s
        except:
            print 'DS test problem'
            del cluster
            return -2.

def mp_worker_wrapper(*args):
    return mp_worker(*args)

def start_process():
    print 'Starting', current_process().name

def main():

    #with hdf.File('out1204878_hetdex.hdf5', 'r') as f:
    #with hdf.File('out1204878_complete.hdf5', 'r') as f:
    with hdf.File('out1204878_allGalaxies_props.hdf5', 'r') as f:
        dset = f[f.keys()[0]]
        #data = dset['RA', 'DEC', 'Z', 'LOSV', 'LOSVD', 'M200', 'HALOID']
        data = dset['RA', 'DEC', 'Z', 'LOSV', 'LOSVD', 'HALOID']

    #mask = (data['M200']/0.72 >= 1e13) & (data['Z'] < 0.5)
    #data = data[mask]

    # try to reduce footprint
    #del mask

    hids = np.unique(data['HALOID'])
    halos = np.array(find_indices(data['HALOID'], hids))

    p = Pool(cpu_count(), maxtasksperchild=2, initializer=start_process)

    result = p.imap(mp_worker_wrapper, izip(halos, repeat(data)),
            chunksize=3)

    p.close()
    p.join()

    finalResult = np.ones(hids.shape, dtype=[('HALOID', '>i8'), ('DS', '>f4')])
    finalResult['HALOID'] = hids
    finalResult['DS'] = [DS for DS in result]

    with hdf.File('out1204878_allGalaxies_DSresult.hdf5', 'w') as f:
        f['DSresult'] = finalResult
        f.flush()

    return finalResult
if __name__ == "__main__":
    main()
