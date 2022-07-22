# -*- coding: utf-8 -*-
"""
Takes a pair of maps where one map has values for Detector 1 and the other
map has values for Detector 2, and produces Burial Depth and WEH% maps.
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
import logging
from pathlib import Path
import sys

import numpy as np
import rasterio

from vipersci import nss

logger = logging.getLogger(__name__)


def arg_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    # Sooo many inputs each time.  Kind of a mess.
    # Should definitely set up @file config reading.
    parser.add_argument(
        "--bd_mod",
        type=Path,
        required=True,
        help="A CSV file provided by the NSS team with the Burial Depth "
             "model."
    )
    parser.add_argument(
        "--det1",
        type=Path,
        required=True,
        help="A GeoTIFF file."
    )
    parser.add_argument(
        "--det2",
        type=Path,
        required=True,
        help="A GeoTIFF file."
    )
    parser.add_argument(
        "-o", "--output",
        default="nss_model_",
        type=Path,
        help="The output prefix.  Will create three TIFF files that end in "
             "'bd.tif', 'weh.tif', and 'uweh.tif' and start with this. "
             "Default: %(default)s"
    )
    parser.add_argument(
        "--weh_mod",
        type=Path,
        required=True,
        help="A CSV file provided by the NSS team with the WEH model."
    )

    return parser


def main():
    args = arg_parser().parse_args()

    det1_data = rasterio.open(args.det1)
    det1 = det1_data.read(1, masked=True)
    det2_data = rasterio.open(args.det2)
    det2 = det2_data.read(1, masked=True)

    nodata_val = -1
    bd_model = nss.model(
        args.bd_mod, fill_value=nodata_val, bounds_error=False
    )
    weh_model = nss.model(
        args.weh_mod, fill_value=nodata_val, bounds_error=False
    )

    bd_arr = np.full_like(det1, nodata_val, dtype=np.double)
    weh_arr = np.full_like(det1, nodata_val, dtype=np.double)

    bd_arr[~det1.mask] = bd_model(np.column_stack(
        (det1.compressed(), det2.compressed())
    ))
    weh_arr[~det1.mask] = weh_model(np.column_stack(
        (det1.compressed(), det2.compressed())
    ))
    uweh_arr = nss.uniform_weh(
        det1.filled(nodata_val), fill_value=nodata_val, bounds_error=False
    )

    kwds = det1_data.profile
    kwds["nodata"] = nodata_val
    kwds["dtype"] = np.double

    write_tif(args.output, "bd.tif", bd_arr, kwds)
    write_tif(args.output, "weh.tif", weh_arr, kwds)
    write_tif(args.output, "uweh.tif", uweh_arr, kwds)

    return


def write_tif(path: Path, ending: str, arr: np.array, kwds: dict):
    with rasterio.open(
        path.with_name(path.name + ending), "w", **kwds
    ) as dst_dataset:
        dst_dataset.write(arr, 1)
    return


if __name__ == "__main__":
    sys.exit(main())
