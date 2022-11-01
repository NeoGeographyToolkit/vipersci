#!/usr/bin/env python
"""This module has tests for the nirvss module."""

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

import unittest

import numpy as np

from vipersci import nirvss


class TestH20(unittest.TestCase):
    def test_h2o(self):
        self.assertAlmostEqual(4.37177e-05, nirvss.band_depth_H2O(264, 2.5))
        np.testing.assert_allclose(
            np.array([4.735892e-05, 3.877421e-05]),
            nirvss.band_depth_H2O(np.array((260, 270)), np.array((2.5, 2.5))),
            rtol=1e-06,
        )


class TestOH(unittest.TestCase):
    def test_oh(self):
        self.assertAlmostEqual(0.0098995, nirvss.band_depth_OH(248))
        np.testing.assert_allclose(
            np.array([0.009899, 0.011533]),
            nirvss.band_depth_OH(np.array((248, 283))),
            rtol=5e-5,
        )
