#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for the `vis/pds` module."""

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
from pathlib import Path
from unittest.mock import create_autospec, patch

from genshi.template import Template

from vipersci.vis import pds


class TestVersion(unittest.TestCase):
    def test_version_info(self):
        d = pds.version_info()
        self.assertEqual(99.99, d["vid"])


class TestXML(unittest.TestCase):
    def test_write_xml(self):
        product = {
            "dummy": "product",
            "product_id": "dummy_pid",
        }
        m_outdir = create_autospec(Path)
        m_tmpl = create_autospec(Template)
        with patch(
            "vipersci.vis.pds.MarkupTemplate", return_value=m_tmpl
        ) as m_markup, patch("vipersci.vis.pds.resources.read_text") as m_read_text:
            pds.write_xml(product, "raw-template.xml", m_outdir)

            m_read_text.assert_called_once()
            m_markup.assert_called_once()
            m_tmpl.generate.assert_called_once()

    def test_write_xml_custom_template(self):
        product = {
            "dummy": "product",
            "product_id": "dummy_pid",
        }

        path_mock = create_autospec(Path)
        path_mock.exists.return_value = True

        m_outdir = create_autospec(Path)
        m_tmpl = create_autospec(Template)

        with patch("vipersci.vis.pds.Path", return_value=path_mock), patch(
            "vipersci.vis.pds.MarkupTemplate", return_value=m_tmpl
        ) as m_markup:
            pds.write_xml(product, "this_exists.xml", m_outdir)

            path_mock.read_text.assert_called_once()
            m_markup.assert_called_once()
            m_tmpl.generate.assert_called_once()
