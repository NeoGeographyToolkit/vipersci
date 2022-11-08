# -*- coding: utf-8 -*-
"""
Takes a traverse of positions and the following maps: Insolation, Surface
Temperatures, and Ice Stability Depth, and simulates
what the OH and H2O band depths would be.
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

from vipersci import nirvss
from vipersci.carto.nss_modeler import write_tif

logger = logging.getLogger(__name__)


def arg_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-b",
        "--burial_depth",
        type=Path,
        required=True,
        help="A GeoTIFF map whose pixels are the burial depth of the water layer.",
    )
    parser.add_argument(
        "-i",
        "--insolation",
        type=Path,
        required=True,
        help="A GeoTIFF map whose pixels are the insolation value of the surface.",
    )
    parser.add_argument(
        "--temperature",
        type=Path,
        required=True,
        help="A GeoTIFF map whose pixels are the surface temperature.",
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

    return parser


class LocationSimulator:
    def __init__(
        self,
        bd_map: Path,
        insl_map: Path,
        temp_map: Path,
    ):
        """
        :param bd_map: The path to the Burial Depth map.
        :type bd_map: Path
        :param insl_map: The path to the Insolation map.
        :type insl_map: Path
        :param temp_map: The path to the Surface Temperature map.
        :type temp_map: Path

        """
        self.bd_aff, self.bd_arr = self._init_map(bd_map)
        self.insl_aff, self.insl_arr = self._init_map(insl_map)
        self.temp_aff, self.temp_arr = self._init_map(temp_map)

        return

    @staticmethod
    def _init_map(raster: Path):
        # Helper function for __init__()
        data = rasterio.open(raster)
        return data.transform, data.read(1)

    def __call__(self, xycoords: np.ndarray, poisson=False):
        """
        Returns simulated H2O and OH band depth values at the given
        location(s).

        :param xycoords:  A sequence or np.array object of shape (2, ...)
        indicating the projected x, y coordinate to simulate the data for.
        :returns: A two-tuple of values or np.arrays.  If xycoords contained
        only two elements, a two-tuple is returned of the H2O and
        OH band depth values at that location.  If xycoords contains more than
        one  location, then the returned two-tuple will be a numpy array
        of H20 band depth values, and a numpy array of OH band depth values.
        """
        bd_rows, bd_cols = rasterio.transform.rowcol(
            self.bd_aff, xycoords[0], xycoords[1]
        )
        insl_rows, insl_cols = rasterio.transform.rowcol(
            self.insl_aff, xycoords[0], xycoords[1]
        )
        temp_rows, temp_cols = rasterio.transform.rowcol(
            self.temp_aff, xycoords[0], xycoords[1]
        )

        bd_vals = self.bd_arr[bd_rows, bd_cols]
        insl_vals = self.insl_arr[insl_rows, insl_cols]
        temp_vals = self.temp_arr[temp_rows, temp_cols]

        h2o_vals = nirvss.band_depth_H2O(temp_vals, bd_vals)
        oh_vals = nirvss.band_depth_OH(insl_vals)

        return h2o_vals, oh_vals


def main():
    args = arg_parser().parse_args()

    if args.traverse is None:
        # Make ideal detector maps
        bd_data = rasterio.open(args.burial_depth)
        insl_data = rasterio.open(args.insolation)
        temp_data = rasterio.open(args.temperature)

        for a, b in zip((bd_data, insl_data), (insl_data, temp_data)):
            for prop in ("width", "height", "transform"):
                if getattr(a, prop) != getattr(b, prop):
                    raise ValueError(
                        f"The {prop} value of the {a.name} and {b.name} maps are "
                        "different.  They must be the same to output detector maps."
                    )

        h2o = nirvss.band_depth_H2O(
            temp_data.read(1).flatten(), bd_data.read(1).flatten()
        )
        oh = nirvss.band_depth_OH(insl_data.read(1).flatten())

        h2o_arr = h2o.reshape(bd_data.shape)
        oh_arr = oh.reshape(bd_data.shape)

        kwds = bd_data.profile
        write_tif(args.output, "_h2o.tif", h2o_arr, kwds)
        write_tif(args.output, "_oh.tif", oh_arr, kwds)
        return

    else:
        # Make an output traverse file.
        simulator = LocationSimulator(
            args.burial_depth,
            args.insolation,
            args.temperature,
        )

        with open(args.traverse, newline="") as csvin, open(
            args.output, "w", newline=""
        ) as csvout:
            reader = csv.DictReader(csvin)  # expecting at least x and y cols.
            fieldnames = reader.fieldnames + [
                "bd_h2o",
                "bd_oh",
            ]
            writer = csv.DictWriter(csvout, fieldnames=fieldnames)
            writer.writeheader()

            # Would it be faster to read in all the points, feed them all to the
            # simulator, and then write out points?  Maybe, iterating for now:
            for row in reader:
                coords = np.array((row["x"], row["y"]), dtype=float)
                # print(coords)
                # print(coords.shape)
                row["bd_h2o"], row["bd_oh"] = simulator(coords)

                writer.writerow(row)

    return
