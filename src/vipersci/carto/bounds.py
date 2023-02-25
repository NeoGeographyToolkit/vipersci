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
from typing import Callable, Tuple

import numpy as np
from numpy.typing import NDArray


def compute_bounds(
    x_arr: NDArray,
    y_arr: NDArray,
) -> Tuple[float, float, float, float]:
    """Compute cartesian bounds of input coordinates

    Args:
        x_arr: set of x locations
        y_arr: set of y locations

    Returns:
        a tuple (left, bottom, right, top) describing the bounds of the input data
    """
    return (np.amin(x_arr), np.amin(y_arr), np.amax(x_arr), np.amax(y_arr))


def pad_grid_align_bounds(
    left: float,
    bottom: float,
    right: float,
    top: float,
    ground_sample_distance: float,
    padding: int = 0,
) -> Tuple[float, float, float, float]:
    """Given bounds, add a padding and align to a grid of size of
    ground_sample_distance.  That is, the output bounds will be integer multiples of
    ground_sample_distance.

    Args:
        left: xmin of input bounds
        bottom: ymin of input bounds
        right: xmax of input bounds
        top: ymax of input bounds
        ground_sample_distance: Spatial resolution of grid
        padding: Pixels (multiples of ground_sample_distance) of padding to add on
          to bounds
    Returns:
        a tuple (left, bottom, right, top) describing padded and aligned bounds
    """

    def _grid_snap(
        operator: Callable[[float], float],
        value: float,
        ground_sample_distance: float,
    ) -> float:
        """Round value to closest multiple of ground_sample_distance.

        Args:
            operator: Function that defines how value is rounded.  Usually math.floor
              or math.ceil.
            value: value to snap to grid
            ground_sample_distance: defines a grid with origin 0 and cells of this size.

        Returns:
            Rounded value
        """
        return operator(value / ground_sample_distance) * ground_sample_distance

    # Convert from pixels of padding to a buffer in x/y distance units.
    buffer = padding * ground_sample_distance
    # Make sure that bounds are snapped into a grid centered on the
    # origin with a *ground_sample_distance* step.
    left = _grid_snap(math.floor, left - buffer, ground_sample_distance)
    right = _grid_snap(math.ceil, right + buffer, ground_sample_distance)
    bottom = _grid_snap(math.floor, bottom - buffer, ground_sample_distance)
    top = _grid_snap(math.ceil, top + buffer, ground_sample_distance)

    return (left, bottom, right, top)
