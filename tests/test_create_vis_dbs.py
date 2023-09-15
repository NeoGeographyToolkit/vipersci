#!/usr/bin/env python
"""This module has tests for the vis.db.create_vis_dbs functions."""

# Copyright 2023, vipersci developers.
#
# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.

from argparse import ArgumentParser
import unittest
from unittest.mock import patch

from geoalchemy2 import load_spatialite
from sqlalchemy import create_engine
from sqlalchemy.event import listen
from sqlalchemy.orm import Session

from vipersci.vis.db import Base
from vipersci.vis.db import create_vis_dbs as cvd


class TestParser(unittest.TestCase):
    def test_arg_parser(self):
        p = cvd.arg_parser()
        self.assertIsInstance(p, ArgumentParser)
        # self.assertRaises(SystemExit, p.parse_args)
        d = vars(p.parse_args([]))
        self.assertIn("dburl", d)


class TestDatabase(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        listen(self.engine, "connect", load_spatialite)
        self.session = Session(self.engine)

    def tearDown(self):
        Base.metadata.drop_all(self.engine)

    def test_main(self):
        pa_ret_val = cvd.arg_parser().parse_args(["-d", "foo"])
        with patch("vipersci.vis.db.create_vis_dbs.arg_parser") as parser:
            parser.return_value.parse_args.return_value = pa_ret_val
            with patch(
                "vipersci.vis.db.create_vis_dbs.create_engine", return_value=self.engine
            ):
                cvd.main()
