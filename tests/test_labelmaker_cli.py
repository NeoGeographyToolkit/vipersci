#!/usr/bin/env python
"""This module has tests for the vis.pds.labelmaker.inventory functions."""

# Copyright 2023, vipersci developers.
#
# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.

import unittest
from unittest.mock import patch

import vipersci.pds.labelmaker.cli as cli


class TestMain(unittest.TestCase):
    @patch("vipersci.pds.labelmaker.cli.argparse.ArgumentParser", autospec=True)
    def test_main(self, m_parser):
        cli.main()

        m_parser.assert_called()
