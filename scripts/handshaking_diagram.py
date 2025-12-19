# -*- coding: utf-8 -*-
"""
Created on Mon Sep 23 14:15:43 2024

@author: sbamford
"""

import numpy as np
import matplotlib.pyplot as plt

end = 50
a = np.zeros(end)
b = np.zeros(end)
ack = np.zeros(end)


a[5:15] = 1
ack[10:20] = 1

b[30:40] = 1
ack[35:45] = 1

plt.close('all')
fig, ax = plt.subplots()
ax.plot(a + 3, 'b')
ax.plot(b + 1.5, 'b')
ax.plot(ack, 'r')
ax.set_yticks([0.5, 2, 3.5])
ax.set_yticklabels(['Acknowledge', 'Request b', 'Request a'], size=20)
ax.set_xticks([])
ax.set_xlabel('Time (arbitrary units)', size=20)


fig.tight_layout()