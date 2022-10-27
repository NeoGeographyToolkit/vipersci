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

from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np

from vipersci import nss


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

    def testInit(self):
        with patch("vipersci.nss.read_csv", return_value=(self.arr, self.rc, self.cc)):
            ds = nss.DataSimulator(Path("dummy1"), Path("dummy2"))
            self.assertIsInstance(ds, nss.DataSimulator)

    def testCall(self):
        with patch("vipersci.nss.read_csv", return_value=(self.arr, self.rc, self.cc)):
            ds = nss.DataSimulator(Path("dummy1"), Path("dummy2"))
            self.assertRaises(ValueError, ds, 5, 5)
            d1, d2 = ds(0.3, 20)
            self.assertEqual(88, d1)
            self.assertEqual(88, d2)

            d1_arr, d2_arr = ds([0.3, 0.5], [20, 30])
            np.testing.assert_array_almost_equal(np.array([88, 20]), d1_arr)
            np.testing.assert_array_almost_equal(np.array([88, 20]), d2_arr)
