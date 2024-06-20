#!/usr/bin/env python
"""This module has tests for the vis.pano-check functions."""

# Copyright 2023, vipersci developers.
#
# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.

import unittest
from argparse import ArgumentParser
from datetime import datetime, timezone
from functools import partial
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from vipersci.pds import pid as pds
from vipersci.vis import pano_check as pc
from vipersci.vis.db.image_records import ImageRecord


class TestFunctions(unittest.TestCase):
    def test_arg_parser(self):
        p = pc.arg_parser()
        self.assertIsInstance(p, ArgumentParser)

    def test_groupby_2nd(self):
        tuples = [
            ("Alice", "foo"),
            ("Bob", "bar"),
            ("Catherine", "bar"),
        ]
        truth = [
            (
                [
                    "Alice",
                ],
                "foo",
            ),
            (["Bob", "Catherine"], "bar"),
        ]

        grouped = pc.groupby_2nd(tuples)
        self.assertEqual(truth, grouped)


class TestPositionAndPose(unittest.TestCase):
    def setUp(self):
        self.datetimes = (
            datetime(2024, 11, 27, 1, 2, 3, tzinfo=timezone.utc),
            datetime(2024, 11, 28, 1, 2, 3, tzinfo=timezone.utc),
            datetime(2024, 11, 29, 1, 2, 3, tzinfo=timezone.utc),
            datetime(2024, 11, 30, 1, 2, 3, tzinfo=timezone.utc),
        )
        self.times = [x.timestamp() for x in self.datetimes]
        self.x = (-1, 2, 3, 4)
        self.y = (-1, 2, 3, 4)
        self.yaw = (0, 45, 90, 270)

        self.truth = [
            (t, (x, y, yaw))
            for t, x, y, yaw in zip(self.times, self.x, self.y, self.yaw)
        ]

        self.df = pd.DataFrame(
            data={
                "c0": pd.Series(self.times),
                "c1": pd.Series(self.x),
                "c2": pd.Series(self.y),
                "c3": pd.Series(self.yaw),
            }
        )

    def test_get_pp_from_mapserver(self):
        class req_dict(dict):
            def json(self):
                return self

        time_d = {}
        for t, x, y, yaw in zip(self.times, self.x, self.y, self.yaw):
            time_d[t] = req_dict(location=(x, y), yaw=yaw)

        def requests_get_se(url, params, timeout):
            return time_d[params["event_time"]]

        with patch("vipersci.vis.pano_check.requests.get", side_effect=requests_get_se):
            tpp = pc.get_position_and_pose_from_mapserver(self.times, url="foo")
            self.assertEqual(tpp, self.truth)

    def test_get_pp_from_csv(self):
        my_times = self.times.copy()
        my_times[0] += 10

        my_truth = [
            (t, (x, y, yaw)) for t, x, y, yaw in zip(my_times, self.x, self.y, self.yaw)
        ]

        with patch("vipersci.vis.pano_check.pd.read_csv", return_value=self.df):
            tpp = pc.get_position_and_pose_from_csv(my_times, Path("dummy.csv"))
            self.assertEqual(tpp, my_truth)

    def test_check(self):
        pid_list = [
            "241127-010203-ncl-a",
            "241127-010303-ncl-a",
            "241127-010403-ncl-a",
            "241127-010403-ncr-s",
            "241128-010203-ncl-a",
            "241130-010203-ncl-a",
            "241130-010303-ncl-a",
        ]
        pds.VISID(pid_list[0])
        pids = list(map(pds.VISID, pid_list))

        self.assertRaises(ValueError, pc.check, pids)

        im_recs = list()
        for x in pids:
            im_recs.append(
                ImageRecord(
                    product_id=str(x), start_time=x.datetime(), exposure_duration=111
                )
            )

        # Only two groups in the above pid_list
        truth = [
            (pids[0:3], (self.x[0], self.y[0], self.yaw[0])),
            (pids[-2:], (self.x[3], self.y[3], self.yaw[3])),
        ]

        self.assertRaises(TypeError, pc.check, pid_list, "dummy_function")

        with patch("vipersci.vis.pano_check.pd.read_csv", return_value=self.df):
            gffp = partial(pc.get_position_and_pose_from_csv, path="dummy.csv")
            p_groups = pc.check(pids, gffp)
            self.assertEqual(p_groups, truth)

            im_groups = pc.check(im_recs, gffp)
            pid_groups = list()
            for im_list, pose in im_groups:
                pid_list = list(map(pds.VISID, [x.product_id for x in im_list]))
                pid_groups.append((pid_list, pose))
            self.assertEqual(pid_groups, truth)
