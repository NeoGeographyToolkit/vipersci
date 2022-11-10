#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Takes a geospatial vector file and creates either positive or negative
buffered versions of the regions.
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

import geopandas as gp
from shapely.geometry import Polygon, MultiPolygon
from shapely.geometry.collection import GeometryCollection
from shapely.ops import unary_union


def arg_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-b",
        "--buffer",
        type=float,
        help="A positive distance has an effect of dilation; a negative "
        "distance, erosion.",
    )
    parser.add_argument("-o", "--out", help="Output GeoPackage filename.")
    parser.add_argument(
        "gpkg",
        help="The geospatial file with regions to evaluate.  This file "
        "Must have only four geometries, with a category fields of "
        "Deep, Dry, Shallow, and Surficial.",
    )

    return parser


def main():
    isr_order = ("Surficial", "Shallow", "Deep", "Dry")
    index_col = "category"

    parser = arg_parser()
    args = parser.parse_args()

    df = gp.read_file(args.gpkg)
    print("Read in file.")

    categories = df.set_index(index_col)

    if args.buffer == 0:
        parser.error(
            "The buffer value is zero, which would result in no change to the map."
        )
    elif args.buffer < 0:
        # Since we are shrinking the geometries, we must first put them
        # together.
        expanded = list()
        for cat in categories.index:
            if cat == isr_order[0]:
                # The first geometry doesn't combine
                expanded.append(categories.loc[isr_order[0]]["geometry"])
            else:
                # The rest do:
                i = isr_order.index(cat)
                expanded.append(
                    categories.loc[list(isr_order[0 : i + 1])]
                    .dissolve()["geometry"]
                    .iloc[0]
                )

        categories.set_geometry(expanded, inplace=True)

    buffered = categories.buffer(args.buffer)

    print("Buffering complete.")

    for cutting in isr_order[:3]:  # The last geom won't reduce any others.
        for geom in isr_order[isr_order.index(cutting) + 1 :]:
            buffered.loc[geom] = buffered.loc[geom].difference(buffered.loc[cutting])

    # The differencing may have resulted in a GeometryCollection instead
    # of a clean MultiPolygon.
    cleaned = buffered.apply(clean)

    print("Differencing complete.")

    cleaned.to_file(args.out, driver="GPKG")


def clean(geometry):
    if isinstance(geometry, GeometryCollection):
        polys = list()
        for geom in geometry:
            if isinstance(geom, (Polygon, MultiPolygon)):
                polys.append(geom)
        return unary_union(polys)

    else:
        return geometry
