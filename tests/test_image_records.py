#!/usr/bin/env python
"""This module has tests for the image_records module."""

# Copyright 2022-2023, United States Government as represented by the
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
from datetime import datetime, timedelta, timezone

from vipersci.pds.pid import VISID
from vipersci.vis.db import image_records as trp
from vipersci.vis.db.image_requests import ImageRequest  # noqa
from vipersci.vis.db.image_stats import ImageStats  # noqa
from vipersci.vis.db.image_tags import ImageTag, taglist  # noqa
from vipersci.vis.db.junc_image_pano import JuncImagePano  # noqa
from vipersci.vis.db.junc_image_record_tags import JuncImageRecordTag  # noqa
from vipersci.vis.db.junc_image_req_ldst import JuncImageRequestLDST  # noqa
from vipersci.vis.db.ldst import LDST  # noqa
from vipersci.vis.db.light_records import LightRecord  # noqa
from vipersci.vis.db.pano_records import PanoRecord  # noqa
from vipersci.vis.db.ptu_records import PanRecord, TiltRecord  # noqa


class TestImageType(unittest.TestCase):
    def test_init(self):
        self.assertEqual(trp.ImageType.LOSSLESS_ICER_IMAGE, trp.ImageType(1))

    def test_single_flags(self):
        self.assertRaises(ValueError, trp.ImageType, 9)

    def test_not_member(self):
        self.assertRaises(ValueError, trp.ImageType, 1000)


class TestProcessingStage(unittest.TestCase):
    def test_init(self):
        self.assertEqual(trp.ProcessingStage.FLATFIELD, trp.ProcessingStage(2))

    def test_combintation(self):
        self.assertEqual(
            trp.ProcessingStage.FLATFIELD | trp.ProcessingStage.LINEARIZATION,
            trp.ProcessingStage(10),
        )

    def test_not_member(self):
        self.assertRaises(ValueError, trp.ProcessingStage, 15)


