"""NSS model module.

This module contains functions for ingesting the text file format that the
NSS team produces and for providing interpolation for the forward and reverse
models.
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

import logging
import os
from typing import Any, Generator, List, Sequence, Union

import numpy as np
from scipy.interpolate import RegularGridInterpolator

logger = logging.getLogger(__name__)

# type alias for the exhaustive variety of arguments that np.genfromtxt() takes.
Readable = Union[os.PathLike, str, List[str], Generator[Union[str, bytes], Any, Any]]


class DataSimulator:
    """
    The DataSimulator object is initiated with inverse model model files,
    and then can be called to return simulated detector
    data given burial depth and water equivalent hydrogen values.
    """

    def __init__(
        self,
        det1: Readable,
        det2: Readable,
        bounds_error: bool = True,
        fill_value: Any = np.nan,
        rng: np.random.Generator = np.random.default_rng(),
    ):
        """
        :param det1: The path to the Detector 1 inverse model CSV file.
        :type det1: Path
        :param det2: The path to the Detector 2 inverse model CSV file.
        :type det2: Path
        :param bounds_error: If True, when interpolated values are requested
        outside of the domain of the inverse models, a ValueError is raised.
        If False, then fill_value is used.
        :param fill_value: If provided, the value to use for points outside
        of the interpolation domain. If None, values outside the domain are
        extrapolated.
        :param rng: A random generator for the object to use when Poisson
        noise is requested.

        The *bounds_error* and *fill_value* arguments are passed on to the
        model() function, please see its documentation for more information.
        """
        self.det1_model = model(det1, bounds_error=bounds_error, fill_value=fill_value)
        self.det2_model = model(det2, bounds_error=bounds_error, fill_value=fill_value)
        self.rng = rng
        return

    def __call__(
        self,
        bd: Union[float, Sequence, np.ndarray],
        weh: Union[float, Sequence, np.ndarray],
        poisson: bool = False,
    ):
        """
        Returns simulated detector 1 and detector 2 values.

        :param bd:  A single value or sequence of burial depth.
        :param weh: A single value or sequence of water equivalent hydrogen.
        :param poisson: A boolean (default False) indicating whether Poisson
        noise should be added to the returned simulated data.
        :returns: A two-tuple of values or np.arrays.  If *bd* and *weh* are
        singular elements, then a two-tuple is returned of the detector 1 and
        detector 2 values at that location.  If *bd* and *weh* contain more than
        one value each, then the returned two-tuple will be a numpy array
        of detector 1 values, and a numpy array of detector 2 values.
        """
        is_arraylike = True if hasattr(bd, "__iter__") else False

        d1 = self.det1_model(np.column_stack((bd, weh)))
        d2 = self.det2_model(np.column_stack((bd, weh)))

        if poisson:
            d1, d2 = self.rng.poisson(lam=(d1, d2))

        if not is_arraylike:
            return d1.item(), d2.item()

        return d1, d2


class DataModeler:
    """
    The DataModeler object is initiated with model files,
    and then can be called to apply the models to a set of detector 1 & 2
    data to provide burial depth and water equivalent hydrogen values.
    """

    def __init__(
        self,
        bd_mod: Readable,
        weh_mod: Readable,
        fill_value: Any = np.nan,
    ):
        """
        :param bd_mod: The path to the BD model CSV file.
        :type bd_mod: Path
        :param weh_mod: The path to the WEH model CSV file.
        :type weh_mod: Path
        :param fill_value: fill value for nodata regions

        The *fill_value* arguments is passed on to the
        model() function. Please see its documentation for more information.
        """
        self.det1_model = model(bd_mod, bounds_error=False, fill_value=fill_value)
        self.det2_model = model(weh_mod, bounds_error=False, fill_value=fill_value)
        self.fill_value = fill_value
        return

    def __call__(
        self,
        det1: Union[float, Sequence, np.ndarray],
        det2: Union[float, Sequence, np.ndarray],
    ):
        """
        Returns model-provided burial depth, water equivalent hydrogen, and
        uniform water equivalent hydrogen values.

        :param bd:  A single value or sequence of detector 1 values.
        :param weh: A single value or sequence of detector 2 values.
        :returns: A three-tuple of values or np.arrays.  If *det1* and *det2* are
        singular elements, then a three-tuple is returned of the BD, WEH, and UWEH
        values at that location.  If *det1* and *det2* contain more than
        one value each, then the returned three-tuple will be a numpy array
        of BD values, a numpy array of WEH values, and a numpy array of UWEH values.
        """
        is_arraylike = True if hasattr(det1, "__iter__") else False

        bd_arr = np.full_like(det1, self.fill_value, dtype=np.double)
        weh_arr = np.full_like(det1, self.fill_value, dtype=np.double)

        bd_arr[~det1.mask] = self.bd_model(
            np.column_stack((det1.compressed(), det2.compressed()))
        )
        weh_arr[~det1.mask] = self.weh_model(
            np.column_stack((det1.compressed(), det2.compressed()))
        )
        uweh_arr = uniform_weh(
            det1.filled(self.fill_value), fill_value=self.fill_value, bounds_error=False
        )

        if not is_arraylike:
            return bd_arr.item(), weh_arr.item(), uweh_arr.item()

        return bd_arr, weh_arr, uweh_arr


def model(fname: Readable, **kwargs):
    """
    Returns a scipy.interpolate.RegularGridInterpolator "instance" created
    from the data provided in the NSS file *fname*.

    The returned instance can be called with an ndarray of shape (..., 2)
    which contain the x, y coordinates at which to sample the data.

    The Burial Depth and WEH files, are expected to have Detector 1 (He Cd) as
    the x-coordinate and Detector 2 (He Sn) as the y-coordinate.

    Any additional keyword arguments will be passed to
    scipy.interpolate.RegularGridInterpolator().  Please review its
    documentation for more information.
    """

    arr, row_coords, col_coords = read_csv(fname)
    # These are inverted to make calling the RGI instance more "natural" to
    # call as described in the docstring above.
    return RegularGridInterpolator(
        (col_coords, row_coords), np.transpose(arr), **kwargs
    )


def read_csv(fname: Readable):
    """
    Returns three objects: a 2D array of "data", an array of row coordinates,
    and an array of column coordinates.

    The *fname* is expected to be a CSV file provided by the NSS team which
    describes either a forward or reverse model for detector counts.  These
    files are conceptually describing a graph.  These CSV files use the first
    row and first column as "headers" to describe the data within.  The first
    element of the first row is not data and is ignored.  The
    remainder of the first row indicates the column values, and the remainder
    of the first column indicates the row values.  The remaining rectangular
    array are the data.
    """
    f = np.genfromtxt(fname, delimiter=",", missing_values="NaN")

    arr = f[1:, 1:]
    col_coords = f[0, 1:]
    row_coords = f[1:, 0]

    if col_coords[0] > col_coords[-1]:
        col_coords = np.flip(col_coords)
        arr = np.fliplr(arr)

    if row_coords[0] > row_coords[-1]:
        row_coords = np.flip(row_coords)
        arr = np.flipud(arr)

    # arr is in [row, col] order.
    return arr, row_coords, col_coords


def uniform_weh(
    measured: Union[float, Sequence, np.ndarray],
    c0: float = 30.75,
    a: float = 0.0256,
    b: float = 1.0990,
    bounds_error: bool = True,
    fill_value: Any = np.nan,
):
    """Returns fraction of water equivalent hydrogen.

    With 1 corresponding to pure ice, and 0.01 corresponding to 1 wt% WEH.

    The value(s) of *measured* should be epithermal count rates (Detector #1),
    and this model assumes a uniformly distributed water-equivalent
    hydrogen abundance.

    The default values of c0, a, and b correspond to conditions of the Lunar
    Prospector mission in 1998/1999, during the rising phase of cycle 23.
    The state of the sun during VIPER’s mission is yet unknown but may be more
    active – this would reduce the neutron flux.

    bounds_error: bool, optional
    If True, when a value of *measured* is greater than c0 (or less than or
    equal to zero), a ValueError is raised. If False, then *fill_value* is used.

    fill_value: number, optional
    If provided, the value to use for points when *measured* triggers the
    *bounds_error*.
    """
    is_arraylike = True if hasattr(measured, "__iter__") else False

    # Values of *measured* larger than C0 result in unrealistic negative
    # fractions.
    if bounds_error:
        if np.any(measured > c0):
            raise ValueError(f"Value(s) in measured are greater than c0, {c0}.")

        if np.any(measured <= 0):
            raise ValueError("Value(s) in measured are less than or equal to zero.")

    with np.errstate(divide="ignore", invalid="ignore"):
        arr = np.float_power(a * ((c0 / measured) - 1), b)

    if is_arraylike:
        arr[np.logical_or(arr < 0, arr > 1)] = fill_value
    else:
        if arr < 0 or arr > 1:
            arr = fill_value

    return arr
