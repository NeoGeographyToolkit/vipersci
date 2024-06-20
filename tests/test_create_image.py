#!/usr/bin/env python
"""This module has tests for the vis.pds.create_raw functions."""

# Copyright 2022-2023, vipersci developers.
#
# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.

import unittest
from argparse import ArgumentParser
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import create_autospec, Mock, mock_open, patch

import numpy as np
import numpy.testing as npt
from PIL import Image
from sqlalchemy.orm import Session

from vipersci.pds import pid as pds
from vipersci.vis import create_image as ci
from vipersci.vis.db.image_records import ImageRecord


class TestCLI(unittest.TestCase):
    def test_arg_parser(self):
        p = ci.arg_parser()
        self.assertIsInstance(p, ArgumentParser)
        self.assertRaises(SystemExit, p.parse_args)
        d = vars(p.parse_args(["-o", "output_directory", "dummy.json"]))
        self.assertIn("output_dir", d)
        self.assertIn("input", d)

    def test_main(self):
        pa_ret_val = ci.arg_parser().parse_args(
            [
                "input.json",
            ]
        )
        with patch("vipersci.vis.create_image.arg_parser") as parser, patch(
            "vipersci.vis.create_image.create"
        ) as m_create, patch(
            "vipersci.vis.create_image.open", mock_open(read_data='{"json": "dummy"}')
        ):
            parser.return_value.parse_args.return_value = pa_ret_val
            ci.main()
            m_create.assert_called_once()

    def test_main_db(self):
        pa2_ret_val = ci.arg_parser().parse_args(
            [
                "--dburl",
                "db://foo:username@host/db",
                "--tiff",
                "dummy.tif",
                "dummy.json",
            ]
        )
        session_engine_mock = create_autospec(Session)
        session_mock = create_autospec(Session)
        session_engine_mock.__enter__ = Mock(return_value=session_mock)
        with patch("vipersci.vis.create_image.arg_parser") as parser, patch(
            "vipersci.vis.create_image.create"
        ) as m_create, patch("vipersci.vis.create_image.create_engine"), patch(
            "vipersci.vis.create_image.Session", return_value=session_engine_mock
        ), patch(
            "vipersci.vis.create_image.open", mock_open(read_data='{"json": "dummy"}')
        ):
            parser.return_value.parse_args.return_value = pa2_ret_val
            ci.main()
            m_create.assert_called_once()
            session_engine_mock.__enter__.assert_called_once()
            session_mock.commit.assert_called_once()

    def test_main_image(self):

        pa_ret_val = ci.arg_parser().parse_args(["--image", "dummy.png", "input.json"])
        with patch("vipersci.vis.create_image.arg_parser") as parser, patch(
            "vipersci.vis.create_image.create"
        ) as m_create, patch(
            "vipersci.vis.create_image.open", mock_open(read_data='{"json": "dummy"}')
        ), patch(
            "vipersci.vis.create_image.imread"
        ):
            parser.return_value.parse_args.return_value = pa_ret_val
            ci.main()
            m_create.assert_called_once()


class TestBitDepth(unittest.TestCase):
    def test_check_bit_depth(self):
        pid = pds.VISID("231125-143859-ncl-a")
        self.assertIsNone(ci.check_bit_depth(pid, 16))
        self.assertIsNone(ci.check_bit_depth(pid, "UnsignedLSB2"))
        self.assertIsNone(ci.check_bit_depth(pid, np.uint16(5).dtype))

        self.assertRaises(ValueError, ci.check_bit_depth, pid, None)
        self.assertRaises(ValueError, ci.check_bit_depth, pid, 8)

        pids = pds.VISID("231125-143859-ncl-s")
        self.assertIsNone(ci.check_bit_depth(pids, np.uint8(5).dtype))
        self.assertIsNone(ci.check_bit_depth(pids, "Byte"))
        self.assertRaises(ValueError, ci.check_bit_depth, pids, 16)


