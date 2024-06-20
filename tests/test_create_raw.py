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
from vipersci.vis.db.light_records import LightRecord, luminaire_names
from vipersci.vis.pds import create_raw as cr


class TestParser(unittest.TestCase):
    def test_arg_parser(self):
        p = cr.arg_parser()
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
        self.ir = ImageRecord(
            adc_gain=0,
            auto_exposure=0,
            byteQuota=341,
            cameraId=0,
            capture_id=1,
            exposure_duration=111,
            file_byte_offset=256,
            file_creation_datetime="2023-08-01T00:51:51.148919Z",
            file_data_type="UnsignedLSB2",
            file_md5_checksum="b8f1a035e39c223e2b7e236846102c29",
            file_path="231125-140416-ncl-d.tif",
            imageDepth=2,
            image_id=0,
            immediateDownloadInfo=10,
            instrument_name="NavCam Left",
            instrument_temperature=0,
            light_on_hap=None,
            light_on_has=None,
            light_on_hcp=None,
            light_on_hcs=None,
            light_on_hfp=None,
            light_on_hfs=None,
            light_on_nl=None,
            light_on_nr=None,
            lines=2048,
            lobt=1700921056,
            offset=0,
            outputImageType="LOSSY_ICER_IMAGE",
            output_image_mask=8,
            padding=0,
            pga_gain=1.0,
            processing_info=10,
            product_id="231125-140416-ncl-d",
            samples=2048,
            software_name="vipersci",
            software_program_name="vipersci.vis.create_image",
            software_version="0.6.0-dev",
            start_time="2023-11-25T14:04:16Z",
            stereo=1,
            stop_time="2023-11-25T14:04:16.000111Z",
            voltage_ramp=0,
            yamcs_generation_time="2023-08-01T00:51:41.820000Z",
            yamcs_name="/ViperGround/Images/ImageData/Navcam_left_icer",
        )
        self.engine = create_engine("sqlite:///:memory:")
        listen(self.engine, "connect", load_spatialite)
        self.session = Session(self.engine)
        Base.metadata.create_all(self.engine)
        self.session.add(self.ir)
        self.session.commit()

    def tearDown(self):
        Base.metadata.drop_all(self.engine)

    def test_get_lights(self):
        truth = {k: False for k in luminaire_names.values()}
        light_name = list(luminaire_names.values())[0]

        # No lights in the db yet
        li = cr.get_lights(self.ir, self.session)
        self.assertEqual(truth, li)

        # Add an early light
        self.session.add(
            LightRecord(
                name=light_name,
                on=True,
                datetime="2023-11-25T13:04:10Z",
            )
        )
        early = cr.get_lights(self.ir, self.session)
        self.assertEqual(truth, early)

        # A previous light "off" event w/in 10 s
        self.session.add(
            LightRecord(
                name=light_name,
                on=False,
                datetime="2023-11-25T13:04:09Z",
            )
        )
        off = cr.get_lights(self.ir, self.session)
        self.assertEqual(truth, off)

        # Add a light "on" w/in 10 s:
        self.session.add(
            LightRecord(
                name=light_name,
                on=True,
                datetime="2023-11-25T14:04:10Z",
            )
        )
        self.session.add(
            LightRecord(
                name=light_name,
                on=False,
                datetime="2023-11-25T14:04:20Z",
            )
        )
        truth[light_name] = True
        t = cr.get_lights(self.ir, self.session)
        self.assertEqual(truth, t)

        # Now, no session
        t = cr.get_lights(self.ir, None)
        all_false = {k: False for k in luminaire_names.values()}
        self.assertEqual(all_false, t)

    def test_label_dict(self):
        d = cr.label_dict(self.ir, cr.get_lights(self.ir, self.session))
        self.assertEqual(
            d["lid"], f"urn:nasa:pds:viper_vis:data_raw:{self.ir.product_id}"
        )
        self.assertEqual(d["exposure_type"], "Manual")
        self.assertEqual(d["luminaires"][list(luminaire_names.values())[0]], "Off")
        self.assertEqual(d["image_filters"], "Flat field normalization. Linearization.")
        self.assertEqual(d["sample_bits"], 12)

    @patch("vipersci.vis.pds.create_raw.create_engine")
    @patch("vipersci.vis.pds.create_raw.write_xml")
    @patch("vipersci.vis.pds.create_raw.tif_info")
    def test_main(self, m_tif_info, m_write_xml, m_create_engine):
        with patch("vipersci.vis.pds.create_raw.Session", return_value=self.session):
            pa_ret_val = cr.arg_parser().parse_args(
                [
                    "--dburl",
                    "db://foo:username@host/db",
                    self.ir.product_id,
                ]
            )
            with patch("vipersci.vis.pds.create_raw.arg_parser") as parser:
                parser.return_value.parse_args.return_value = pa_ret_val
                with patch("vipersci.vis.db.image_records.isozformat", new=isozformat):
                    cr.main()
                    m_write_xml.assert_called_once()
                    (metadata, template, outdir) = m_write_xml.call_args[0]
                    self.assertEqual(metadata["product_id"], self.ir.product_id)
                    self.assertEqual(outdir, Path.cwd())
                    self.assertEqual(template, "raw-template.xml")
