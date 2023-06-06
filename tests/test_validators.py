#!/usr/bin/env python
"""This module has tests for the validators module."""

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

from datetime import datetime, timezone
import unittest

from vipersci.pds.datetime import fromisozformat
import vipersci.vis.db.validators as vld


class TestValidators(unittest.TestCase):
    def test_validate_datetime_asutc(self):
        dt = datetime(2022, 1, 27, 0, 0, 0, tzinfo=timezone.utc)
        valid = vld.validate_datetime_asutc("foo", dt)
        self.assertEqual(valid, dt)

        t_str = "2023-11-25T14:38:59Z"
        valid = vld.validate_datetime_asutc("foo", t_str)
        self.assertEqual(valid, fromisozformat(t_str))

        # t2_str = "2023-11-25T14:38:59"
        # valid = vld.validate_datetime_asutc("foo", t2_str)
        # self.assertEqual(valid, datetime.fromisoformat(t2_str) )

        dt_e = datetime(2022, 1, 27, 0, 0, 0)
        self.assertRaises(ValueError, vld.validate_datetime_asutc, "foo", dt_e)

        self.assertRaises(
            ValueError,
            vld.validate_datetime_asutc,
            "foo",
            "not interpretable as a datetime",
        )

    def test_validate_purpose(self):
        self.assertEqual(vld.validate_purpose("Science"), "Science")

        self.assertRaises(ValueError, vld.validate_purpose, "not a Purpose")
