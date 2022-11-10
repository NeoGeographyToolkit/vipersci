#!/usr/bin/env python
"""This module has tests for the vis.pds.create_raw functions."""

# Copyright 2022, vipersci developers.
#
# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.

from datetime import datetime, timezone
from pathlib import Path
import unittest
from unittest.mock import create_autospec, mock_open, patch

import numpy as np

from vipersci.pds import pid as pds
from vipersci.vis.db.raw_products import RawProduct
from vipersci.vis.pds import create_raw as cw


class TestBitDepth(unittest.TestCase):
    def test_check_bit_depth(self):
        pid = pds.VISID("231125-143859-ncl-a")
        self.assertIsNone(cw.check_bit_depth(pid, 16))
        self.assertIsNone(cw.check_bit_depth(pid, "UnsignedLSB2"))
        self.assertIsNone(cw.check_bit_depth(pid, np.uint16(5).dtype))

        self.assertRaises(ValueError, cw.check_bit_depth, pid, None)
        self.assertRaises(ValueError, cw.check_bit_depth, pid, 8)

        pids = pds.VISID("231125-143859-ncl-s")
        self.assertIsNone(cw.check_bit_depth(pids, np.uint8(5).dtype))
        self.assertRaises(ValueError, cw.check_bit_depth, pids, 16)


class TestMakeRaw(unittest.TestCase):
    def setUp(self) -> None:
        self.startUTC = datetime(2022, 1, 27, 0, 0, 0, tzinfo=timezone.utc)
        self.d = {
            "adcGain": 0,
            "autoExposure": 0,
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
            "outputImageMask": 2,
            "outputImageType": "JBIG2_IMAGE",
            "padding": 0,
            "ppaGain": 0,
            "processingInfo": 20,
            "slog": False,
            "stereo": 1,
            "temperature": 0,
            "voltageRamp": 0,
        }

    def test_no_image(self):
        rp = cw.make_raw_product(self.d, None, None)
        self.assertIsInstance(rp, RawProduct)

    @patch("vipersci.vis.pds.create_raw.write_tiff")
    @patch(
        "vipersci.vis.pds.create_raw.tif_info",
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
        rp = cw.make_raw_product(self.d, image, Path("outdir/"))
        self.assertIsInstance(rp, RawProduct)

        prp = cw.make_raw_product(self.d, Path("dummy.tif"), Path("outdir/"))
        self.assertIsInstance(prp, RawProduct)

        bad_d = self.d
        bad_d["imageWidth"] = 2
        self.assertRaises(
            ValueError, cw.make_raw_product, bad_d, image, Path("outdir/")
        )


class TestTIFF(unittest.TestCase):
    @patch("vipersci.vis.pds.create_raw.datetime", wraps=datetime)
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

        with patch("vipersci.vis.pds.create_raw.open", mock_open(read_data=b"test")):
            with patch("vipersci.vis.pds.create_raw.read_tiff", return_value=info):
                d = cw.tif_info(mock_path)

                self.assertEqual(d["file_byte_offset"], 10)
                self.assertEqual(d["file_data_type"], "UnsignedMSB2")

    @patch("vipersci.vis.pds.create_raw.imsave")
    def test_write_tiff(self, mock_imsave):
        pid = pds.VISID("231125-143859-ncl-a")
        image = np.array([[5, 5], [5, 5]], dtype=np.uint16)
        outpath = cw.write_tiff(pid, image, Path("dummy/"))
        self.assertEqual(outpath, Path("dummy/231125-143859-ncl-a.tif"))
        mock_imsave.assert_called_once_with(
            str(outpath),
            image,
            check_contrast=False,
            description="VIPER NavCam Left 231125-143859-ncl-a",
            metadata=None,
        )
