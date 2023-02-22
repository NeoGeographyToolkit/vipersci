#!/usr/bin/env python
"""This module has tests for functions used internally in heatmaps.heatmap"""

# Copyright 2022, United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0
#
# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.

import numpy as np
import rasterio
from rasterio.coords import BoundingBox
import shapely
import unittest

from vipersci.carto import heatmap, bounds


class TestBounds(unittest.TestCase):
    def test_simple(self):
        initial_bounds = (0, 0, 10, 10)
        expected_bounds = initial_bounds
        out_bounds = bounds.pad_grid_align_bounds(*initial_bounds, 1)
        self.assertEqual(out_bounds, expected_bounds)

    def test_padded(self):
        initial_bounds = (0, 0, 10, 10)
        expected_bounds = (-1, -1, 11, 11)
        out_bounds = bounds.pad_grid_align_bounds(*initial_bounds, 1, padding=1)
        self.assertEqual(out_bounds, expected_bounds)

    def test_small_gsd(self):
        initial_bounds = (0, 0, 10, 10)
        expected_bounds = initial_bounds
        out_bounds = bounds.pad_grid_align_bounds(*initial_bounds, 0.1)
        self.assertEqual(out_bounds, expected_bounds)

    def test_origin_adjust(self):
        initial_bounds = (1, 1, 9, 9)
        expected_bounds = (0, 0, 10, 10)
        out_bounds = bounds.pad_grid_align_bounds(*initial_bounds, 2)
        self.assertEqual(out_bounds, expected_bounds)

    def test_buffered_mask_full(self):
        points = shapely.geometry.LineString([(0, 0), (1, 0), (1, 1), (0, 1)])
        gsd = 1
        b = BoundingBox(*bounds.pad_grid_align_bounds(0, 0, 1, 1, gsd, 1))
        t = rasterio.transform.from_origin(b.left, b.top, gsd, gsd)
        mask = heatmap.buffered_mask(points, t, buffer=1)
        self.assertTrue(np.array_equal(np.full((3, 3), False), mask))
