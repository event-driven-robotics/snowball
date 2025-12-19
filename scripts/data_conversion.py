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

pathToRepo = "/path/to/repo" # Change this

def convertFile(file):
    addresses = []
    addressStrings = []
    bits = []
    with open(file, 'r') as fileOpened:
        for line in fileOpened:
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
                    bits = []
                    polarityString = 'a' if token == 2 else 'b'
                    addresses.append(address + (token - 2) * 0.5)
                    addressStrings.append(str(address) + polarityString)
            except ValueError: # Handle blank lines
                continue
    return addresses, addressStrings
    
#%% Generate histogram for single encoder experiment

addressEventsInFile = os.path.join(pathToRepo, 'encoder\\input_addr.dec')
addressesIn, addressStringsIn = convertFile(addressEventsInFile)
print("Address-events in:")
print(' '.join(addressStringsIn))
print()

sensorIn = [0, 0.5] * 32 #  Shortcut to reading in the file 'input_D.dec'
addressEventsOutFile = os.path.join(pathToRepo, 'outputs\\output_enc_addr_attempt_2.dec')
addressesOut, addressStringsOut = convertFile(addressEventsOutFile)
print("Address-events out:")
print(' '.join(addressStringsOut))
print()

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
                          + ('b' if np.mod(x, 1) == 0.5 else 'a') 
                          for x in addressRange]
plt.xticks(addressRange, addressStringsSequence)
ax.tick_params(axis='y', which='major', labelsize=14)
ax.tick_params(axis='x', which='major', labelsize=14, rotation=60)
plt.plot([0.75, 0.75], [0, maxY], '--k')
plt.xlabel('Sensor address', fontsize=14)
plt.ylabel('Count of address-events', fontsize=14)  
        
fig.tight_layout()

#%% Generate histogram for encoder array experiment

sensorIn = [0, 0.5] * 32 #  Shortcut to reading in the file 'input_D.dec'
addressEventsOutFile = os.path.join(pathToRepo, 'outputs\\output_encX8_addr.dec')
addressesOut, addressStringsOut = convertFile(addressEventsOutFile)
print("Address-events out:")
print(' '.join(addressStringsOut))
print()

allAddresses = sensorIn + addressesOut

numBins = int((max(allAddresses) - min(allAddresses)) * 2) + 1
binRange = (min(allAddresses) - 0.25, max(allAddresses) + 0.25)
countsIn, _ = np.histogram(sensorIn, bins=numBins, range=binRange)
countsOut, _ = np.histogram(addressesOut, bins=numBins, range=binRange)
addressRange = np.linspace(min(allAddresses), max(allAddresses), numBins)

plt.close('all')
fig, ax = plt.subplots()
ax.bar(addressRange, height=countsOut, width=0.35, color='r')
ax.bar(addressRange, height=countsIn, width=0.35, color='b')
maxY = max(max(countsIn), max(countsOut)) + 1
plt.yticks(list(range(0, maxY, 4)))
addressStringsSequence = [(str(int(x)) if x > 0.5 else '')
                          + ('b' if np.mod(x, 1) == 0.5 else 'a') 
                          for x in addressRange]
plt.xticks(addressRange, addressStringsSequence)
ax.tick_params(axis='y', which='major', labelsize=14)
ax.tick_params(axis='x', which='major', labelsize=14, rotation=60)
plt.plot([0.75, 0.75], [0, maxY], '--k')
plt.xlabel('Sensor address', fontsize=14)
plt.ylabel('Count of address-events', fontsize=14)
        
#%% Generate histogram for halfway through encoder array experiment

addressSelected = []
countOfSensor1Events = 0
for address in addressesOut:
    addressSelected.append(int(address))
    if address < 2:
        countOfSensor1Events += 1
    if countOfSensor1Events == 64:
        break

numBins = int(max(addressSelected) - min(addressSelected)) + 1
binRange = (min(addressSelected) - 0.25, max(addressSelected) + 0.25)
countsOut, _ = np.histogram(addressSelected, bins=numBins, range=binRange)
addressRange = np.linspace(min(addressSelected), max(addressSelected), numBins)

plt.close('all')
fig, ax = plt.subplots()
ax.bar(addressRange, height=countsOut, width=0.8, color='r')
maxY = max(countsOut) + 1
plt.yticks(list(range(0, maxY, 4)))
ax.tick_params(axis='y', which='major', labelsize=14)
ax.tick_params(axis='x', which='major', labelsize=14, rotation=60)
plt.xlabel('Sensor address', fontsize=14)
plt.ylabel('Count of address-events out', fontsize=14)

print(countsOut)

#%% Generate histogram for decoder experiment

addressEventsInFile = os.path.join(pathToRepo, 'decoder\\input_addr.dec')
addressesIn, addressStringsIn = convertFile(addressEventsInFile)
print("Address-events in:")
print(' '.join(addressStringsIn))
print()

addressEventsOutFile = os.path.join(pathToRepo, 'outputs\\output_dec_addr.dec')
addressesOut, addressStringsOut = convertFile(addressEventsOutFile)
print("Address-events out:")
print(' '.join(addressStringsOut))
print()

localEventsOutFile = os.path.join(pathToRepo, 'outputs\\output_dec_local.dec')
localOut = [0, 0.5]  #  Shortcut to reading in the file 'output_decT.dec'
print("Local events out:")
print('f e') # Shortcut to reading that file
print()

allAddresses = addressesIn + localOut + addressesOut

numBins = int((max(allAddresses) - min(allAddresses)) * 2) + 1
binRange = (min(allAddresses) - 0.25, max(allAddresses) + 0.25)
countsIn, _ = np.histogram(addressesIn, bins=numBins, range=binRange)
countsOut, _ = np.histogram(addressesOut + localOut, bins=numBins, range=binRange)
addressRange = np.linspace(min(allAddresses), max(allAddresses), numBins)

plt.close('all')
fig, ax = plt.subplots()
ax.bar(addressRange+0.05, height=countsOut, width=0.25, color='r')
ax.bar(addressRange-0.05, height=countsIn, width=0.25, color='b')
maxY = max(max(countsIn), max(countsOut)) + 0.25
plt.yticks([0, 1])
addressStringsSequence = [(str(int(x)) if x > 0.5 else '')
                          + ('b' if np.mod(x, 1) == 0.5 else 'a') 
                          for x in addressRange]
plt.xticks(addressRange, addressStringsSequence)
ax.tick_params(axis='y', which='major', labelsize=14)
ax.tick_params(axis='x', which='major', labelsize=14, rotation=60)
plt.plot([0.75, 0.75], [0, 1.05], '--k')
plt.xlabel('Sensor address', fontsize=14)
plt.ylabel('Count of address-events', fontsize=14) 
    
fig.tight_layout()