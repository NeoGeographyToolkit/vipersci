"""Creates a PDS4 Collection Inventory CSV file from the provided XML labels.
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

import logging
from pathlib import Path

from vipersci import util
from vipersci.pds.labelmaker import get_lidvidfile, write_inventory

logger = logging.getLogger(__name__)


def add_parser(subparsers):
    parser = subparsers.add_parser("inventory", help=__doc__)

    parser.add_argument(
        "-n",
        "--name",
        required=True,
        help="The name that will be used to form the name of the output file.  If "
        "'-n foobar' is given, the output file will be collection_foobar.csv ",
    )
    parser.add_argument(
        "-m",
        "--member",
        choices=["P", "S"],
        default="P",
        help="Indicates whether the products are a primary (P) or secondary (S) member "
        "of the collection.  All products will be marked identically. "
        "Default: %(default)s",
    )
    parser.add_argument(
        "labelfiles",
        type=Path,
        nargs="+",
        help="Path(s) to all XML label files to be included in the output collection "
        "file.",
    )
    parser.set_defaults(func=main)
    return parser


def main(args):
    util.set_logger(args.verbose)

    outpath = Path(f"collection_{args.name}.csv")

    labels = []
    for path in args.labelfiles:
        labels.append(get_lidvidfile(path))

    write_inventory(outpath, labels, args.member)
