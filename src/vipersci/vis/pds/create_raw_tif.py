"""Creates Raw VIS TIFF files from source 16-bit images.

This program is meant to help manually build test data sets.
"""

# Copyright 2022, United States Government as represented by the
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
import logging
from pathlib import Path

from skimage.io import imread

from vipersci.pds import pid as pds
from vipersci.vis.pds.create_raw import write_tiff
from vipersci import util

logger = logging.getLogger(__name__)


def arg_parser():
    parser = argparse.ArgumentParser(
        description=__doc__, parents=[util.parent_parser()]
    )
    parser.add_argument(
        "-p",
        "--product_id",
        required=True,
        help="The desired Product ID of the output image.",
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        type=Path,
        default=Path.cwd(),
        help="Output directory for TIFF file.",
    )
    parser.add_argument(
        "image", type=Path, help="Input image file, must be an unsigned 16-bit image."
    )
    return parser


def main():
    args = arg_parser().parse_args()
    util.set_logger(args.verbose)

    pid = pds.VISID(args.product_id)

    image = imread(str(args.image))

    write_tiff(pid, image, args.output_dir)

    return
