"""Check to see if an image has anomalous pixels which may indicate that those pixels
in the detector may be of concern.
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
import logging
import sys
from pathlib import Path

import numpy as np
from skimage.filters import median
from skimage.io import imread

from vipersci import util

logger = logging.getLogger(__name__)


def arg_parser():
    parser = argparse.ArgumentParser(
        description=__doc__, parents=[util.parent_parser()]
    )
    parser.add_argument(
        "-t",
        "--tolerance",
        type=float,
        default=3,
        help="The number of standard deviations of the difference between the image "
        "and its median filter to 'trigger' on.",
    )
    parser.add_argument("input", type=Path, help="VIS Image.")
    return parser


def main():
    parser = arg_parser()
    args = parser.parse_args()
    util.set_logger(args.verbose)

    image = imread(args.input)

    indices = check(image, args.tolerance)

    print(f"There are {len(indices[0])} anomalous pixels.")
    print(f"or {100 * len(indices[0]) / image.size} %")
    print(indices)


def check(image, tolerance=3):
    """
    Returns indices of the elements of *image* which exceed *tolerance* standard
    devations of the difference between *image* and a median-filtered version of it.
    """

    blurred = median(image)
    difference = image.astype(int) - blurred.astype(int)
    threshold = tolerance * np.std(difference)
    logger.info(f"threshold: {threshold}")

    anom_pixel_indices = np.nonzero(np.abs(difference) > threshold)

    return anom_pixel_indices


if __name__ == "__main__":
    sys.exit(main())
