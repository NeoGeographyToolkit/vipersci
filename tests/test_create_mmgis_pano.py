#!/usr/bin/env python
"""This module has tests for the vis.create_mmgis_pano functions."""

# Copyright 2023, vipersci developers.
#
# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.

import unittest
from argparse import ArgumentParser
from pathlib import Path
from unittest.mock import create_autospec, mock_open, patch

import numpy as np

from vipersci.pds import pid as pds
from vipersci.vis import create_mmgis_pano as cp


class TestCLI(unittest.TestCase):
    def test_arg_parser(self):
        p = cp.arg_parser()
        self.assertIsInstance(p, ArgumentParser)
        # self.assertRaises(SystemExit, p.parse_args)
        d = vars(
            p.parse_args(
                ["--dburl", "db://foo:username@host/db", "product_id_goes_here"]
            )
        )
        self.assertIn("dburl", d)
        self.assertIn("input", d)

    # def test_main(self):
    #     pa_ret_val = cp.arg_parser().parse_args(
    #         ["231126-000000-ncl-s.dummy", "231126-000000-ncr-s.dummy"]
    #     )
    #     with patch("vipersci.vis.create_pano.arg_parser") as parser, patch(
    #         "vipersci.vis.create_pano.create"
    #     ) as m_create:
    #         parser.return_value.parse_args.return_value = pa_ret_val
    #         cp.main()
    #         m_create.assert_called_once()

    #     pa2_ret_val = cp.arg_parser().parse_args(
    #         [
    #             "--dburl",
    #             "db://foo:username@host/db",
    #             "231126-000000-ncl-s.dummy",
    #             "231126-000000-ncr-s.dummy",
    #         ]
    #     )
    #     session_engine_mock = create_autospec(Session)
    #     session_mock = create_autospec(Session)
    #     session_engine_mock.__enter__ = Mock(return_value=session_mock)
    #     with patch("vipersci.vis.create_pano.arg_parser") as parser, patch(
    #         "vipersci.vis.create_pano.create"
    #     ) as m_create, patch("vipersci.vis.create_pano.create_engine"), patch(
    #         "vipersci.vis.create_pano.Session", return_value=session_engine_mock
    #     ):
    #         parser.return_value.parse_args.return_value = pa2_ret_val
    #         cp.main()
    #         m_create.assert_called_once()
    #         session_engine_mock.__enter__.assert_called_once()
    #         session_mock.commit.assert_called_once()


class TestOther(unittest.TestCase):
    def test_longname(self):
        ln = cp.longname(Path("path/to/240225-000000-pan.dummy"))
        self.assertEqual(ln, "2024-02-25T00-00-00-pan")

    def test_mmgis_data(self):
        pd = {
            "rover_pan_max": 30,
            "rover_pan_min": 5,
            "samples": 5000,
            "lines": 2048,
            "rover_tilt_max": 20,
            "rover_tilt_min": -10,
            "product_id": "240225-000000-pan",
        }
        d = cp.mmgis_data(pd)
        self.assertEqual(d["azmax"], pd["rover_pan_max"])
        self.assertEqual(d["azmin"], pd["rover_pan_min"])
        self.assertEqual(d["columns"], pd["samples"])
        self.assertEqual(d["rows"], pd["lines"])
        self.assertEqual(d["elmax"], pd["rover_tilt_max"])
        self.assertEqual(d["elmin"], pd["rover_tilt_min"])
        self.assertEqual(d["name"], pd["product_id"])
        self.assertTrue(d["isPanoramic"])


class TestCreate(unittest.TestCase):

    @patch("vipersci.vis.create_mmgis_pano.json.dump")
    @patch("vipersci.vis.create_mmgis_pano.imread")
    @patch("vipersci.vis.create_mmgis_pano.imsave")
    @patch("vipersci.vis.create_mmgis_pano.equalize_adapthist")
    @patch(
        "vipersci.vis.create_mmgis_pano.rescale_intensity",
        return_value=create_autospec(np.ndarray),
    )
    @patch("vipersci.vis.create_mmgis_pano.resize")
    @patch("vipersci.vis.create_mmgis_pano.mmgis_data")
    def test_nodb(
        self,
        m_mmgis_data,
        m_resize,
        m_rescale_int,
        m_eq_adapt,
        m_imsave,
        m_imread,
        m_dump,
    ):
        self.assertRaises(ValueError, cp.create, pds.PanoID("240225-000000-pan"))
        self.assertRaises(ValueError, cp.create, ("Not a recognized", "type."))

        path_mock = create_autospec(Path)
        info = {"file_path": "240225-000000-pan.tif"}
        with patch(
            "vipersci.vis.create_mmgis_pano.json.load", return_value=info
        ) as m_load, patch(
            "vipersci.vis.create_mmgis_pano.open", mock_open()
        ) as m_open:
            cp.create(path_mock)
            self.assertEqual(m_open.call_count, 2)
            self.assertEqual(m_resize.call_count, 1)
            self.assertEqual(m_rescale_int.call_count, 2)
            self.assertEqual(m_eq_adapt.call_count, 1)
            self.assertEqual(m_imsave.call_count, 2)
            self.assertEqual(m_load.call_count, 1)
            self.assertEqual(m_dump.call_count, 1)
            m_imread.assert_called_once_with(str(Path(info["file_path"])))
            m_mmgis_data.assert_called_once_with(info, 0.0)
