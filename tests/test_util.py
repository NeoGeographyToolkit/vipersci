#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for the `util` module."""

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
import logging
import unittest

import vipersci.util as util


class TestUtil(unittest.TestCase):
    def test_parent_parser(self):
        self.assertIsInstance(util.parent_parser(), argparse.ArgumentParser)

    def test_logging(self):
        util.set_logger(verblvl=0)
        logger = logging.getLogger()
        self.assertEqual(30, logger.getEffectiveLevel())
