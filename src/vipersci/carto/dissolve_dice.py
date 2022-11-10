#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Takes GPKG file nominally created by tri2gpkg.py, and creates a simplified
geometry of the different ISR types.
"""

# Copyright 2021-2022, United States Government as represented by the
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

import geopandas as gp
import pandas as pd
import shapely

logger = logging.getLogger(__name__)


def arg_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-o", "--out", help="Output GeoPackage filename")
    parser.add_argument(
        "gpkg", help="The geospatial file containing polygon geometries."
    )

    return parser


def main():
    args = arg_parser().parse_args()

    df = gp.read_file(args.gpkg)

    print("Read in file.")

    if (df.has_z).any():
        df["geometry"] = df.apply(
            lambda row: shapely.ops.transform(
                lambda x, y, z=None: (x, y), row["geometry"]
            ),
            axis=1,
            result_type="expand",
        )

        print("Converted geometries to 2D.")
    # print(df)

    # based on VIPER-SCI-PLN-002:
    # 0 m: Surficial
    # 0 - 0.5 m: Shallow
    # 0.5 - 1 m: Deep
    # > 1 m: Dry
    df["category"] = pd.cut(
        df["Depth (m)"].astype(float),
        (-1, 0, 0.5, 1, 10),
        labels=["Surficial", "Shallow", "Deep", "Dry"],
    ).astype(str)

    print("Added categories.")

    dissolved = df.dissolve(by="category")

    print("Dissolved geometries.")

    dissolved.to_file(args.out, driver="GPKG")
