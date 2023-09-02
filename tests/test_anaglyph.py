#!/usr/bin/env python
"""This module has tests for the anaglyph module."""

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
from argparse import ArgumentParser
from pathlib import Path
from unittest.mock import call, create_autospec, Mock, patch

import numpy as np
from PIL import Image

from vipersci.vis import anaglyph


class TestFunctions(unittest.TestCase):
    def setUp(self):
        self.left = np.array(
            [
                [0, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 1, 0],
                [0, 0, 0, 0],
            ]
        )
        self.right = np.array(
            [
                [0, 1, 0, 0],
                [0, 0, 1, 0],
                [0, 0, 0, 0],
                [0, 0, 0, 0],
            ]
        )

    def test_arg_parser(self):
        p = anaglyph.arg_parser()
        self.assertIsInstance(p, ArgumentParser)

    def test_correlate_and_shift(self):
        result = anaglyph.correlate_and_shift(self.left, self.right)
        np.testing.assert_array_equal(result, self.left)

    def test_anaglyph(self):
        truth = np.dstack((self.left, self.right, self.right))
        result = anaglyph.anaglyph(self.left, self.right)
        np.testing.assert_array_equal(result, truth)

        align_truth = np.dstack((self.left, self.left, self.left))
        align_result = anaglyph.anaglyph(self.left, self.right, align=True)
        np.testing.assert_array_equal(align_result, align_truth)

        rgb_result = anaglyph.anaglyph(
            np.dstack((self.left, self.left, self.left)),
            np.dstack((self.right, self.right, self.right)),
        )
        np.testing.assert_array_equal(rgb_result, truth)

    def test_anaglyph_exceptions(self):
        self.assertRaises(
            ValueError, anaglyph.anaglyph, self.left, np.delete(self.right, 3, 0)
        )
        self.assertRaises(
            ValueError, anaglyph.anaglyph, np.array([0, 1]), np.array([0, 1])
        )
        self.assertRaises(ValueError, anaglyph.anaglyph, self.left, np.array([0, 1]))

    @patch("vipersci.vis.anaglyph.imread")
    @patch("vipersci.vis.anaglyph.Image.fromarray")
    @patch("vipersci.vis.anaglyph.anaglyph")
    def test_create(self, m_anaglyph, m_fromarray, m_imread):
        m_im = create_autospec(Image)
        m_im.save = Mock()
        m_fromarray.return_value = m_im
        left = Path("dummy/left.tif")
        right = Path("dummy/right.tif")
        out = Path("out.tif")

        anaglyph.create(left, right, out)

        m_imread.assert_has_calls([call(left), call(right)])
        m_anaglyph.assert_called_once()
        m_fromarray.assert_called_once()
        m_im.save.assert_called_once_with(out)

    @patch("vipersci.vis.anaglyph.imread")
    @patch("vipersci.vis.anaglyph.Image.fromarray")
    def test_main(self, m_fromarray, m_imread):
        left = "left.tif"
        right = "right.tif"
        out = "out.tif"

        m_im = create_autospec(Image)
        m_im.save = Mock()
        m_fromarray.return_value = m_im

        pa_ret_val = anaglyph.arg_parser().parse_args(["-a", left, right, out])
        with patch("vipersci.vis.anaglyph.arg_parser") as parser:
            with patch("vipersci.vis.anaglyph.anaglyph") as m_anaglyph:
                parser.return_value.parse_args.return_value = pa_ret_val

                anaglyph.main()

                m_imread.assert_has_calls([call(Path(left)), call(Path(right))])
                m_anaglyph.assert_called_once()
                m_fromarray.assert_called_once()
                m_im.save.assert_called_once_with(Path(out))

        m_fromarray.reset_mock()
        m_imread.reset_mock()
        m_im.reset_mock()
        m_im.save.reset_mock()
        pa_ret_val = anaglyph.arg_parser().parse_args(["-s", left, right, out])
        with patch("vipersci.vis.anaglyph.arg_parser") as parser:
            parser.return_value.parse_args.return_value = pa_ret_val

            anaglyph.main()
            m_imread.assert_has_calls([call(Path(left)), call(Path(right))])
            m_fromarray.assert_called_once()
            m_im.save.assert_called_once_with(Path(out))

        m_fromarray.reset_mock()
        m_imread.reset_mock()
        m_im.reset_mock()
        m_im.save.reset_mock()
        pa_ret_val = anaglyph.arg_parser().parse_args(["-w", left, right, out])
        with patch("vipersci.vis.anaglyph.arg_parser") as parser:
            parser.return_value.parse_args.return_value = pa_ret_val

            anaglyph.main()
            m_imread.assert_has_calls([call(Path(left)), call(Path(right))])
            self.assertEqual(m_fromarray.call_count, 2)
            m_im.save.assert_called_once()

        m_fromarray.reset_mock()
        m_imread.reset_mock()
        m_im.reset_mock()
        m_im.save.reset_mock()
        pa_ret_val = anaglyph.arg_parser().parse_args(["-a", "-r", left, right, out])
        pa_ret_val.anaglyph = False
        with patch("vipersci.vis.anaglyph.arg_parser") as parser:
            with patch("vipersci.vis.anaglyph.correlate_and_shift") as m_corr_and_shift:
                parser.return_value.parse_args.return_value = pa_ret_val

                anaglyph.main()

                m_corr_and_shift.called_once()
                parser.error.called_once()
