#!/usr/bin/env python
"""This module has tests for the light_records module."""

# Copyright 2023, United States Government as represented by the
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

from datetime import datetime, timezone

from vipersci.vis.db import light_records as lr


class TestLights(unittest.TestCase):
    def setUp(self):
        self.t1 = datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        self.t2 = datetime(2023, 1, 1, 0, 0, 8, tzinfo=timezone.utc)
        self.t3 = datetime(2023, 1, 1, 0, 0, 12, tzinfo=timezone.utc)

    def test_init(self):
        good = lr.LightRecord(
            name="navLeft",
            start_time=self.t1,
            last_time=self.t2,
        )
        self.assertEqual(good.name, "NavLight Left")

    def test_init_fail(self):
        self.assertRaises(
            ValueError,
            lr.LightRecord,
            name="not a name",
            start_time=self.t1,
            last_time=self.t2,
        )

        self.assertRaises(
            ValueError,
            lr.LightRecord,
            name="not a name",
            start_time=self.t3,
            last_time=self.t2,
        )
