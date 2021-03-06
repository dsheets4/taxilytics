#!/usr/bin/env python

# Source: https://on4wp7.codeplex.com/SourceControl/changeset/view/21455#EvilTransform.cs
# Copyright (C) 1000 - 9999 Somebody Anonymous
# NO WARRANTY OR GUARANTEE

# Other modifications from: https://github.com/googollee/eviltransform

"""
This file provides the transform to shift the 2011 Shenzhen data to WGS-84
"""

import math
from datetime import datetime
import numpy as np
import pandas as pd

from processing.coordinates import eviltransform


a = 6378245.0
ee = 0.00669342162296594323


def _transformLat(x, y):
    ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * np.sqrt(np.fabs(x))
    ret += (20.0 * np.sin(6.0 * x * math.pi) + 20.0 * np.sin(2.0 * x * math.pi)) * 2.0 / 3.0
    ret += (20.0 * np.sin(y * math.pi) + 40.0 * np.sin(y / 3.0 * math.pi)) * 2.0 / 3.0
    ret += (160.0 * np.sin(y / 12.0 * math.pi) + 320 * np.sin(y * math.pi / 30.0)) * 2.0 / 3.0
    return ret


def _transformLon(x, y):
    ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * np.sqrt(np.fabs(x))
    ret += (20.0 * np.sin(6.0 * x * math.pi) + 20.0 * np.sin(2.0 * x * math.pi)) * 2.0 / 3.0
    ret += (20.0 * np.sin(x * math.pi) + 40.0 * np.sin(x / 3.0 * math.pi)) * 2.0 / 3.0
    ret += (150.0 * np.sin(x / 12.0 * math.pi) + 300.0 * np.sin(x / 30.0 * math.pi)) * 2.0 / 3.0
    return ret


def delta(wgLon, wgLat):
    """ Shifts data from WGS84 to Chinese coordinates """
    dLat = _transformLat(wgLon - 105.0, wgLat - 35.0)
    dLon = _transformLon(wgLon - 105.0, wgLat - 35.0)
    radLat = wgLat / 180.0 * math.pi
    magic = math.sin(radLat)
    magic = 1 - ee * magic * magic
    sqrtMagic = np.sqrt(magic)
    dLat = (dLat * 180.0) / ((a * (1 - ee)) / (magic * sqrtMagic) * math.pi)
    dLon = (dLon * 180.0) / (a / sqrtMagic * np.cos(radLat) * math.pi)
    return dLon, dLat


def wgs2gcj(wgLon, wgLat):
    dLon, dLat = delta(wgLon, wgLat)
    mgLat = wgLat + dLat
    mgLon = wgLon + dLon
    return mgLon, mgLat


def gcj2wgs_estimate(gcjLon, gcjLat):
    dLon, dLat = delta(gcjLon, gcjLat)
    mgLat = gcjLat - dLat
    mgLon = gcjLon - dLon
    return mgLon, mgLat


def gcj2wgs(gcjLon, gcjLat):
    df = pd.DataFrame({'lon': gcjLon, 'lat': gcjLat})

    def refine_gcj(sample):
        sample.lat, sample.lon = eviltransform.gcj2wgs_exact(sample.lat, sample.lon)
        return sample
    df = df.apply(refine_gcj, axis=1)
    return df['lon'], df['lat']
