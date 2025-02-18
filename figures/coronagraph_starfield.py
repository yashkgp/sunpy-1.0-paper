"""
===========================================================
Identifying stars in a STEREO/SECCHI COR2 coronagraph image
===========================================================

How to use the `Vizier star catalog <https://vizier.u-strasbg.fr>`_ to
identify bright points in a STEREO/SECCHI COR 2 image as stars.
As a bonus, we also identify Mars.
"""
import matplotlib.pyplot as plt

# astroquery is not a dependency of SunPy so will likely need to be
# installed.
from astroquery.vizier import Vizier
import astropy.units as u
from astropy.coordinates import SkyCoord, get_body_barycentric

import sunpy.map
from sunpy.coordinates import get_body_heliographic_stonyhurst, frames
from sunpy.net import helioviewer

###############################################################################
# Let's download a STEREO-A SECCHI COR2 image from Helioviewer which provide
# pre-processed images and load it into a Map.
hv = helioviewer.HelioviewerClient()
f = hv.download_jp2('2014/05/15 07:54', observatory='STEREO_A', instrument='SECCHI', detector='COR2')
cor2 = sunpy.map.Map(f)

###############################################################################
# To efficiently search the star field we need to know what stars are near the
# Sun as observed by STEREO. This can be found by find the difference vector
# between the Sun and the location of STEREO.
stereo = cor2.observer_coordinate.transform_to('icrs').cartesian
sun = get_body_barycentric('sun', time=cor2.date)
diff = sun - stereo
search_coord = SkyCoord(diff, frame='icrs')

###############################################################################
# Let's look up bright stars using the Vizier search capability provided by
# astroquery (note that this is not a required package of SunPy so you will likely
# need to install it). We will search the GAIA2 star catalog and only stars with magnitude
# brighter than 7.
vv = Vizier(columns=['**'], row_limit=-1, column_filters={'Gmag': '<7'}, timeout=1200)
vv.ROW_LIMIT = -1
result = vv.query_region(search_coord, radius=4 * u.deg, catalog='I/345/gaia2')

###############################################################################
# Now we load each star into a coordinate and transform it into the COR2
# image coordinates. Since we don't know the distance to each of these stars
# we will just put them very far away.
hpc_coords = []
for this_object in result[0]:
    tbl_crds = SkyCoord(this_object['RA_ICRS'] * u.deg, this_object['DE_ICRS'] * u.deg,
                        1e12 * u.km, frame='icrs', obstime=cor2.date)
    hpc_coords.append(tbl_crds.transform_to(
        frames.Helioprojective(observer=cor2.observer_coordinate)))

# get the location of mars
mars = get_body_heliographic_stonyhurst(
    'mars', cor2.date, observer=cor2.observer_coordinate)
mars_hpc = mars.transform_to(
    frames.Helioprojective(observer=cor2.observer_coordinate))

# now plot
fig = plt.figure(figsize=(5,5))
ax = fig.add_subplot(111, projection=cor2)

cor2.plot(axes=ax, vmin=0, vmax=600)
cor2.draw_limb()

ax.plot_coord(mars_hpc, 's', color='white',
              fillstyle='none', markersize=12, label='Mars')
for this_coord in hpc_coords:
    ax.plot_coord(this_coord, 'o', color='white', fillstyle='none')

lon, lat = ax.coords
lon.set_major_formatter('d.dd')
lat.set_major_formatter('d.dd')

ax.legend()
plt.savefig('fig_coronagraph_starfield.pdf')