class TestImageRecord(unittest.TestCase):
    def setUp(self):
        self.startUTC = datetime(2022, 1, 27, 0, 0, 0, tzinfo=timezone.utc)
        self.d = dict(
            adc_gain=63,
            auto_exposure=False,
            bad_pixel_table_id=0,
            capture_id=0,
            exposure_duration=111,
            file_creation_datetime=datetime.now(timezone.utc),
            file_path="/path/to/dummy",
            light_on_hap=False,
            light_on_has=False,
            light_on_hcp=False,
            light_on_hcs=False,
            light_on_hfp=False,
            light_on_hfs=False,
            light_on_nl=False,
            light_on_nr=False,
            icer_byte_quota=493448,
            image_id=0,
            instrument_name="NavCam Left",
            instrument_temperature=128,
            lines=2048,
            lobt=self.startUTC.timestamp(),
            md5_checksum="dummychecksum",
            minLoss=0,
            mission_phase="Test",
            offset=16324,
            # onboard_compression_ratio=5,
            onboard_compression_type="ICER",
            output_image_mask=8,
            output_image_type="?",
            padding=0,
            pga_gain=0,
            processing_info=0,
            purpose="Engineering",
            samples=2048,
            slog=False,
            stereo=False,
            voltage_ramp=109,
        )
        self.extras = dict(foo="bar")

    def test_init(self):
        rp = trp.ImageRecord(**self.d)
        self.assertEqual("220127-000000-ncl-c", str(rp.product_id))

        d = self.d.copy()
        d.update(self.extras)
        rpl = trp.ImageRecord(**d)
        self.assertEqual("220127-000000-ncl-c", str(rpl.product_id))

        d = self.d.copy()
        d["capture_id"] = 65537
        ir_ci = trp.ImageRecord(**d)
        self.assertEqual(1, ir_ci.waypoint_id)
        self.assertEqual(1, ir_ci.unique_capture_id)

    def test_init_slog(self):
        d_slog = {
            "adcGain": 0,
            "autoExposure": 0,
            "cameraId": 0,
            "captureId": 1,
            "exposureTime": 511,
            "imageDepth": 2,
            "imageHeight": 2048,
            "imageWidth": 2048,
            "imageId": 0,
            "immediateDownloadInfo": 24,
            "temperature": 0,
            "lobt": 1698350400,
            "offset": 0,
            "outputImageMask": 16,
            "padding": 0,
            "pgaGain": 1.0,
            "processingInfo": 26,
            "product_id": "231026-200000-ncl-s",
            "stereo": 1,
            "voltageRamp": 0,
            "yamcs_generation_time": "2023-10-26T20:00:00Z",
            "yamcs_reception_time": "2023-10-26T20:03:00Z",
            "yamcs_name": "/ViperGround/Images/ImageData/Navcam_left_slog",
        }
        ir_slog = trp.ImageRecord(**d_slog)
        self.assertEqual("NavCam Left", ir_slog.instrument_name)

        d2_slog = d_slog.copy()
        del d2_slog["outputImageMask"]
        trp.ImageRecord(**d2_slog)

        d3_slog = d_slog.copy()
        del d3_slog["product_id"]
        del d3_slog["outputImageMask"]
        trp.ImageRecord(**d3_slog)

        err_slog = d_slog.copy()
        err_slog["product_id"] = "231026-200000-ncl-z"  # bad compression letter
        err_slog["outputImageMask"] = None
        self.assertRaises(ValueError, trp.ImageRecord, **err_slog)

        # for k in dir(rp):
        #     if k.startswith(("_", "validate_")):
        #         continue

        #     print(f"{k}: {getattr(rp, k)}")

    def test_init_errors(self):
        d = self.d.copy()
        d["start_time"] = self.startUTC + timedelta(hours=1)
        self.assertRaises(ValueError, trp.ImageRecord, **d)

        d = self.d.copy()
        del d["instrument_name"]
        self.assertRaises(ValueError, trp.ImageRecord, **d)

        d = self.d.copy()
        d["product_id"] = "220127-010000-ncl-b"
        self.assertRaises(ValueError, trp.ImageRecord, **d)

        d = self.d.copy()
        d["product_id"] = "220127-000000-ncr-b"
        self.assertRaises(ValueError, trp.ImageRecord, **d)

        d = self.d.copy()
        d["product_id"] = "220127-000000-ncl-b"
        d["onboard_compression_ratio"] = 999
        self.assertRaises(ValueError, trp.ImageRecord, **d)

        d = self.d.copy()
        del d["lobt"]
        d["start_time"] = self.startUTC  # correct
        d["product_id"] = "220127-000001-ncl-c"  # pid.datetime incorrect
        self.assertRaises(ValueError, trp.ImageRecord, **d)

        d = self.d.copy()
        d["cameraId"] = 1
        self.assertWarns(UserWarning, trp.ImageRecord, **d)

        d = self.d.copy()
        d["product_id"] = "220127-000001-ncl-s"  # pid.compression incorrect
        del d["output_image_mask"]
        del d["processing_info"]
        self.assertRaises(ValueError, trp.ImageRecord, **d)

        d = self.d.copy()
        del d["output_image_mask"]
        del d["icer_byte_quota"]
        self.assertRaises(ValueError, trp.ImageRecord, **d)

        d = self.d.copy()
        d["processing_info"] = 99
        self.assertWarns(UserWarning, trp.ImageRecord, **d)

    # Commented out while this exception has been converted to a warning until we
    # sort out the Yamcs parameter.
    # def test_mcam_id(self):
    #     rp = trp.RawProduct(**self.d)
    #     self.assertRaises(ValueError, setattr, rp, "mcam_id", 5)

    def test_product_id(self):
        rp = trp.ImageRecord(**self.d)
        self.assertRaises(NotImplementedError, setattr, rp, "product_id", "dummy")

    # def test_purpose(self):
    #     rp = trp.ImageRecord(**self.d)
    #     self.assertRaises(ValueError, setattr, rp, "purpose", "dummy")

    def test_lt(self):
        ir1 = trp.ImageRecord(**self.d)
        v = VISID("230127-000000-ncl-a")
        ir2 = trp.ImageRecord(
            product_id=str(v), start_time=v.datetime(), exposure_duration=111
        )
        self.assertTrue(ir1 < ir2)

        self.assertEqual(NotImplemented, ir1.__lt__("not an ImageRecord"))

    def test_update(self):
        rp = trp.ImageRecord(**self.d)
        k = "foo"
        self.assertTrue(k not in rp.labelmeta)

        rp.update(self.extras)
        self.assertTrue(k in rp.labelmeta)

        rp.update({"file_md5_checksum": "foo"})
        self.assertEqual(rp.file_md5_checksum, "foo")

    # def test_labeldict(self):
    #     din = self.d
    #     din.update(self.extras)
    #     rp = trp.ImageRecord(**din)
    #     d = rp.label_dict()
    #     self.assertEqual(d["samples"], rp.samples)

    def test_synonym(self):
        din = self.d
        del din["exposure_duration"]
        din["exposureTime"] = 400
        del din["samples"]
        din["imageWidth"] = 4
        rp = trp.ImageRecord(**din)
        self.assertEqual(rp.exposure_duration, 400)
        rp.exposureTime = 500
        self.assertEqual(rp.exposure_duration, 500)

    def test_fromyamcs(self):
        name = "/ViperGround/Images/ImageData/Navcam_left_slog"
        reception_time = datetime.now(timezone.utc)
        generation_time = reception_time - timedelta(minutes=1)
        d = {
            "adcGain": 0,
            "autoExposure": 0,
            "cameraId": 0,
            "captureId": 1,
            "exposureTime": 111,
            "haz1LightState": "OFF",
            "haz2LightState": "OFF",
            "haz3LightState": "OFF",
            "haz4LightState": "OFF",
            "haz5LightState": "OFF",
            "haz6LightState": "OFF",
            "imageDepth": 1,
            "imageHeight": 2048,
            "imageId": 0,
            "imageWidth": 2048,
            "immediateDownloadInfo": 10,
            "lobt": 1700921056,
            "navLeftLightState": "ON",
            "navRightLightState": "ON",
            "offset": 0,
            "outputImageMask": 16,
            "outputImageType": "JBIG2_IMAGE",
            "padding": 0,
            "ppaGain": 0,
            "processingInfo": 26,
            "stereo": 1,
            "temperature": 0,
            "voltageRamp": 0,
        }
        rp = trp.ImageRecord(
            yamcs_name=name,
            yamcs_generation_time=generation_time,
            yamcs_reception_time=reception_time,
            **d,
            onboard_compression_ratio=16
        )
        self.assertEqual(rp.yamcs_name, name)
        self.assertEqual(rp.samples, d["imageWidth"])

    def test_fromxml(self):
        t = """<?xml version="1.0" encoding="UTF-8"?>
<?xml-model href="http://pds.nasa.gov/pds4/pds/v1/PDS4_PDS_1I00.sch" schematypens="http://purl.oclc.org/dsdl/schematron"?>
<?xml-model href="http://pds.nasa.gov/pds4/disp/v1/PDS4_DISP_1I00_1510.sch" schematypens="http://purl.oclc.org/dsdl/schematron"?>
<?xml-model href="http://pds.nasa.gov/pds4/img/v1/PDS4_IMG_1I00_1860.sch" schematypens="http://purl.oclc.org/dsdl/schematron"?>
<?xml-model href="http://pds.nasa.gov/pds4/msn/v1/PDS4_MSN_1I00_1300.sch" schematypens="http://purl.oclc.org/dsdl/schematron"?>
<?xml-model href="http://pds.nasa.gov/pds4/proc/v1/PDS4_PROC_1I00_1210.sch" schematypens="http://purl.oclc.org/dsdl/schematron"?>

<Product_Observational
    xmlns="http://pds.nasa.gov/pds4/pds/v1"
    xmlns:disp="http://pds.nasa.gov/pds4/disp/v1"
    xmlns:img="http://pds.nasa.gov/pds4/img/v1"
    xmlns:msn="http://pds.nasa.gov/pds4/msn/v1"
    xmlns:proc="http://pds.nasa.gov/pds4/proc/v1"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="
    http://pds.nasa.gov/pds4/pds/v1 http://pds.nasa.gov/pds4/pds/v1/PDS4_PDS_1I00.xsd
    http://pds.nasa.gov/pds4/disp/v1 http://pds.nasa.gov/pds4/disp/v1/PDS4_DISP_1I00_1510.xsd
    http://pds.nasa.gov/pds4/img/v1 http://pds.nasa.gov/pds4/img/v1/PDS4_IMG_1I00_1860.xsd
    http://pds.nasa.gov/pds4/msn/v1 http://pds.nasa.gov/pds4/msn/v1/PDS4_MSN_1I00_1300.xsd
    http://pds.nasa.gov/pds4/proc/v1 http://pds.nasa.gov/pds4/proc/v1/PDS4_PROC_1I00_1210.xsd
">
  <Identification_Area>
    <logical_identifier>urn:nasa:pds:viper_vis:raw:231125-143859-ncl-d</logical_identifier>
    <version_id>0.1</version_id>
    <title>VIPER Visible Imaging System NavCam Left image - 231125-143859-ncl-d</title>
    <information_model_version>1.18.0.0</information_model_version>
    <product_class>Product_Observational</product_class>
    <Modification_History>
      <Modification_Detail>
        <modification_date>2022-10-19</modification_date>
        <version_id>0.1</version_id>
        <description>Illegal version number for testing</description>
      </Modification_Detail>
    </Modification_History>
  </Identification_Area>
  <Observation_Area>
    <Time_Coordinates>
      <start_date_time>2023-11-25T14:38:59Z</start_date_time>
      <stop_date_time>2023-11-25T14:38:59.000111Z</stop_date_time>
    </Time_Coordinates>
    <Primary_Result_Summary>
      <purpose>Navigation</purpose>
      <processing_level>Raw</processing_level>
    </Primary_Result_Summary>
    <Investigation_Area>
      <name>VIPER</name>
      <type>Mission</type>
      <Internal_Reference>
        <lid_reference>urn:nasa:pds:viper</lid_reference>
        <reference_type>data_to_investigation</reference_type>
      </Internal_Reference>
    </Investigation_Area>
    <Observing_System>
      <Observing_System_Component>
        <name>VIPER</name>
        <type>Host</type>
        <Internal_Reference>
            <lid_reference>urn:nasa:pds:context:instrument_host:spacecraft.viper</lid_reference>
            <reference_type>is_instrument_host</reference_type>
        </Internal_Reference>
      </Observing_System_Component>
      <Observing_System_Component>
        <name>NavCam Left</name>
        <type>Instrument</type>
        <Internal_Reference>
            <lid_reference>urn:nasa:pds:context:instrument_host:spacecraft.viper.navcam_left</lid_reference>
            <reference_type>is_instrument</reference_type>
        </Internal_Reference>
      </Observing_System_Component>
    </Observing_System>
    <Target_Identification>
      <name>Moon</name>
      <type>Satellite</type>
      <Internal_Reference>
        <lid_reference>urn:nasa:pds:context:target:satellite.earth.moon</lid_reference>
        <reference_type>data_to_target</reference_type>
      </Internal_Reference>
    </Target_Identification>
    <Discipline_Area>
        <disp:Display_Settings>
            <Local_Internal_Reference>
                <local_identifier_reference>image2d</local_identifier_reference>
                <local_reference_type>display_settings_to_array</local_reference_type>
            </Local_Internal_Reference>
            <disp:Display_Direction>
                <disp:horizontal_display_axis>Sample</disp:horizontal_display_axis>
                <disp:horizontal_display_direction>Left to Right</disp:horizontal_display_direction>
                <disp:vertical_display_axis>Line</disp:vertical_display_axis>
                <disp:vertical_display_direction>Top to Bottom</disp:vertical_display_direction>
            </disp:Display_Direction>
        </disp:Display_Settings>
        <img:Imaging>
           <Local_Internal_Reference>
               <local_identifier_reference>image2d</local_identifier_reference>
               <local_reference_type>imaging_parameters_to_image_object</local_reference_type>
           </Local_Internal_Reference>
           <img:Detector>
               <img:first_line>1</img:first_line>
               <img:first_sample>1</img:first_sample>
               <img:lines>2048</img:lines>
               <img:samples>2048</img:samples>
               <img:gain_number>1</img:gain_number>
               <img:analog_offset>0</img:analog_offset>
               <img:bad_pixel_replacement_table_id>0</img:bad_pixel_replacement_table_id>
           </img:Detector>
           <img:Exposure>
               <img:exposure_duration unit="microseconds">111</img:exposure_duration>
               <img:exposure_type>Manual</img:exposure_type>
           </img:Exposure>
            <img:Illumination>
                <img:LED_Illumination_Source>
                    <img:name>NavLight Left</img:name>
                    <img:illumination_state>Off</img:illumination_state>
                    <img:illumination_wavelength unit="nm">453</img:illumination_wavelength>
                </img:LED_Illumination_Source><img:LED_Illumination_Source>
                    <img:name>NavLight Right</img:name>
                    <img:illumination_state>Off</img:illumination_state>
                    <img:illumination_wavelength unit="nm">453</img:illumination_wavelength>
                </img:LED_Illumination_Source><img:LED_Illumination_Source>
                    <img:name>HazLight Aft Port</img:name>
                    <img:illumination_state>Off</img:illumination_state>
                    <img:illumination_wavelength unit="nm">453</img:illumination_wavelength>
                </img:LED_Illumination_Source><img:LED_Illumination_Source>
                    <img:name>HazLight Aft Starboard</img:name>
                    <img:illumination_state>Off</img:illumination_state>
                    <img:illumination_wavelength unit="nm">453</img:illumination_wavelength>
                </img:LED_Illumination_Source><img:LED_Illumination_Source>
                    <img:name>HazLight Center Port</img:name>
                    <img:illumination_state>Off</img:illumination_state>
                    <img:illumination_wavelength unit="nm">453</img:illumination_wavelength>
                </img:LED_Illumination_Source><img:LED_Illumination_Source>
                    <img:name>HazLight Center Starboard</img:name>
                    <img:illumination_state>Off</img:illumination_state>
                    <img:illumination_wavelength unit="nm">453</img:illumination_wavelength>
                </img:LED_Illumination_Source><img:LED_Illumination_Source>
                    <img:name>HazLight Fore Port</img:name>
                    <img:illumination_state>Off</img:illumination_state>
                    <img:illumination_wavelength unit="nm">453</img:illumination_wavelength>
                </img:LED_Illumination_Source><img:LED_Illumination_Source>
                    <img:name>HazLight Fore Starboard</img:name>
                    <img:illumination_state>Off</img:illumination_state>
                    <img:illumination_wavelength unit="nm">453</img:illumination_wavelength>
                </img:LED_Illumination_Source>
            </img:Illumination>
        <img:Onboard_Compression>
            <img:onboard_compression_class>Lossy</img:onboard_compression_class>
            <img:onboard_compression_type>ICER</img:onboard_compression_type>
            <img:onboard_compression_ratio>64</img:onboard_compression_ratio>
        </img:Onboard_Compression>
        <img:Sampling>
            <img:sample_bits>12</img:sample_bits>
            <img:sample_bit_mask>2#0000111111111111</img:sample_bit_mask>
        </img:Sampling>
        <img:Instrument_State>
            <img:Device_Temperatures>
                <img:Device_Temperature>
                    <img:device_name>NavCam Left</img:device_name>
                    <img:temperature_value unit="K">0</img:temperature_value>
                </img:Device_Temperature>
            </img:Device_Temperatures>
        </img:Instrument_State>
        </img:Imaging>
        <msn:Mission_Information>
            <msn:mission_phase_name>TEST</msn:mission_phase_name>
        </msn:Mission_Information>
        <proc:Processing_Information>
            <Local_Internal_Reference>
                <local_identifier_reference>image2d</local_identifier_reference>
                <local_reference_type>processing_information_to_data_object</local_reference_type>
            </Local_Internal_Reference>
            <proc:Process>
                <proc:process_owner_institution_name>VIPER Visible Imaging System Team,
                NASA Ames Research Center</proc:process_owner_institution_name>
                <proc:Software>
                    <proc:name>vipersci</proc:name>
                    <proc:software_version_id>0.1.0</proc:software_version_id>
                    <proc:software_type>Python</proc:software_type>
                    <proc:Software_Program>
                        <proc:name>vipersci.vis.pds.create_raw</proc:name>
                    </proc:Software_Program>
                </proc:Software>
            </proc:Process>
        </proc:Processing_Information>
    </Discipline_Area>
  </Observation_Area>
  <File_Area_Observational>
    <File>
      <file_name>231125-143859-ncl-d.tif</file_name>
      <creation_date_time>2022-10-19T17:27:04.097587Z</creation_date_time>
    </File>
    <Array_2D_Image>
        <local_identifier>image2d</local_identifier>
        <md5_checksum>8c708f5745ad2b6d9bac6036062bbd31</md5_checksum>
        <offset unit="byte">256</offset>
        <axes>2</axes>
        <axis_index_order>Last Index Fastest</axis_index_order>
        <Element_Array>
            <data_type>UnsignedLSB2</data_type>
            <unit>DN</unit>
        </Element_Array>
        <Axis_Array>
            <axis_name>Line</axis_name>
            <elements>2048</elements>
            <sequence_number>1</sequence_number>
        </Axis_Array>
        <Axis_Array>
            <axis_name>Sample</axis_name>
            <elements>2048</elements>
            <sequence_number>2</sequence_number>
        </Axis_Array>
    </Array_2D_Image>
  </File_Area_Observational>
</Product_Observational>
        """  # noqa: E501
        rp = trp.ImageRecord.from_xml(t.encode())
        self.assertEqual("231125-143859-ncl-d", rp.product_id)

        t_not_viper_vis = t.replace(
            "<logical_identifier>urn:nasa:pds:viper_vis:raw:231125-143859-ncl-d",
            "<logical_identifier>urn:nasa:pds:NOT_viper_vis:raw:231125-143859-ncl-d",
        )
        self.assertRaises(
            ValueError, trp.ImageRecord.from_xml, t_not_viper_vis.encode()
        )

        t_not_raw = t.replace(
            "<logical_identifier>urn:nasa:pds:viper_vis:raw:231125-143859-ncl-d",
            "<logical_identifier>urn:nasa:pds:viper_vis:NOT_raw:231125-143859-ncl-d",
        )
        self.assertRaises(ValueError, trp.ImageRecord.from_xml, t_not_raw.encode())
