#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Determines accrual statistics based on geospatial vector files containing
regions of interest and a path geometry.

The geospatial files that can be provided are any that can be opened by
geopandas.read_file() which includes GeoPackages, Shapefiles, GeoJSON, and
more.
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
from collections import Counter
from typing import Optional

import geopandas as gp
from shapely.geometry import LineString, box


def arg_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-a",
        "--areas",
        help="The geospatial file containing polygons or multi-polygons to "
        "evaluate the path against.  There should be one (multi)polygon "
        "for each category.",
    )
    parser.add_argument(
        "--iloc",
        default=0,
        type=int,
        help="If the path file has more than one geometry, select this "
        "indexed geometry.",
    )
    parser.add_argument("path", help="A geospatial file that contains geometries.")
    return parser


def main():
    parser = arg_parser()
    args = parser.parse_args()

    df = gp.read_file(args.path)
    path = df.iloc[args.iloc]
    # print(path)

    areas = gp.read_file(args.areas)

    if df.crs != areas.crs:
        parser.error(
            f"""\
The area and path have different coordinate reference systems.
    area CRS: {areas.crs}
    path CRS: {df.crs}
"""
        )

    try:
        accrual = accumulate(path["geometry"], areas)
    except ValueError as err:
        parser.error(err.msg)

    accumulated_length = sum(accrual.values())

    if accumulated_length != path["geometry"].length:
        print(f"Sum of the counted lengths: {accumulated_length}")
        print("This is different from the input total length!")

    print(f'Total length: {path["geometry"].length}')
    print(accrual)


def accumulate(
    path: LineString, areas: gp.GeoDataFrame, counter: Optional[dict] = None
) -> Counter:
    """Returns a collections.Counter of floating point accumulations
    of the length of *Path* against each of the geometries in *areas*.

    The *path* LineString is expected to be in the projection/CRS of *areas*.

    If a *counter* dict-like (which can be a collections.Counter object)
    is provided, returned accumulations will be added to those values
    provided in *counter*.
    """
    if not box(*areas.total_bounds).contains(path["geometry"]):
        raise ValueError(
            "The specified path geometry is not entirely contained within "
            "the area's bounding box."
        )

    if counter is None:
        counter = Counter()
    else:
        counter = Counter(counter)

    for area in areas.itertuples():
        counter[area.category] += path.intersection(area.geometry).length

    return counter
