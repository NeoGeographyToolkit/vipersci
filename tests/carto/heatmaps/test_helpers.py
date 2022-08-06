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
from rasterio import transform
import shapely
import unittest

from vipersci.carto import heatmap as hm


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
