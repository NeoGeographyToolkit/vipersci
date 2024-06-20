#!/usr/bin/env python
"""This module has tests for the vis.pds.create_raw functions."""

# Copyright 2022-2023, vipersci developers.
#
# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.

import unittest
from argparse import ArgumentParser
from pathlib import Path
from unittest.mock import patch

from datetime_sqlite import isozformat
from geoalchemy2 import load_spatialite
from sqlalchemy import create_engine
from sqlalchemy.event import listen
from sqlalchemy.orm import Session

from vipersci.vis.db import Base
from vipersci.vis.db.image_records import ImageRecord
from vipersci.vis.db.junc_image_pano import JuncImagePano
from vipersci.vis.db.pano_records import PanoRecord
from vipersci.vis.pds import create_pano_product as cpp


class TestParser(unittest.TestCase):
    def test_arg_parser(self):
        p = cpp.arg_parser()
        self.assertIsInstance(p, ArgumentParser)
        self.assertRaises(SystemExit, p.parse_args)
        d = vars(
            p.parse_args(
                ["--dburl", "db://foo:username@host/db", "product_id_goes_here"]
            )
        )
        self.assertIn("dburl", d)
        self.assertIn("template", d)
        self.assertIn("tiff", d)
        self.assertIn("output_dir", d)
        self.assertIn("input", d)


