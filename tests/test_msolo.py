#!/usr/bin/env python
"""This module has tests for the msolo module."""

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

from vipersci import msolo


class TestM20(unittest.TestCase):
    def test_m20(self):
        self.assertAlmostEqual(2.5991128778755347e-08, msolo.mass20(264, 2.5))
        np.testing.assert_allclose(
            np.array([2.969826e-08, 2.127974e-08]),
            msolo.mass20(np.array((260, 270)), np.array((2.5, 2.5))),
            rtol=1e-06,
        )


class TestM40(unittest.TestCase):
    def test_m40(self):
        self.assertAlmostEqual(3.056263805647861e-10, msolo.mass40(248))
        np.testing.assert_allclose(
            np.array([3.056264e-10, 5.310990e-11]),
            msolo.mass40(np.array((248, 283))),
            rtol=5e-5,
        )
