#!/usr/bin/env python
"""This module has tests for functions used internally in heatmaps.heatmap"""

# Copyright 2022, vipersci developers.
#
# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.

import numpy as np
from rasterio import transform
import shapely
import unittest

from vipersci.heatmaps import heatmap as hm


class TestHeatmapAreaBin(unittest.TestCase):
    def test_transform_frombuffer_withgrid_simple(self):
        t = hm.transform_frombuffer_withgrid(0, 10, 1, 1)
        self.assertEqual(t, transform.from_origin(-1, 11, 1, 1))

    def test_transform_frombuffer_withgrid_nobuffer(self):
        t = hm.transform_frombuffer_withgrid(0, 10, 0, 1)
        self.assertEqual(t, transform.from_origin(0, 10, 1, 1))

    def test_transform_frombuffer_withgrid_smallgsd(self):
        t = hm.transform_frombuffer_withgrid(0, 10, 0, 0.1)
        self.assertEqual(t, transform.from_origin(0, 10, 0.1, 0.1))

    def test_transform_frombuffer_withgrid_origin_snap_to_gsd(self):
        t = hm.transform_frombuffer_withgrid(1, 9, 0, 2)
        self.assertEqual(t, transform.from_origin(0, 10, 2, 2))

    def test_buffered_mask_full(self):
        points = shapely.geometry.LineString([(0, 0), (1, 0), (1, 1), (0, 1)])
        t = hm.transform_frombuffer_withgrid(0, 1, 1, 1)
        mask = hm.buffered_mask(points, t, buffer=1)
        self.assertTrue(np.array_equal(np.full((3, 3), False), mask))