class TestCreate(unittest.TestCase):
    def test_create(self):
        d = {"meta": "data"}
        with patch("vipersci.vis.create_image.make_image_record") as m_mir:
            ci.create(d, json=False)
            m_mir.assert_called_once_with(d, None, Path.cwd(), "tif")

        with patch("vipersci.vis.create_image.make_image_record") as m_mir, patch(
            "vipersci.vis.create_image.write_json"
        ) as m_wj:
            session_mock = create_autospec(Session)
            ci.create(d, session=session_mock)
            m_wj.assert_called_once()


class TestMakeImage(unittest.TestCase):
    def setUp(self) -> None:
        self.startUTC = datetime(2022, 1, 27, 0, 0, 0, tzinfo=timezone.utc)
        self.d = {
            "adcGain": 0,
            "autoExposure": 0,
            "byteQuota": 1677,
            "cameraId": 0,
            "captureId": 1,
            "exposureTime": 111,
            "imageDepth": 1,
            "imageHeight": 2048,
            "imageId": 0,
            "imageWidth": 2048,
            "immediateDownloadInfo": 10,
            "instrument_name": "NavCam Left",
            "lobt": 1700921056,
            "offset": 0,
            "outputImageMask": 8,
            "outputImageType": "JBIG2_IMAGE",
            "padding": 0,
            "ppaGain": 0,
            "processingInfo": 0,
            "slog": False,
            "stereo": 1,
            "temperature": 0,
            "voltageRamp": 0,
        }

    def test_no_image(self):
        rp = ci.make_image_record(self.d, None)
        self.assertIsInstance(rp, ImageRecord)

    @patch("vipersci.vis.create_image.write_tiff")
    @patch(
        "vipersci.vis.create_image.tif_info",
        return_value={
            "file_byte_offset": 10,
            "file_creation_datetime": datetime.fromtimestamp(1700921056, timezone.utc),
            "file_data_type": "UnsignedMSB2",
            "file_md5_checksum": "md5",
            "file_path": "dummy.tif",
            "lines": 2048,
            "samples": 2048,
        },
    )
    def test_image(self, mock_tif_info, mock_write_tiff):
        image = np.array([[5, 5], [5, 5]], dtype=np.uint16)
        rp = ci.make_image_record(self.d, image, Path("outdir/"))
        self.assertIsInstance(rp, ImageRecord)

        prp = ci.make_image_record(self.d, Path("dummy.tif"), Path("outdir/"))
        self.assertIsInstance(prp, ImageRecord)

        bad_d = self.d
        bad_d["imageWidth"] = 2
        self.assertRaises(
            ValueError, ci.make_image_record, bad_d, image, Path("outdir/")
        )

    @patch("vipersci.vis.create_image.write_png")
    @patch(
        "vipersci.vis.create_image.png_info",
        return_value={
            "file_creation_datetime": datetime.fromtimestamp(1700921056, timezone.utc),
            "file_data_type": "UnsignedMSB2",
            "file_md5_checksum": "md5",
            "file_path": "dummy.tif",
            "lines": 2048,
            "samples": 2048,
        },
    )
    def test_png(self, mock_png_info, mock_write_png):
        image = np.array([[5, 5], [5, 5]], dtype=np.uint16)
        rp = ci.make_image_record(self.d, image, Path("outdir/"), "png")
        self.assertIsInstance(rp, ImageRecord)

        prp = ci.make_image_record(self.d, Path("dummy.png"), Path("outdir/"), "png")
        self.assertIsInstance(prp, ImageRecord)

    def test_bad_imgtype(self):
        self.assertRaises(
            ValueError,
            ci.make_image_record,
            self.d,
            Path("dummy.foo"),
            Path("outdir/"),
            "tif",
        )
        self.assertRaises(
            ValueError,
            ci.make_image_record,
            self.d,
            np.array([[5, 5], [5, 5]], dtype=np.uint16),
            Path("outdir/"),
            "foo",
        )


class TestJSON(unittest.TestCase):
    @patch("vipersci.vis.create_image.json.dump")
    def test_write_json(self, m_dump):
        mock_path = create_autospec(Path)
        mock_path.name = "dummy_dir"
        d = {"key": "value", "key2": "value2", "product_id": "dummy_pid"}
        ci.write_json(d, mock_path)
        m_dump.called_once()


