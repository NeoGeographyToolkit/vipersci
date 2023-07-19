"""Inspects VIS and other images.
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
import json
import logging
from typing import Union
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt
from scipy import stats
from skimage.exposure import equalize_adapthist
from skimage.io import imread

from vipersci import util

logger = logging.getLogger(__name__)

ImageType = Union[npt.NDArray[np.uint16], npt.NDArray[np.uint8]]


def arg_parser():
    parser = argparse.ArgumentParser(
        description=__doc__, parents=[util.parent_parser()]
    )
    parser.add_argument(
        "--clahe",
        action="store_true",
        help="Apply Contrast Limited Adaptive Histogram Equalization (CLAHE) to the "
        "input image.",
    )
    parser.add_argument(
        "-g",
        "--grid",
        action="store_true",
        help="If given will display the OpenMCT 'grid' on the image.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path.cwd(),
        help="If given, will write output image to this file.",
    )
    parser.add_argument("--vmin", type=float, help="Minimum DN value to display.")
    parser.add_argument("--vmax", type=float, help="Maximum DN value to display.")
    parser.add_argument("input", type=Path, help="File containing image or JSON label.")
    return parser


def main():
    args = arg_parser().parse_args()
    util.set_logger(args.verbose)

    if ".json" == args.input.suffix.lower():
        with open(args.input, "r") as f:
            info = json.load(f)

            p = Path(info["file_path"])
            if not p.is_absolute():
                p = args.input.parent / p

        logger.info(f"Reading {p}")
        image = imread(p)
        imtitle = info["product_id"]
    else:
        image = imread(args.input)
        imtitle = args.input.name

    logger.info(describe(image, "image as loaded:"))

    if args.clahe:
        image = equalize_adapthist(image)
        logger.info(describe(image, "image after CLAHE:"))

    plot_img_and_hist(
        image, title=imtitle, vmin=args.vmin, vmax=args.vmax, grid=args.grid, save=False
    )

    return


def describe(image: ImageType, message: str):
    lines = list()
    d = stats.describe(image.ravel())
    lines.append(message)
    lines.append(f"  shape: {image.shape}  dtype: {image.dtype}")
    lines.append(f"  minmax: {d.minmax}  mean: {d.mean}  variance: {d.variance}")
    # lines.append("  " + pprint.pformat(
    #     stats.describe(image.ravel()), indent=2
    # ))
    return "\n".join(lines)


def plot_img_and_hist(
    image, images=None, title="Image", vmin=None, vmax=None, grid=False, save=False
):
    """Plot an image along with its histogram"""
    if images is None:
        images = [
            image,
        ]
    else:
        images.insert(0, image)

    fig, axes = plt.subplots(1, len(images) + 1)

    ax_images = axes[:-1]
    ax_hist = axes[-1]

    fig.suptitle(title)

    # Display image
    for ax, im in zip(ax_images, images):
        ax.imshow(
            im,
            cmap=plt.cm.gray,
            vmin=vmin if vmin is not None else np.amin(im),
            vmax=vmax if vmax is not None else np.amax(im),
        )
        if grid:
            ax.axhline(im.shape[0] / 4, color="blue")
            ax.axhline(im.shape[0] / 2, color="blue")
            ax.axhline(im.shape[0] * 3 / 4, color="blue")
            ax.axvline(im.shape[1] / 4, color="blue")
            ax.axvline(im.shape[1] / 2, color="blue")
            ax.axvline(im.shape[1] * 3 / 4, color="blue")
        # ax.set_axis_off()

    # Display histogram
    # ax_hist.hist(image.ravel(), bins=bins, histtype="bar", log=True)
    hist_dn, hist_counts = np.unique(image, return_counts=True)
    ax_hist.fill_between(hist_dn, hist_counts, alpha=0.2, color="C0")
    ax_hist.scatter(hist_dn, hist_counts, marker=".")
    ax_hist.set_yscale("log")
    ax_hist.set_xlabel("DN")
    ax_hist.set_ylabel("Pixel Count")
    if vmin is not None:
        ax_hist.axvline(vmin, color="gray")
    if vmax is not None:
        ax_hist.axvline(vmax, color="gray")

    fig.tight_layout()
    # fig.set_dpi(300)
    # fig.set_size_inches(w=6.4, h=4.8)
    plt.show()

    if save:
        fname = input("Filename (blank to not save):")
        if len(fname) > 0:
            fig.savefig(fname, dpi=300)
