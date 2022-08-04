#!/usr/bin/env python
"""This module has tests for heatmap.area_bin"""

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

import unittest

import numpy as np
from rasterio import transform, windows

from vipersci.carto import heatmap as hm


class TestHeatmapAreaBin(unittest.TestCase):
    def test_area_bin_3x3(self):
        x_arr = [0.5, 1.5, 2.5]
        y_arr = [0.5, 1.5, 2.5]
        x, y = np.meshgrid(x_arr, y_arr)
        values = np.ones(len(x_arr) * len(y_arr))
        averages, counts = hm.area_bin(
            values,
            x.ravel(),
            y.ravel(),
            transform.from_bounds(0, 0, 3, 3, 3, 3),
            windows.Window(0, 0, 3, 3),
        )

        self.assertTrue(np.array_equal(averages, np.ones((3, 3))))
        self.assertTrue(np.array_equal(counts, np.ones((3, 3))))
        # TODO: proper frequency tests
