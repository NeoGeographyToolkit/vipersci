"""Creates Raw VIS TIFF files from source 16-bit images.

At this time, this program allows a user to explicitly specify
the Product ID, but in the future the Product ID will be generated
based on image metadata.
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

import numpy as np
from skimage.io import imread, imsave

from vipersci.pds import pid as pds
from vipersci import util

logger = logging.getLogger(__name__)


def arg_parser():
    parser = argparse.ArgumentParser(
        description=__doc__,
        parents=[util.parent_parser()]
    )
    parser.add_argument(
        "-p", "--product_id",
        help="The desired Product ID of the output image."
    )
    parser.add_argument(
        "-o", "--output_dir",
        type=Path,
        default=Path.cwd(),
        help="Output directory for TIFF file."
    )
    parser.add_argument(
        "image",
        type=Path,
        help="Input image file, must be an unsigned 16-bit image."
    )
    return parser


def main():
    args = arg_parser().parse_args()
    util.set_logger(args.verbose)

    # Eventually, this will be replaced by data gathered from the
    # telemetry stream.  For now, we fake

    pid = pds.VISID(args.product_id)

    image = imread(str(args.image))

    if image.dtype != np.uint16:
        raise ValueError(
            f"The input image is not a uint16, it is {image.dtype}"
        )

    desc = f"VIPER {pds.vis_instruments[pid.instrument]} {pid}"

    logger.info(desc)

    imsave(
        str(pid) + ".tif",
        image,
        check_contrast=False,
        description=desc,
        metadata=None
    )

    return
