# -*- coding: utf-8 -*-
"""
For a list of files, 
where each file has (max) one plain-text token on each line,
print the corresponding addresses as a list of decimal numbers 
with the polarity as a suffix, 
and create a histogram of addresses.

The tokens are:
    0: address-bit 0
    1: address-bit 1
    2: polarity 'flood'
    3: polarity 'ebb'    
"""

import numpy as np
import os
import matplotlib.pyplot as plt

def convertFile(file):
    addresses = []
    addressStrings = []
    bits = []
    dd = 0
    with open(file, 'r') as fileOpened:
        for line in fileOpened:
            dd += 1
            print(dd)
            try:
                token = int(line[0])
                if token < 2:
                    bits.append(token)
                if token >= 2:
                    bits.append(1)
                    bits.reverse()
                    address = 0
                    for bit in bits:
                        address = (address << 1) | bit
                    if address == 22:
                        x = 1
                    bits = []
                    polarityString = 'f' if token == 2 else 'e'
                    addresses.append(address + (token - 2) * 0.5)
                    addressStrings.append(str(address) + polarityString)
            except ValueError: # Handle blank lines
                continue
    return addresses, addressStrings

pathToRepo = "C:\\repos\\tactile_repos\\snowball" 
filesToConvert = [
    os.path.join(pathToRepo, 'incrementer\\input_L.dec'),
    os.path.join(pathToRepo, 'decrementer\\input_L.dec'),
    os.path.join(pathToRepo, 'outputs\\output_inc.dec'),
    os.path.join(pathToRepo, 'outputs\\output_incX8.dec'),
    os.path.join(pathToRepo, 'outputs\\output_decR.dec'),
    ]

for file in filesToConvert:
    addresses, addressStrings = convertFile(file)
    # Perform conversion
    # Print the result
    print(file)
    print(' '.join(addressStrings))
    print()
    
#%% Generate histogram for single encoder experiment

addressEventsInFile = os.path.join(pathToRepo, 'incrementer\\input_L.dec')
addressesIn, addressStringsIn = convertFile(addressEventsInFile)
sensorIn = [0, 0.5] * 32 #  Shortcut to reading in the file 'input_D.dec'
addressEventsOutFile = os.path.join(pathToRepo, 'outputs\\output_inc.dec')
addressesOut, addressStringsOut = convertFile(addressEventsOutFile)

allAddresses = addressesIn + sensorIn + addressesOut

numBins = int((max(allAddresses) - min(allAddresses)) * 2) + 1
binRange = (min(allAddresses) - 0.25, max(allAddresses) + 0.25)
countsIn, _ = np.histogram(addressesIn + sensorIn, bins=numBins, range=binRange)
countsOut, _ = np.histogram(addressesOut, bins=numBins, range=binRange)
addressRange = np.linspace(min(allAddresses), max(allAddresses), numBins)

plt.close('all')
fig, ax = plt.subplots()
ax.bar(addressRange+0.05, height=countsOut, width=0.25, color='r')
ax.bar(addressRange-0.05, height=countsIn, width=0.25, color='b')
maxY = max(max(countsIn), max(countsOut)) + 1
plt.yticks(list(range(0, maxY, 4)))
addressStringsSequence = [(str(int(x)) if x > 0.5 else '')
                          + ('e' if np.mod(x, 1) == 0.5 else 'f') 
                          for x in addressRange]
plt.xticks(addressRange, addressStringsSequence)
ax.tick_params(axis='y', which='major', labelsize=14)
ax.tick_params(axis='x', which='major', labelsize=14, rotation=60)
plt.plot([0.75, 0.75], [0, maxY], '--k')
        
        
#%% Generate histogram for encoder array experiment

sensorIn = [0, 0.5] * 32 #  Shortcut to reading in the file 'input_D.dec'
addressEventsOutFile = os.path.join(pathToRepo, 'outputs\\output_incX8.dec')
addressesOut, addressStringsOut = convertFile(addressEventsOutFile)

allAddresses = sensorIn + addressesOut

numBins = int((max(allAddresses) - min(allAddresses)) * 2) + 1
binRange = (min(allAddresses) - 0.25, max(allAddresses) + 0.25)
countsIn, _ = np.histogram(sensorIn, bins=numBins, range=binRange)
countsOut, _ = np.histogram(addressesOut, bins=numBins, range=binRange)
addressRange = np.linspace(min(allAddresses), max(allAddresses), numBins)

plt.close('all')
fig, ax = plt.subplots()
ax.bar(addressRange+0.05, height=countsOut, width=0.25, color='r')
ax.bar(addressRange-0.05, height=countsIn, width=0.25, color='b')
maxY = max(max(countsIn), max(countsOut)) + 1
plt.yticks(list(range(0, maxY, 4)))
addressStringsSequence = [(str(int(x)) if x > 0.5 else '')
                          + ('e' if np.mod(x, 1) == 0.5 else 'f') 
                          for x in addressRange]
plt.xticks(addressRange, addressStringsSequence)
ax.tick_params(axis='y', which='major', labelsize=14)
ax.tick_params(axis='x', which='major', labelsize=14, rotation=60)
plt.plot([0.75, 0.75], [0, maxY], '--k')
        
        