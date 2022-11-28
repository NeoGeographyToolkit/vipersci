#!/usr/bin/env python
"""This module has tests for the nss_modeler module."""

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
from unittest.mock import mock_open, patch

import numpy as np

from vipersci.carto import nss_modeler as nm


class TestParser(unittest.TestCase):
    def test_parser(self):
        parser = nm.arg_parser()
        self.assertIsInstance(parser, argparse.ArgumentParser)


class TestWrite(unittest.TestCase):
    def test_write_tif(
        self,
    ):
        m = mock_open()
        arr = np.array([1, 2])
        path = Path("dummy")
        ending = "end.tif"
        kwds = {"foo": "bar"}
        with patch("vipersci.carto.nss_modeler.rasterio.open", m):
            nm.write_tif(path, ending, arr, kwds)

        m.assert_called_once_with(path.with_name(path.name + ending), "w", **kwds)
        handle = m()
        handle.write.assert_called_once_with(arr, 1)
