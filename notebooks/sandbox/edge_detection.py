# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# ### Last time step at the surface

# <codecell>

from netCDF4 import Dataset

url = 'http://omgsrv1.meas.ncsu.edu:8080/thredds/dodsC/fmrc/sabgom/'
url += 'SABGOM_Forecast_Model_Run_Collection_best.ncd'

nc = Dataset(url)
temp = nc.variables['temp']
if temp.standard_name == 'sea_water_potential_temperature':
    temp = temp[-1, -1, ...]

# <codecell>

import matplotlib.pyplot as plt

figsize = (7, 7)
cbarkw = dict(shrink=0.6, extend='both')

fig, ax = plt.subplots(figsize=figsize)

i = ax.imshow(temp, origin='lower')
cbar = fig.colorbar(i, **cbarkw)
_ = ax.axis('off')

# <codecell>

import cv2
import numpy as np

def matplotlib_to_opencv(i):
    image = i._rgbacache
    # RGB to BGR.
    r, g, b, a = cv2.split(image)
    return np.flipud(cv2.merge([b, g, r, a]))

image = matplotlib_to_opencv(i)
img = cv2.GaussianBlur(image, (3, 3), 0)
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

fig, ax = plt.subplots(figsize=figsize)
ax.imshow(gray, cmap=plt.cm.gray)
_ = ax.axis('off')

# <markdowncell>

# ### Sobel

# <codecell>

ddepth = cv2.CV_16S
kw = dict(ksize=3, scale=1, delta=0, borderType=cv2.BORDER_DEFAULT)

# Gradient-X.
grad_x = cv2.Sobel(gray, ddepth, 1, 0, **kw)

# Gradient-Y.
grad_y = cv2.Sobel(gray, ddepth, 0, 1, **kw)

# Converting back to uint8.
abs_grad_x = cv2.convertScaleAbs(grad_x)
abs_grad_y = cv2.convertScaleAbs(grad_y)

sobel = cv2.addWeighted(abs_grad_x, 0.5, abs_grad_y, 0.5, 0)
sobel_no_blend = cv2.add(abs_grad_x, abs_grad_y)

# <markdowncell>

# ### Scharr

# <codecell>

# Gradient-X
grad_x = cv2.Scharr(gray, ddepth, 1, 0)

# Gradient-Y.
grad_y = cv2.Scharr(gray, ddepth, 0, 1)

# Converting back to uint8.
abs_grad_x = cv2.convertScaleAbs(grad_x)
abs_grad_y = cv2.convertScaleAbs(grad_y)

scharr = cv2.addWeighted(abs_grad_x, 0.5, abs_grad_y, 0.5, 0)
scharr_no_blend = cv2.add(abs_grad_x, abs_grad_y)

# <codecell>

def turn_off_labels(ax):
    ax.axes.get_xaxis().set_visible(False)
    ax.axes.get_yaxis().set_visible(False)


kw = dict(cmap=plt.cm.Greys_r)

fig, ((ax0, ax1), (ax2, ax3)) = plt.subplots(ncols=2, nrows=2, figsize=(9, 8))
ax0.imshow(sobel, **kw)
ax0.set_title('Sobel')

ax1.imshow(scharr, **kw)
ax1.set_title('Scharr')

ax2.imshow(sobel_no_blend, **kw)
ax2.set_title('Sobel no weights')

ax3.imshow(scharr_no_blend, **kw)
ax3.set_title('Scharr no weights')

map(turn_off_labels, (ax0, ax1, ax2, ax3))
fig.tight_layout(h_pad=0.1, w_pad=0.5)

# <markdowncell>

# ### Laplacian

# <codecell>

ddepth = cv2.CV_16S
kw = dict(ksize=3, scale=1, delta=0, borderType=cv2.BORDER_DEFAULT)

gray_lap = cv2.Laplacian(gray, ddepth, **kw)
laplacian = cv2.convertScaleAbs(gray_lap)

fig, ax = plt.subplots(figsize=figsize)
ax.imshow(laplacian, cmap=plt.cm.Greys_r)
_ = ax.axis('off')

# <markdowncell>

# ### Interactive Canny

# <codecell>

from IPython.display import display
from IPython.html.widgets import interact, fixed

def canny_threshold(image, gray, threshold=0, ratio=3, ksize=3):
    detected_edges = cv2.GaussianBlur(gray, (3, 3), 0)
    detected_edges = cv2.Canny(detected_edges, threshold,
                               threshold*ratio,
                               apertureSize=ksize)
    # Just add some colours to edges from original data.
    mask = np.ma.masked_equal(detected_edges, 0).mask
    img = np.ma.masked_array(np.flipud(temp), mask)
    
    fig, ax = plt.subplots(figsize=figsize)
    cs = ax.imshow(img)
    cbar = fig.colorbar(cs, ax=ax, **cbarkw)
    ax.axis('off')
    plt.show()

lims = (0, 100)
w = interact(canny_threshold, threshold=lims,
             image=fixed(image), gray=fixed(gray),
             ratio=fixed(3), ksize=fixed(3))

display(w)

# <markdowncell>

# ### Contour problem

# <codecell>

from skimage import measure

contours = measure.find_contours(temp, 28.1)

fig, ax = plt.subplots(figsize=figsize)
kw = dict(interpolation='nearest', cmap=plt.cm.gray,
          origin='lower')
ax.imshow(temp, **kw)

for n, contour in enumerate(contours):
    ax.plot(contour[:, 1], contour[:, 0], linewidth=2, color='r')

_ = ax.axis('off')

