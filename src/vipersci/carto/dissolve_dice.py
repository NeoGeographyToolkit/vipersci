#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Takes GPKG file nominally created by tri102gpkg.py, and creates a simplified
geometry of the different ISR types.
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
import pandas as pd
import shapely

logger = logging.getLogger(__name__)


def arg_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-o",
        "--out",
        help="Output GeoPackage filename"
    )
    parser.add_argument(
        "gpkg", help="The geospatial file containing polygon geometries."
    )

    return parser


def main():
    args = arg_parser().parse_args()

    df = gp.read_file(args.gpkg)

    print("Read in file.")

    if (df.has_z).any():
        df['geometry'] = df.apply(
            lambda row: shapely.ops.transform(
                lambda x, y, z=None: (x, y),
                row["geometry"]
            ),
            axis=1,
            result_type="expand"
        )

        print("Converted geometries to 2D.")
    # print(df)

    # based on VIPER-SCI-PLN-002:
    # 0 m: Surficial
    # 0 - 0.5 m: Shallow
    # 0.5 - 1 m: Deep
    # > 1 m: Dry
    df['category'] = pd.cut(
        df["Depth (m)"],
        (-1, 0, 0.5, 1, 10),
        labels=["Surficial", "Shallow", "Deep", "Dry"]
    ).astype(str)

    print("Added categories.")

    dissolved = df.dissolve(by="category")

    print("Dissolved geometries.")

    dissolved.to_file(args.out, driver="GPKG")


if __name__ == "__main__":
    sys.exit(main())
