"""Gather Rover locations from a REST-based service.
"""

# Copyright 2023, United States Government as represented by the
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
import getpass
import http.client as http_client
import logging
import sys
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
from requests.auth import HTTPBasicAuth

from vipersci import util

logger = logging.getLogger(__name__)


def arg_parser():
    parser = argparse.ArgumentParser(
        description=__doc__, parents=[util.parent_parser()]
    )
    parser.add_argument(
        "-s",
        "--start",
        default=datetime(2020, 1, 1, tzinfo=timezone.utc),
        help="An ISO8601 datetime to start the query at.",
    )
    parser.add_argument(
        "-e",
        "--end",
        default=datetime.now(tz=timezone.utc),
        help="An ISO8601 datetime to end the query at.",
    )
    parser.add_argument(
        "-f",
        "--frequency",
        help="A frequency between the start and end times, using pandas 'Offset alias' "
        "string notation (https://pandas.pydata.org/pandas-docs/stable/user_guide/"
        "timeseries.html#offset-aliases). Could be 'S' for secondly.",
    )
    parser.add_argument(
        "-u",
        "--url",
        required=True,
        help="URL to which event_times may be posted and for which location and "
        "orientation will be returned.",
    )
    parser.add_argument("--user", help="Username to authenticate to URL with.")
    parser.add_argument(
        "-p",
        "--password",
        action="store_true",
        help="If given will trigger asking for a password.",
    )
    parser.add_argument(
        "-o", "--output", type=Path, help="Output path for CSV file output."
    )
    return parser


def main():
    parser = arg_parser()
    args = parser.parse_args()
    util.set_logger(args.verbose)

    if args.verbose >= 2:
        http_client.HTTPConnection.debuglevel = 1

    basic_auth = None
    if args.password:
        if args.user:
            username = args.user
        else:
            username = getpass.getuser()

        print(f"For username {username}")
        basic_auth = HTTPBasicAuth(username, getpass.getpass())

    t_start = datetime.fromisoformat(args.start)
    t_end = datetime.fromisoformat(args.end)

    if args.frequency:
        times = pd.date_range(t_start, t_end, freq=args.frequency).tolist()

        unix_times = []
        for t in times:
            unix_times.append(t.timestamp())

        tpp = get_position_and_pose(unix_times, args.url, auth=basic_auth)
    else:
        tpp = get_position_and_pose_range(
            t_start.timestamp(), t_end.timestamp(), args.url, auth=basic_auth
        )

    if args.output is not None:
        with open(args.output, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["UTC datetime", "x", "y", "yaw"])
            for row in tpp:
                dt = datetime.fromtimestamp(row[0], tz=timezone.utc)
                writer.writerow(
                    [
                        dt.isoformat(),
                    ]
                    + list(row[1:])
                )


def get_position_and_pose(times: list, url: str, crs: str = "VIPER:910101", auth=None):
    """
    Given a list of unix times and a URL that requests can be made against,
    return a list of two-tuples whose first element is the time and
    whose second element is a three-tuple of x-location, y-location,
    and yaw.
    """

    tpp = []

    for t in times:
        logger.info(f"unix timestamp: {t}")
        position_result = requests.get(
            url,
            params={
                "event_time": t,  # Event time in unix datetime.
                "margin_seconds": 2,  # Some "margin time" around the event to search.
                "format": "xyyaw",  # Could also be xyyaw_uncertainty
                "time_format": "unix_seconds",
                "source": "ROVER",
                "limit": 0,
                "crs_code": crs,
            },
            verify=False,
            auth=auth,
            timeout=2,
        )
        logger.debug(position_result)
        position_result.raise_for_status()
        rj = position_result.json()
        logger.info(rj)

        tpp.append(
            (rj["event_seconds"], rj["location"][0], rj["location"][1], rj["yaw"])
        )

    return tpp


def get_position_and_pose_range(
    start_time, stop_time, url: str, crs: str = "VIPER:910101", auth=None
):
    tpp = []

    track_result = requests.get(
        url,
        params={
            "min_time": start_time,
            "max_time": stop_time,
            "all": False,
            "format": "xyyaw",
            "crs_code": crs,
            "time_format": "unix_seconds",
            "source": "ROVER",
            "start_end_only": False,
            "simplify": False,
            "order": "asc",
        },
        verify=False,
        auth=auth,
        timeout=2,
    )
    logger.debug(track_result)
    track_result.raise_for_status()
    rj = track_result.json()
    logger.info(rj)

    if isinstance(rj["event_seconds"], Sequence):
        for time, loc, yaw in zip(rj["event_seconds"], rj["location"], rj["yaw"]):
            tpp.append((time, loc[0], loc[1], yaw))
    else:
        tpp.append(
            (rj["event_seconds"], rj["location"][0], rj["location"][1], rj["yaw"])
        )

    return tpp


if __name__ == "__main__":
    sys.exit(main())
