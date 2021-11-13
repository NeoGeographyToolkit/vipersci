#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''Converts the vertices in a .tri10 file to a GeoCSV or GeoPackage file.

A .tri10 file is a comma separated value file where each line contains ten
elements which describe a triangular facet.  The first nine elements are the
X, Y, and Z coordinates of the verticies, in this order
x1, y1, z1, x2, y2, z2, x3, y3, z3

The last element is a data value of some kind representing the value of
"the facet".  So for a depth to ice file, that value would be the depth in
meters.

The depth-to-ice .tri10 files sometimes have a -1 to indicate surface ice
(instead of zero).

This file format is not particularly a standard, but is simple to process.
'''

# Copyright 2021, vipersci developers.
#
# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.

import argparse
import csv

from pathlib import Path
from pyproj import CRS, Transformer
from osgeo import ogr, osr

ogr.UseExceptions()

sites = dict(  # lon first, then lat
    nobile=(31.1492746341015, -85.391176037601),
    haworth=(0, -90),  # the Haworth DEMs are polar stereographic, apparently.
    spole=(0, -90),
    npole=(0, 90)
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-o", "--output", help="Optional name of output file.", required=False
    )
    parser.add_argument(
        "-c", "--csv", action="store_true", required=False,
        help="Will output a GeoCSV instead of a GeoPackage file."
    )
    parser.add_argument(
        "--lat", type=float, required=False,
        help="Latitude for the center of the stereographic projection."
    )
    parser.add_argument(
        "--lon", type=float, required=False,
        help="Longitude for the center of the stereographic projection."
    )
    parser.add_argument(
        "-s", "--site", choices=sites.keys(), required=False,
        help="Specifying a site, sets the latitude and longitude for the "
             "center of projection."
    )
    parser.add_argument('file', help='.tri10 file')

    args = parser.parse_args()

    try:
        lon, lat = get_lonlat(args, sites)
    except ValueError as err:
        parser.error(err)

    if args.output is None:
        outfile = Path(args.file).with_suffix(".gpkg")
    else:
        outfile = Path(args.output)

    radius = 1737400
    cart = CRS.from_proj4(f"+proj=cart +a={radius} +b={radius}")
    # pstere = CRS.from_proj4(f"+proj=stere +lat_0=90 +lat_ts=-90 +R={radius}")
    pstere = CRS.from_proj4(
        f"+proj=stere +lat_0={lat} +lon_0={lon} +R={radius}"
    )
    transformer = Transformer.from_crs(cart, pstere)

    if args.csv:
        with open(args.file, "r") as f:
            with open(outfile.with_suffix(".csv"), "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["wkt", "depth"])
                for line in f:
                    tokens = line.split()
                    writer.writerow([get_wkt_depth(transformer, tokens)])
    else:
        # Write GeoPackage
        driver = ogr.GetDriverByName("GPKG")
        datasource = driver.CreateDataSource(str(outfile))
        srs = osr.SpatialReference()
        srs.ImportFromWkt(pstere.to_wkt())
        layer = datasource.CreateLayer("depth", srs, ogr.wkbPolygon25D)
        layer.CreateField(ogr.FieldDefn("Depth (m)", ogr.OFTReal))

        with open(args.file, "r") as f:
            for line in f:
                tokens = line.split()
                wkt, depth = get_wkt_depth(transformer, tokens)
                feature = ogr.Feature(layer.GetLayerDefn())
                feature.SetField("Depth (m)", depth)
                feature.SetGeometry(ogr.CreateGeometryFromWkt(wkt))
                layer.CreateFeature(feature)

        # This closes and saves the data source
        del datasource


def get_lonlat(args, sites):
    if args.site is None:
        if args.lat is None:
            raise ValueError("There is no latitude.")
        else:
            lat = args.lat

        if args.lon is None:
            raise ValueError("There is no longitude.")
        else:
            lon = args.lon
    else:
        lon, lat = sites[args.site]

    return lon, lat


def get_wkt_depth(transformer, tokens: list):
    in_m = list(map(lambda x: float(x) * 1000, tokens[:9]))

    v1 = transformer.transform(in_m[0], in_m[1], in_m[2])
    v2 = transformer.transform(in_m[3], in_m[4], in_m[5])
    v3 = transformer.transform(in_m[6], in_m[7], in_m[8])

    wkt = make_wkt(v1, v2, v3)
    if float(tokens[9]) == -1:
        depth = 0
    else:
        depth = tokens[9]

    return wkt, depth


def make_wkt(v1: list, v2: list, v3: list) -> str:
    c_list = ", ".join(
        [
            " ".join(map(str, v1)),
            " ".join(map(str, v2)),
            " ".join(map(str, v3)),
            " ".join(map(str, v1))
        ]
    )
    return (f"POLYGON Z (({c_list}))")


if __name__ == "__main__":
    main()
