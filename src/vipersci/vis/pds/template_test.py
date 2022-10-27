"""
Test creation of PDS labels.

Takes a JSON file and a Genshi XML template, and uses the JSON file to fill
out the template.
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

import argparse
import json
import logging
import sys
from pathlib import Path

# import genshi
# from genshi.template import TemplateLoader
from genshi.template import MarkupTemplate

from vipersci import util

logger = logging.getLogger(__name__)


def arg_parser():
    parser = argparse.ArgumentParser(
        description=__doc__, parents=[util.parent_parser()]
    )
    parser.add_argument("-j", "--json", type=Path, help="Path to .json file to load.")
    parser.add_argument("input", type=Path, help="Genshi XML file template.")
    parser.add_argument("output", type=Path, help="Output XML label.")
    return parser


def main():
    args = arg_parser().parse_args()
    util.set_logger(args.verbose)

    with open(args.json, "r") as f:
        info = json.load(f)

    # loader = TemplateLoader()
    # tmpl = loader.load(str(args.input))
    tmpl = MarkupTemplate(args.input.read_text())
    stream = tmpl.generate(**info)
    args.output.write_text(stream.render())


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
