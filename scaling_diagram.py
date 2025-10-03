# -*- coding: utf-8 -*-
"""
Create scaling diagram based on numbers manually brought here from analysis 
of snbl vs paer ams/spectre simulations 
"""

import numpy as np
import matplotlib.pyplot as plt

pairs = [
    5,
    16,
    50,
    158,
    500,
]

inputs = np.array(pairs) * 2

transistors_snbl = [
    1840,
    5890,
    18400,
    58100,
    184000,
]

transistors_paer_matched = [
1580,
3900,
13400,
55800,
144000,
]

transistors_paer_nominal = [
1800,
3420,
11200,
45100,
113000,
]

latency_snbl = [
29.4,
143,
614,
2620,
10700,
]

latency_paer_matched = [
12.1,
41.5,
131,
611,
2260,
]

latency_paer_nominal = [
12.2,
41.2,
130,
607,
2240,
]

energy_snbl = [
9.19,
43.4,
187,
777,
3080,
]

energy_paer_matched = [
7.97,
17.4,
47.8,
131,
343
]

energy_paer_nominal = [
10.4,
12.8,
18.9,
23.5,
27
]

def loglog_slope(x, y):
    """
    Fit log(y) = m * log(x) + c and return rounded m
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    # Filter invalid points
    mask = (x > 0) & (y > 0) & np.isfinite(x) & np.isfinite(y)
    if mask.sum() < 2:
        raise ValueError("Need at least two valid (x>0, y>0, finite) points.")

    x = x[mask]
    y = y[mask]

    lx, ly = np.log10(x), np.log10(y)

    # Linear regression
    coeffs, cov = np.polyfit(lx, ly, 1, cov=True)
    m, _ = coeffs

    # Helper: round to 3 significant figures
    def round_sf(val, sf=3):
        if val == 0 or not np.isfinite(val):
            return val
        return float(f"{val:.{sf}g}")

    return round_sf(m)

plt.close('all')

linewidth = 1

fig, ax = plt.subplots()
legend = []

def add_line(data, linespec, desc):
    ax.loglog(inputs, data, linespec, linewidth=linewidth)
    legend.append(desc + ', grad=' + str(loglog_slope(inputs, data)))


add_line(transistors_snbl, '-or', 'Transistor count - This work')
add_line(transistors_paer_matched, '--or', 'Transistor count - P-AER, matched capacity')
add_line(transistors_paer_nominal, '--xr', 'Transistor count - P-AER, slack=1')

add_line(latency_snbl, '-og', 'Latency(ns) - This work')
add_line(latency_paer_matched, '--og', 'Latency (ns) - P-AER, matched capacity')
add_line(latency_paer_nominal, '--xg', 'Latency (ns) - P-AER, slack=1')

add_line(energy_snbl, '-ob', 'Energy (pJ/event) - This work')
add_line(energy_paer_matched, '--ob', 'Energy (pJ/event) - P-AER, matched capacity')
add_line(energy_paer_nominal, '--xb', 'Energy (pJ/event) - P-AER, slack=1')

ax.set_title('Scaling trends')
ax.set_ylabel('')
ax.legend(legend)
ax.set_axisbelow(True)
ax.minorticks_on()
ax.grid(True, which='major', color='0.6', linewidth=0.8)
ax.grid(True, which='minor', color='0.85', linewidth=0.5)
ax.set_xlabel('Inputs')




