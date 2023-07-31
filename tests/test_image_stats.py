#!/usr/bin/env python
"""This module has tests for the image_stats module."""

# Copyright 2022-2023, United States Government as represented by the
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

from vipersci.vis.db import image_stats as rs


class TestRawStats(unittest.TestCase):
    def setUp(self):
        self.d = dict(
            blur=0.5,
            mean=2096.5,
            std=1027.3,
        )

    def test_init(self):
        stats = rs.ImageStats(**self.d)
        self.assertEqual(2096.5, stats.mean)
