#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Converts the vertices in a .triN file to a GeoCSV or GeoPackage file.

A .tri10 file is a whitespace separated value file where each line contains ten
elements which describe a triangular facet.  The first nine elements are the
X, Y, and Z coordinates of the verticies, in this order:
x1 y1 z1 x2 y2 z2 x3 y3 z3

The last element is a data value of some kind representing the value of
"the facet".  So for a depth to ice file, that value would be the depth in
meters.

The depth-to-ice .tri10 files sometimes have a -1 to indicate surface ice
(instead of zero).

These files can sometimes have more than 10 elements, and these 'triN' files
have additional columns of data values that should be associated with the
facet in the output file.

This file format is not particularly a standard, but is simple to process.
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

# import csv
from pathlib import Path

import geopandas
from pyproj import CRS, Transformer

# from osgeo import ogr, osr
from shapely.geometry import Polygon

from vipersci import util

logger = logging.getLogger(__name__)

stere_crs = "+proj=stere +lon_0={} +lat_0={} +R=1737400"
sites = dict(  # lon first, then lat
    spole=stere_crs.format(0, -90),
    npole=stere_crs.format(0, 90),
    nobile=stere_crs.format(31.1492746341015, -85.391176037601),
    # the Haworth DEMs are polar stereographic, apparently.
    haworth=stere_crs.format(0, -90),
    viper=stere_crs.format(31.6218, -85.42088),
)


def arg_parser():
    parser = argparse.ArgumentParser(
        description=__doc__, parents=[util.parent_parser()]
    )
    parser.add_argument(
        "-o", "--output", help="Optional name of output file.", required=False
    )
    parser.add_argument(
        "-c",
        "--csv",
        action="store_true",
        required=False,
        help="Will output a GeoCSV instead of a GeoPackage file.",
    )
    parser.add_argument(
        "-s",
        "--site",
        choices=sites.keys(),
        required=False,
        help="Specifying a site, sets the latitude and longitude for the "
        "center of projection.",
    )
    parser.add_argument(
        "--s_srs",
        default="+proj=cart +a=1737400 +b=1737400",
        help="The source CRS or SRS of the .tri10 data. Default: %(default)s",
    )
    parser.add_argument(
        "--t_srs",
        help="The CRS or SRS of the output file.  The various -s options are "
        "short-hands for this.",
    )
    parser.add_argument(
        "--value_names",
        default="Depth (m)",
        help="This text will be used as the title of the data value field in "
        "the output file.  If there are commas, this text is split on "
        "the commas and whitespace stripped, to produce a list of value "
        "fields in the output. Default: %(default)s",
    )
    parser.add_argument(
        "--value_columns",
        default="9",
        help="This should be a comma-separated list of integers (or just one) "
        "specifying which columns from the .tri file get the names from "
        "-v.  The first 9 columns (zero is the first) have facet "
        "coordinates, so typically this value (or list) starts at 9. "
        "Default: %(default)s",
    )
    parser.add_argument(
        "--value_file",
        help="If provided another whitespace-separated file will be read in, "
        "and the value(s) from the column(s) indicated by --value_columns "
        "will be used as the value(s).",
    )
    parser.add_argument(
        "--remove_facets",
        type=float,
        help="If provided, any facets with this value will not be included in the "
        "output GeoPackage.  Ignored if there is more than one value_column.",
    )
    parser.add_argument(
        "--replace_with_zero",
        help="If there is a value that should be replaced with zero, it can "
        "be provided here.  If the --value_name is 'Depth (m)' this will "
        "automatically be set to '-1'.  If you want to override that, "
        "you can set '--replace_with_zero 0'.",
    )
    parser.add_argument(
        "--keep_z",
        action="store_true",
        help="Will retain the Z value in the output geometries, otherwise "
        "collapses to 2D geometries.",
    )
    parser.add_argument(
        "--keep_all_facets",
        action="store_true",
        help="Will retain all of the triangular facets of the original .tri10 "
        "file, which will result in a very large file.  By default, "
        "adjoining facets with identical values will be merged into "
        "larger polygons.",
    )
    parser.add_argument("file", help=".tri10 file")
    return parser


def arg_checks(args):
    value_keys = list(map(lambda x: x.strip(), args.value_names.strip().split(",")))
    col_idxs = list(
        map(lambda x: int(x.strip()), args.value_columns.strip().split(","))
    )

    if not args.keep_all_facets and len(value_keys) > 1:
        raise ValueError(
            "In order to dissolve facets into larger polygons, there can "
            "be only one --value_column.  Either reduce to one, or set "
            "--keep_all_facets."
        )

    if args.site is not None:
        t_srs = sites[args.site]
    else:
        if args.t_srs is None:
            raise ValueError(
                "Neither a site (-s) nor a target SRS (--t_srs) was provided."
            )
        else:
            t_srs = args.t_srs

    if args.output is None:
        outfile = Path(args.file).with_suffix(".gpkg")
    else:
        outfile = Path(args.output)

    if "Depth (m)" in args.value_names:
        replace_with_zero = -1
    else:
        replace_with_zero = args.replace_with_zero

    return value_keys, col_idxs, t_srs, outfile, replace_with_zero


