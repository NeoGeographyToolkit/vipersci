"""
The dotmap module takes scalar values with 2D coordinates and creates a simple
"dot" based map with a filled circle of a given value at each input point.
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
from typing import Tuple, Sequence

import numpy as np
from numpy.typing import NDArray
import rasterio
from rasterio.coords import BoundingBox
from rasterio.features import rasterize
from shapely.geometry import Point

from vipersci.carto.bounds import compute_bounds, pad_grid_align_bounds
from vipersci.carto.heatmap import as_ndarray


def generate_dotmap(
    x_coords: Sequence,
    y_coords: Sequence,
    values: Sequence,
    radius: float,
    ground_sample_distance: float,
    padding: int = 0,
    nodata: float = -1,
) -> Tuple[rasterio.Affine, NDArray[np.float32]]:
    """
    Creates a simple "dotmap" by drawing a filled circle with the
    provided value at each point.  Subsequent points will be drawn
    on top of any other circles they may overlap.

    Parameters:
        x_coords: x coordinates of the data points
        y_coords: y coordinates of the data points
        values: values of the data points
        ground_sample_distance: Spatial resolution of the output data
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

    padding = padding + math.ceil(radius / ground_sample_distance)
    bounds = BoundingBox(
        *pad_grid_align_bounds(
            *compute_bounds(as_ndarray(x_coords), as_ndarray(y_coords)),
            ground_sample_distance,
            padding
        )
    )

    transform = rasterio.transform.from_origin(
        bounds.left, bounds.top, ground_sample_distance, ground_sample_distance
    )
    out_shape = (
        math.floor((bounds.top - bounds.bottom) / ground_sample_distance),
        math.floor((bounds.right - bounds.left) / ground_sample_distance),
    )

    shapes = []
    for x, y, val in zip(x_coords, y_coords, values):
        shapes.append((Point(x, y).buffer(radius), val))

    output = rasterize(
        shapes, out_shape=out_shape, fill=nodata, transform=transform, dtype=np.float32
    )
    return transform, output
