import pylab as pyl
import h5py as hdf
from addHaloInfo import find_indices_single
from scipy import stats

def scatterDensity(ax, xdat, ydat, extent, bins=[50,50], thresh=3):

    hh, locx, locy = pyl.histogram2d(xdat, ydat, range=extent, bins=bins)
    posx = pyl.digitize(xdat, locx)
    posy = pyl.digitize(ydat, locy)

    # finds the bins which contain points. posx = 0 for points outside "range"
    ind = (posx > 0) & (posx <= bins[0]) & (posy > 0) & (posy <= bins[1])
    # values of histogram with points in the bins.
    hhsub = hh[posx[ind] - 1, posy[ind] - 1]

    xdat1 = xdat[ind][hhsub < thresh] # low density points
    ydat1 = ydat[ind][hhsub < thresh]
    hh[hh < thresh] = pyl.nan # fill the areas with low density by NaNs

    ax.scatter(xdat1, ydat1, s=20, c='0.8')
    ax.imshow(pyl.log10(hh.T), cmap='gray_r',
            extent=pyl.array(extent).flatten(),
            interpolation='nearest')


fig, ax = pyl.subplots(1, 2, squeeze=True)

with hdf.File('out1204878_hetdex.hdf5', 'r') as f:
    dset = f[f.keys()[0]]
    data = dset.value

# now we need to make a mask for the data
#mask1 = (data['M200']/0.72 >= 1e13) & (data['Z'] < 0.5)
#mask2 = (data['g'] < 22) | (data['Oii'] > 3.5)
#mask = mask1 & mask2

#dataMasked = data[mask]
dataMasked = data

hids = pyl.unique(dataMasked['HALOID'])

halos = find_indices_single(dataMasked['HALOID'], hids)

xdat = dataMasked['VRMS'][halos]/pyl.sqrt(3)
ydat = dataMasked['LOSVD'][halos]

# filter out NaNs
xdat = xdat[~pyl.isnan(ydat)]
ydat = ydat[~pyl.isnan(ydat)]

# LOSVD comparison
scatterDensity(ax[0], xdat, ydat, extent=[[xdat.min(), xdat.max()],
    [ydat.min(), ydat.max()]])

# add 1-1 line, and best fit line
ax[0].plot([99,800],[99, 800], lw=2, c='#a60628', label='1:1')
slope, intercept, r_value, p_value, std_err = stats.linregress(xdat,ydat)
x = pyl.linspace(0,800)
line = slope*x + intercept
ax[0].plot(x, line, lw=2, c='#188487', label='Best Fit')

# adjust
ax[0].set_xlim(100,800)
ax[0].set_ylim(0,800)

# labels
ax[0].set_xlabel('$LOSVD_{True}$ ($km s^{-1})$')
ax[0].set_ylabel('$LOSVD_{Rec}$ ($km s^{-1})$')

# now the mass
xdat = dataMasked['M200'][halos]
ydat = dataMasked['MASS'][halos]
xdat = pyl.log10(xdat[~pyl.isnan(ydat) & (ydat != 0.0)])
ydat = pyl.log10(ydat[~pyl.isnan(ydat) & (ydat != 0.0)])

scatterDensity(ax[1], xdat, ydat, extent=[[xdat.min(), xdat.max()],
    [ydat.min(), ydat.max()]])

# add 1-1 line, and best fit line
ax[1].plot([12.5,15],[12.5, 15], lw=2, c='#a60628', label='1:1')
slope, intercept, r_value, p_value, std_err = stats.linregress(xdat,ydat)
x = pyl.linspace(12.5,15)
line = slope*x + intercept
ax[1].plot(x, line, lw=2, c='#188487', label='Best Fit')

ax[1].set_xlim(12.75, 14.5)
ax[1].set_ylim(9,15)

ax[1].set_xlabel('Log $M_{200\!,True}$ ($M_{\odot})$')
ax[1].set_ylabel('Log $M_{200\!,Rec}$ ($M_{\odot})$')

pyl.show()
