#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import time

import rpy2.rinterface as rinterface
import rpy2.robjects as robjects
from rpy2.robjects.packages import importr

# Start R timing
startTime = time.time()

rinterface.initr()

r = robjects.r
grdevices = importr('grDevices')
graphics = importr('graphics')

data_array = [0.5384, 0.4882, 0.5829, 0.7071, 0.7386, 0.8259, 0.7633, 0.7869, 0.8303, 0.7802, 0.8121, 0.8504, 0.8658, 0.8115, 0.814, 0.8136, 0.7503, 0.0237, 0.7368, 0.7307, 0.1242, 0.3123, 0.7286, 0.0691, 0.1867, 0.8277, 0.506, 0.707, 0.8409, 0.7511, 0.803, 0.6278, 0.792, 0.8165, 0.8387, 0.864, 0.8285, 0.7897, 0.7511, 0.7754, 0.7076, 0.2891, 0.1108, 0.4819, 0.6706, 0.6028, 0.6289, 0.6001, 0.6658, 0.719, 0.773, 0.8148, 0.8268, 0.827, 0.7847, 0.8019, 0.814, 0.7991, 0.8683, 0.8475, 0.8103, 0.799, 0.7816, 0.7454, 0.7982, 0.752, 0.752, 0.6268, 0.0552, 0.0731, 0.6626, 0.748, 0.7738, 0.8365, 0.8411, 0.8763, 0.7929, 0.8376, 0.8241, 0.7862, 0.7792, 0.7902, 0.8078, 0.8204, 0.0927, 0.7266, 0.7873, 0.7521, 0.05, 0.0446, 0.0226, 0.0852, 0.0793, 0.3474, 0.1396, 0.6583, 0.7534, 0.8351, 0.7936, 0.8047, 0.836, 0.8235, 0.8058, 0.7936, 0.8262, 0.8139, 0.7869, 0.7748, 0.8278, 0.1223, 0.7563, 0.0291, 0.6821, 0.0443, 0.0796, 0.016, 0.0775, 0.7212, 0.7382, 0.8203, 0.8133, 0.8129, 0.7942, 0.8015, 0.7933, 0.8405, 0.813, 0.8159, 0.8426, 0.7929, 0.7719, 0.7898, 0.7539, 0.137, 0.0362, 0.1345, 0.1748, 0.2453, 0.273, 0.2737, 0.6617, 0.5928, 0.7878, 0.8936, 0.7906, 0.7366, 0.7952, 0.8098, 0.7873, 0.8051, 0.8248, 0.835, 0.8041, 0.7716, 0.77, 0.7804, 0.0375, 0.5522, 0.7375, 0.4584, 0.6603, 0.6735, 0.6985, 0.0481, 0.7623, 0.8087, 0.8247, 0.7806, 0.7793, 0.8883, 0.7657, 0.8163, 0.8231, 0.7996, 0.8077, 0.7684, 0.761, 0.7835, 0.8099, 0.1639, 0.1496, 0.757, 0.7139, 0.76, 0.5772, 0.087, 0.0365, 0.0445, 0.7864, 0.8281, 0.6857, 0.8495, 0.8118, 0.8098, 0.8347, 0.7841, 0.8566, 0.7949, 0.7832, 0.7606, 0.7449, 0.1543, 0.3029, 0.1283, 0.1507, 0.1047, 0.2336, 0.0173, 0.078, 0.5322, 0.6085, 0.8098, 0.8268, 0.8245, 0.7841, 0.9329, 0.8006, 0.7775, 0.8168, 0.8222, 0.7931, 0.8103, 0.8051, 0.7232, 0.6616, 0.0097, -0.0038, 0.0512, 0.2414, 0.0514, 0.1239, 0.1557, 0.6627, 0.7314, 0.7644, 0.7972, 0.858, 0.8849, 0.814, 0.845, 0.7915, 0.7945, 0.7741, 0.8439, 0.7424, 0.5773, 0.7817, 0.2651, 0.0452, 0.05, 0.9211, 0.6564, 0.6136, 0.433, 0.6368, 0.7325, 0.7242, 0.8336, 0.7464, 0.7743, 0.8311, 0.7772, 0.8256, 0.788, 0.7847, 0.809, 0.798, 0.7826, 0.7783, 0.7505, 0.7426, 0.68, 0.0617, 0.0774, 0.4762, 0.0607, 0.0604, 0.5279, 0.5775, 0.3558, 0.7426, 0.78, 0.8104, 0.8077, 0.7731, 0.7863, 0.7836, 0.7901, 0.8242, 0.8004, 0.6833, 0.822, 0.8073, 0.7545, 0.0333, -0.0175, 0.6835, 0.1628, 0.0201, 0.0583, 0.1863, 0.3165, 0.5837, 0.7191, 0.788, 0.7827, 0.7486, 0.7977, 0.8004, 0.7825, 0.7613, 0.8365, 0.8085, 0.9533, 0.7631, 0.7421, 0.0347, 0.0973, 0.0539, 0.2871]

