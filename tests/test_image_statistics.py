#!/usr/bin/env python
"""This module has tests for the image_statistics module."""

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
import unittest

import numpy as np

from vipersci.vis import image_statistics


class TestParser(unittest.TestCase):
    def test_parser(self):
        parser = image_statistics.arg_parser()
        self.assertIsInstance(parser, argparse.ArgumentParser)


class TestCompute(unittest.TestCase):
    def setUp(self):
        self.image = np.array(
            [
                [0, 1, 1000, 3000, 3001, 3002, 3003, 3004, 3005, 3006, 4096],
                [0, 1, 1000, 3000, 3001, 3002, 3003, 3004, 3005, 3006, 4096],
                [0, 1, 1000, 3000, 3001, 3002, 3003, 3004, 3005, 3006, 4096],
                [0, 1, 1000, 3000, 3001, 3002, 3003, 3004, 3005, 3006, 4096],
                [0, 1, 1000, 3000, 3001, 3002, 3003, 3004, 3005, 3006, 4096],
                [0, 1, 1000, 3000, 3001, 3002, 3003, 3004, 3005, 3006, 4096],
                [0, 1, 1000, 3000, 3001, 3002, 3003, 3004, 3005, 3006, 4096],
                [0, 1, 1000, 3000, 3001, 3002, 3003, 3004, 3005, 3006, 4096],
                [0, 1, 1000, 3000, 3001, 3002, 3003, 3004, 3005, 3006, 4096],
                [0, 1, 1000, 3000, 3001, 3002, 3003, 3004, 3005, 3006, 4096],
                [0, 1, 1000, 3000, 3001, 3002, 3003, 3004, 3005, 3006, 4096],
            ],
            dtype=np.uint16,
        )

    def test_compute(self):
        stats = image_statistics.compute(self.image)
        self.assertEqual(stats["blur"], 1.0)
        self.assertAlmostEqual(stats["mean"], 2374.36363636)
        self.assertAlmostEqual(stats["std"], 1310.43637928)
