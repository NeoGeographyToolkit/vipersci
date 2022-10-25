#!/usr/bin/env python
"""This module has tests for the pds.datetime functions."""

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

import datetime
import unittest

from vipersci.pds import datetime as pdsdt


class TestIsoZ(unittest.TestCase):
    def test_isozformat(self):
        dt = datetime.datetime(2022, 10, 1, 13, 20, 0, tzinfo=datetime.timezone.utc)
        self.assertEqual(pdsdt.isozformat(dt), "2022-10-01T13:20:00Z")

        no_tz = dt.replace(tzinfo=None)

        self.assertRaises(ValueError, pdsdt.isozformat, no_tz)
