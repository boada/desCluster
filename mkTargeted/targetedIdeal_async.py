from multiprocessing import Pool
import h5py as hdf
import numpy as np
from numpy.lib import recfunctions as rfns
from data_handler import mkTruth, mkHalo
from halo_handler import find_indices, find_indices_multi
from calc_cluster_props import (updateArray, findClusterRedshift, findLOSV,\
                                findLOSVD, findLOSVDmcmc, calc_mass_Evrard)
import os

class AsyncFactory:
    def __init__(self, func, cb_func):
        self.func = func
        self.cb_func = cb_func
        self.pool = Pool(maxtasksperchild=10)

    def call(self,*args, **kwargs):
        self.pool.apply_async(self.func, args, kwargs, self.cb_func)

    def wait(self):
        self.pool.close()
        self.pool.join()

def worker(pos, data, center):
    #print "PID: %d \t Value: %d" % (os.getpid(), pos)
    data = updateArray(data)
    data = findClusterRedshift(data)
    #data = findSeperationSpatial(data, center)
    data = findLOSV(data)
    data = findLOSVD(data)
    # try:
    #     data = findLOSVDgmm(data)
    # except RuntimeError:
    #     print(pos, 'RuntimeError')
    #     data['LOSVDgmm'] = -1.0
    data = findLOSVDmcmc(data)
    data = calc_mass_Evrard(data, A1D = 1177, alpha = 0.364)
    return pos, data

def cb_func((pos, data)):
    if pos % 1000 == 0:
        print pos
    results['IDX'][pos] = pos
    results['CLUSZ'][pos] = data['CLUSZ'][0]
    results['LOSVD'][pos] = data['LOSVD'][0]
    results['LOSVDgmm'][pos] = data['LOSVDgmm'][0]
    results['R200'][pos] = data['R200'][0]
    results['MASS'][pos] = data['MASS'][0]
    results['LOSVD_err'][pos] = data['LOSVD_err'][0]
    results['LOSVDgmm_err'][pos] = data['LOSVDgmm_err'][0]

if __name__ == "__main__":

    async_worker = AsyncFactory(worker, cb_func)
    halo = mkHalo()
    truth = mkTruth()

    gmask = truth['g'] < 22
    Oiimask = truth['Oii'] > 3.5
    zmask = truth['Z'] > 0.4
    mask = (zmask & Oiimask) | (gmask & ~zmask) | (Oiimask & ~zmask)

    truth = truth[mask]

    mask = (halo['m200c']/0.72 >= 1e13) & (halo['upid'] == -1)
    maskedHalo = halo[mask]
    hids, uniqueIdx = np.unique(maskedHalo['id'], return_index=True)

    # now we find all member halos of the most massive halos
    subHalos = find_indices(halo['upid'], hids)

    # now find all the corresponding galaxies
    gals = find_indices_multi(truth['HALOID'], halo['id'], subHalos)

    # make the results container
    results = np.zeros((len(subHalos),), dtype=[('IDX', '>i4'), ('HALOID',
        '>i8'), ('ZSPEC', '>f4'), ('VRMS', '>f4'), ('M200c', '>f4'), ('CLUSZ',
            '>f4'), ('LOSVD', '>f4'), ('LOSVDgmm', '>f4'), ('MASS', '>f4'),
            ('R200', '>f4'), ('NGAL', '>i4')])
    newnewData = np.zeros(results.size, dtype=[('LOSVD_err', '>f4', (2,)),
            ('LOSVDgmm_err', '>f4', (2,))])
    results = rfns.merge_arrays((results, newnewData), usemask=False,
            asrecarray=False, flatten=True)

    #x = [i for i,g in enumerate(gals) if g.size >10]

    print('do work')
    for i, SH in enumerate(subHalos):
        center = (maskedHalo['ra'][uniqueIdx[i]],
                maskedHalo['dec'][uniqueIdx[i]])
        if gals[i].size >= 5:
            async_worker.call(i, truth[gals[i]], center)
            # update results array
            results['NGAL'][i] = gals[i].size
            results['ZSPEC'][i] = maskedHalo['zspec'][uniqueIdx[i]]
            results['VRMS'][i] = maskedHalo['vrms'][uniqueIdx[i]]/np.sqrt(3)
            results['M200c'][i] = maskedHalo['m200c'][uniqueIdx[i]]/0.72
        else:
            results['IDX'][i] = i
            results['NGAL'][i] = gals[i].size
            results['ZSPEC'][i] = maskedHalo['zspec'][uniqueIdx[i]]
            results['VRMS'][i] = maskedHalo['vrms'][uniqueIdx[i]]/np.sqrt(3)
            results['M200c'][i] = maskedHalo['m200c'][uniqueIdx[i]]/0.72

    async_worker.wait()

    try:
        os.remove('result_targetedIdeal.hdf5')
    except OSError:
        pass
    with hdf.File('result_targetedIdeal.hdf5', 'w') as f:
        f['result_targetedIdeal'] = results
