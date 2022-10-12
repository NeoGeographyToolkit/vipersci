#!/usr/bin/env python
"""This module has tests for the table_raw_products module."""

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

# from pathlib import Path
from datetime import datetime, timedelta, timezone
import unittest
# from unittest.mock import patch

from vipersci.vis.db import raw_products as trp


class TestRawProduct(unittest.TestCase):

    def setUp(self):
        self.startUTC = datetime(2022, 1, 27, 0, 0, 0, tzinfo=timezone.utc)
        self.d = dict(
            adc_gain=63,
            auto_exposure=False,
            bad_pixel_table_id=0,
            capture_id=0,
            exposure_time=111,
            file_creation_datetime=datetime.now(timezone.utc),
            file_path="/path/to/dummy",
            hazlight_aft_port_on=False,
            hazlight_aft_starboard_on=False,
            hazlight_center_port_on=False,
            hazlight_center_starboard_on=False,
            hazlight_fore_port_on=False,
            hazlight_fore_starboard_on=False,
            image_id=0,
            instrument_name="NavCam Left",
            instrument_temperature=128,
            lines=2048,
            lobt=self.startUTC.timestamp(),
            mcam_id=1,
            md5_checksum="dummychecksum",
            mission_phase="Test",
            navlight_left_on=False,
            navlight_right_on=False,
            offset=16324,
            onboard_compression_ratio=5,
            onboard_compression_type="ICER",
            output_image_mask=0,
            output_image_type="?",
            padding=0,
            pga_gain=0,
            processing_info=0,
            purpose="Engineering",
            samples=2048,
            stereo=False,
            voltage_ramp=109,
        )

    def test_init(self):
        rp = trp.Raw_Product(**self.d)
        self.assertEqual("220127-000000-ncl-b", str(rp.product_id))

        # for k in dir(rp):
        #     if k.startswith(("_", "validate_")):
        #         continue

        #     print(f"{k}: {getattr(rp, k)}")

    def test_init_errors(self):
        d = self.d.copy()
        d["start_time"] = self.startUTC + timedelta(hours=1)
        self.assertRaises(ValueError, trp.Raw_Product, **d)

        d = self.d.copy()
        del d["instrument_name"]
        self.assertRaises(ValueError, trp.Raw_Product, **d)

        d = self.d.copy()
        d["product_id"] = "220127-010000-ncl-b"
        self.assertRaises(ValueError, trp.Raw_Product, **d)

        d = self.d.copy()
        d["product_id"] = "220127-000000-ncr-b"
        self.assertRaises(ValueError, trp.Raw_Product, **d)

        d = self.d.copy()
        d["product_id"] = "220127-000000-ncl-b"
        d["onboard_compression_ratio"] = 999
        self.assertRaises(ValueError, trp.Raw_Product, **d)

    def test_mcam_id(self):
        rp = trp.Raw_Product(**self.d)
        self.assertRaises(ValueError, setattr, rp, "mcam_id", 5)

    def test_onboard_compression_type(self):
        rp = trp.Raw_Product(**self.d)
        self.assertRaises(ValueError, setattr, rp, "onboard_compression_type", "dummy")

    def test_product_id(self):
        rp = trp.Raw_Product(**self.d)
        self.assertRaises(NotImplementedError, setattr, rp, "product_id", "dummy")

    def test_purpose(self):
        rp = trp.Raw_Product(**self.d)
        self.assertRaises(ValueError, setattr, rp, "purpose", "dummy")