vector = robjects.FloatVector(data_array)

ts = r.ts(vector, start=robjects.IntVector([2000,4]), frequency=23)

file = open("routput.png", 'a')

grdevices.png(file=file.name, width=800, height=600)

r.layout(r.matrix(robjects.IntVector([1,2,3,4]), ncol=1, nrow=4))

## PLOT 1: Raw NDVI values

r.par(mar=robjects.FloatVector([0, 4, .2, 4]))   # mar für die Abstände ausserhalb des plots in der Reihenfolge unten - links - oben - rechts. Oben Null, der Rest sind default-Werte

r.plot(ts, type="l", axes=False, ylab="Raw NDVI value", xlab="")
r.box()
r.axis(2, labels=robjects.StrVector(['0', '0.2', '0.4', '0.6', '0.8', '1']), at=robjects.FloatVector([0, 0.2, 0.4, 0.6, 0.8, 1]))
r.abline(v=[2000, 2014, 1], col="lightgrey", lty=2) # vertikale linien bei jedem jahr, lty ist line type
r.abline(h=robjects.FloatVector([0, 0.2000, 0.4000, 0.6000, 0.8000]), col="lightgrey", lty=2)

## PLOT 2:

r.par(mar=robjects.IntVector([0, 4, 0, 4]))
r.plot(ts, type="l", col="grey", axes=False, ylab="Asym Gaussian fitting", xlab="")
r.box()
r.axis(4, labels=robjects.StrVector(['0', '0.2', '0.4', '0.6', '0.8', '1']), at=robjects.FloatVector([0, 0.2, 0.4, 0.6, 0.8, 1]))
r.abline(v=[2000, 2014, 1], col="lightgrey", lty=2)
r.abline(h=robjects.FloatVector([0, 0.2000, 0.4000, 0.6000, 0.8000]), col="lightgrey", lty=2)

## PLOT 3:

r.par(mar=robjects.IntVector([0, 4, 0, 4]))
r.plot(ts, type="l", col="grey", axes=False, ylab="Double logistic fitting", xlab="")
r.box()
r.axis(2, labels=robjects.StrVector(['0', '0.2', '0.4', '0.6', '0.8', '1']), at=robjects.FloatVector([0, 0.2, 0.4, 0.6, 0.8, 1]))
r.abline(v=[2000, 2014, 1], col="lightgrey", lty=2)
r.abline(h=robjects.FloatVector([0, 0.2000, 0.4000, 0.6000, 0.8000]), col="lightgrey", lty=2)

## PLOT 4:

r.par(mar=robjects.IntVector([2, 4, 0, 4]))
r.plot(ts, type="l", col="grey", axes=False, ylab="Trends", xlab="")
r.box()
r.axis(4, labels=robjects.StrVector(['0', '0.2', '0.4', '0.6', '0.8', '1']), at=robjects.FloatVector([0, 0.2, 0.4, 0.6, 0.8, 1]))
r.axis(1, labels=robjects.StrVector(['2000', '2002', '2004', '2006', '2008', '2010', '2012', '2014']), at=robjects.FloatVector([2000, 2002, 2004, 2006, 2008, 2010, 2012, 2014]))
r.abline(v=[2000, 2014, 1], col="lightgrey", lty=2)
r.abline(h=robjects.FloatVector([0, 0.2000, 0.4000, 0.6000, 0.8000]), col="lightgrey", lty=2)

# Close the device
grdevices.dev_off()

file.close()

# End R timing and log it
endTime = time.time()
print 'It took ' + str(endTime - startTime) + ' seconds to initalize R and draw a plot.'