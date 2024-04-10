"""Creates anaglyphs and other simple stereo-related products.
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
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from PIL import Image
from skimage.io import imread
from skimage.registration import phase_cross_correlation

from vipersci import util

logger = logging.getLogger(__name__)


def arg_parser():
    parser = argparse.ArgumentParser(
        description=__doc__, parents=[util.parent_parser()]
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-a", "--anaglyph", action="store_true", help="Creates a red/cyan anaglyph"
    )
    group.add_argument(
        "-s",
        "--side_by_side",
        action="store_true",
        help="Creates a side-by-side image.",
    )
    group.add_argument(
        "-w", "--wiggle", action="store_true", help="Creates a wiggle GIF."
    )
    parser.add_argument(
        "-r",
        "--register",
        action="store_true",
        help="Performs an automatic registration which may align the images better.",
    )
    parser.add_argument(
        "left",
        type=Path,
        help="Path to image file which will be the stereo-left image.",
    )
    parser.add_argument(
        "right",
        type=Path,
        help="Path to image file which will be the stereo-right image.",
    )
    parser.add_argument(
        "out",
        type=Path,
        help="Path to write the output image to.",
    )
    return parser


def main():
    parser = arg_parser()
    args = parser.parse_args()
    util.set_logger(args.verbose)

    left = imread(args.left)
    right = imread(args.right)

    if args.register:
        right = correlate_and_shift(left, right)

    if args.anaglyph:
        a = anaglyph(left, right)
        im = Image.fromarray(a)
        im.save(args.out)
    elif args.side_by_side:
        im = Image.fromarray(np.hstack((left, right)))
        im.save(args.out)
    elif args.wiggle:
        left_im = Image.fromarray(left)
        right_im = Image.fromarray(right)
        left_im.save(
            args.out,
            save_all=True,
            append_images=[
                right_im,
            ],
            duration=400,
            loop=0,  # forever
            dispose=0,
        )
    else:
        parser.error("Argument added but not handled by the program.")

    return


def anaglyph(left: NDArray, right: NDArray, align=False) -> NDArray:
    """Return a 3D array arranged as three 2D arrays derived from *left* and *right*
    that represent a red/cyan anaglyph.

    If *align* is true, then scikit-image's phase_cross_correlation function will
    be used to improve alignment between *left* and *right* which might result
    in a better anaglyph.
    """
    if left.shape != right.shape:
        raise ValueError(
            f"The left image shape {left.shape} does not match the right {right.shape}"
        )

    if align:
        right = correlate_and_shift(left, right)

    if len(left.shape) == 2:
        red = left
    elif len(left.shape) == 3 and left.shape[2] == 3:
        red = left[..., 0]
    else:
        raise ValueError(
            f"Don't know how to deal with {left.shape} dimensions in the left image."
        )

    if len(right.shape) == 2:
        green = right
        blue = right
    elif len(right.shape) == 3 and left.shape[2] == 3:
        green = right[..., 1]
        blue = right[..., 2]
    else:
        raise ValueError(
            f"Don't know how to deal with {right.shape} dimensions in the right image."
        )

    return np.dstack((red, green, blue))


def correlate_and_shift(left: NDArray, right: NDArray) -> NDArray:
    """
    Returns an array that is the result of aligning the *right* array to the
    *left* array.

    This is a thin wrapper for scikit-image's phase_cross_correlation()
    function with performs the correlation, and then shifts the array.
    """
    shift = tuple(
        phase_cross_correlation(left, right, normalization=None)[0].astype(int)
    )
    logger.info(f"Right image shift: {shift}")
    return np.roll(right, shift, (0, 1))


def create(left: Path, right: Path, output: Path, align=False):
    """
    This is a wrapper for the anaglyph() function which can be given
    Path objects to read from and write to.
    """
    left_arr = imread(left)
    right_arr = imread(right)
    a = anaglyph(left_arr, right_arr, align)
    im = Image.fromarray(a)
    im.save(output)
    return
