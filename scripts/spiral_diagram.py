# -*- coding: utf-8 -*-
"""
Created on Sun May  7 10:19:37 2023

@author: sbamford
"""


import matplotlib.pyplot as plt
import numpy as np

theta = 0
rotation = 0.001
targetDist = 5
xs = []
ys = []
xsSpiral = []
ysSpiral = []
count = 0
cumDist = 0
xPrev = 0
yPrev = 0
while count < 100:
    theta = theta + rotation
    x = theta * np.cos(theta)
    y = theta * np.sin(theta)
    dist = np.sqrt((x - xPrev) ** 2 + (y - yPrev) ** 2)
    cumDist += dist
    xPrev = x
    yPrev = y
    theta = theta + rotation
    if count > 0:
        xsSpiral.append(x)
        ysSpiral.append(y)
    if cumDist >= targetDist:
        xs.append(x)
        ys.append(y)
        count += 1
        cumDist = 0

plt.close("all")
ax = plt.subplot()
ax.plot(xsSpiral, ysSpiral, '-')
ax.plot(xs, ys, 'o', markersize=20, markeredgecolor='black', markeredgewidth=1, markerfacecolor='white')
ax.set_aspect('equal')
for idx in range(100):
    ax.text(xs[idx], ys[idx], str(idx + 1), horizontalalignment='center',
     verticalalignment='center')