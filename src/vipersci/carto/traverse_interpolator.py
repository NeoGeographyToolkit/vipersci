#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Takes input JSON file, and creates an output CSV file.
"""

# Copyright 2022, United States Government as represented by the
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
import csv
import logging
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Point

logger = logging.getLogger(__name__)


def arg_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-i",
        "--interval",
        type=float,
        default=1.0,
        help="The time interval in seconds to interpolate the provided " "traverse at.",
    )
    parser.add_argument("-o", "--output", type=Path, help="Output CSV file.")
    parser.add_argument(
        "json",
        type=Path,
        help="The JSON file that contains a traverse."
        # Assumed to be GeoJSON from the Map Server.
    )

    return parser


def main():
    args = arg_parser().parse_args()

    points = list()
    df = gpd.read_file(args.json)
    # ['start_time', 'uuid', 'item_type', 'end_time', 'duration', 'name',
    # 'color', 'text_color', 'activity_type', 'style', 'geometry']

    last_point = Point(0, 0)
    last_time = None
    for row in df.itertuples():
        if row.name != "Driving":
            continue

        # If two consecutive "Driving" segments have the same end and
        # beginning coordinates, but the time is different, that means
        # that time passed while we sat there.
        # print(f"Points: {row.geometry.coords[0]} == {last_point.coords[0]} ")
        # print(f"Times: {row.start_time} != {last_time}")
        if (
            row.geometry.coords[0] == last_point.coords[0]
            and row.start_time != last_time
        ):
            time_intervals = interval_count(last_time, row.start_time, args.interval)
            for s in range(time_intervals):
                t = last_time + (s * args.interval)
                points.append({"time": t, "x": last_point.x, "y": last_point.y})

        time_intervals = interval_count(row.start_time, row.end_time, args.interval)
        for s in range(time_intervals):
            t = row.start_time + (s * args.interval)
            p = row.geometry.interpolate(s / time_intervals, normalized=True)
            points.append({"time": t, "x": p.x, "y": p.y})
        last_time = row.end_time
        last_point = Point(row.geometry.coords[-1])

    with open(args.output, "w", newline="") as csvfile:
        fieldnames = ["time", "x", "y"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for d in points:
            writer.writerow(d)

    return


def interval_count(start, stop, step):
    # This seems too simple, and I feel like there should be a one-liner that
    # does this.  Until there is, this pattern gets used twice, so a function
    # it is.
    total_time = stop - start
    return int(total_time / step)
