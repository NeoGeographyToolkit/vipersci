"""Check to see if images could be made into a panorama.
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
import itertools
import logging
from datetime import datetime, timezone
from functools import partial
from pathlib import Path
from typing import Iterable, Union

import pandas as pd
import requests
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from vipersci import util
from vipersci.pds import pid as pds
from vipersci.vis.db.image_records import ImageRecord

logger = logging.getLogger(__name__)


def arg_parser():
    parser = argparse.ArgumentParser(
        description=__doc__, parents=[util.parent_parser()]
    )
    parser.add_argument(
        "--csv",
        type=Path,
        help="Path to CSV file with times and locations.  Ignored if --url is set.",
    )
    parser.add_argument(
        "-d",
        "--dburl",
        help="Database with an image_records table to read from. "
        "If not given, no database will be written to.  Example: "
        "postgresql://postgres:NotTheDefault@localhost/visdb",
    )
    parser.add_argument(
        "-s",
        "--since",
        default=0,
        help="An ISO8601 datetime after which should be searched for images "
        "in the database.",
    )
    parser.add_argument(
        "-u",
        "--until",
        default=datetime.now(tz=timezone.utc),
        help="An ISO8601 datetime before which should be searched for images "
        "in the database.",
    )
    parser.add_argument(
        "--url",
        help="URL to which event_times may be posted and for which location and "
        "orientation will be returned.",
    )
    parser.add_argument(
        "--input", nargs="*", required=False, help="VIS Image Record Product IDs."
    )
    return parser


def main():
    parser = arg_parser()
    args = parser.parse_args()
    util.set_logger(args.verbose)

    gppf = None
    if args.url is not None:
        gppf = partial(get_position_and_pose_from_mapserver, url=args.url)
    elif args.csv is not None:
        gppf = partial(get_position_and_pose_from_csv, path=args.csv)
    else:
        parser.error(
            "Neither --url nor --csv were given.  Need at least one to be a "
            "source for position and pose with time."
        )

    if args.input is not None:
        pids = list(map(pds.VISID, args.input))
        pano_groups = check(pids, gppf)

    else:
        if args.dburl is None:
            parser.error("To query images between times, you must enter a --dburl.")
        t_since = datetime.fromisoformat(args.since)
        t_until = datetime.fromisoformat(args.until)
        if args.until < args.since:
            parser.error(
                f"The -s argument ({args.since}) must be less than the -u "
                f"argument ({args.until})."
            )

        engine = create_engine(args.dburl)
        with Session(engine) as session:
            result = session.scalars(
                select(ImageRecord).where(
                    t_since <= ImageRecord.start_time, ImageRecord.start_time <= t_until
                )
            )
            pano_groups = check(result, gppf)

    for pg in pano_groups:
        print(f"For position and pose {pg[1]}:")
        for p in pg[0]:
            print(f"\t{p}")


def check(
    images: Iterable[Union[pds.VISID, ImageRecord]], get_pos_pose_func=None
) -> list:
    """
    Returns a list of two-tuples.  The first element in each two-tuple is a list of
    items from *images* which could be made into a panorama, and the second element
    is the position and pose associated with those *images*.

    The *get_pos_pose_func* should be a function that takes a list of timestamp times
    and returns an object that represents a position and pose at that time (please see
    get_position_and_pose_from_df() and get_position_and_pose_from_mapserver() in this
    module.  These functions may need to be wrapped via functools.partial() so that the
    function passed here takes only a list of timestamp times.

    If the iterable does not contain all ImageRecord objects or all VISID objects,
    a TypeError will be raised.
    """
    if get_pos_pose_func is None:
        raise ValueError("A function must be provided to get_pos_pose_func.")

    raw_vids = []
    image_records = None
    if all(map(isinstance, images, itertools.repeat(ImageRecord))):
        image_records = {}
        for im in images:
            vid = pds.VISID(im.product_id)  # type: ignore  # noqa
            image_records[vid] = im
            raw_vids.append(vid)
    elif all(map(isinstance, images, itertools.repeat(pds.VISID))):
        raw_vids = list(images)  # type: ignore  # noqa
    else:
        raise TypeError(
            "The provided iterable does not contain all ImageRecords or "
            f"all VISIDs, it is {images}."
        )

    raw_vids.sort()
    vids = pds.VISID.best_compression(raw_vids)

    vids_by_time = {}
    times = []
    for v in vids:
        if v.compression == "s":
            continue
        ts = v.datetime().timestamp()
        if ts not in vids_by_time:
            vids_by_time[ts] = v
            times.append(ts)

    tpp = get_pos_pose_func(times)
    grouped = groupby_2nd(tpp)

    pano_groups = []
    for t_list, position_pose in grouped:
        if len(t_list) > 1:
            # We have a pano group
            if image_records is not None:
                ids = [image_records[vids_by_time[t]] for t in t_list]
            else:
                ids = [vids_by_time[t] for t in t_list]
            pano_groups.append((ids, position_pose))

    return pano_groups


def get_position_and_pose_from_csv(
    times: list,
    path: Path,
    time_column=0,
    x_column=1,
    y_column=2,
    yaw_column=3,
):
    """
    Given a list of timestamp times and a Path to a CSV file with the specified columns,
    return a list of two-tuples whose first element is the time and whose
    second element is three-tuple of x-location, y-location, and yaw.

    If None is given for any of the x-, y-, or yaw- columns, they are ignored
    from the CSV read.
    """
    uc = []
    for c in (time_column, x_column, y_column, yaw_column):
        if c is not None:
            uc.append(c)

    df = pd.read_csv(path, usecols=uc)

    tpp = []
    for t in times:
        row = df.iloc[(df.iloc[:, time_column] - t).abs().argsort()[:1]]
        tpp.append((t, tuple(row.values.flatten().tolist()[1:])))

    return tpp


def get_position_and_pose_from_mapserver(
    times: list, url: str, crs: str = "VIPER:910101"
):
    """
    Given a list of times and a URL that requests can be made against,
    return a list of two-tuples whose first element is the time and
    whose second element is a three-tuple of x-location, y-location,
    and yaw.
    """

    tpp = []

    for t in times:
        position_result = requests.get(
            url,
            params={
                "event_time": t,
                "crs_code": crs,
            },
            timeout=2,
        )
        rj = position_result.json()

        tpp.append((t, (rj["location"][0], rj["location"][1], rj["yaw"])))

    return tpp


def groupby_2nd(
    tuples: list,
):
    """
    Given a list of sorted two-tuples, determine groupings based on the
    second element of the two-tuple.

    The returned list of two-tuples contains one "group" per element.  The
    first element of the two tuple is the list of input first elements that have
    the same input second element, and the second element of the two-tuple is the
    input second element.

    The list should be sorted by increasing order on the second element of the tuple.

    For example::

        >>> t = [("Alice", "foo"), ("Bob", "bar"), ("Catherine", "bar")]
        >>> g = groupby_2nd(t)
        >>> print(g)
        [(["Alice",], "foo"), (["Bob", "Catherine"], "bar")]
    """

    def keyfunc(t: tuple):
        return t[1]

    grouped = []
    for _, g in itertools.groupby(tuples, key=keyfunc):
        first = []
        second = ""
        for elem in g:
            first.append(elem[0])
            second = elem[1]
        grouped.append((first, second))

    return grouped
