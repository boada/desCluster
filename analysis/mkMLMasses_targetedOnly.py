import numpy as np
import h5py as hdf
from sklearn.ensemble import RandomForestRegressor
from numpy.lib import recfunctions as rfns
from itertools import permutations, izip
import multiprocessing
from halo_handler import find_indices

def child_initializer(_rf):
    print 'Starting', multiprocessing.current_process().name
    global model
    model = _rf

def updateArray(data):
    ''' Adds the results containers to the data product. '''

    newData = np.zeros(data.size)
    data = rfns.append_fields(data, ['ML_pred_1d', 'ML_pred_2d',
        'ML_pred_2d2', 'ML_pred_3d', 'ML_pred_1d_err', 'ML_pred_2d_err',
        'ML_pred_2d2_err', 'ML_pred_3d_err' ], [newData, newData, newData,
            newData, newData, newData, newData, newData], dtypes='>f4',
            usemask=False)

    return data


def splitData(data, test_size=0.3):
    def splitList(alist, wanted_parts=1):
        ''' Breaks a list into a number of parts. If it does not divide evenly
        then the last list wil have an extra element.

        '''

        length = len(alist)
        return [alist[i*length // wanted_parts: (i+1)*length // wanted_parts]\
                for i in range(wanted_parts)]

    np.random.shuffle(data)
    sl = splitList(data, int(1/test_size))

    c = permutations(range(int(1/test_size)))

    prev_i = -1
    for i,j, k in c:
        if i == prev_i:
            continue
        else:
            test = sl[i]
            train = np.append(sl[j], sl[k])
        prev_i = i
        #print test
        #print train

        yield train, test

def addMasses(data, generator):
    ''' This does all of the heavy lifting to get the new masses assigned to
    the right places.

    '''

    i = 0
    for train, test in generator:
        rf = RandomForestRegressor(n_estimators=1000, min_samples_leaf=1,
                verbose=1, n_jobs=-1)
        X = np.log10(train['M200c'])

    ############
    #### 1d ####
    ############
        y = np.column_stack([np.log10(train['LOSVD'])])
        rf.fit(y, X)
        obs = np.column_stack([np.log10(test['LOSVD'])])
        mrf = rf.predict(obs)

        data['ML_pred_1d'][test['IDX']] = mrf

        # errors
        print('Calculating Error')
        p = multiprocessing.Pool(maxtasksperchild=1000,
                initializer=child_initializer, initargs=([rf]))
        result = p.map(mp_worker_wrapper, izip(obs, mrf))
        p.close()
        p.join()
        data['ML_pred_1d_err'][test['IDX']] = result

    #############
    #### 2d #####
    #############
        y = np.column_stack([np.log10(train['LOSVD']), train['ZSPEC']])
        rf.fit(y, X)
        obs = np.column_stack([np.log10(test['LOSVD']), test['ZSPEC']])
        mrf = rf.predict(obs)

        data['ML_pred_2d'][test['IDX']] = mrf
        # errors
        print('Calculating Error, 2d')
        p = multiprocessing.Pool(maxtasksperchild=1000,
                initializer=child_initializer, initargs=([rf]))
        result = p.map(mp_worker_wrapper, izip(obs, mrf))
        p.close()
        p.join()
        data['ML_pred_2d_err'][test['IDX']] = result

    #############
    #### 2d #####
    #############
        y = np.column_stack([np.log10(train['LOSVD']), train['NGAL']])
        rf.fit(y, X)
        obs = np.column_stack([np.log10(test['LOSVD']), test['NGAL']])
        mrf = rf.predict(obs)

        data['ML_pred_2d2'][test['IDX']] = mrf
        # errors
        print('Calculating Error, 2d2')
        p = multiprocessing.Pool(maxtasksperchild=1000,
                initializer=child_initializer, initargs=([rf]))
        result = p.map(mp_worker_wrapper, izip(obs, mrf))
        p.close()
        p.join()
        data['ML_pred_2d2_err'][test['IDX']] = result


    ##############
    ##### 3d #####
    ##############
        y = np.column_stack([np.log10(train['LOSVD']), train['ZSPEC'],
            train['NGAL']])
        rf.fit(y, X)
        obs = np.column_stack([np.log10(test['LOSVD']), test['ZSPEC'],
            test['NGAL']])
        mrf = rf.predict(obs)

        data['ML_pred_3d'][test['IDX']] = mrf
        # errors
        print('Calculating Error, 3d')
        p = multiprocessing.Pool(maxtasksperchild=1000,
                initializer=child_initializer, initargs=([rf]))
        result = p.map(mp_worker_wrapper, izip(obs, mrf))
        p.close()
        p.join()
        data['ML_pred_3d_err'][test['IDX']] = result

        print(i)
        i+=1


    return data

def mp_pred_ints(obs, mrf):
    preds = []
    for pred in model.estimators_:
        try:
            preds.append(pred.predict(obs[:,np.newaxis]))
        except ValueError:
            preds.append(pred.predict(obs.reshape(1,-1)))

    #err_down = mrf - np.std(preds)
    #err_up = mrf + np.std(preds)

    # Bessel corrected std
    err = np.std(preds, ddof=1)

    return err

def mp_worker_wrapper(args):
    return mp_pred_ints(*args)

if __name__ == "__main__":

    ### Perfect ###
    ################
    with hdf.File('./result_targetedPerfect.hdf5', 'r') as f:
        dset  = f[f.keys()[0]]
        perfect = dset['IDX', 'HALOID', 'ZSPEC', 'M200c', 'NGAL', 'LOSVD',
        'LOSVD_err', 'MASS']
        #data = dset.value

    ### Targeted ###
    ################
    with hdf.File('./result_targetedRealistic.hdf5', 'r') as f:
        dset  = f[f.keys()[0]]
        target = dset['IDX', 'HALOID', 'ZSPEC', 'M200c', 'NGAL', 'LOSVD',
        'LOSVD_err', 'MASS']
        #data = dset.value


    # this finds the galaxies that were observed with the targeted realistic
    # observations and then computes all of their masses using the perfect
    # observations of the same clusters. This might work better for comparisons
    # down the line. Right now there is something funny going on with things.
    idx = find_indices(perfect['HALOID'], target['HALOID'])
    idx = np.ravel(idx)
    data = perfect[idx]
    data['IDX'] = target['IDX']

    # add the extra fields
    data = updateArray(data)

    # You have to clean the data here. This is almost certainly from the fact
    # that some of the HALOIDS are repeated at different redshifts. I have a
    # prior on the LOSVD calculation which will limit the LOSVD to a maxium.
    # Because the clusters are so far apart the LOSVD is super high.

    mask = ((np.log10(data['LOSVD']) > 3.12 ) & (data['M200c'] < 10**14.5) |
        (data['LOSVD'] < 50))
    maskedDataT = data[~mask]
    badData = data[mask]

#    sl_targeted = splitData(maskedDataT, 0.3)
#    data = addMasses(data, sl_targeted)
#    with hdf.File('targetedPerfect_MLmasses_realisticOnly.hdf5', 'w') as f:
#        f['predicted masses'] = data
#        f.flush()

    ### Survey ###
    ##############
    print 'SURVEY!'
    with hdf.File('./surveyCompletePerfect.hdf5', 'r') as f:
        dset  = f[f.keys()[0]]
        data = dset['IDX', 'HALOID', 'ZSPEC', 'M200c', 'NGAL', 'LOSVD',
        'LOSVD_err', 'MASS']
        #data = dset.value

    # add the extra fields
    data = updateArray(data)

    # You have to clean the data here. This is almost certainly from the fact
    # that some of the HALOIDS are repeated at different redshifts. I have a
    # prior on the LOSVD calculation which will limit the LOSVD to a maxium.
    # Because the clusters are so far apart the LOSVD is super high.
    mask = ((np.log10(data['LOSVD']) > 3.12 ) & (data['M200c'] < 10**14.5) |
        (data['LOSVD'] < 50))
    maskedDataS = data[~mask]
    badData = data[mask]

    sl_survey = splitData(maskedDataS, 0.3)
    data = addMasses(data, sl_survey)
    with hdf.File('surveyCompletePerfect_MLmasses.hdf5', 'w') as f:
        f['predicted masses'] = data
        f.flush()
