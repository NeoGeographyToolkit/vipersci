#!/usr/bin/env python
"""This module has tests for the vis.pds.labelmaker.generic functions."""

# Copyright 2023, vipersci developers.
#
# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.

import unittest
from argparse import ArgumentParser
from pathlib import Path
from unittest.mock import create_autospec, patch

import vipersci.pds.labelmaker.generic as gen
from vipersci import util


class TestParser(unittest.TestCase):
    def test_add_parser(self):
        parser = ArgumentParser()
        subparsers = parser.add_subparsers()
        gen.add_parser(subparsers)

        d = vars(
            parser.parse_args(
                ["generic", "--json", "dumb.json", "template.xml", "out.xml"]
            )
        )
        self.assertIn("json", d)
        self.assertIn("template", d)
        self.assertIn("output", d)

    def test_main(self):
        parser = ArgumentParser(parents=[util.parent_parser()])
        subparsers = parser.add_subparsers()
        gen.add_parser(subparsers)

        args = parser.parse_args(
            ["generic", "--json", "dumb.json", "template.xml", "out.xml"]
        )

        args.json = create_autospec(Path)

        with patch(
            "vipersci.pds.labelmaker.generic.json.loads", return_value={"dummy": "dict"}
        ) as m_jsonloads, patch(
            "vipersci.pds.labelmaker.generic.write_xml",
        ) as m_write_xml:
            gen.main(args)

            m_jsonloads.assert_called_once()
            m_write_xml.assert_called_once()
