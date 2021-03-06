import pylab as pyl
from astLib import astStats
from sklearn.ensemble import RandomForestRegressor
from sklearn.cross_validation import train_test_split
import h5py as hdf

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

f = hdf.File('result_targetedIdeal.hdf5', 'r')
dset  = f[f.keys()[0]]
data = dset.value
f.close()
mask = (pyl.log10(data['LOSVD']) > 3.12 ) & (data['M200c'] < 10**14.5)
maskedData = data[~mask]
badData = data[mask]
train, test = train_test_split(maskedData, test_size=0.3)

# plot one to one lines
ax1.plot([12,15], [12,15], c='k')
ax2.plot([12,15], [12,15], c='k')
ax3.plot([12,15], [12,15], c='k')
ax4.plot([12,15], [12,15], c='k')
ax1s.axhline(0)
ax2s.axhline(0)
ax3s.axhline(0)
ax4s.axhline(0)

# now for the plotting
y_ = astStats.runningStatistic(pyl.log10(test['M200c']), pyl.log10(test['MASS']),
        pyl.percentile, binNumber=20, q=[16, 50, 84])
quants = pyl.array(y_[1])
ax1.plot(y_[0],quants[:,1], c='#348ABD')
ax1.fill_between(y_[0], quants[:,2], quants[:,0], facecolor='#348ABD',
    alpha=0.4, edgecolor='#348ABD')
err = calc_err(test['MASS'], test['M200c'])
y_ = astStats.runningStatistic(pyl.log10(test['M200c']), err, pyl.percentile,
        binNumber=20, q=[16, 50, 84])
quants = pyl.array(y_[1])
ax1s.plot(y_[0],quants[:,1], c='#348ABD')
ax1s.fill_between(y_[0], quants[:,2], quants[:,0], facecolor='#348ABD',
    alpha=0.4, edgecolor='#348ABD')


rf = RandomForestRegressor(n_estimators=1000, min_samples_leaf=1, verbose=1)
X = pyl.log10(train['M200c'])

############
#### 1d ####
############
y = pyl.column_stack([pyl.log10(train['LOSVD'])])
rf.fit(y, X)
obs = pyl.column_stack([pyl.log10(test['LOSVD'])])
mrf = rf.predict(obs)
y_ = astStats.runningStatistic(pyl.log10(test['M200c']), mrf,
        pyl.percentile, binNumber=20, q=[16, 50, 84])
quants = pyl.array(y_[1])
ax2.plot(y_[0],quants[:,1], c='#7A68A6')
ax2.fill_between(y_[0], quants[:,2], quants[:,0], facecolor='#7A68A6',
    alpha=0.4, edgecolor='#7A68A6')
err = calc_err(10**mrf, test['M200c'])
y_ = astStats.runningStatistic(pyl.log10(test['M200c']), err, pyl.percentile,
        binNumber=20, q=[16, 50, 84])
quants = pyl.array(y_[1])
ax2s.plot(y_[0],quants[:,1], c='#7A68A6')
ax2s.fill_between(y_[0], quants[:,2], quants[:,0], facecolor='#7A68A6',
    alpha=0.4, edgecolor='#7A68A6')

#############
#### 2d #####
#############
y = pyl.column_stack([pyl.log10(train['LOSVD']), train['ZSPEC']])
rf.fit(y, X)
obs = pyl.column_stack([pyl.log10(test['LOSVD']), test['ZSPEC']])
mrf = rf.predict(obs)
y_ = astStats.runningStatistic(pyl.log10(test['M200c']), mrf,
        pyl.percentile, binNumber=20, q=[16, 50, 84])
quants = pyl.array(y_[1])
ax3.plot(y_[0],quants[:,1], c='#CF4457')
ax3.fill_between(y_[0], quants[:,2], quants[:,0], facecolor='#CF4457',
    alpha=0.4, edgecolor='#CF4457')
err = calc_err(10**mrf, test['M200c'])
y_ = astStats.runningStatistic(pyl.log10(test['M200c']), err, pyl.percentile,
        binNumber=20, q=[16, 50, 84])
quants = pyl.array(y_[1])
ax3s.plot(y_[0],quants[:,1], c='#CF4457')
ax3s.fill_between(y_[0], quants[:,2], quants[:,0], facecolor='#CF4457',
    alpha=0.4, edgecolor='#CF4457')

##############
##### 3d #####
##############
y = pyl.column_stack([pyl.log10(train['LOSVD']), train['ZSPEC'], train['NGAL']])
rf.fit(y, X)
obs = pyl.column_stack([pyl.log10(test['LOSVD']), test['ZSPEC'], test['NGAL']])
mrf = rf.predict(obs)

y_ = astStats.runningStatistic(pyl.log10(test['M200c']), mrf,
        pyl.percentile, binNumber=20, q=[16, 50, 84])
quants = pyl.array(y_[1])
ax4.plot(y_[0],quants[:,1], c='#E24A33')
ax4.fill_between(y_[0], quants[:,2], quants[:,0], facecolor='#E24A33',
    alpha=0.4, edgecolor='#E24A33')
err = calc_err(10**mrf, test['M200c'])
y_ = astStats.runningStatistic(pyl.log10(test['M200c']), err, pyl.percentile,
        binNumber=20, q=[16, 50, 84])
quants = pyl.array(y_[1])
ax4s.plot(y_[0],quants[:,1], c='#E24A33')
ax4s.fill_between(y_[0], quants[:,2], quants[:,0], facecolor='#E24A33',
    alpha=0.4, edgecolor='#E24A33')


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
ax2.text(14, 12.25, '$ML_{\sigma}$', fontsize=18, horizontalalignment='center')
ax3.text(14, 12.25, '$ML_{\sigma, z}$', fontsize=18,
    horizontalalignment='center')
ax4.text(14, 12.25, '$ML_{\sigma, z, Ngal}$', fontsize=18,
        horizontalalignment='center')
