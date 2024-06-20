#!/usr/bin/env python
"""This module has tests for the vis.pds.labelmaker.inventory functions."""

# Copyright 2023, vipersci developers.
#
# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.

import unittest
from argparse import ArgumentParser
from unittest.mock import patch

import vipersci.pds.labelmaker.inventory as inv
from vipersci import util


class TestParser(unittest.TestCase):
    def test_add_parser(self):
        parser = ArgumentParser()
        subparsers = parser.add_subparsers()
        inv.add_parser(subparsers)

        d = vars(
            parser.parse_args(
                ["inventory", "--name", "dumbname", "file1.xml", "file2.xml"]
            )
        )
        self.assertIn("name", d)
        self.assertIn("member", d)
        self.assertIn("labelfiles", d)

    def test_main(self):
        parser = ArgumentParser(parents=[util.parent_parser()])
        subparsers = parser.add_subparsers()
        inv.add_parser(subparsers)

        args = parser.parse_args(
            ["inventory", "--name", "dumbname", "file1.xml", "file2.xml"]
        )

        with patch(
            "vipersci.pds.labelmaker.inventory.get_lidvidfile",
            return_value={"dummy": "dict"},
        ) as m_get_lidvid, patch(
            "vipersci.pds.labelmaker.inventory.write_inventory",
        ) as m_write_inv:
            inv.main(args)

            self.assertEqual(2, m_get_lidvid.call_count)
            m_write_inv.assert_called_once()
