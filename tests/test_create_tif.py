#!/usr/bin/env python
"""This module has tests for the vipersci.vis.create_tif functions."""

# Copyright 2023, vipersci developers.
#
# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.

import unittest
from argparse import ArgumentParser
from pathlib import Path
from unittest.mock import patch

import vipersci.pds.pid as pds
import vipersci.vis.create_tif as ct


class TestParser(unittest.TestCase):
    def test_arg_parser(self):
        p = ct.arg_parser()
        self.assertIsInstance(p, ArgumentParser)
        self.assertRaises(SystemExit, p.parse_args)
        d = vars(p.parse_args(["-p", "product_id_goes_here", "dummy.png"]))
        self.assertIn("product_id", d)
        self.assertIn("output_dir", d)
        self.assertIn("image", d)


class TestMain(unittest.TestCase):
    @patch("vipersci.vis.create_tif.write_tiff")
    @patch("vipersci.vis.create_tif.imread")
    def test_main(self, m_imread, m_writetiff):
        fn = "dummy.png"
        pid = pds.VISID("231125-140902-ncl-c")
        pa_ret_val = ct.arg_parser().parse_args(
            [
                "--product_id",
                str(pid),
                fn,
            ]
        )
        with patch("vipersci.vis.create_tif.arg_parser") as parser:
            parser.return_value.parse_args.return_value = pa_ret_val
            ct.main()
            m_imread.assert_called_once_with(fn)
            m_writetiff.assert_called_once()
            self.assertEqual(m_writetiff.call_args[0][0], pid)
            self.assertEqual(m_writetiff.call_args[0][2], Path.cwd())
