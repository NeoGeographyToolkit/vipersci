#!/usr/bin/env python
"""This module has tests for the vis.pds.create_pano functions."""

# Copyright 2023, vipersci developers.
#
# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.

from datetime import datetime, timezone
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np

from vipersci.vis.db.pano_products import PanoProduct
from vipersci.vis.pds import create_pano as cp


class TestMakePano(unittest.TestCase):
    def setUp(self) -> None:
        self.startUTC = datetime(2022, 1, 27, 0, 0, 0, tzinfo=timezone.utc)
        self.d = {
            "instrument_name": "NavCam Left",
            "lines": 2048,
            "product_id": "230421-200000-ncl-pan",
            "samples": 6000,
        }

    def test_no_image(self):
        pp = cp.make_pano_product(self.d)
        self.assertIsInstance(pp, PanoProduct)

    @patch("vipersci.vis.pds.create_pano.imsave")
    @patch(
        "vipersci.vis.pds.create_pano.tif_info",
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
    def test_image(self, mock_tif_info, mock_imsave):
        image = np.array([[5, 5], [5, 5]], dtype=np.uint16)
        pp = cp.make_pano_product(self.d, image, Path("outdir/"))
        self.assertIsInstance(pp, PanoProduct)
        mock_imsave.assert_called_once()
        mock_tif_info.assert_called_once()

        mock_imsave.reset_mock()
        mock_tif_info.reset_mock()

        prp = cp.make_pano_product(self.d, Path("dummy.tif"), Path("outdir/"))
        self.assertIsInstance(prp, PanoProduct)
        mock_imsave.assert_not_called()
        mock_tif_info.assert_called_once()
