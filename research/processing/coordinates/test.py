#!/usr/bin/env python
# -*- coding: utf-8 -*-
# From: https://github.com/googollee/eviltransform/blob/master/python/test.py

import timeit
import unittest
from datetime import datetime

import pandas as pd

from processing.coordinates import eviltransform
from processing.coordinates import transform

TESTS = [
    # wgsLat, wgsLng, gcjLat, gcjLng
    (31.1774276, 121.5272106, 31.17530398364597, 121.531541859215),  # shanghai
    (22.543847, 113.912316, 22.540796131694766, 113.9171764808363),  # shenzhen
    (39.911954, 116.377817, 39.91334545536069, 116.38404722455657)  # beijing
]

TESTS_bd = [
    # bdLat, bdLng, wgsLat, wgsLng
    (29.199786, 120.019809, 29.196131605295484, 120.00877901149691),
    (29.210504, 120.036455, 29.206795749156136, 120.0253853970846)
]


class EvilTransformTestCase(unittest.TestCase):

    def test_wgs2gcj(self):
        for wgsLat, wgsLng, gcjLat, gcjLng in TESTS:
            ret = eviltransform.wgs2gcj(wgsLat, wgsLng)
            self.assertAlmostEqual(ret[0], gcjLat, 6)
            self.assertAlmostEqual(ret[1], gcjLng, 6)

    def test_bd2wgs(self):
        for bdLat, bdLng, wgsLat, wgsLng in TESTS_bd:
            ret = eviltransform.bd2wgs(bdLat, bdLng)
            self.assertAlmostEqual(ret[0], wgsLat, 6)
            self.assertAlmostEqual(ret[1], wgsLng, 6)

    def test_gcj2wgs(self):
        for wgsLat, wgsLng, gcjLat, gcjLng in TESTS:
            ret = eviltransform.gcj2wgs(gcjLat, gcjLng)
            self.assertLess(eviltransform.distance(
                ret[0], ret[1], wgsLat, wgsLng), 5)

    def test_gcj2wgs_exact(self):
        for wgsLat, wgsLng, gcjLat, gcjLng in TESTS:
            ret = eviltransform.gcj2wgs_exact(gcjLat, gcjLng)
            self.assertLess(eviltransform.distance(
                ret[0], ret[1], wgsLat, wgsLng), .5)

    def test_z_speed(self):
        n = 100000
        tests = (
            ('eviltransform.wgs2gcj',
                lambda: eviltransform.wgs2gcj(TESTS[0][0], TESTS[0][1])),
            ('eviltransform.gcj2wgs',
                lambda: eviltransform.gcj2wgs(TESTS[0][0], TESTS[0][1])),
            ('eviltransform.gcj2wgs_exact',
                lambda: eviltransform.gcj2wgs_exact(TESTS[0][0], TESTS[0][1])),
            ('eviltransform.distance', lambda: eviltransform.distance(*TESTS[0]))
        )
        print('\n' + '='*30)
        for name, func in tests:
            sec = timeit.timeit(func, number=n)
            print('%s\t%.2f ns/op' % (name, sec * 1e9 / n))


class VectorTransformTestCase(unittest.TestCase):
    # Shenzhen Stadium
    wgs84_data = [(114.0869236, 22.5621291)]
    gcj02_data = [(114.0920540, 22.559447)]

    def run_conversion(self, func, input_pos, expected_pos):
        df = pd.DataFrame(input_pos,
                          columns=['longitude', 'latitude'],
                          index=[datetime.now()])
        converted = func(df['longitude'], df['latitude'])
        self.assertAlmostEqual(converted[0][0], expected_pos[0][0], 6)
        self.assertAlmostEqual(converted[1][0], expected_pos[0][1], 6)

    def test_wgs2gcj(self):
        self.run_conversion(transform.wgs2gcj, self.wgs84_data, self.gcj02_data)

    def test_gcj2wgs(self):
        self.run_conversion(transform.gcj2wgs, self.gcj02_data, self.wgs84_data)

    def test_z_speed(self):
        n = 3
        wgs_df = pd.DataFrame(self.wgs84_data,
                              columns=['lon', 'lat'],
                              index=[datetime.now()])
        gcj_df = pd.DataFrame(self.gcj02_data,
                              columns=['lon', 'lat'],
                              index=[datetime.now()])
        tests = (
            ('transform.wgs2gcj',
                lambda: transform.wgs2gcj(wgs_df['lon'], wgs_df['lat'])),
            ('transform.gcj2wgs',
                lambda: transform.gcj2wgs(gcj_df['lon'], gcj_df['lat'])),
        )
        print('\n' + '='*30)
        for name, func in tests:
            sec = timeit.timeit(func, number=n)
            print('%s\t%.2f ns/op' % (name, sec * 1e9 / n))


if __name__ == '__main__':
    unittest.main()
