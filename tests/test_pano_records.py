#!/usr/bin/env python
"""This module has tests for the pano_records module."""

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
from datetime import datetime, timedelta, timezone

from vipersci.vis.db import pano_records as tpp
from vipersci.vis.db.image_records import ImageRecord  # noqa
from vipersci.vis.db.image_requests import ImageRequest  # noqa
from vipersci.vis.db.junc_image_pano import JuncImagePano  # noqa
from vipersci.vis.db.junc_image_record_tags import JuncImageRecordTag  # noqa
from vipersci.vis.db.junc_image_req_ldst import JuncImageRequestLDST  # noqa


class TestPanoRecord(unittest.TestCase):
    def setUp(self):
        self.startUTC = datetime(2022, 1, 27, 0, 0, 0, tzinfo=timezone.utc)
        self.source_products = ["220127-000000-ncl-d", "220127-000005-ncl-d"]
        self.d = dict(
            file_creation_datetime=datetime.now(timezone.utc),
            file_path="/path/to/dummy",
            lines=2048,
            md5_checksum="dummychecksum",
            mission_phase="Test",
            purpose="Engineering",
            samples=2048,
            source_pids=self.source_products,
            start_time=self.startUTC,
        )
        self.extras = dict(foo="bar")

    def test_init(self):
        p = tpp.PanoRecord(**self.d)
        self.assertEqual("220127-000000-ncl-pan", str(p.product_id))

        d = self.d
        d.update(self.extras)
        ppl = tpp.PanoRecord(**d)
        self.assertEqual("220127-000000-ncl-pan", str(ppl.product_id))

        # Force alternate time
        d = self.d.copy()
        d["start_time"] = self.startUTC + timedelta(hours=1)
        pp2 = tpp.PanoRecord(**d)
        self.assertEqual("220127-010000-ncl-pan", str(pp2.product_id))

        # Remove explicit time signature
        d = self.d.copy()
        del d["start_time"]
        pp3 = tpp.PanoRecord(**d)
        self.assertEqual("220127-000000-ncl-pan", str(pp3.product_id))

        # print(f"{k}: {getattr(rp, k)}")

    def test_init_errors(self):
        d = self.d.copy()
        d["product_id"] = "220127-010000-ncl-b"
        self.assertRaises(ValueError, tpp.PanoRecord, **d)

        d = self.d.copy()
        d["product_id"] = "220127-000000-ncr-b"
        self.assertRaises(ValueError, tpp.PanoRecord, **d)

    def test_product_id(self):
        p = tpp.PanoRecord(**self.d)
        self.assertRaises(NotImplementedError, setattr, p, "product_id", "dummy")

    def test_purpose(self):
        p = tpp.PanoRecord(**self.d)
        self.assertRaises(ValueError, setattr, p, "purpose", "dummy")

    def test_update(self):
        p = tpp.PanoRecord(**self.d)
        k = "foo"
        self.assertTrue(k not in p.labelmeta)

        p.update(self.extras)
        self.assertTrue(k in p.labelmeta)

    # def test_labeldict(self):
    #     din = self.d
    #     din.update(self.extras)
    #     p = tpp.PanoRecord(**din)
    #     d = p.label_dict()
    #     self.assertEqual(d["samples"], p.samples)
