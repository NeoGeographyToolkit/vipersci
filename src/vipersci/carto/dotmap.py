"""
The dotmap module takes scalar values with 2D coordinates and creates a simple
"dot" based map with a filled circle of a given value at each input point.
"""

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
from typing import Tuple, Sequence

import numpy as np
from numpy.typing import NDArray
import rasterio
from rasterio.features import rasterize
from shapely.geometry import Point


def generate_dotmap(
    x_coords: Sequence,
    y_coords: Sequence,
    values: Sequence,
    radius: float,
    gsd: float,
    padding: float = 0,
    nodata: float = -1,
) -> Tuple[rasterio.Affine, NDArray[np.float32]]:
    """
    Creates a simple "dotmap" by drawing a filled circle with the provided value at each point.  Subsequent points
    will be drawn on top of any other circles they may overlap.

    Parameters:
        x_coords: x coordinates of the data points
        y_coords: y coordinates of the data points
        values: values of the data points
        gsd: Ground sample distance - spatial resolution of the output data
        radius: The radius of the circles to be drawn at each input point
        padding: Square padding in pixels to add to the bounds of data when
            returning an array.  If None (the default), the value of *radius*
            converted to pixels will be used.
        nodata: the fill value to use where points are not present. Defaults to -1.
    Returns:
        A tuple (transform, output)
        transform: transform used to georeference the output data
        output: the output data containing circles drawn at each point.
    """
    transform, out_shape = transform_frombuffer_withgrid(
        x_coords, y_coords, padding, radius=radius, gsd=gsd
    )
    shapes = []
    for x, y, val in zip(x_coords, y_coords, values):
        shapes.append((Point(x, y).buffer(radius), val))

    output = rasterize(
        shapes, out_shape=out_shape, fill=nodata, transform=transform, dtype=np.float32
    )
    return transform, output


def transform_frombuffer_withgrid(
    x_arr, y_arr, padding, radius, gsd
) -> Tuple[rasterio.Affine, Tuple[int, int]]:
    """
    Returns a rasterio Affine transform and a computed shape of the output based on the specified value of
    *gsd* (ground sample distance) and the bounds of the input points.
    """
    # Convert from pixels of padding to a buffer in x/y distance units.
    buffer = (padding * gsd) + radius
    west = np.amin(x_arr)
    east = np.amax(x_arr)
    north = np.amax(y_arr)
    south = np.amin(y_arr)
    bwest = west - buffer
    beast = east + buffer
    bnorth = north + buffer
    bsouth = south - buffer
    # Make sure that "west" and "north" are snapped into a grid centered on the
    # origin with a *ground_sample_distance* step.
    west = math.floor(bwest / gsd) * gsd
    east = math.ceil(beast / gsd) * gsd
    north = math.ceil(bnorth / gsd) * gsd
    south = math.floor(bsouth / gsd) * gsd
    transform = rasterio.transform.from_origin(west, north, gsd, gsd)
    out_shape = (math.floor((east - west) / gsd), math.floor((north - south) / gsd))

    return transform, out_shape