class TestPNG(unittest.TestCase):

    @patch("vipersci.vis.create_image.file_info", return_value={"file_path": "name"})
    def test_png_info(self, mock_fi):
        mock_im = create_autospec(Image)
        mock_im.size = [10, 20]
        with patch("vipersci.vis.create_image.Image.open", return_value=mock_im):
            d = ci.png_info(Path("dummy.png"))
            self.assertDictEqual(d, {"lines": 20, "samples": 10, "file_path": "name"})

    @patch("vipersci.vis.create_image.imsave")
    def test_write_png(self, mock_imsave):
        pid = pds.VISID("231125-143859-ncl-a")
        image = np.array([[5, 5], [5, 5]], dtype=np.uint16)
        outpath = ci.write_png(pid, image, Path("dummy/"))
        self.assertEqual(outpath, Path("dummy/231125-143859-ncl-a.png"))

        self.assertEqual(mock_imsave.call_args.args[0], str(outpath))
        npt.assert_array_equal(mock_imsave.call_args.args[1], image)
        self.assertEqual(mock_imsave.call_args.kwargs["check_contrast"], False)
        self.assertIn("pnginfo", mock_imsave.call_args.kwargs)

        image_bool = np.array([[5, 5], [5, 5]], dtype=np.bool_)
        ci.write_png(pds.VISID("231125-143859-ncl-s"), image_bool, Path("dummy/"))

        image_32 = np.array([[5, 5], [5, 5]], dtype=np.int32)
        ci.write_png(pid, image_32, Path("dummy/"))


class TestTIFF(unittest.TestCase):
    @patch("vipersci.vis.create_image.datetime", wraps=datetime)
    def test_tif_info(self, mock_datetime):
        info = {
            "ifds": [
                {
                    "tags": {
                        273: {"data": (10,)},
                        258: {"data": (16,)},
                        256: {"data": (2048,)},
                        257: {"data": (2048,)},
                    }
                },
            ],
            "bigEndian": "MSB",
        }
        mock_datetime.fromtimestamp.return_value = datetime.fromtimestamp(
            1700921056, timezone.utc
        )

        mock_path = create_autospec(Path)
        mock_path.name = "dummy.tif"

        with patch("vipersci.vis.create_image.util.md5", return_value="hex"):
            with patch("vipersci.vis.create_image.read_tiff", return_value=info):
                d = ci.tif_info(mock_path)

                self.assertEqual(d["file_byte_offset"], 10)
                self.assertEqual(d["file_data_type"], "UnsignedMSB2")

        info2 = {
            "ifds": [
                {
                    "tags": {
                        273: {"data": (10,)},
                        258: {"data": (8,)},
                        256: {"data": (2048,)},
                        257: {"data": (2048,)},
                    }
                },
            ],
            "bigEndian": "MSB",
        }

        with patch("vipersci.vis.create_image.util.md5", return_value="hex"):
            with patch("vipersci.vis.create_image.read_tiff", return_value=info2):
                d = ci.tif_info(mock_path)

                self.assertEqual(d["file_data_type"], "UnsignedByte")

    @patch("vipersci.vis.create_image.imsave")
    def test_write_tiff(self, mock_imsave):
        pid = pds.VISID("231125-143859-ncl-a")
        image = np.array([[5, 5], [5, 5]], dtype=np.uint16)
        outpath = ci.write_tiff(pid, image, Path("dummy/"))
        self.assertEqual(outpath, Path("dummy/231125-143859-ncl-a.tif"))
        mock_imsave.assert_called_once_with(
            str(outpath),
            image,
            check_contrast=False,
            description="VIPER NavCam Left 231125-143859-ncl-a",
            metadata=None,
        )

        image_bool = np.array([[5, 5], [5, 5]], dtype=np.bool_)
        ci.write_tiff(pds.VISID("231125-143859-ncl-s"), image_bool, Path("dummy/"))

        image_32 = np.array([[5, 5], [5, 5]], dtype=np.int32)
        ci.write_tiff(pid, image_32, Path("dummy/"))
