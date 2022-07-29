#!/usr/bin/env python
"""This module has tests for heatmap.area_bin"""

# Copyright 2022, vipersci developers.
#
# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.

import numpy as np
from rasterio import transform, windows

from vipersci.heatmaps import heatmap as hm


def test_area_bin_3x3():
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
    assert np.array_equal(averages, np.ones((3, 3)))
    assert np.array_equal(counts, np.ones((3, 3)))
    # TODO: proper frequency tests