def main():
    parser = arg_parser()
    args = parser.parse_args()
    util.set_logger(args.verbose)

    try:
        (value_keys, col_idxs, t_srs, outfile, replace_with_zero) = arg_checks(args)
    except ValueError as err:
        parser.error(str(err))

    s_crs = CRS(args.s_srs)
    t_crs = CRS(t_srs)
    transformer = Transformer.from_crs(s_crs, t_crs)

    values = {k: [] for k in value_keys}

    polys = list()
    with open(args.file, "r") as f:
        logger.info(f"Reading vertices from {args.file}")
        for line in f:
            tokens = line.split()

            if len(col_idxs) == 1 and float(tokens[col_idxs[0]]) == args.remove_facets:
                continue

            poly = vertexes_to_poly(transformer, tokens[:9], args.keep_z)
            polys.append(poly)

            for i, col in enumerate(col_idxs):
                values[value_keys[i]].append(
                    replace_with(0, replace_with_zero, tokens[col])
                )

    if args.value_file is not None:
        values = {k: [] for k in value_keys}  # Re-initialize and empty.
        with open(args.value_file, "r") as vf:
            for line in vf:
                tokens = line.split()
                for i, col in enumerate(col_idxs):
                    values[value_keys[i]].append(
                        replace_with(0, replace_with_zero, tokens[col])
                    )

        if len(values[value_keys[0]]) != len(polys):
            parser.error(
                "The provided value_file has a different number of entries "
                "than the provided .tri file with facet vertices."
            )

    values["geometry"] = polys
    gdf = geopandas.GeoDataFrame(values, crs=t_crs)
    logger.info(gdf.describe())

    if not args.keep_all_facets:
        logger.info("Dissolving polygons.")
        gdf = gdf.dissolve(by=value_keys[0])

    if args.csv:
        gdf.to_file(outfile.with_suffix(".csv"), driver="CSV")
    else:
        logger.info(f"Writing {outfile}")
        gdf.to_file(outfile, driver="GPKG")

    # if args.csv:
    #     with open(args.file, "r") as f:
    #         with open(outfile.with_suffix(".csv"), "w", newline="") as csvfile:
    #             writer = csv.writer(csvfile)
    #             writer.writerow(["WKT", args.value_name])
    #             for line in f:
    #                 tokens = line.split()
    #                 writer.writerow([get_wkt_value(transformer, tokens)])
    # else:
    #     # Write GeoPackage
    #     driver = ogr.GetDriverByName("GPKG")
    #     datasource = driver.CreateDataSource(str(outfile))
    #     srs = osr.SpatialReference()
    #     srs.ImportFromWkt(pstere.to_wkt())
    #     layer = datasource.CreateLayer("depth", srs, ogr.wkbPolygon25D)
    #     layer.CreateField(ogr.FieldDefn(args.value_name, ogr.OFTReal))

    #     with open(args.file, "r") as f:
    #         for line in f:
    #             tokens = line.split()
    #             wkt, value = get_wkt_value(transformer, tokens)
    #             feature = ogr.Feature(layer.GetLayerDefn())
    #             feature.SetField(args.value_name, value)
    #             feature.SetGeometry(ogr.CreateGeometryFromWkt(wkt))
    #             layer.CreateFeature(feature)

    #     # This closes and saves the data source
    #     del datasource

    return


def vertexes_to_poly(transformer, tokens: list, z=True):
    in_m = list(map(lambda x: float(x) * 1000, tokens))

    v1 = transformer.transform(in_m[0], in_m[1], in_m[2])
    v2 = transformer.transform(in_m[3], in_m[4], in_m[5])
    v3 = transformer.transform(in_m[6], in_m[7], in_m[8])

    if z:
        poly = Polygon([v1, v2, v3])
    else:
        poly = Polygon([v1[:-1], v2[:-1], v3[:-1]])

    if poly.area == 0:
        raise ValueError(f"This polygon has zero area: {poly}")

    return poly


def replace_with(replacement_val, replacement_check, value):
    if float(value) == replacement_check:
        return replacement_val
    else:
        return float(value)


# def get_wkt_value(transformer, tokens: list):
#     in_m = list(map(lambda x: float(x) * 1000, tokens[:9]))
#
#     v1 = transformer.transform(in_m[0], in_m[1], in_m[2])
#     v2 = transformer.transform(in_m[3], in_m[4], in_m[5])
#     v3 = transformer.transform(in_m[6], in_m[7], in_m[8])
#
#     wkt = make_wkt(v1, v2, v3)
#     if float(tokens[9]) == -1:
#         value = 0
#     else:
#         value = tokens[9]
#
#     return wkt, value


# def make_wkt(v1: list, v2: list, v3: list) -> str:
#     c_list = ", ".join(
#         [
#             " ".join(map(str, v1)),
#             " ".join(map(str, v2)),
#             " ".join(map(str, v3)),
#             " ".join(map(str, v1))
#         ]
#     )
#     return (f"POLYGON Z (({c_list}))")
