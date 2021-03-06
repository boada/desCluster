import pylab as pyl
from astLib import astStats
from sklearn.cross_validation import train_test_split
from sklearn.metrics import median_absolute_error, mean_squared_error
import h5py as hdf
from prob_propigator import prob1d
from prob_propigator_3d import prob2d
from prob_propigator_4d import prob3d


def calc_err(pred, true):
    return (pred - true)/true

golden_mean = (pyl.sqrt(5.)-1.0)/2.0
f = pyl.figure(1, figsize=(10,10*golden_mean))

ax1 = pyl.subplot2grid((3,4), (0,0), rowspan=2)
ax2 = pyl.subplot2grid((3,4), (0,1), rowspan=2, sharex=ax1)
ax3 = pyl.subplot2grid((3,4), (0,2), rowspan=2, sharex=ax1, sharey=ax2)
ax4 = pyl.subplot2grid((3,4), (0,3), rowspan=2, sharex=ax1, sharey=ax2)

# now for the bottom bits
ax1s = pyl.subplot2grid((3,4), (2,0))
ax2s = pyl.subplot2grid((3,4), (2,1), sharex=ax1s)
ax3s = pyl.subplot2grid((3,4), (2,2), sharex=ax1s, sharey=ax2s)
ax4s = pyl.subplot2grid((3,4), (2,3), sharex=ax1s, sharey=ax2s)

ax2.set_yticklabels([])
ax1.set_xticklabels([])
ax2s.set_yticklabels([])


### Targeted ###
################
f = hdf.File('result_targetedIdeal.hdf5', 'r')
dset  = f[f.keys()[0]]
data = dset.value
f.close()
mask = (pyl.log10(data['LOSVD']) > 3.12 ) & (data['M200c'] < 10**14.5)
maskedDataT = data[~mask]
badData = data[mask]
trainT, testT = train_test_split(maskedDataT, test_size=0.3)

### Survey ###
##############
f = hdf.File('surveyComplete.hdf5', 'r')
dset  = f[f.keys()[0]]
data = dset.value
f.close()
mask = (pyl.log10(data['LOSVD']) > 3.12 ) & (data['M200c'] < 10**14.5)
maskedDataS = data[~mask]
badData = data[mask]
trainS, testS = train_test_split(maskedDataS, test_size=0.3)

# plot one to one lines
ax1.plot([12,15.5], [12,15.5], c='k', zorder=0)
ax2.plot([12,15.5], [12,15.5], c='k', zorder=0)
ax3.plot([12,15.5], [12,15.5], c='k', zorder=0)
ax4.plot([12,15.5], [12,15.5], c='k', zorder=0)
ax1s.axhline(0)
ax2s.axhline(0)
ax3s.axhline(0)
ax4s.axhline(0)

# now for the plotting
###################
#### Power Law ####
###################
for d, c, style in zip([maskedDataT, maskedDataS], ['#7A68A6', '#188487'],
        ['-', '--']):
    y_ = astStats.runningStatistic(pyl.log10(d['M200c']),
            pyl.log10(d['MASS']),
            pyl.percentile, binNumber=20, q=[16, 50, 84])
    quants = pyl.array(y_[1])
    ax1.plot(y_[0],quants[:,1], style, c=c)
    ax1.fill_between(y_[0], quants[:,2], quants[:,0], facecolor=c,
        alpha=0.4, edgecolor=c)
    err = calc_err(d['MASS'], d['M200c'])
    y_ = astStats.runningStatistic(pyl.log10(d['M200c']), err,
            pyl.percentile, binNumber=20, q=[16, 50, 84])
    quants = pyl.array(y_[1])
    ax1s.plot(y_[0],quants[:,1], style, c=c)
    ax1s.fill_between(y_[0], quants[:,2], quants[:,0], facecolor=c,
        alpha=0.4, edgecolor=c)
    print('MAE', median_absolute_error(pyl.log10(d['M200c']),
                pyl.log10(d['MASS'])))
    print('RMSE', pyl.sqrt(mean_squared_error(pyl.log10(d['M200c']),
                    pyl.log10(d['MASS']))))
### Add Legend ###
##################
line1 = pyl.Line2D([], [], ls='-', color='#7A68A6')
line2 = pyl.Line2D([], [], ls='--', color='#188487')
ax1.legend((line1, line2), ('Targeted', 'Survey'), loc=2)


