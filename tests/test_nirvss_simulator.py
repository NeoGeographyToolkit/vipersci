#!/usr/bin/env python
"""This module has tests for the nirvss_simulator module."""

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

from vipersci.carto import nirvss_simulator as ns


class TestParser(unittest.TestCase):
    def test_parser(self):
        parser = ns.arg_parser()
        self.assertIsInstance(parser, argparse.ArgumentParser)


class TestLocationSimulator(unittest.TestCase):
    @patch("vipersci.carto.nirvss_simulator.rasterio.open")
    def test__init_map(self, mock_rasterio_data):
        ns.LocationSimulator._init_map(Path("dummy/path.raster"))
        mock_rasterio_data.transform.called_once()
        mock_rasterio_data.read.called_once_with(1)

    @patch(
        "vipersci.carto.nirvss_simulator.rasterio.transform.rowcol", return_value=(0, 0)
    )
    @patch(
        "vipersci.carto.nirvss_simulator.LocationSimulator._init_map",
        return_value=("xform", "array"),
    )
    def test_call(self, mock_init_map, mock_rowcol):
        simulator = ns.LocationSimulator(
            Path("dummy/bd.tif"), Path("dummy/insl.tif"), Path("dummy/temp.tif")
        )
        simulator.bd_arr = np.array([[2.5, 2.5], [2.5, 2.5]])
        simulator.insl_arr = np.array([[248, 248], [248, 248]])
        simulator.temp_arr = np.array([[264, 264], [264, 264]])

        h2o, oh = simulator(np.array([0, 0]))
        self.assertAlmostEqual(h2o, 4.371779725275095e-05)
        self.assertAlmostEqual(oh, 0.009899494936611665)
