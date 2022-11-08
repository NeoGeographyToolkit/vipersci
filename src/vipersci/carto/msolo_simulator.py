# -*- coding: utf-8 -*-
"""
Takes a traverse of positions and the following maps: Surface
Temperatures and Ice Stability Depth, and simulates
what the mass20 and mass40 signal intensities would be.
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

from vipersci import msolo
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
        temp_rows, temp_cols = rasterio.transform.rowcol(
            self.temp_aff, xycoords[0], xycoords[1]
        )

        bd_vals = self.bd_arr[bd_rows, bd_cols]
        temp_vals = self.temp_arr[temp_rows, temp_cols]

        m20 = msolo.mass20(temp_vals, bd_vals)
        m40 = msolo.mass40(temp_vals)

        return m20, m40


def main():
    args = arg_parser().parse_args()

    if args.traverse is None:
        # Make ideal detector maps
        bd_data = rasterio.open(args.burial_depth)
        temp_data = rasterio.open(args.temperature)

        for prop in ("width", "height", "transform"):
            if getattr(bd_data, prop) != getattr(temp_data, prop):
                raise ValueError(
                    f"The {prop} value of the {bd_data.name} and {temp_data.name} maps "
                    "are different.  They must be the same to output detector maps."
                )

        m20 = msolo.mass20(temp_data.read(1).flatten(), bd_data.read(1).flatten())
        m40 = msolo.mass40(temp_data.read(1).flatten())

        m20_arr = m20.reshape(bd_data.shape)
        m40_arr = m40.reshape(bd_data.shape)

        kwds = bd_data.profile
        write_tif(args.output, "_m20.tif", m20_arr, kwds)
        write_tif(args.output, "_m40.tif", m40_arr, kwds)
        return

    else:
        # Make an output traverse file.
        simulator = LocationSimulator(
            args.burial_depth,
            args.temperature,
        )

        with open(args.traverse, newline="") as csvin, open(
            args.output, "w", newline=""
        ) as csvout:
            reader = csv.DictReader(csvin)  # expecting at least x and y cols.
            fieldnames = reader.fieldnames + [
                "m20",
                "m40",
            ]
            writer = csv.DictWriter(csvout, fieldnames=fieldnames)
            writer.writeheader()

            # Would it be faster to read in all the points, feed them all to the
            # simulator, and then write out points?  Maybe, iterating for now:
            for row in reader:
                coords = np.array((row["x"], row["y"]), dtype=float)
                # print(coords)
                # print(coords.shape)
                row["m20"], row["m40"] = simulator(coords)

                writer.writerow(row)

    return
