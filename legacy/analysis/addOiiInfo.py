import pyfits as pyf
import numpy as np
import h5py as hdf
from astLib import astCalc, astStats
from collections import Counter
from multiprocessing import Pool, cpu_count
from itertools import izip

def absMag(mag, dl):
    return astCalc.absMag(mag, dl)

def mp_wrapper(args):
    return absMag(*args)

# start the workers
p = Pool(cpu_count())

with pyf.open('./oii/sdss12_oii_flux_v2.fits') as f:
    sdssData = f[1].data

    # convert to DES magnitudes
    g = sdssData['g'] - 0.104 * (sdssData['g'] - sdssData['r']) + 0.01
    r = sdssData['r'] - 0.102 * (sdssData['g'] - sdssData['r']) + 0.02

    dl = np.array(p.map(astCalc.dl, sdssData['redshift']))
    xdat = np.array(p.map(mp_wrapper, izip(r, dl)))
    ydat = g - r

    bins = [50,50]
    extent = [[-26,-10],[-1,4]]
    _, locx, locy = np.histogram2d(xdat, ydat, range=extent, bins=bins)

    # need the Oii luminosity
    lum = sdssData['oii_3726_flux']*4.*np.pi*(dl* 3.0857e24)**2. *1e-17

# now we loop over the catalog galaxies to add the info
with hdf.File('./out1204878_complete.hdf5', 'r+') as f:
    dset = f[f.keys()[0]]
    catg = dset['g']
    catr = dset['r']
    catRedshift = dset['Z']
    catOii = dset['Oii']

    dl = np.array(p.map(astCalc.dl, catRedshift))
    x = np.array(p.map(mp_wrapper, izip(catr, dl)))

    # close down the pool
    p.close()
    p.join()

    y = catg - catr

    xbin = np.digitize(x, locx)
    ybin = np.digitize(y, locy)

    # find the unique pairs of bins
    pairs = [(x_,y_) for x_,y_ in zip(xbin, ybin)]
    c = Counter(pairs)

    for bins, number in c.items():
        # need this bit to handle the situation of data outside the bin range
        if bins[0] == len(locx) or bins[1] == len(locy):
            lumes = []
        else:
            # find all of the points inside the bin we are interested in
            i = (locx[bins[0]-1] < xdat) & (xdat < locx[bins[0]]) &\
                (locy[bins[1]-1] < ydat) & (ydat < locy[bins[1]])
            lumes = lum[i]

        # now we have to find all of the bins.
        binMask = (xbin == bins[0]) & (ybin == bins[1])

        if len(lumes) > 10:
            # make a histogram of the flux values
            px, x = np.histogram(np.log10(lumes), bins=20, normed=True)

            # resample the distribution
            x = np.linspace(x[0], x[-1], len(px))
            s = astStats.slice_sampler(px, N=number, x=x)

            catOii[binMask] = (10**s)/(4*np.pi*(3.0857e24*dl[binMask])**2 \
                *1e-17)

        elif len(lumes) >= 1:
            s = np.mean(np.log10(lumes))

            catOii[binMask] = (10**s)/(4*np.pi*(3.0857e24*dl[binMask])**2 \
                *1e-17)
        else:
            catOii[binMask] = 0.

    dset['Oii'] = catOii
    f.flush()

