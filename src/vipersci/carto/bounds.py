"""
The bounds module is used to calculate a bounding box for a set of 2d spatial data.
"""

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

import math

import numpy as np
from numpy.typing import NDArray
from rasterio.coords import BoundingBox


def compute_bounds(
    x_arr: NDArray,
    y_arr: NDArray,
) -> BoundingBox:
    """Compute cartesian bounds of input coordinates

    Args:
        x_arr (NDArray): set of x locations
        y_arr (NDArray): set of y locations

    Returns:
        BoundingBox: Rasterio bounding box of input locations
    """
    return BoundingBox(np.amin(x_arr), np.amin(y_arr), np.amax(x_arr), np.amax(y_arr))


def pad_grid_align_bounds(
    bounds: BoundingBox, ground_sample_distance: float, padding: int = 0
) -> BoundingBox:
    """Given bounds, add a padding and align to a grid of size of
    ground_sample_distance.  That is, the output bounds will be integer multiples of
    ground_sample_distance.

    Args:
        bounds (BoundingBox): Input bounds to modify
        ground_sample_distance (float): Spatial resolution of grid
        padding (int): Pixels (multiples of ground_sample_distance) of padding to add on to bounds
    """

    # Convert from pixels of padding to a buffer in x/y distance units.
    buffer = padding * ground_sample_distance
    xmin = bounds.left
    xmax = bounds.right
    ymin = bounds.bottom
    ymax = bounds.top
    bxmin = xmin - buffer
    bxmax = xmax + buffer
    bymin = ymin - buffer
    bymax = ymax + buffer
    # Make sure that bounds are snapped into a grid centered on the
    # origin with a *ground_sample_distance* step.
    left = math.floor(bxmin / ground_sample_distance) * ground_sample_distance
    right = math.ceil(bxmax / ground_sample_distance) * ground_sample_distance
    bottom = math.floor(bymin / ground_sample_distance) * ground_sample_distance
    top = math.ceil(bymax / ground_sample_distance) * ground_sample_distance

    return BoundingBox(left, bottom, right, top)
