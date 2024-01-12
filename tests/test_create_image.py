#!/usr/bin/env python
"""This module has tests for the vis.pds.create_raw functions."""

# Copyright 2022-2023, vipersci developers.
#
# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.

from datetime import datetime, timezone
from pathlib import Path
import unittest
from unittest.mock import create_autospec, patch

import numpy as np

from vipersci.pds import pid as pds
from vipersci.vis.db.image_records import ImageRecord
from vipersci.vis import create_image as ci


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
        self.assertRaises(ValueError, ci.check_bit_depth, pids, 16)


class TestMakeImage(unittest.TestCase):
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
        rp = ci.make_image_record(self.d, None, None)
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
