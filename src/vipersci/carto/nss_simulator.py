# -*- coding: utf-8 -*-
"""
Takes a traverse of positions, a Burial Depth map, and a WEH map, and
simulates (with Poisson noise) what the Detector 1 and Detector 2 counts
from NSS might be at each location.

If no traverse is given, and both the Burial Depth map and the WEH map
have the same map characteristics, then instead of writing out a CSV file
that would simulate a traverse, this program will create a Detector1 map
and a Detector2 map that are the maps of the ideal detector values at
each location.
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

import argparse
import csv
import logging
from pathlib import Path

import numpy as np
import rasterio

from vipersci import nss
from vipersci.carto.nss_modeler import write_tif

logger = logging.getLogger(__name__)


def arg_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    # Sooo many inputs each time.  Kind of a mess.
    # Should definitely set up @file config reading.
    parser.add_argument(
        "-b",
        "--burial_depth",
        type=Path,
        required=True,
        help="A GeoTIFF map whose pixels are the burial depth of the water " "layer. ",
    )
    parser.add_argument(
        "--det1",
        type=Path,
        required=True,
        help="A CSV file provided by the NSS team with the Detector 1 "
        "two-layer model.",
    )
    parser.add_argument(
        "--det2",
        type=Path,
        required=True,
        help="A CSV file provided by the NSS team with the Detector 2 "
        "two-layer model.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="The output CSV file or if -t is not given, this will be used "
        "as the prefix for the two output maps, which will end in "
        "_d1.tif and _d2.tif .",
    )
    parser.add_argument("-t", "--traverse", type=Path, help="Input CSV file.")
    parser.add_argument(
        "-w",
        "--weh",
        type=Path,
        required=True,
        help="A GeoTIFF map whose pixels are the water-equivalent-hydrogen "
        "percentage.",
    )

    return parser


class LocationSimulator:
    def __init__(
        self,
        bd_map: Path,
        weh_map: Path,
        det1: Path,
        det2: Path,
        bounds_error=True,
        fill_value=np.nan,
        rng=np.random.default_rng(),
    ):
        """
        :param bd_map: The path to the Burial Depth map.
        :type bd_map: Path
        :param weh_map: The path to the Water Equivalent Hydrogen map.
        :type weh_map: Path

        The other arguments (*det1*, *det2*, *bounds_error*, fill_value*,
        and *rng*) are passed to the nss.DataSimulator constructor,
        please see its documentation for more information.
        """
        self.bd_aff, self.bd_arr = self._init_map(bd_map)
        self.weh_aff, self.weh_arr = self._init_map(weh_map)

        self.ds = nss.DataSimulator(
            det1, det2, bounds_error=bounds_error, fill_value=fill_value, rng=rng
        )
        return

    @staticmethod
    def _init_map(raster: Path):
        # Helper function for __init__()
        data = rasterio.open(raster)
        return data.transform, data.read(1)

    def __call__(self, xycoords: np.ndarray, poisson=False):
        """
        Returns simulated detector 1 and detector 2 values at the given
        location(s).

        :param xycoords:  A sequence or np.array object of shape (2, ...)
        indicating the projected x, y coordinate to simulated the data for.
        :param poisson: A boolean (default False) indicating whether Poisson
        noise should be added to the returned simulated data.
        :returns: A two-tuple of values or np.arrays.  If xycoords contained
        only two elements, a two-tuple is returned of the detector 1 and
        detector 2 values at that location.  If xycoords contains more than
        one  location, then the returned two-tuple will be a numpy array
        of detector 1 values, and a numpy array of detector 2 values.
        """
        bd_rows, bd_cols = rasterio.transform.rowcol(
            self.bd_aff, xycoords[0], xycoords[1]
        )
        weh_rows, weh_cols = rasterio.transform.rowcol(
            self.weh_aff, xycoords[0], xycoords[1]
        )

        bd_vals = self.bd_arr[bd_rows, bd_cols]
        weh_vals = self.weh_arr[weh_rows, weh_cols]

        return self.ds(bd_vals, weh_vals, poisson=poisson)


def main():
    args = arg_parser().parse_args()

    if args.traverse is None:
        # Make ideal detector maps
        bd_data = rasterio.open(args.burial_depth)
        weh_data = rasterio.open(args.weh)

        for prop in ("width", "height", "transform"):
            if getattr(bd_data, prop) != getattr(weh_data, prop):
                raise ValueError(
                    f"The {prop} value of the Burial Depth and WEH map are "
                    "different.  They must be the same to output detector maps."
                )

        ds = nss.DataSimulator(
            args.det1, args.det2, bounds_error=False, fill_value=None
        )

        d1, d2 = ds(bd_data.read(1).flatten(), weh_data.read(1).flatten())

        d1_arr = d1.reshape(bd_data.shape)
        d2_arr = d2.reshape(bd_data.shape)

        kwds = bd_data.profile
        write_tif(args.output, "_d1.tif", d1_arr, kwds)
        write_tif(args.output, "_d2.tif", d2_arr, kwds)
        return

    else:
        # Make an output traverse file.
        simulator = LocationSimulator(
            args.burial_depth,
            args.weh,
            args.det1,
            args.det2,
            bounds_error=False,
            fill_value=None,
        )

        with open(args.traverse, newline="") as csvin, open(
            args.output, "w", newline=""
        ) as csvout:
            reader = csv.DictReader(csvin)  # expecting at least x and y cols.
            fieldnames = reader.fieldnames + ["det1", "det2", "det1pois", "det2pois"]
            writer = csv.DictWriter(csvout, fieldnames=fieldnames)
            writer.writeheader()

            # Would it be faster to read in all the points, feed them all to the
            # simulator, and then write out points?  Maybe, iterating for now:
            for row in reader:
                coords = np.array((row["x"], row["y"]), dtype=float)
                # print(coords)
                # print(coords.shape)
                row["det1"], row["det2"] = simulator(coords)
                row["det1pois"], row["det2pois"] = simulator(coords, poisson=True)

                writer.writerow(row)

    return
