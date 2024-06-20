#!/usr/bin/env python
"""This module has tests for the vis.pds.labelmaker.bundle functions."""

# Copyright 2023, vipersci developers.
#
# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.

import unittest
from argparse import ArgumentParser
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import create_autospec, patch

import vipersci.pds.labelmaker.bundle as bun
from vipersci import util


class TestCollection(unittest.TestCase):
    def setUp(self):
        self.base = {
            "bundle_lid": "urn.pds:bundle",
            "investigation_name": "nameo",
            "investigation_type": "typeo",
            "investigation_lid": "urn:pds:nameo",
            "host_name": "hosto",
            "host_lid": "urn:pds:hosto",
            "target_name": "Moon",
            "target_type": "Satellite",
            "target_lid": "urn:pds:Moon",
        }

        self.label1 = {
            "lid": "urn.pds:bundle:collection",
            "collection_type": "Data",
            "vid": "0.1",
            "instruments": {"urn:pds:leftcam": "NavCam Left"},
            "purposes": [
                "Science",
            ],
            "processing_levels": [
                "Raw",
            ],
            "start_date_time": datetime(2023, 10, 1, 20, 00, 00, tzinfo=timezone.utc),
            "stop_date_time": datetime(2023, 10, 1, 20, 00, 1, tzinfo=timezone.utc),
        }
        self.label1.update(self.base)

        self.label2 = {
            "lid": "urn.pds:bundle:collection",
            "collection_type": "Data",
            "vid": "2.0",
            "instruments": {"urn:pds:rightcam": "NavCam Right"},
            "purposes": [
                "Science",
            ],
            "processing_levels": [
                "Derived",
            ],
            "start_date_time": datetime(2023, 11, 1, 20, 00, 00, tzinfo=timezone.utc),
            "stop_date_time": datetime(2023, 11, 1, 20, 00, 1, tzinfo=timezone.utc),
        }
        self.label2.update(self.base)

    def test_add_parser(self):
        parser = ArgumentParser()
        subparsers = parser.add_subparsers()
        bun.add_parser(subparsers)

        d = vars(
            parser.parse_args(
                [
                    "bundle",
                    "--config",
                    "dumb.yml",
                    "-t",
                    "template.xml",
                    "file1.xml",
                    "file2.xml",
                ]
            )
        )
        self.assertIn("config", d)
        self.assertIn("template", d)
        self.assertIn("labelfiles", d)

    @patch("vipersci.pds.labelmaker.bundle.ET.fromstring")
    @patch(
        "vipersci.pds.labelmaker.bundle.get_common_label_info",
        return_value={"lid": "urn:pds:dummy:pid"},
    )
    def test_get_label_info(self, m_gcli, m_fromstring):
        p = create_autospec(Path)
        d = bun.get_label_info(p)

        m_fromstring.assert_called_once()
        m_gcli.assert_called_once()
        self.assertEqual(d["bundle_lid"], "urn:pds:dummy")

    def test_check_and_derive(self):
        config = self.base.copy()
        config["modification_details"] = [{"version": "1.0"}, {"version": "2.0"}]

        d = bun.check_and_derive(config, [self.label1, self.label2])

        self.assertEqual(
            {
                "collections": [
                    {
                        "lid": "urn.pds:bundle:collection::0.1",
                        "type": "bundle_has_data_collection",
                    },
                    {
                        "lid": "urn.pds:bundle:collection::2.0",
                        "type": "bundle_has_data_collection",
                    },
                ],
                "vid": "2.0",
                "instruments": {
                    "urn:pds:leftcam": "NavCam Left",
                    "urn:pds:rightcam": "NavCam Right",
                },
                "purposes": {"Science"},
                "processing_levels": {"Derived", "Raw"},
                "start_date_time": "2023-10-01T20:00:00Z",
                "stop_date_time": "2023-11-01T20:00:01Z",
            },
            d,
        )

    def test_main(self):
        parser = ArgumentParser(parents=[util.parent_parser()])
        subparsers = parser.add_subparsers()
        bun.add_parser(subparsers)

        args = parser.parse_args(
            [
                "bundle",
                "-c",
                "dummy.yml",
                "-t",
                "template.xml",
                "file1.xml",
                "file2.xml",
            ]
        )

        args.config = create_autospec(Path)

        config = self.base.copy()
        config["modification_details"] = [{"version": "1.0"}, {"version": "2.0"}]

        path_mock = create_autospec(Path)
        path_mock.exists.return_value = False

        with patch(
            "vipersci.pds.labelmaker.bundle.yaml.safe_load", return_value=config
        ) as m_yamlload, patch(
            "vipersci.pds.labelmaker.bundle.get_label_info",
            side_effect=(self.label1, self.label2),
        ) as m_get_label, patch(
            "vipersci.pds.labelmaker.bundle.write_xml"
        ) as m_write_xml, patch(
            "vipersci.pds.labelmaker.bundle.Path", return_value=path_mock
        ) as m_path:
            bun.main(args)

            m_yamlload.assert_called_once()
            self.assertEqual(m_get_label.call_count, 2)
            m_path.assert_called_once()
            m_write_xml.assert_called_once()
