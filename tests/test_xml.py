#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for the `pds/xml` module."""

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
import xml.etree.ElementTree as ET
from textwrap import dedent

from vipersci.pds import xml


class TestXML(unittest.TestCase):
    def setUp(self):
        self.xmltext = dedent(
            """\
        <?xml version="1.0" encoding="UTF-8"?>
        <?xml-model href="https://pds.nasa.gov/pds4/pds/v1/PDS4_PDS_1K00.sch"
          schematypens="http://purl.oclc.org/dsdl/schematron"?>
        <Product_Collection
          xmlns="http://pds.nasa.gov/pds4/pds/v1"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xsi:schemaLocation="http://pds.nasa.gov/pds4/pds/v1
          https://pds.nasa.gov/pds4/pds/v1/PDS4_PDS_1K00.xsd">
        <File_Area_Inventory>
          <File>
            <file_name></file_name>
            <creation_date_time>2023-11-02T23:12:59.083415Z</creation_date_time>
          </File>
          <Inventory>
            <offset unit="byte">0</offset>
            <parsing_standard_id>PDS DSV 1</parsing_standard_id>
            <records>4</records>
            <record_delimiter>Carriage-Return Line-Feed</record_delimiter>
            <field_delimiter>Comma</field_delimiter>
          </Inventory>
        </File_Area_Inventory>
        </Product_Collection>
        """
        )

    def test_find_text(self):
        root = ET.fromstring(self.xmltext)
        self.assertRaises(
            ValueError,
            xml.find_text,
            root,
            ".//pds:File_Area_Inventory/pds:Inventory/pds:offset",
            unit_check="bit",
        )

        self.assertRaises(
            ValueError,
            xml.find_text,
            root,
            ".//pds:File_Area_Inventory/pds:File/pds:file_name",
        )

        self.assertRaises(
            ValueError,
            xml.find_text,
            root,
            ".//pds:File_Area_Inventory/pds:File/pds:md5",
        )
