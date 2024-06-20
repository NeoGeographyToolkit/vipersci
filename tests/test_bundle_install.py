#!/usr/bin/env python
"""This module has tests for the vipersci.pds.bundle_install functions."""

# Copyright 2022-2024, vipersci developers.
#
# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.

import unittest
import xml.etree.ElementTree as ET
from argparse import ArgumentParser
from pathlib import Path
from textwrap import dedent
from unittest.mock import create_autospec, mock_open, patch

import vipersci.pds.bundle_install as bi


class TestCLI(unittest.TestCase):
    def test_arg_parser(self):
        p = bi.arg_parser()
        self.assertIsInstance(p, ArgumentParser)
        self.assertRaises(SystemExit, p.parse_args)
        d = vars(p.parse_args(["src_dir", "bld_dir"]))
        self.assertIn("source_directory", d)
        self.assertIn("build_directory", d)

    def test_main(self):
        pa_ret_val = bi.arg_parser().parse_args(["src_dir", "build_dir"])
        bundle = ET.fromstring(
            dedent(
                """\
                <?xml version="1.0" encoding="UTF-8"?>
                <?xml-model href="http://pds.nasa.gov/pds4/pds/v1/PDS4_PDS_1L00.sch" schematypens="http://purl.oclc.org/dsdl/schematron"?><Product_Bundle xmlns="http://pds.nasa.gov/pds4/pds/v1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://pds.nasa.gov/pds4/pds/v1 http://pds.nasa.gov/pds4/pds/v1/PDS4_PDS_1L00.xsd">
                <Identification_Area>
                    <logical_identifier>urn:nasa:pds:viper_vis</logical_identifier>
                    <version_id>99.99</version_id>
                    <title>VIPER Visible Imaging System Products Bundle</title>
                    <information_model_version>1.21.0.0</information_model_version>
                    <product_class>Product_Bundle</product_class>
                    <Citation_Information>
                        <author_list>Ross Beyer and Uland Wong</author_list>
                        <publication_year>2023</publication_year>
                        <description>VIPER Visible Imaging System Products Bundle</description>
                    </Citation_Information>
                    <Modification_History>
                        <Modification_Detail>
                            <modification_date>2023-10-28</modification_date>
                            <version_id>99.99</version_id>
                            <description>Bogus testing version</description>
                        </Modification_Detail>
                    </Modification_History>
                </Identification_Area>
                <Context_Area>
                    <Time_Coordinates>
                        <start_date_time>2023-10-26T20:00:00Z</start_date_time>
                        <stop_date_time>2023-11-09T17:05:00.000511Z</stop_date_time>
                    </Time_Coordinates>
                    <Primary_Result_Summary>
                        <purpose>Science</purpose>
                        <processing_level>Raw</processing_level><processing_level>Derived</processing_level>
                    </Primary_Result_Summary>
                    <Investigation_Area>
                        <name>VIPER</name>
                        <type>Mission</type>
                        <Internal_Reference>
                            <lid_reference>urn:nasa:pds:viper</lid_reference>
                            <reference_type>bundle_to_investigation</reference_type>
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
                        </Observing_System_Component><Observing_System_Component>
                            <name>NavCam Right</name>
                            <type>Instrument</type>
                            <Internal_Reference>
                                <lid_reference>urn:nasa:pds:context:instrument:viper.vis</lid_reference>
                                <reference_type>is_instrument</reference_type>
                            </Internal_Reference>
                        </Observing_System_Component>
                    </Observing_System>
                    <Target_Identification>
                        <name>Moon</name>
                        <type>Satellite</type>
                        <Internal_Reference>
                            <lid_reference>urn:nasa:pds:context:target:satellite.earth.moon</lid_reference>
                            <reference_type>bundle_to_target</reference_type>
                        </Internal_Reference>
                    </Target_Identification>
                </Context_Area>
                <Bundle>
                    <bundle_type>Archive</bundle_type>
                </Bundle>
                <Bundle_Member_Entry>
                    <lidvid_reference>urn:nasa:pds:viper_vis:data_raw::99.99</lidvid_reference>
                    <member_status>Primary</member_status>
                    <reference_type>bundle_has_data_collection</reference_type>
                </Bundle_Member_Entry>
                <File_Area_Text>
                    <File>
                        <file_name>readme</file_name>
                    </File>
                </File_Area_Text>
                </Product_Bundle>
            """  # noqa: E501
            )
        )
        collection = ET.fromstring(
            dedent(
                """\
                <?xml version="1.0" encoding="UTF-8"?>
                <?xml-model href="http://pds.nasa.gov/pds4/pds/v1/PDS4_PDS_1L00.sch" schematypens="http://purl.oclc.org/dsdl/schematron"?><Product_Collection xmlns="http://pds.nasa.gov/pds4/pds/v1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://pds.nasa.gov/pds4/pds/v1 http://pds.nasa.gov/pds4/pds/v1/PDS4_PDS_1L00.xsd">
                <Identification_Area>
                        <logical_identifier>urn:nasa:pds:viper_vis:data_raw</logical_identifier>
                        <version_id>99.99</version_id>
                        <title>VIPER Visible Imaging System Raw Data Collection</title>
                    <information_model_version>1.21.0.0</information_model_version>
                    <product_class>Product_Collection</product_class>
                    <Citation_Information>
                        <author_list>Ross Beyer and Uland Wong</author_list>
                        <publication_year>2023</publication_year>
                        <description>VIPER Visible Imaging System Raw Data Collection</description>
                    </Citation_Information>
                    <Modification_History>
                        <Modification_Detail>
                            <modification_date>2023-10-28</modification_date>
                            <version_id>99.99</version_id>
                            <description>Bogus testing version</description>
                        </Modification_Detail>
                    </Modification_History>
                </Identification_Area>
                <Context_Area>
                    <Time_Coordinates>
                        <start_date_time>2023-10-26T20:00:00Z</start_date_time>
                        <stop_date_time>2023-11-09T17:05:00.000511Z</stop_date_time>
                    </Time_Coordinates>
                    <Primary_Result_Summary>
                        <purpose>Science</purpose>
                        <processing_level>Raw</processing_level>
                    </Primary_Result_Summary>
                    <Investigation_Area>
                        <name>VIPER</name>
                        <type>Mission</type>
                        <Internal_Reference>
                            <lid_reference>urn:nasa:pds:viper</lid_reference>
                            <reference_type>collection_to_investigation</reference_type>
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
                                <lid_reference>urn:nasa:pds:context:instrument:viper.vis</lid_reference>
                                <reference_type>is_instrument</reference_type>
                            </Internal_Reference>
                        </Observing_System_Component><Observing_System_Component>
                            <name>NavCam Right</name>
                            <type>Instrument</type>
                            <Internal_Reference>
                                <lid_reference>urn:nasa:pds:context:instrument:viper.vis</lid_reference>
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
                        <creation_date_time>2024-01-29T22:07:08.297641Z</creation_date_time>
                    </File>
                    <Inventory>
                        <offset unit="byte">0</offset>
                        <parsing_standard_id>PDS DSV 1</parsing_standard_id>
                        <records>10</records>
                        <record_delimiter>Carriage-Return Line-Feed</record_delimiter>
                        <field_delimiter>Comma</field_delimiter>
                        <Record_Delimited>
                            <fields>2</fields>
                            <groups>0</groups>
                            <Field_Delimited>
                                <name>Member Status</name>
                                <field_number>1</field_number>
                                <data_type>ASCII_String</data_type>
                                <maximum_field_length unit="byte">1</maximum_field_length>
                                <description>
                                  P indicates primary member of the collection
                                  S indicates secondary member of the collection
                                </description>
                            </Field_Delimited>
                            <Field_Delimited>
                                <name>LIDVID_LID</name>
                                <field_number>2</field_number>
                                <data_type>ASCII_LIDVID_LID</data_type>
                                <maximum_field_length unit="byte">255</maximum_field_length>
                                <description>
                                  The LID or LIDVID of a product that is a member
                                  of the collection.
                                </description>
                            </Field_Delimited>
                        </Record_Delimited>
                        <reference_type>inventory_has_member_product</reference_type>
                    </Inventory>
                </File_Area_Inventory>
                </Product_Collection>
                """  # noqa: E501
            )
        )
        inventory = dedent(
            """\
        P,urn:nasa:pds:viper_vis:data_raw:240225-200000-ncl-d::99.99
        """
        )
        with patch("vipersci.pds.bundle_install.arg_parser") as parser, patch(
            "vipersci.pds.bundle_install.copy2"
        ), patch(
            "vipersci.pds.bundle_install.ET.fromstring",
            side_effect=[bundle, collection],
        ), patch(
            "vipersci.pds.bundle_install.open", mock_open(read_data=inventory)
        ), patch(
            "vipersci.pds.bundle_install.get_lidvidfile",
            return_value={
                "lid": "urn:nasa:pds:viper_vis:data_raw:240225-200000-ncl-d",
                "vid": "99.99",
                "productfile": "240225-200000-ncl-d.tif",
            },
        ):
            build_path = create_autospec(Path)
            src_path = create_autospec(Path)
            src_col_dir = create_autospec(Path)
            src_col_dir.rglob.return_value = [
                create_autospec(Path),
            ]
            src_path.__truediv__.return_value = src_col_dir
            pa_ret_val.build_directory = build_path
            pa_ret_val.source_directory = src_path
            parser.return_value.parse_args.return_value = pa_ret_val
            bi.main()
