#!/usr/bin/env python
"""This module has tests for the vis.pds.labelmaker functions."""

# Copyright 2023, vipersci developers.
#
# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.

import unittest
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from textwrap import dedent
from unittest.mock import call, create_autospec, mock_open, patch

import pandas as pd

import vipersci.pds.labelmaker as lm
from genshi.template import Template


class TestFunctions(unittest.TestCase):
    def setUp(self):
        self.xmltext = dedent(
            """\
        <?xml version="1.0" encoding="UTF-8"?>
        <?xml-model href="https://pds.nasa.gov/pds4/pds/v1/PDS4_PDS_1K00.sch"
          schematypens="http://purl.oclc.org/dsdl/schematron"?>
        <Product_Collection
          xmlns="http://pds.nasa.gov/pds4/pds/v1"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xsi:schemaLocation="http://pds.nasa.gov/pds4/pds/v1
          https://pds.nasa.gov/pds4/pds/v1/PDS4_PDS_1K00.xsd">
        <Identification_Area>
            <logical_identifier>urn:nasa:pds:dummy_lid</logical_identifier>
            <version_id>1.0</version_id>
          <Modification_History>
            <Modification_Detail>
              <modification_date>2023-10-28</modification_date>
              <version_id>0.1</version_id>
              <description>Bogus testing version</description>
            </Modification_Detail>
          </Modification_History>
        </Identification_Area>
        <Context_Area>
          <Time_Coordinates>
            <start_date_time>2023-10-26T20:00:00Z</start_date_time>
            <stop_date_time>2023-10-26T20:00:00.000511Z</stop_date_time>
          </Time_Coordinates>
          <Primary_Result_Summary>
            <purpose>Engineering</purpose>
            <processing_level>Raw</processing_level>
          </Primary_Result_Summary>
          <Investigation_Area>
            <name>MISSIONNAME</name>
            <type>Mission</type>
            <Internal_Reference>
              <lid_reference>urn:nasa:pds:missionname</lid_reference>
              <reference_type>collection_to_investigation</reference_type>
            </Internal_Reference>
          </Investigation_Area>
          <Observing_System>
            <Observing_System_Component>
              <name>MISSIONNAME</name>
              <type>Host</type>
              <Internal_Reference>
                <lid_reference>urn:nasa:pds:context:instrument_host:spacecraft.missionname</lid_reference>
                <reference_type>is_instrument_host</reference_type>
              </Internal_Reference>
            </Observing_System_Component>
            <Observing_System_Component>
                <name>NavCam Left</name>
                <type>Instrument</type>
                <Internal_Reference>
                    <lid_reference>urn:nasa:pds:context:instrument_host:spacecraft.missionname.navcam_left</lid_reference>
                    <reference_type>is_instrument</reference_type>
                </Internal_Reference>
            </Observing_System_Component><Observing_System_Component>
                <name>NavCam Right</name>
                <type>Instrument</type>
                <Internal_Reference>
                    <lid_reference>urn:nasa:pds:context:instrument_host:spacecraft.missionname.navcam_right</lid_reference>
                    <reference_type>is_instrument</reference_type>
                </Internal_Reference>
            </Observing_System_Component>
          </Observing_System>
          <Target_Identification>
            <name>Moon</name>
            <type>Satellite</type>
            <Internal_Reference>
              <lid_reference>urn:nasa:pds:context:target:satellite.earth.moon</lid_reference>
              <reference_type>collection_to_target</reference_type>
            </Internal_Reference>
          </Target_Identification>
        </Context_Area>
        <Collection>
          <collection_type>Data</collection_type>
        </Collection>
        <File_Area_Inventory>
          <File>
            <file_name>collection_data_raw.csv</file_name>
            <creation_date_time>2023-11-02T23:12:59.083415Z</creation_date_time>
          </File>
          <Inventory>
            <offset unit="byte">0</offset>
            <parsing_standard_id>PDS DSV 1</parsing_standard_id>
            <records>4</records>
            <record_delimiter>Carriage-Return Line-Feed</record_delimiter>
            <field_delimiter>Comma</field_delimiter>
          </Inventory>
        </File_Area_Inventory>
        </Product_Collection>
        """
        )

    def test_get_lidvidfile(self):
        mock_path = create_autospec(Path)
        mock_path.read_text.return_value = dedent(
            """\
            <?xml version="1.0" encoding="UTF-8"?>
            <?xml-model
              href="https://pds.nasa.gov/pds4/pds/v1/PDS4_PDS_1K00.sch"
              schematypens="http://purl.oclc.org/dsdl/schematron"?>
            <Product_Observational
              xmlns="http://pds.nasa.gov/pds4/pds/v1"
              xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
              xsi:schemaLocation="http://pds.nasa.gov/pds4/pds/v1
              https://pds.nasa.gov/pds4/pds/v1/PDS4_PDS_1K00.xsd">
            <Identification_Area>
                <logical_identifier>urn:nasa:pds:dummy_lid</logical_identifier>
                <version_id>1.0</version_id>
            </Identification_Area>
            <File_Area_Observational>
              <File>
                <file_name>product.name</file_name>
              </File>
            </File_Area_Observational>
            </Product_Observational>
            """
        )

        truth = {
            "lid": "urn:nasa:pds:dummy_lid",
            "vid": "1.0",
            "productfile": "product.name",
        }

        d = lm.get_lidvidfile(mock_path)

        self.assertEqual(truth, d)

    def test_get_common_label_info(self):
        root = ET.fromstring(self.xmltext)
        host_lid = "urn:nasa:pds:context:instrument_host:spacecraft.missionname"
        truth = {
            "lid": "urn:nasa:pds:dummy_lid",
            "vid": "1.0",
            "start_date_time": datetime(2023, 10, 26, 20, 00, 00, tzinfo=timezone.utc),
            "stop_date_time": datetime(
                2023, 10, 26, 20, 00, 00, 511, tzinfo=timezone.utc
            ),
            "investigation_name": "MISSIONNAME",
            "investigation_type": "Mission",
            "investigation_lid": "urn:nasa:pds:missionname",
            "host_name": "MISSIONNAME",
            "host_lid": host_lid,
            "target_name": "Moon",
            "target_type": "Satellite",
            "target_lid": "urn:nasa:pds:context:target:satellite.earth.moon",
            "instruments": {
                "NavCam Left": f"{host_lid}.navcam_left",
                "NavCam Right": f"{host_lid}.navcam_right",
            },
            "purposes": [
                "Engineering",
            ],
            "processing_levels": [
                "Raw",
            ],
        }
        d = lm.get_common_label_info(root, area="pds:Context_Area")
        self.assertEqual(truth, d)

    def test_gather_info(self):
        df = pd.DataFrame(
            data={
                "vid": ["0.1", "0.1", "1.0"],
                "instruments": [
                    {
                        "urn:nasa:pds:ncl": "NavCam Left",
                        "urn:nasa:pds:ncr": "NavCam Right",
                    },
                    {
                        "urn:nasa:pds:ncl": "NavCam Left",
                        "urn:nasa:pds:ncr": "NavCam Right",
                    },
                    {"urn:nasa:pds:acl": "AftCam Left"},
                ],
                "purposes": [
                    [
                        "Engineering",
                    ],
                    [
                        "Science",
                    ],
                    [
                        "Science",
                    ],
                ],
                "processing_levels": [
                    [
                        "Raw",
                    ],
                    [
                        "Raw",
                    ],
                    [
                        "Derived",
                    ],
                ],
                "start_date_time": [
                    datetime(2023, 10, 1, 20, 00, 00, tzinfo=timezone.utc),
                    datetime(2023, 10, 15, 20, 00, 00, tzinfo=timezone.utc),
                    datetime(2023, 11, 1, 20, 00, 00, tzinfo=timezone.utc),
                ],
                "stop_date_time": [
                    datetime(2023, 10, 1, 20, 00, 1, tzinfo=timezone.utc),
                    datetime(2023, 10, 15, 20, 00, 1, tzinfo=timezone.utc),
                    datetime(2023, 11, 1, 20, 00, 1, tzinfo=timezone.utc),
                ],
            }
        )

        truth = {
            "vid": "2.0",
            "instruments": {
                "urn:nasa:pds:ncl": "NavCam Left",
                "urn:nasa:pds:ncr": "NavCam Right",
                "urn:nasa:pds:acl": "AftCam Left",
            },
            "purposes": {"Engineering", "Science"},
            "processing_levels": {"Raw", "Derived"},
            "start_date_time": "2023-10-01T20:00:00Z",
            "stop_date_time": "2023-11-01T20:00:01Z",
        }
        d = lm.gather_info(df, [{"version": "0.1"}, {"version": "2.0"}])
        self.assertEqual(truth, d)

    def test_assert_unique(self):
        self.assertIsNone(lm.assert_unique("a", pd.Series(["a", "a"])))
        self.assertRaises(ValueError, lm.assert_unique, "a", pd.Series(["b", "b"]))
        self.assertRaises(ValueError, lm.assert_unique, "a", pd.Series(["a", "b"]))

    def test_vid_max(self):
        mod_details = [
            {"version": "1.0"},
            {"version": "1.1"},
            {"version": "2.0"},
        ]
        self.assertEqual(lm.vid_max(mod_details), 2.0)
        self.assertEqual(lm.vid_max(mod_details, 2.0), 2.0)
        self.assertRaises(ValueError, lm.vid_max, mod_details, 3.0)

    def test_write_inventory(self):
        m = mock_open()
        labels = [
            {"lid": "lid1", "vid": "1.0"},
            {"lid": "lid2", "vid": "1.0"},
        ]
        with patch("vipersci.pds.labelmaker.open", m):
            lm.write_inventory(Path("dummy_path"), labels)

        handle = m()
        handle.write.assert_has_calls(
            [call("P,lid1::1.0\r\n"), call("P,lid2::1.0\r\n")]
        )

    def test_write_xml(self):
        m_path = create_autospec(Path)
        m_tmpl_path = create_autospec(Path)
        m_tmpl = create_autospec(Template)
        with patch(
            "vipersci.pds.labelmaker.MarkupTemplate", return_value=m_tmpl
        ) as m_markup:
            lm.write_xml({"lid": "dummy_lid", "vid": "1.0"}, m_path, m_tmpl_path)

        m_tmpl_path.read_text.assert_called_once()
        m_markup.assert_called_once()
        m_tmpl.generate.assert_called_once()
        m_path.write_text.assert_called_once()
