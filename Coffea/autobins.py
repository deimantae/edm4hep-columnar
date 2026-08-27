"""
Automatic histogram binning for Coffea, inspired by ROOT.
Adapted from ROOT TH1::BufferEmpty, TH1::FindNewAxisLimits and THLimitsFinder.
https://root.cern.ch/doc/v632/classTH1.html
"""

import math
import awkward as ak
import numpy as np


def optimize(al, ah, nbins):
    # Choose histogram bin width and axis limits
    # Adapted from ROOT THLimitsFinder::Optimize
    ntemp = nbins
    while True:
        awidth = (ah - al) / ntemp # approx bin width
        jlog = int(math.log10(awidth)) # bin width in exponential form
        if awidth <= 1:
            jlog -= 1
        # ROOT subtracts 1e-10 to avoid precision problems
        sigfig = awidth * 10.0**(-jlog) - 1e-10

        # Round mantissa
        if sigfig <= 1:
            siground = 1.0
        elif sigfig <= 2:
            siground = 2.0
        elif sigfig <= 5:
            siground = 5.0
        else:
            siground = 1.0
            jlog += 1

        BinWidth = siground * 10.0**jlog

        # Get new bounds from new BinWidth
        alb = al/BinWidth
        lwid = int(alb)
        if alb < 0:
            lwid -= 1
        BinLow = BinWidth * lwid

        alb = ah / BinWidth + 1.00001
        kwid = int(alb)
        if alb < 0:
            kwid -= 1
        BinHigh = BinWidth * kwid

        optimized_bins = kwid - lwid
        if 2 * optimized_bins == nbins:
            ntemp += 1
            continue

        break

    atest = BinWidth * 0.0001
    if al - BinLow >= atest:
        BinLow += BinWidth
    if BinHigh - ah >= atest:
        BinHigh -= BinWidth

    return BinLow, BinHigh, BinWidth


def find_good_limits(minimum, maximum, nbins):
    # Adapted from ROOT THLimitsFinder::FindGoodLimits and OptimizeLimits

    if minimum >= maximum:
        minimum -= 1.0
        maximum += 1.0

    difference = maximum - minimum

    # Add 10% margin
    delta = 0.1 * difference
    lower = minimum - delta
    upper = maximum + delta

    # Do not cross 0 if all values have the same sign
    if lower < 0 and minimum >= 0:
        lower = 0.0

    if upper > 0 and maximum <= 0:
        upper = 0.0

    BinLow, BinHigh, _ = optimize(lower, upper, nbins)

    # Add 1% margin around the original range
    delta = 0.01 * difference
    minimum = min(BinLow, minimum - delta)
    maximum = max(BinHigh, maximum + delta)

    return minimum, maximum


def extend_axis(value, minimum, maximum):
    # Adapted from ROOT TH1::FindNewAxisLimits
    width = maximum - minimum

    while value < minimum:
        minimum -= width
        width *= 2

    while value >= maximum:
        maximum += width
        width *= 2

    return minimum, maximum


def autobin_range(values, nbins=100, buffer_size=1000):
    # Convert the Awkward array into the values passed to ROOT TH1::Fill
    values = np.asarray(
        ak.drop_none(ak.flatten(values, axis=None), axis=0),
        dtype=np.float64
    )

    if len(values) == 0:
        return None

    # Adapted from ROOT TH1::BufferEmpty
    n_buffered = min(buffer_size, len(values))
    buffered = values[:n_buffered]
    buffered = buffered[np.isfinite(buffered)]

    if len(buffered) == 0:
        return None

    # Determine the initial limits from buffered values
    minimum = float(np.min(buffered))
    maximum = float(np.max(buffered))
    minimum, maximum = find_good_limits(minimum, maximum, nbins)

    # Extend the axis if values fall outside the initial range
    start = n_buffered

    while start < len(values):
        remaining = values[start:]
        outside = np.logical_or(
            remaining < minimum,
            remaining >= maximum
        )
        indices = np.flatnonzero(np.isfinite(remaining) & outside)
        if len(indices) == 0:
            break
        index = start + indices[0]
        minimum, maximum = extend_axis(values[index], minimum, maximum)
        start = index + 1

    return minimum, maximum
