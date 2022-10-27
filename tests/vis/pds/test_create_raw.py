#!/usr/bin/env python
"""This module has tests for the pds.create_raw functions."""

# Copyright 2022, vipersci developers.
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


class TestInfo(unittest.TestCase):
    def test_tiff_info(self):
        tuples = (
            (
                ("220117", "010101", "ncl"),
                (datetime.date(2022, 1, 17), datetime.time(1, 1, 1), "ncl"),
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
