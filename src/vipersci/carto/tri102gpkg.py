#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''Converts the vertices in a .tri10 file to a GeoCSV or GeoPackage file.

A .tri10 file is a whitespace separated value file where each line contains ten
elements which describe a triangular facet.  The first nine elements are the
X, Y, and Z coordinates of the verticies, in this order:
x1 y1 z1 x2 y2 z2 x3 y3 z3

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
# import csv
from pathlib import Path

import geopandas
from pyproj import CRS, Transformer
# from osgeo import ogr, osr
from shapely import Polygon

# ogr.UseExceptions()

stere_crs = "+proj=stere +lon_0={} +lat_0={} +R=1737400"
sites = dict(  # lon first, then lat
    spole=stere_crs.format(0, -90),
    npole=stere_crs.format(0, 90),
    nobile=stere_crs.format(31.1492746341015, -85.391176037601),
    # the Haworth DEMs are polar stereographic, apparently.
    haworth=stere_crs.format(0, -90),
)


def arg_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-o", "--output", help="Optional name of output file.", required=False
    )
    parser.add_argument(
        "-c", "--csv", action="store_true", required=False,
        help="Will output a GeoCSV instead of a GeoPackage file."
    )
    parser.add_argument(
        "-s", "--site", choices=sites.keys(), required=False,
        help="Specifying a site, sets the latitude and longitude for the "
             "center of projection."
    )
    parser.add_argument(
        "--s_srs",
        default="+proj=cart +a=1737400 +b=1737400",
        help="The source CRS or SRS of the .tri10 data."
    )
    parser.add_argument(
        "--t_srs",
        help="The CRS or SRS of the output file.  The various -s options are "
             "short-hands for this."
    )
    parser.add_argument(
        "-v", "--value_name",
        default="Depth (m)",
        help="This text will be used as the title of the data value field in "
             "the output file."
    )
    parser.add_argument(
        "--keep_z",
        action="store_true",
        help="Will retain the Z value in the output geometries, otherwise "
             "collapses to 2D geometries."
    )
    parser.add_argument(
        "--keep_all_facets",
        action="store_true",
        help="Will retain all of the triangular facets of the original .tri10 "
             "file, which will result in a very large file.  By default, "
             "adjoining facets with identical values will be merged into "
             "larger polygons."
    )
    parser.add_argument("file", help=".tri10 file")
    return parser


def main():
    parser = arg_parser()
    args = parser.parse_args()

    if args.sites is not None:
        t_srs = sites[args.sites]
    else:
        if args.t_srs is None:
            parser.error(
                "Neither a site (-s) nor a target SRS (--t_srs) was provided."
            )
        else:
            t_srs = args.t_srs

    if args.output is None:
        outfile = Path(args.file).with_suffix(".gpkg")
    else:
        outfile = Path(args.output)

    s_crs = CRS(args.s_srs)
    t_crs = CRS(t_srs)
    transformer = Transformer.from_crs(s_crs, t_crs)

    polys = list()
    values = list()
    with open(args.file, "r") as f:
        for line in f:
            tokens = line.split()
            poly, value = get_poly_value(transformer, tokens, args.keep_z)
            polys.append(poly)
            values.append(value)

    gdf = geopandas.GeoDataFrame(
        {args.value_name: values, "geometry": polys},
        crs=t_crs
    )

    if not args.keep_all_facets:
        gdf = gdf.dissolve(by=args.value_name)

    if args.csv:
        gdf.to_file(outfile.with_suffix(".csv"), driver="CSV")
    else:
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


def get_poly_value(transformer, tokens: list, z=True):
    in_m = list(map(lambda x: float(x) * 1000, tokens[:9]))

    v1 = transformer.transform(in_m[0], in_m[1], in_m[2])
    v2 = transformer.transform(in_m[3], in_m[4], in_m[5])
    v3 = transformer.transform(in_m[6], in_m[7], in_m[8])

    if z:
        poly = Polygon(v1, v2, v3)
    else:
        poly = Polygon(v1[-1], v2[-1], v3[-1])
    if float(tokens[9]) == -1:
        value = 0
    else:
        value = tokens[9]

    return poly, value


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


if __name__ == "__main__":
    main()
