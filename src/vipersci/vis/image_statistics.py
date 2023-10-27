"""Produces various statistics from images.
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
from textwrap import dedent
from typing import Union
from pathlib import Path

import numpy as np
import numpy.typing as npt
from skimage.io import imread
from skimage import measure

from vipersci import util

logger = logging.getLogger(__name__)

ImageType = Union[npt.NDArray[np.uint16], npt.NDArray[np.uint8]]

UNDEREXPOSED_THRESHOLD = 4095 * 0.2
OVEREXPOSED_THRESHOLD = 4095 * 0.8


def arg_parser():
    parser = argparse.ArgumentParser(
        description=__doc__, parents=[util.parent_parser()]
    )
    parser.add_argument(
        "image",
        type=Path,
        help="Path to image file which will be read and statistics computed.",
    )
    return parser


def main():
    args = arg_parser().parse_args()
    util.set_logger(args.verbose)

    image = imread(str(args.image))

    print(pprint(image))

    return


def compute(
        image: ImageType,
        overexposed_thresh=OVEREXPOSED_THRESHOLD,
        underexposed_thresh=UNDEREXPOSED_THRESHOLD
) -> dict:
    d = {
        "blur": measure.blur_effect(image),
        "mean": np.mean(image),
        "std": np.std(image),
        "over_exposed": (image > overexposed_thresh).sum(),
        "under_exposed": (image < underexposed_thresh).sum(),
        # "aggregate_noise":
        # number of dead pixels
    }

    return d


def pprint(
        image: ImageType,
        overexposed_thresh=OVEREXPOSED_THRESHOLD,
        underexposed_thresh=UNDEREXPOSED_THRESHOLD,
) -> str:
    d = compute(image, overexposed_thresh, underexposed_thresh)

    s = dedent(
        f"""\
        blur: {d['blur']} (0 for no blur, 1 for maximal blur)
        mean: {d['mean']}
        std: {d['std']} 
        over-exposed: {d['over_exposed']} pixels, {100 * d['over_exposed'] / image.size} %
        under-exposed: {d['under_exposed']} pixels, {100 * d['under_exposed'] / image.size} %\
        """
    )
    return s
