#!/usr/bin/env python
"""This module has tests for the vis.pano-check functions."""

# Copyright 2023, vipersci developers.
#
# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.

from argparse import ArgumentParser
from datetime import datetime, timezone
import unittest
from unittest.mock import patch

from vipersci.vis import pano_check as pc


class TestFunctions(unittest.TestCase):
    # def test_arg_parser(self):
    #     p = pc.arg_parser()
    #     self.assertIsInstance(p, ArgumentParser)

    def test_groupby_2nd(self):
        tuples = [
            ("Alice", "foo"),
            ("Bob", "bar"),
            ("Catherine", "bar"),
        ]
        truth = [
            (["Alice",], "foo"),
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
            (t, (x, y, yaw)) for t, x, y, yaw in zip(
                self.times, self.x, self.y, self.yaw
            )
        ]

    def test_get_pp_from_mapserver(self):
        class req_dict(dict):
            def json(self):
                return self

        time_d = {}
        for t, x, y, yaw in zip(self.times, self.x, self.y, self.yaw):
            time_d[t] = req_dict(location=(x, y), yaw=yaw)

        def requests_get_se(url, params):
            return time_d[params["event_time"]]

        with patch("vipersci.vis.pano_check.requests.get", side_effect=requests_get_se):
            tpp = pc.get_position_and_pose_from_mapserver(self.times, url="foo")
            self.assertEqual(tpp, self.truth)

    # def test_get_pp_from_df(self):
