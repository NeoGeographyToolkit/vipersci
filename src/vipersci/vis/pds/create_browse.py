"""Creates Browse VIS PDS Products.

This module builds "browse" VIS data products from VIS Image Products.
"""

# Copyright 2022-2024, United States Government as represented by the
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
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Union

import numpy as np
import numpy.typing as npt
from skimage.exposure import equalize_adapthist, rescale_intensity
from skimage.io import imread, imsave
from skimage.transform import resize

from vipersci import util
from vipersci.pds.datetime import isozformat
from vipersci.pds.labelmaker import get_lidvidfile
from vipersci.pds.xml import find_text, ns
from vipersci.vis.pds import write_xml

logger = logging.getLogger(__name__)

ImageType = Union[npt.NDArray[np.uint16], npt.NDArray[np.uint8]]


def arg_parser():
    parser = argparse.ArgumentParser(
        description=__doc__, parents=[util.parent_parser()]
    )
    parser.add_argument(
        "-t",
        "--template",
        default="browse-template.xml",
        help="Genshi XML file template.  Will default to the browse-template.xml "
        "file distributed with the module.",
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        type=Path,
        default=Path.cwd(),
        help="Output directory for label. Defaults to current working directory.  "
        "Output file names are fixed based on product_id, and will be over-written.",
    )
    parser.add_argument(
        "input",
        type=Path,
        help="PDS XML label file of product to create a browse product from.",
    )
    return parser


def main():
    parser = arg_parser()
    args = parser.parse_args()
    util.set_logger(args.verbose)

    metadata = get_product_info(args.input)

    if metadata["productfile"] is None:
        raise ValueError(f"Could not fine a file_name in {args.input}")

    image_path = args.input.parent / metadata["productfile"]

    try:
        image = rescale_intensity(
            equalize_adapthist(imread(image_path)), in_range="image", out_range="uint8"
        )
    except FileNotFoundError as err:
        parser.error(str(err))

    metadata["source_lidvid"] = metadata["lid"] + "::" + metadata["vid"]
    metadata["source_product_type"] = (
        f"data_to_{metadata['type'].lower()}_source_product"
    )

    # Adjust LID
    lid_tokens = metadata["lid"].split(":")
    lid_tokens[4] = "browse"
    metadata["product_id"] = lid_tokens[5] + "-browse"
    lid_tokens[5] = metadata["product_id"]
    metadata["lid"] = ":".join(lid_tokens)

    # Adjust title
    title_tokens = metadata["title"].split(" - ")
    title_words = title_tokens[0].split()
    title_words.insert(-1, "browse")
    metadata["title"] = " ".join(title_words) + f" - {metadata['product_id']}"

    # Scale down image to be no larger than 1024 pixels in the maximum direction
    max_dim = max(np.shape(image))
    if max_dim > 1024:
        scale = max_dim / 1024
        new_shape = tuple(int(x / scale) for x in np.shape(image))
        image = rescale_intensity(
            resize(image, new_shape), in_range="image", out_range="uint8"
        )

    metadata["file_path"] = metadata["product_id"] + ".png"
    out_im_path = args.output_dir / metadata["file_path"]
    imsave(out_im_path, image, check_contrast=False)

    metadata["file_creation_datetime"] = isozformat(
        datetime.fromtimestamp(out_im_path.stat().st_mtime, timezone.utc)
    )
    metadata["file_md5_checksum"] = util.md5(out_im_path)

    write_xml(metadata, args.template, args.output_dir)


def get_product_info(xml_path: Path):
    d = get_lidvidfile(xml_path)

    label = ET.fromstring(xml_path.read_text())
    d["title"] = find_text(label, "./pds:Identification_Area/pds:title")
    d["type"] = find_text(
        label, "./pds:Observation_Area/pds:Primary_Result_Summary/pds:processing_level"
    )
    d["modification_details"] = get_modification_details(label)
    return d


def get_modification_details(element_tree: ET.Element):
    mod_history = []
    for mod_detail in element_tree.findall(".//pds:Modification_Detail", ns):
        d = {}
        for key in ("modification_date", "version_id", "description"):
            d[key] = find_text(mod_detail, f"pds:{key}")
        mod_history.append(d)

    return mod_history
