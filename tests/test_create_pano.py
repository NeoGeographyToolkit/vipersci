#!/usr/bin/env python
"""This module has tests for the vis.create_pano functions."""

# Copyright 2023, vipersci developers.
#
# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.

import unittest
from argparse import ArgumentParser
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import create_autospec, Mock, patch

import numpy as np
from geoalchemy2 import load_spatialite
from sqlalchemy import create_engine
from sqlalchemy.event import listen
from sqlalchemy.orm import Session

from vipersci.vis import create_pano as cp
from vipersci.vis.db import Base
from vipersci.vis.db.image_records import ImageRecord
from vipersci.vis.db.pano_records import PanoRecord


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
        self.assertIn("output_dir", d)
        self.assertIn("inputs", d)

    def test_main(self):
        pa_ret_val = cp.arg_parser().parse_args(
            ["231126-000000-ncl-s.dummy", "231126-000000-ncr-s.dummy"]
        )
        with patch("vipersci.vis.create_pano.arg_parser") as parser, patch(
            "vipersci.vis.create_pano.create"
        ) as m_create:
            parser.return_value.parse_args.return_value = pa_ret_val
            cp.main()
            m_create.assert_called_once()

        pa2_ret_val = cp.arg_parser().parse_args(
            [
                "--dburl",
                "db://foo:username@host/db",
                "231126-000000-ncl-s.dummy",
                "231126-000000-ncr-s.dummy",
            ]
        )
        session_engine_mock = create_autospec(Session)
        session_mock = create_autospec(Session)
        session_engine_mock.__enter__ = Mock(return_value=session_mock)
        with patch("vipersci.vis.create_pano.arg_parser") as parser, patch(
            "vipersci.vis.create_pano.create"
        ) as m_create, patch("vipersci.vis.create_pano.create_engine"), patch(
            "vipersci.vis.create_pano.Session", return_value=session_engine_mock
        ):
            parser.return_value.parse_args.return_value = pa2_ret_val
            cp.main()
            m_create.assert_called_once()
            session_engine_mock.__enter__.assert_called_once()
            session_mock.commit.assert_called_once()


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
        pp = cp.make_pano_record(self.d)
        self.assertIsInstance(pp, PanoRecord)

    @patch("vipersci.vis.create_pano.imsave")
    @patch(
        "vipersci.vis.create_pano.tif_info",
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
        pp = cp.make_pano_record(self.d, image, Path("outdir/"))
        self.assertIsInstance(pp, PanoRecord)
        mock_imsave.assert_called_once()
        mock_tif_info.assert_called_once()

        mock_imsave.reset_mock()
        mock_tif_info.reset_mock()

        prp = cp.make_pano_record(self.d, Path("dummy.tif"), Path("outdir/"))
        self.assertIsInstance(prp, PanoRecord)
        mock_imsave.assert_not_called()
        mock_tif_info.assert_called_once()


class TestCreate(unittest.TestCase):
    def test_nodb(self):
        self.assertRaises(ValueError, cp.create, [1, 2, 3])
        self.assertRaises(
            FileNotFoundError,
            cp.create,
            ["231126-000000-ncl-s.dummy", "231126-000000-ncr-s.dummy"],
        )

        path_mock = create_autospec(Path)
        path_mock.exists.return_value = True

        with patch("vipersci.vis.create_pano.Path", return_value=path_mock), patch(
            "vipersci.vis.create_pano.imread"
        ) as m_imread, patch("vipersci.vis.create_pano.np.hstack"), patch(
            "vipersci.vis.create_pano.make_pano_record"
        ) as m_mpr, patch(
            "vipersci.vis.create_pano.write_json"
        ) as m_write_json, patch(
            "vipersci.vis.create_pano.isinstance",
            side_effect=[True, True, False, True, False, True],
        ):
            cp.create(["231126-000000-ncl-s.dummy", "231126-000000-ncr-s.dummy"])

            self.assertEqual(m_imread.call_count, 2)
            self.assertEqual(m_mpr.call_args[0][2], Path.cwd())
            m_write_json.assert_called_once()

    def test_db(self):
        ir1 = ImageRecord(
            adc_gain=0,
            auto_exposure=0,
            cameraId=0,
            capture_id=1,
            exposure_duration=111,
            file_byte_offset=256,
            file_creation_datetime="2023-08-01T00:51:51.148919Z",
            file_data_type="UnsignedLSB2",
            file_md5_checksum="b8f1a035e39c223e2b7e236846102c29",
            file_path="231126-000000-ncl-s",
            imageDepth=2,
            image_id=0,
            immediateDownloadInfo=16,
            instrument_name="NavCam Left",
            instrument_temperature=0,
            lines=2048,
            lobt=1700956800,
            offset=0,
            outputImageType="SLOG_ICER_IMAGE",
            output_image_mask=16,
            padding=0,
            pga_gain=1.0,
            processing_info=26,
            product_id="231126-000000-ncl-s",
            samples=2048,
            software_name="vipersci",
            software_program_name="vipersci.vis.create_image",
            software_version="0.6.0-dev",
            start_time="2023-11-26T00:00:00Z",
            stereo=1,
            stop_time="2023-11-26T00:00:00.000111Z",
            voltage_ramp=0,
            yamcs_generation_time="2023-11-26T00:00:00Z",
            yamcs_name="/ViperGround/Images/ImageData/Navcam_left_slog",
        )
        ir2 = ImageRecord(
            adc_gain=0,
            auto_exposure=0,
            cameraId=1,
            capture_id=2,
            exposure_duration=111,
            file_byte_offset=256,
            file_creation_datetime="2023-08-01T00:51:51.148919Z",
            file_data_type="UnsignedLSB2",
            file_md5_checksum="b8f1a035e39c223e2b7e236846102c29",
            file_path="231126-000000-ncr-s",
            imageDepth=2,
            image_id=0,
            immediateDownloadInfo=16,
            instrument_name="NavCam Right",
            instrument_temperature=0,
            lines=2048,
            lobt=1700956800,
            offset=0,
            outputImageType="SLOG_ICER_IMAGE",
            output_image_mask=16,
            padding=0,
            pga_gain=1.0,
            processing_info=26,
            product_id="231126-000000-ncr-s",
            samples=2048,
            software_name="vipersci",
            software_program_name="vipersci.vis.create_image",
            software_version="0.6.0-dev",
            start_time="2023-11-26T00:00:00Z",
            stereo=1,
            stop_time="2023-11-26T00:00:00.000111Z",
            voltage_ramp=0,
            yamcs_generation_time="2023-11-26T00:00:00Z",
            yamcs_name="/ViperGround/Images/ImageData/Navcam_left_slog",
        )
        engine = create_engine("sqlite:///:memory:")
        listen(engine, "connect", load_spatialite)
        session = Session(engine)
        Base.metadata.create_all(engine)
        session.add(ir1)
        session.add(ir2)
        session.commit()

        path_mock = create_autospec(Path)
        path_mock.exists.return_value = True

        with patch("vipersci.vis.create_pano.Path", return_value=path_mock), patch(
            "vipersci.vis.create_pano.imread"
        ) as m_imread, patch("vipersci.vis.create_pano.np.hstack"), patch(
            "vipersci.vis.create_pano.make_pano_record"
        ) as m_mpr, patch(
            "vipersci.vis.create_pano.isinstance",
            side_effect=[True, True, True, True, True, True],
        ):
            session.add_all = Mock()
            cp.create(
                ["231126-000000-ncl-s", "231126-000000-ncr-s"],
                session=session,
                json=False,
            )

            self.assertEqual(m_imread.call_count, 2)
            self.assertEqual(m_mpr.call_args[0][2], Path.cwd())
