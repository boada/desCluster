from mk_survey import *
from data_handler import *
import multiprocessing
import numpy as np
from numpy.lib import recfunctions as rfns
import h5py as hdf
from os import environ

# shared data... This is where the big catalog goes
import myglobals

def mp_worker(ra, dec, ramax, decmax):
    tile = np.unique(find_tile(ra, dec, data=myglobals.data))
    catalog = mk_catalog(tile)
    # These are the individual IFUs, 96 of them
    for ifu in gen_ifus(ra, dec):
        print ifu
        try:
            result = np.append(result, apply_mask(ifu[0], ifu[1], ifu[2],
                ifu[3], catalog))
        except NameError:
            result = apply_mask(ifu[0], ifu[1], ifu[2], ifu[3], catalog)
    return result
        #return 0

def mp_worker_wrapper(args):
    return mp_worker(*args)

def mp_handler(ra, dec):
    # get this so we can use map
    #from itertools import repeat, izip
    # only list the tiles we'll need for the whole survey
    #tiles = np.unique(find_tile(ra, dec, data=data))
    # load those tiles -- catalog will be really big
    #catalog = mk_catalog(tiles)

    ### Here is the parallization ###
    #p = multiprocessing.Pool(1)
    #result = p.map(mp_worker_wrapper, izip(gen_pointings(ra, dec),
    #    repeat(catalog, 115*27)))
    #result = p.map(mp_worker_wrapper, gen_pointings(ra, dec))

    #p.close()
    #p.join()

    result = mp_worker_wrapper(gen_pointings(ra, dec).next())
    return rfns.stack_arrays(result, usemask=False)

if __name__ == "__main__":
# survey bounds
    RAmax = 430
    RAmin = 292
    DECmax = -10
    DECmin = -20

    # here we are making 25 surveys
    for ra, dec in zip(np.random.rand(1)*(RAmax-RAmin)+RAmin,
            np.random.rand(1)*(DECmax-DECmin)+DECmin):
    #for ra, dec in zip([346], [-10]):
        if ra > 360:
            ra -= 360.
        print ra, dec
        # make the tiles across the boundary friendly.
        data = fix_tiles()
        # now we make the individual pointings, 115x27 of them
        try:
            for p in gen_pointings(ra, dec):
                try:
                    tile = np.append(tile, find_tile(p[0], p[1], data=data))
                    tile = np.append(tile, find_tile(p[2], p[3], data=data))
                except NameError:
                    tile = find_tile(p[0], p[1], data=data)
                    tile = np.append(tile, find_tile(p[2], p[3], data=data))
        except ValueError:
            print 'OUT OF BOUNDS!'
            break
	tile = np.unique(tile)
        print tile
        # load the data -- only the tiles we are going to use
#        global catalog
#        catalog = load_tiles(tile)

        # trim down the the data list to make the finding faster
        # only returns the tiles found in the previous step.
        myglobals.data = np.asarray([d1 for d1 in data if d1['name'] in tile],
                dtype=data.dtype)

        #############################
        ### LOAD THE CATALOG DATA ###
        #############################
        #myglobals.catalog = mk_catalog(tile)
        ###################
        ### DO THE WORK ###
        ###################
        print 'do work'
        result = mp_handler(ra, dec)
        print len(result)

        # write it all to a file
        print 'ID number is', environ['LSB_JOBID']
        f = hdf.File('out'+str(environ['LSB_JOBID'])+'.hdf5', 'w')
        f['dset'] = result
        f.close()
        print 'done'