#!/usr/bin/env python
"""This module has tests for the pds.pid functions."""

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

# import contextlib
# import shutil
import datetime
import unittest

# from pathlib import Path

from vipersci.pds import pid


class TestVIPERID(unittest.TestCase):
    def test_init_tuple(self):
        tuples = (
            (
                ("220117", "010101", "ncl"),
                (datetime.date(2022, 1, 17), datetime.time(1, 1, 1), "ncl"),
            ),
            (
                ("220117", "010101", "ncl"),
                (datetime.date(2022, 1, 17), datetime.time(1, 1, 1), "NavCam Left"),
            ),
            (
                ("220117", "010101001", "aim"),
                (datetime.datetime(2022, 1, 17, 1, 1, 1, 1000), "aim"),
            ),
            (
                ("231225", "182000", "acr"),
                (datetime.date(2023, 12, 25), datetime.time(18, 20, 0), "acr"),
            ),
            (
                ("240330", "121212", "hap"),
                (datetime.datetime(2024, 3, 30, 12, 12, 12), "hap"),
            ),
        )
        for truth, t in tuples:
            with self.subTest():
                p = pid.VIPERID(*t)
                self.assertTupleEqual(truth, (p.date, p.time, p.instrument))

    def test_init_string(self):
        string_tuples = (
            ("220117-010101-ncl", "220117-010101-ncl"),
            ("220117-010101-ncl", "220117-010101-NCL"),
            ("220117-010101-ncl", "20220117-010101-ncl"),
            ("231225-182000-acr", "231225-182000-acr ignored"),
        )
        for s in string_tuples:
            with self.subTest():
                p = pid.VIPERID(s[1])
                self.assertEqual(s[0], str(p))

    def test_init_bad_tuples(self):
        tuples = (
            ("not a datetime", "ncl"),
            ("not a date", datetime.time(1, 1, 1), "ncl"),
            (datetime.date(2024, 1, 1), "not a time", "ncl"),
            (datetime.datetime(2022, 1, 17, 1, 1, 1), "not an instrument"),
        )
        for t in tuples:
            with self.subTest(t):
                self.assertRaises(ValueError, pid.VIPERID, *t)

    def test_init_bad_strings(self):
        strings = (
            "220117-010101-aaa",
            "220117-10101-ncl",
            "foobar",
        )
        for s in strings:
            with self.subTest(s):
                self.assertRaises(ValueError, pid.VIPERID, s)

    def test_init_too_many_args(self):
        self.assertRaises(
            IndexError,
            pid.VIPERID,
            datetime.date(2024, 1, 1),
            datetime.time(1, 1, 1),
            "aim",
            "more than three arguments",
        )
        self.assertRaises(
            IndexError,
            pid.VIPERID,
        )

    def test_init_zero_args(self):
        self.assertRaises(IndexError, pid.VIPERID)

    def test_repr(self):
        s = "This is a VIPER ID: 220117-010101-ncl"
        p = pid.VIPERID(s)
        self.assertEqual("VIPERID('220117-010101-ncl')", repr(p))

    def test_lt(self):
        p1 = pid.VIPERID("231120-010101-acl")
        p2 = pid.VIPERID("231121-010101-acl")
        p3 = pid.VIPERID("231121-010102-acl")
        p4 = pid.VIPERID("231121-010102-ncl")
        self.assertTrue(p1 < p2)
        self.assertTrue(p2 < p3)
        self.assertTrue(p3 < p4)

    def test_datetime(self):
        p = pid.VIPERID("231121-010101-acl")
        self.assertEqual(p.datetime(), datetime.datetime(2023, 11, 21, 1, 1, 1))


