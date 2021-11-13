#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Determines accrual statistics based on geospatial vector files containing
regions of interest and a path geometry.

The geospatial files that can be provided are any that can be opened by
geopandas.read_file() which includes GeoPackages, Shapefiles, GeoJSON, and
more.
"""

# Copyright 2021, vipersci developers.
#
# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.

import argparse
from collections import Counter
import logging
import sys

import geopandas as gp
from shapely.geometry import LineString, box

logger = logging.getLogger(__name__)


def arg_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-a", "--areas",
        help="The geospatial file containing polygons or multi-polygons to "
             "evaluate the path against.  There should be one (multi)polygon "
             "for each category."
    )
    parser.add_argument(
        "--iloc",
        default=0,
        type=int,
        help="If the path file has more than one geometry, select this "
             "indexed geometry."
    )
    parser.add_argument(
        "path",
        help="A geospatial file that contains geometries."
    )
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

    if not box(*areas.total_bounds).contains(path["geometry"]):
        parser.error(
            "The first geometry in the path is not entirely contained within "
            "the area's bounding box."
        )

    accrual = accumulate(path["geometry"], areas)

    accumulated_length = sum(accrual.values())

    if accumulated_length != path["geometry"].length:
        print(f"Sum of the counted lengths: {accumulated_length}")
        print(f"This is different from the input total length!")

    print(f'Total length: {path["geometry"].length}')
    print(accrual)


def accumulate(
    path: LineString, areas: gp.GeoDataFrame, counter: dict=None
) -> Counter:
    """Returns a collections.Counter of floating point accumulations
    of the length of *Path* against each of the geometries in *areas*.

    The *path* LineString is expected to be in the projection/CRS of *areas*.

    If a *counter* dict-like (which can be a collections.Counter object)
    is provided, returned accumulations will be added to those values
    provided in *counter*.
    """
    if counter is None:
        counter = Counter()
    else:
        counter = Counter(counter)

    for area in areas.itertuples():
        counter[area.category] += path.intersection(area.geometry).length

    return counter


if __name__ == "__main__":
    sys.exit(main())
