"""Generically takes a Genshi XML template and a JSON or YAML file to complete
the template.
"""

# Copyright 2021-2022, United States Government as represented by the
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

import json
import logging
from pathlib import Path

import yaml

from vipersci import util
from vipersci.pds.labelmaker import write_xml

logger = logging.getLogger(__name__)


def add_parser(subparsers):
    parser = subparsers.add_parser("generic", help=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-j", "--json", type=Path, help="Path to .json file to load.")
    group.add_argument("-y", "--yaml", type=Path, help="Path to .yml file to load.")
    parser.add_argument("template", type=Path, help="Genshi XML file template.")
    parser.add_argument("output", type=Path, help="Output XML label.")
    parser.set_defaults(func=main)
    return parser


def main(args):
    util.set_logger(args.verbose)

    info = {}
    if args.json is not None:
        info = json.loads(args.json.read_text())
    elif args.yaml is not None:
        info = yaml.safe_load(args.yaml.read_text())

    write_xml(info, args.output, args.template)