for train, test, c, style in zip([trainT, trainS], [testT, testS], ['#7A68A6',
    '#188487'], ['-', '--']):

    ############
    #### 1d ####
    ############
    print('1d')
    mrf = prob1d(train, test)['MASS']
    mask = pyl.where(pyl.isnan(mrf))[0]
    mrf = pyl.delete(mrf, mask)
    test2 = pyl.delete(test, mask)
    print(mrf.size, test2.size)

    y_ = astStats.runningStatistic(pyl.log10(test2['M200c']), mrf,
            pyl.percentile, binNumber=20, q=[16, 50, 84])
    quants = pyl.array(y_[1])
    ax2.plot(y_[0],quants[:,1], style, c=c)
    ax2.fill_between(y_[0], quants[:,2], quants[:,0], facecolor=c,
        alpha=0.4, edgecolor=c)
    err = calc_err(10**mrf, test2['M200c'])
    y_ = astStats.runningStatistic(pyl.log10(test2['M200c']), err,
            pyl.percentile, binNumber=20, q=[16, 50, 84])
    quants = pyl.array(y_[1])
    ax2s.plot(y_[0],quants[:,1], style, c=c)
    ax2s.fill_between(y_[0], quants[:,2], quants[:,0], facecolor=c,
        alpha=0.4, edgecolor=c)
    print('MAE', median_absolute_error(pyl.log10(test2['M200c']), mrf))
    print('RMSE', pyl.sqrt(mean_squared_error(pyl.log10(test2['M200c']),
            mrf)))
    #############
    #### 2d #####
    #############
    print('2d')
    mrf = prob2d(train, test)['MASS']
    mask = pyl.where(pyl.isnan(mrf))[0]
    mrf = pyl.delete(mrf, mask)
    test2 = pyl.delete(test, mask)
    print(mrf.size, test2.size)

    y_ = astStats.runningStatistic(pyl.log10(test2['M200c']), mrf,
            pyl.percentile, binNumber=20, q=[16, 50, 84])
    quants = pyl.array(y_[1])
    ax3.plot(y_[0],quants[:,1], style, c=c)
    ax3.fill_between(y_[0], quants[:,2], quants[:,0], facecolor=c,
        alpha=0.4, edgecolor=c)
    err = calc_err(10**mrf, test2['M200c'])
    y_ = astStats.runningStatistic(pyl.log10(test2['M200c']), err,
            pyl.percentile, binNumber=20, q=[16, 50, 84])
    quants = pyl.array(y_[1])
    ax3s.plot(y_[0],quants[:,1], style, c=c)
    ax3s.fill_between(y_[0], quants[:,2], quants[:,0], facecolor=c,
        alpha=0.4, edgecolor=c)
    print('MAE', median_absolute_error(pyl.log10(test2['M200c']), mrf))
    print('RMSE', pyl.sqrt(mean_squared_error(pyl.log10(test2['M200c']),
            mrf)))
    ##############
    ##### 3d #####
    ##############
    print('3d')
    mrf = prob3d(train, test)['MASS']
    mask = pyl.where(pyl.isnan(mrf))[0]
    mrf = pyl.delete(mrf, mask)
    test2 = pyl.delete(test, mask)
    print(mrf.size, test2.size)

    y_ = astStats.runningStatistic(pyl.log10(test2['M200c']), mrf,
            pyl.percentile, binNumber=20, q=[16, 50, 84])
    quants = pyl.array(y_[1])
    ax4.plot(y_[0],quants[:,1], style, c=c)
    ax4.fill_between(y_[0], quants[:,2], quants[:,0], facecolor=c,
        alpha=0.4, edgecolor=c)
    err = calc_err(10**mrf, test2['M200c'])
    y_ = astStats.runningStatistic(pyl.log10(test2['M200c']), err,
            pyl.percentile, binNumber=20, q=[16, 50, 84])
    quants = pyl.array(y_[1])
    ax4s.plot(y_[0],quants[:,1], style, c=c)
    ax4s.fill_between(y_[0], quants[:,2], quants[:,0], facecolor=c,
        alpha=0.4, edgecolor=c)
    print('MAE', median_absolute_error(pyl.log10(test2['M200c']), mrf))
    print('RMSE', pyl.sqrt(mean_squared_error(pyl.log10(test2['M200c']),
            mrf)))

#### tweak ####
ax1.set_xticks([12,13,14,15])
ax2.set_xticks([12,13,14,15])
ax2s.set_xticks([12,13,14,15])
#ax2s.set_yticks([0.04,0.02,0,-0.02, -0.04])
#ax1s.set_yticks([0.04,0.02,0,-0.02, -0.04])
ax1.set_ylim(ax2.get_ylim())
ax1s.set_ylim(ax2s.get_ylim())

ax1.set_ylabel('Log $M_{pred}$ $(M_\odot)$')
ax1s.set_ylabel('$\epsilon$')
ax1s.set_xlabel('Log M $(M_\odot)$')
ax2s.set_xlabel('Log M $(M_\odot)$')
ax3s.set_xlabel('Log M $(M_\odot)$')
ax4s.set_xlabel('Log M $(M_\odot)$')

ax1.text(14, 12.25, 'Power Law', fontsize=18, horizontalalignment='center')
ax2.text(14, 12.25, '$Prob_{\sigma}$', fontsize=18, horizontalalignment='center')
ax3.text(14, 12.25, '$Prob_{\sigma, z}$', fontsize=18,
    horizontalalignment='center')
ax4.text(14, 12.25, '$Prob_{\sigma, z, Ngal}$', fontsize=18,
        horizontalalignment='center')
