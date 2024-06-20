#!/usr/bin/env python
"""This module has tests for the vis.pds.labelmaker.collection functions."""

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

import vipersci.pds.labelmaker.collection as co
from vipersci import util


class TestCollection(unittest.TestCase):
    def setUp(self):
        self.base = {
            "collection_lid": "urn.pds:collection",
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
        co.add_parser(subparsers)

        d = vars(
            parser.parse_args(
                [
                    "collection",
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

    @patch("vipersci.pds.labelmaker.collection.ET.fromstring")
    @patch(
        "vipersci.pds.labelmaker.collection.get_common_label_info",
        return_value={"lid": "urn:pds:dummy:pid"},
    )
    def test_get_label_info(self, m_gcli, m_fromstring):
        p = create_autospec(Path)
        d = co.get_label_info(p)

        m_fromstring.assert_called_once()
        m_gcli.assert_called_once()
        self.assertEqual(d["collection_lid"], "urn:pds:dummy")

    def test_check_and_derive(self):
        config = self.base.copy()
        config["collection_type"] = "Data"
        config["modification_details"] = [{"version": "1.0"}, {"version": "2.0"}]

        d = co.check_and_derive(config, [self.label1, self.label2])

        self.assertEqual(
            {
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
        co.add_parser(subparsers)

        args = parser.parse_args(
            [
                "collection",
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
        config["collection_type"] = "Data"
        config["modification_details"] = [{"version": "1.0"}, {"version": "2.0"}]

        path_mock = create_autospec(Path)
        path_mock.exists.return_value = False

        with patch(
            "vipersci.pds.labelmaker.collection.yaml.safe_load", return_value=config
        ) as m_yamlload, patch(
            "vipersci.pds.labelmaker.collection.get_label_info",
            side_effect=(self.label1, self.label2),
        ) as m_get_label, patch(
            "vipersci.pds.labelmaker.collection.write_inventory"
        ) as m_write_inventory, patch(
            "vipersci.pds.labelmaker.collection.write_xml"
        ) as m_write_xml, patch(
            "vipersci.pds.labelmaker.collection.Path", return_value=path_mock
        ) as m_path:
            co.main(args)

            m_yamlload.assert_called_once()
            self.assertEqual(m_get_label.call_count, 2)
            self.assertEqual(m_path.call_count, 2)
            m_write_inventory.assert_called_once()
            m_write_xml.assert_called_once()

        # The collection XML label already exists:
        path_mock.exists.return_value = True
        with patch(
            "vipersci.pds.labelmaker.collection.yaml.safe_load", return_value=config
        ), patch("vipersci.pds.labelmaker.collection.Path", return_value=path_mock):
            self.assertRaises(FileExistsError, co.main, args)

        # The collection XML label doesn't exist, but the collection inventory does.
        path_mock2 = create_autospec(Path)
        path_mock2.exists.side_effect = (False, True)
        with patch(
            "vipersci.pds.labelmaker.collection.yaml.safe_load", return_value=config
        ), patch(
            "vipersci.pds.labelmaker.collection.get_label_info",
            side_effect=(self.label1, self.label2),
        ), patch(
            "vipersci.pds.labelmaker.collection.Path", return_value=path_mock2
        ):
            self.assertRaises(FileExistsError, co.main, args)
