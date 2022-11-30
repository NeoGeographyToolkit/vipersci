#!/usr/bin/env python
"""This module has tests for the nss_simulator module."""

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
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np

from vipersci.carto import nss_simulator as ns


class TestParser(unittest.TestCase):
    def test_parser(self):
        parser = ns.arg_parser()
        self.assertIsInstance(parser, argparse.ArgumentParser)


class TestLocationSimulator(unittest.TestCase):
    def setUp(self) -> None:
        self.rc = np.array([10, 30, 60])
        self.cc = np.array([0, 0.5, 1])
        self.arr = np.array(
            [
                [100, 200, 300],
                [10, 20, 30],
                [1, 2, 3],
            ]
        )

    @patch("vipersci.carto.nss_simulator.rasterio.open")
    def test__init_map(self, mock_rasterio_data):
        ns.LocationSimulator._init_map(Path("dummy/path.raster"))
        mock_rasterio_data.transform.called_once()
        mock_rasterio_data.read.called_once_with(1)

    @patch(
        "vipersci.carto.nss_simulator.rasterio.transform.rowcol", return_value=(0, 0)
    )
    @patch(
        "vipersci.carto.nss_simulator.LocationSimulator._init_map",
        return_value=("xform", "array"),
    )
    def test_call(self, mock_init_map, mock_rowcol):
        with patch("vipersci.nss.read_csv", return_value=(self.arr, self.rc, self.cc)):
            simulator = ns.LocationSimulator(
                Path("dummy/bd.tif"),
                Path("dummy/weh.tif"),
                Path("dummy/det1.csv"),
                Path("dummy/det2.csv"),
            )
            simulator.bd_arr = np.array([[0.5, 0.5], [0.5, 0.5]])
            simulator.weh_arr = np.array([[20, 20], [20, 20]])

            d1, d2 = simulator(np.array([0, 0]))
            self.assertAlmostEqual(d1, 110)
            self.assertAlmostEqual(d2, 110)
