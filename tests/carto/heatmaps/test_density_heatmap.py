#!/usr/bin/env python
"""This module has tests for heatmap.generate_density_heatmap"""

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

import math
from typing import Tuple
import unittest

import numpy as np
from rasterio import transform, windows

from vipersci.carto import heatmap as hm


class TestHeatmapAreaBin(unittest.TestCase):
    def test_density_heatmap_3x3_uniform(self):
        self.uniform_density_heatmap_runner((3, 3), processes=1)

    def test_density_heatmap_30x50_uniform(self):
        self.uniform_density_heatmap_runner((30, 50), processes=8)

    def test_density_heatmap_31x17_uniform(self):
        self.uniform_density_heatmap_runner((31, 17), processes=8)

    def test_density_heatmap_100x100_uniform(self):
        self.uniform_density_heatmap_runner((100, 100), processes=8)

    def test_density_heatmap_gsd_exception(self):
        try:
            self.uniform_density_heatmap_runner((5, 5), gsd=10, processes=8)
        except ValueError:
            self.assertTrue(True)
        else:
            self.assertTrue(False)

    def test_density_heatmap_diag(self, processes: int = 1):
        shape = (10, 10)
        x = np.arange(0.5, shape[1] - 0.5, 1)
        y = np.arange(0.5, shape[0] - 0.5, 1)
        values = np.ones(shape[0] - 1)
        affine_transform, out_freq, out_avg = hm.generate_density_heatmap(
            x, y, values, gsd=1, radius=1, padding=0, processes=processes
        )

        expected_output = np.zeros(shape)
        max_i = min(shape[0], shape[1])
        for i in range(0, max_i - 1):
            xc = i + 1
            yc = max_i - i - 1
            expected_output[xc][yc] = 1

        self.assertTrue(np.array_equal(out_avg, expected_output))
        self.assertEqual(
            affine_transform,
            transform.from_bounds(
                -1, 0, shape[1] - 1, shape[0], shape[1], shape[0]
            )
        )

        expected_freq = np.zeros(shape, dtype=np.int32)
        for i in range(1, max_i):
            xc = i
            yc = max_i - i
            expected_freq[xc][yc] = 1
        self.assertTrue(np.array_equal(expected_freq, out_freq))

    def uniform_density_heatmap_runner(
        self,
        shape: Tuple[int, int],
        gsd: float = 1,
        radius: float = 1,
        padding: float = 0,
        processes: int = 1,
    ):
        x_arr = np.arange(0.5, shape[1], 1)
        y_arr = np.arange(0.5, shape[0], 1)
        x, y = np.meshgrid(x_arr, y_arr)
        values = np.ones(len(x_arr) * len(y_arr))
        affine_transform, frequencies, out_avg = hm.generate_density_heatmap(
            x.ravel(),
            y.ravel(),
            values,
            gsd=gsd,
            radius=radius,
            padding=padding,
            processes=processes,
        )

        expected_result = np.ones((shape[0] + 1, shape[1] + 1))
        for i in range(0, shape[0] + 1):
            expected_result[i][0] = 0
        for i in range(0, shape[1] + 1):
            expected_result[0][i] = 0
        self.assertTrue(np.array_equal(out_avg, expected_result))

        expected_bounds = (
            math.floor(0.5 - radius),
            math.ceil(0.5 - radius),
            math.ceil(shape[1] - 1.5 + radius),
            math.ceil(shape[0] - 0.5 + radius),
        )
        self.assertEqual(
            expected_bounds,
            windows.bounds(
                windows.get_data_window(out_avg), affine_transform
            )
        )
        # TODO create proper frequency tests
        self.assertLessEqual(np.amax(frequencies), 4)
        self.assertGreaterEqual(np.amin(frequencies), 0)