class TestDatabase(unittest.TestCase):
    def setUp(self) -> None:
        self.pr = PanoRecord(
            file_creation_datetime="2023-11-27T22:19:47.216057Z",
            file_md5_checksum="9e9e7de3e8943ca2b355e5a5ffd47858",
            file_path="231109-170000-ncl-pan.tif",
            lines=2048,
            product_id="231109-170000-ncl-pan",
            rover_pan_max=180.0,
            rover_pan_min=-180.0,
            rover_tilt_max=15,
            rover_tilt_min=-50,
            samples=12288,
            software_name="vipersci",
            software_program_name="vipersci.vis.create_pano",
            software_version="0.7.0-dev",
            source_pids=[
                "231109-170000-ncl-c",
                "231109-170100-ncl-c",
                "231109-170200-ncl-c",
            ],
            start_time="2023-11-09T17:00:00Z",
            stop_time="2023-11-09T17:05:00.000511Z",
        )
        ir1 = ImageRecord(
            adc_gain=0,
            auto_exposure=0,
            byteQuota=341,
            cameraId=0,
            capture_id=1,
            exposure_duration=511,
            file_byte_offset=256,
            file_creation_datetime="2023-11-27T22:18:11.879458Z",
            file_data_type="UnsignedLSB2",
            file_md5_checksum="cd30229a7803ec35fbf21a3da254ad10",
            file_path="231109-170000-ncl-d.tif",
            imageDepth=2,
            image_id=0,
            immediateDownloadInfo=24,
            instrument_name="NavCam Left",
            instrument_temperature=0,
            lines=2048,
            lobt=1699549200,
            offset=0,
            output_image_mask=8,
            padding=0,
            pga_gain=1.0,
            processing_info=10,
            product_id="231109-170000-ncl-d",
            samples=2048,
            software_name="vipersci",
            software_program_name="vipersci.vis.create_image",
            software_version="0.7.0-dev",
            start_time="2023-11-09T17:00:00Z",
            stereo=1,
            stop_time="2023-11-09T17:02:00.000511Z",
            voltage_ramp=0,
            yamcs_generation_time="2023-11-09T17:00:00Z",
            yamcs_name="/ViperGround/Images/ImageData/Navcam_left_icer",
            yamcs_reception_time="2023-11-09T17:05:00Z",
        )
        ir2 = ImageRecord(
            adc_gain=0,
            auto_exposure=0,
            byteQuota=341,
            cameraId=0,
            capture_id=1,
            exposure_duration=511,
            file_byte_offset=256,
            file_creation_datetime="2023-11-27T22:18:12.948617Z",
            file_data_type="UnsignedLSB2",
            file_md5_checksum="781d510b1f7f7a4048f7a9eea596b9e6",
            file_path="231109-170100-ncl-d.tif",
            imageDepth=2,
            image_id=0,
            immediateDownloadInfo=24,
            instrument_name="NavCam Left",
            instrument_temperature=0,
            lines=2048,
            lobt=1699549260,
            offset=0,
            output_image_mask=8,
            padding=0,
            pga_gain=1.0,
            processing_info=10,
            product_id="231109-170100-ncl-d",
            samples=2048,
            software_name="vipersci",
            software_program_name="vipersci.vis.create_image",
            software_version="0.7.0-dev",
            start_time="2023-11-09T17:01:00Z",
            stereo=1,
            stop_time="2023-11-09T17:01:00.000511Z",
            voltage_ramp=0,
            yamcs_generation_time="2023-11-09T17:01:00Z",
            yamcs_name="/ViperGround/Images/ImageData/Navcam_left_icer",
            yamcs_reception_time="2023-11-09T17:06:00Z",
        )
        ir3 = ImageRecord(
            adc_gain=0,
            auto_exposure=0,
            byteQuota=341,
            cameraId=0,
            capture_id=1,
            exposure_duration=511,
            file_byte_offset=256,
            file_creation_datetime="2023-11-27T22:18:14.068725Z",
            file_data_type="UnsignedLSB2",
            file_md5_checksum="ee7a86d7ed7a436d23dd6b87ae6c3058",
            file_path="231109-170200-ncl-d.tif",
            imageDepth=2,
            image_id=0,
            immediateDownloadInfo=24,
            instrument_name="NavCam Left",
            instrument_temperature=0,
            lines=2048,
            lobt=1699549320,
            offset=0,
            output_image_mask=8,
            padding=0,
            pga_gain=1.0,
            processing_info=10,
            product_id="231109-170200-ncl-d",
            samples=2048,
            software_name="vipersci",
            software_program_name="vipersci.vis.create_image",
            software_version="0.7.0-dev",
            start_time="2023-11-09T17:02:00Z",
            stereo=1,
            stop_time="2023-11-09T17:02:00.000511Z",
            voltage_ramp=0,
            yamcs_generation_time="2023-11-09T17:02:00Z",
            yamcs_name="/ViperGround/Images/ImageData/Navcam_left_icer",
            yamcs_reception_time="2023-11-09T17:07:00Z",
        )
        self.engine = create_engine("sqlite:///:memory:")
        listen(self.engine, "connect", load_spatialite)
        self.session = Session(self.engine)
        Base.metadata.create_all(self.engine)
        to_add = [
            self.pr,
        ]
        for ir in (ir1, ir2, ir3):
            self.session.add(ir)
            a = JuncImagePano()
            a.image_record = ir
            a.pano_record = self.pr
            to_add.append(a)

        self.session.add_all(to_add)
        self.session.commit()

    def tearDown(self):
        Base.metadata.drop_all(self.engine)

    def test_label_dict(self):
        d = cpp.label_dict(self.pr)
        self.assertEqual(
            d["lid"], f"urn:nasa:pds:viper_vis:data_derived:{self.pr.product_id}"
        )
        self.assertEqual(d["source_product_type"], "data_to_raw_source_product")
        self.assertEqual(d["instruments"][0]["name"], "NavCam Left")

    @patch("vipersci.vis.pds.create_pano_product.create_engine")
    @patch("vipersci.vis.pds.create_pano_product.write_xml")
    def test_main(self, m_write_xml, m_create_engine):
        with patch(
            "vipersci.vis.pds.create_pano_product.Session", return_value=self.session
        ):
            pa_ret_val = cpp.arg_parser().parse_args(
                [
                    "--dburl",
                    "db://foo:username@host/db",
                    self.pr.product_id,
                ]
            )
            with patch("vipersci.vis.pds.create_pano_product.arg_parser") as parser:
                parser.return_value.parse_args.return_value = pa_ret_val
                with patch("vipersci.vis.db.image_records.isozformat", new=isozformat):
                    cpp.main()
                    m_write_xml.assert_called_once()
                    (metadata, template, outdir) = m_write_xml.call_args[0]
                    self.assertEqual(metadata["product_id"], self.pr.product_id)
                    self.assertEqual(outdir, Path.cwd())
                    self.assertEqual(template, "pano-template.xml")
