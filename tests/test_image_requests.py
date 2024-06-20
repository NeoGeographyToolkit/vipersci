#!/usr/bin/env python
"""This module has tests for the image_requests module."""

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
from datetime import datetime, timezone

from vipersci.vis.db import image_requests as ir
from vipersci.vis.db.junc_image_req_ldst import JuncImageRequestLDST  # noqa


class TestEnums(unittest.TestCase):
    def test_Status(self):
        self.assertEqual(ir.Status.WORKING, ir.Status(1))
        self.assertEqual(ir.Status.PLANNED, ir.Status(4))

    def test_CameraType(self):
        self.assertEqual(ir.CameraType.NAVCAM, ir.CameraType(1))
        self.assertEqual(ir.CameraType.AFTCAM, ir.CameraType(2))
        self.assertEqual(ir.CameraType.HAZCAM, ir.CameraType(3))

    def test_CompressionType(self):
        self.assertEqual(ir.CompressionType.LOSSLESS, ir.CompressionType(1))
        self.assertEqual(ir.CompressionType.LOSSY, ir.CompressionType(2))

    def test_ImageMode(self):
        self.assertEqual(ir.ImageMode.LEFT, ir.ImageMode(1))
        self.assertEqual(ir.ImageMode.PANORAMA, ir.ImageMode(4))


class TestImageRequest(unittest.TestCase):
    def setUp(self):
        self.mini = {
            "title": "Mini Request",
            "justification": "Saw a great crater.",
            "status": ir.Status.IMMEDIATE,
            "users": "Rick Elphic",
            "request_time": datetime.now(tz=timezone.utc),
        }

        self.stereo = {
            "title": "Dummy Title",
            "justification": "Greatest Rock of All Time.",
            "status": "WORKING",
            "users": "Ross A. Beyer (VIS), Tony Colaprete",
            "request_time": datetime.now(tz=timezone.utc),
            "target_location": "Rim of the big crater.",
            "rover_location": "A few meters away from the big crater.",
            "rover_orientation": "Any",
            "camera_type": ir.CameraType.NAVCAM,
            "imaging_mode": ir.ImageMode.STEREO,
            "compression": ir.CompressionType.LOSSY,
            "luminaires": "default",
            "exposure_time": "Default",
        }

        self.pano = self.stereo.copy()
        self.pano["imaging_mode"] = ir.ImageMode.PANORAMA
        self.pano.update(
            {
                "caltarget_required": True,
                "aftcam_pair": True,
                "chin_down_navcam_pair": True,
                "slices": 6,
            }
        )

    def test_init(self):
        ir1 = ir.ImageRequest(**self.mini)
        self.assertEqual(ir1.status, ir.Status.IMMEDIATE)

        ir2 = ir.ImageRequest(**self.stereo)
        self.assertEqual(ir2.imaging_mode, ir.ImageMode.STEREO)

        ir3 = ir.ImageRequest(**self.pano)
        self.assertEqual(ir3.slices, 6)

    def test_init_raise(self):
        d = self.stereo.copy()
        d["luminaires"] = "not a luminaire"
        self.assertRaises(ValueError, ir.ImageRequest, **d)

        e = self.stereo.copy()
        e["hazcams"] = "ncl,hfp"
        self.assertRaises(ValueError, ir.ImageRequest, **e)