class TestVISID(unittest.TestCase):
    def test_init_tuple(self):
        tuples = (
            (
                ("220117", "010101", "ncl", "a"),
                (datetime.date(2022, 1, 17), datetime.time(1, 1, 1), "ncl", "a"),
            ),
            (
                ("220117", "010101", "ncl", "b"),
                (datetime.date(2022, 1, 17), datetime.time(1, 1, 1), "ncl", 5),
            ),
            (
                ("240330", "121212", "hap", "d"),
                (datetime.date(2024, 3, 30), datetime.time(12, 12, 12), "hap", "d"),
            ),
        )
        for truth, t in tuples:
            with self.subTest(truth=truth, test=t):
                vid = pid.VISID(*t)
                self.assertTupleEqual(
                    truth,
                    (
                        vid.date,
                        vid.time,
                        vid.instrument,
                        vid.compression,
                    ),
                )

    def test_init_string(self):
        string_tuples = (
            ("220117-010101-ncl-a", "220117-010101-ncl-a"),
            ("220117-010101-ncl-b", "220117-010101-NCL-b"),
            ("231225-182000-acr-d", "231225-182000-acr-d ignored"),
        )
        for s in string_tuples:
            vid = pid.VISID(s[1])
            with self.subTest(truth=s[0], ccid=vid):
                self.assertEqual(s[0], str(vid))

    def test_init_dict(self):
        d = dict(
            lobt=1643241600, instrument_name="NavCam Left", onboard_compression_ratio=5
        )
        vid = pid.VISID(d)
        self.assertEqual("220127-000000-ncl-b", str(vid))

    def test_init_bad_tuples(self):
        tuples = ((datetime.date(2024, 1, 1), datetime.time(1, 1, 1), "ncl", "z"),)
        for t in tuples:
            with self.subTest(test=t):
                self.assertRaises(ValueError, pid.VISID, *t)

    def test_init_bad_strings(self):
        strings = (
            "220117-010101-ncl",
            "220117-010101-aaa-a",
            "220117-010101-ncl-z",
            "foobar",
        )
        for s in strings:
            with self.subTest(test=s):
                self.assertRaises(ValueError, pid.VISID, s)

    def test_init_bad_dict(self):
        dicts = (
            dict(lobt=0, instrument_name="NavCam Left", onboard_compression_ratio=5),
            dict(
                lobt=1643241600,
                start_time=datetime.datetime(
                    2023, 1, 27, 0, 0, 0, tzinfo=datetime.timezone.utc
                ),
                instrument_name="NavCam Left",
                onboard_compression_ratio=5,
            ),
        )
        for d in dicts:
            with self.subTest(test=d):
                self.assertRaises(ValueError, pid.VISID, d)

    def test_init_wrong_arg_count(self):
        # (datetime.date(2024, 1, 1), datetime.time(1, 1, 1), "ncl")
        self.assertRaises(
            IndexError,
            pid.VISID,
            "1",
            "2",
            "3",
            "4",
            "5",
        )
        self.assertRaises(IndexError, pid.VISID, "1", "2")
        self.assertRaises(
            IndexError,
            pid.VISID,
        )

    def test_repr(self):
        s = "This is a VISID: 220117-010101-ncl-a"
        cid = pid.VISID(s)
        self.assertEqual("VISID('220117-010101-ncl-a')", repr(cid))

    def test_lt(self):
        vid1 = pid.VISID("220117-010101-ncl-a")
        vid2 = pid.VISID("220117-010101-ncl-b")
        vid3 = pid.VISID("220117-010101-ncl-c")
        vid4 = pid.VISID("220117-010101-ncl-d")
        self.assertTrue(vid1 < vid2)
        self.assertTrue(vid2 < vid3)
        self.assertTrue(vid3 < vid4)

        vids = [vid3, vid4, vid1, vid2]
        self.assertEqual(sorted(vids), [vid1, vid2, vid3, vid4])


class TestStrings(unittest.TestCase):
    def test_str_(self):
        test = "This is a VIPER Id: 220117-010101-aim"
        truth = "220117-010101-aim"
        self.assertEqual(truth, pid.VIPERID(test).__str__())
