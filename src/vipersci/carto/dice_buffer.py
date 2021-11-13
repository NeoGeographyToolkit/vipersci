#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Takes a geospatial vector file and creates positive and negative buffered
versions of the regions.
"""

# Copyright 2021, Ross A. Beyer.
#
# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.

import argparse
import logging
import sys

import geopandas as gp
from shapely.geometry import Polygon, MultiPolygon
from shapely.geometry.collection import GeometryCollection
from shapely.ops import unary_union

logger = logging.getLogger(__name__)


def arg_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-b", "--buffer",
        type=float,
        help="A positive distance has an effect of dilation; a negative "
             "distance, erosion."
    )
    parser.add_argument(
        "-o",
        "--out",
        help="Output GeoPackage filename."
    )
    parser.add_argument(
        "gpkg",
        help="The geospatial file with regions to evaluate.  This file "
             "Must have only four geometries, with a category fields of "
             "Deep, Dry, Shallow, and Surficial."
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
            "The buffer value is zero, which would result in no change to "
            "the map."
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
                    categories.loc[
                        list(isr_order[0:i + 1])
                    ].dissolve()["geometry"].iloc[0]
                )

        categories.set_geometry(expanded, inplace=True)

    buffered = categories.buffer(args.buffer)

    print("Buffering complete.")

    for cutting in isr_order[:3]:  # The last geom won't reduce any others.
        for geom in isr_order[isr_order.index(cutting) + 1:]:
            buffered.loc[geom] = buffered.loc[geom].difference(
                buffered.loc[cutting]
            )

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


if __name__ == "__main__":
    sys.exit(main())
