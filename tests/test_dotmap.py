#!/usr/bin/env python
"""This module has tests for dotmap.generate_dotmap"""

# Copyright 2023, United States Government as represented by the
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
from vipersci.carto.dotmap import generate_dotmap


def test_single_point():
    """
    Test creating a raster with 1 data point
    """
    x_arr = [0]
    y_arr = [0]
    value_arr = [1]
    transform, raster = generate_dotmap(
        x_arr, y_arr, value_arr, radius=1, ground_sample_distance=1, padding=0
    )

    assert (-1, -1, 1, 1) == rasterio.windows.bounds(
        rasterio.windows.Window(0, 0, raster.shape[1], raster.shape[0]), transform
    )
    assert np.array_equal(raster, [[1, 1], [1, 1]])


def test_single_point_padded():
    """
    Test creating a raster with 1 data point and padding
    """
    x_arr = [0]
    y_arr = [0]
    value_arr = [1]
    transform, raster = generate_dotmap(
        x_arr, y_arr, value_arr, radius=1, ground_sample_distance=1, padding=1
    )
    assert (-2, -2, 2, 2) == rasterio.windows.bounds(
        rasterio.windows.Window(0, 0, raster.shape[1], raster.shape[0]), transform
    )
    assert np.array_equal(
        raster, [[-1, -1, -1, -1], [-1, 1, 1, -1], [-1, 1, 1, -1], [-1, -1, -1, -1]]
    )


def test_2_overlapping_points():
    """
    Test creating a raster with 2 overlapping data points
    """
    x_arr = [0, 1]
    y_arr = [0, 1]
    value_arr = [1, 2]
    transform, raster = generate_dotmap(
        x_arr, y_arr, value_arr, radius=1, ground_sample_distance=1, padding=0
    )

    assert (-1, -1, 2, 2) == rasterio.windows.bounds(
        rasterio.windows.Window(0, 0, raster.shape[1], raster.shape[0]), transform
    )
    assert np.array_equal(raster, [[-1, 2, 2], [1, 2, 2], [1, 1, -1]])


def test_single_detailed_point():
    """
    Test creating a raster with 1 data point and high raster resolution
    """
    x_arr = [0]
    y_arr = [0]
    value_arr = [1]
    transform, raster = generate_dotmap(
        x_arr, y_arr, value_arr, radius=1, ground_sample_distance=0.25, padding=0
    )

    assert (-1, -1, 1, 1) == rasterio.windows.bounds(
        rasterio.windows.Window(0, 0, raster.shape[1], raster.shape[0]), transform
    )
    assert np.array_equal(
        raster,
        [
            [-1] * 2 + [1] * 4 + [-1] * 2,
            [-1] + [1] * 6 + [-1],
            [1] * 8,
            [1] * 8,
            [1] * 8,
            [1] * 8,
            [-1] + [1] * 6 + [-1],
            [-1] * 2 + [1] * 4 + [-1] * 2,
        ],
    )


def test_horizontal_line():
    x_arr = [0, 1, 2, 3, 4]
    y_arr = [0] * len(x_arr)
    value_arr = [1] * len(x_arr)
    transform, raster = generate_dotmap(
        x_arr, y_arr, value_arr, radius=1, ground_sample_distance=0.5, padding=0
    )

    assert (-1, -1, 5, 1) == rasterio.windows.bounds(
        rasterio.windows.Window(0, 0, raster.shape[1], raster.shape[0]), transform
    )

    assert np.array_equal(
        raster,
        [
            [-1] + [1] * 10 + [-1],
            [1] * 12,
            [1] * 12,
            [-1] + [1] * 10 + [-1],
        ],
    )
