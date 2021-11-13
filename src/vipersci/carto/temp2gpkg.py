#!/usr/bin/env python
'''Takes the vertices in a .tri10 file and the value in a text file and
converts to a GeoCSV or GeoPackage file.'''

# Copyright 2021, Ross A. Beyer (rbeyer@rossbeyer.net)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import csv

from pathlib import Path
from pyproj import CRS, Transformer
from osgeo import ogr, osr

from tri102csv import sites, get_wkt_depth, get_lonlat

ogr.UseExceptions()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-t", "--tri", help="tri10 file with mesh vertices."
    )
    parser.add_argument(
        "-o", "--output", help="Optional name of output file.", required=False
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

    driver = ogr.GetDriverByName("GPKG")
    datasource = driver.CreateDataSource(str(outfile.with_suffix(".gpkg")))
    srs = osr.SpatialReference()
    srs.ImportFromWkt(pstere.to_wkt())
    layer = datasource.CreateLayer("temp", srs, ogr.wkbPolygon25D)
    layer.CreateField(ogr.FieldDefn("Surface Temperature (K)", ogr.OFTReal))

    with open(args.file, "r") as tempfile:
        with open(args.tri, "r") as trifile:
            for tline, triline in zip(tempfile, trifile):
                wkt, depth = get_wkt_depth(transformer, triline.split())
                temperature = tline.split()[-1]
                feature = ogr.Feature(layer.GetLayerDefn())
                feature.SetField("Surface Temperature (K)", temperature)
                feature.SetGeometry(ogr.CreateGeometryFromWkt(wkt))
                layer.CreateFeature(feature)

    # This closes and saves the data source
    del datasource


if __name__ == "__main__":
    main()
