"""Helps to build PDS4 Bundle and Collection XML labels and files.
"""

# Copyright 2023, United States Government as represented by the
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

import argparse

from vipersci import util
from vipersci.pds.labelmaker.bundle import add_parser as bundle_ap
from vipersci.pds.labelmaker.collection import add_parser as collection_ap
from vipersci.pds.labelmaker.generic import add_parser as generic_ap
from vipersci.pds.labelmaker.inventory import add_parser as inventory_ap


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, parents=[util.parent_parser()]
    )
    subparsers = parser.add_subparsers(
        title="subcommands",
        description="valid subcommands",
        help="additional help available via '%(prog)s subcommand -h'",
    )
    bundle_ap(subparsers)
    collection_ap(subparsers)
    inventory_ap(subparsers)
    generic_ap(subparsers)
    args = parser.parse_args()
    args.func(args)
