"""Creates VIS Panorama Products.

This module is meant to kick off the process to take a series of
VIS images and create a Panorama Product from them.

At this time, this module is currently just a stub, and only dumbly
mosaics the provided images together, it does not yet return a proper
Panorama Product, only a mock-up of one.

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
from typing import Any, Dict, Iterable, Union, Optional, MutableSequence
from pathlib import Path

import numpy as np
import numpy.typing as npt
from skimage.io import imread, imsave  # maybe just imageio here?
from skimage.transform import resize
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import vipersci
from vipersci.vis.db.raw_products import RawProduct
from vipersci.vis.db.pano_products import PanoProduct
from vipersci.pds import pid as pds
from vipersci.vis.pds.create_raw import tif_info, write_json, write_xml
from vipersci import util

logger = logging.getLogger(__name__)

ImageType = Union[npt.NDArray[np.uint16], npt.NDArray[np.uint8]]


def arg_parser():
    parser = argparse.ArgumentParser(
        description=__doc__, parents=[util.parent_parser()]
    )
    parser.add_argument(
        "-b",
        "--bottom",
        nargs="*",
        help="Any AftCam and front-down NavCam images that should go on the 'bottom "
        "row.'  Literal '-' can be provided to indicate blank positions on the bottom "
        "row.  This is an emphemeral option that is expected to go away when we can "
        "get our hands on better pointing information.",
    )
    parser.add_argument(
        "-d",
        "--dburl",
        help="Database with a raw_products table and a panorama_products table which "
        "will be read from and written to. If not given, no database will be "
        "written to. "
        "Example: postgresql://postgres:NotTheDefault@localhost/visdb",
    )
    parser.add_argument(
        "--nojson",
        action="store_false",
        dest="json",
        help="Disables creation of .json output.",
    )
    parser.add_argument(
        "-t",
        "--template",
        type=Path,
        help="Genshi XML file template.  Will default to the pano-template.xml "
        "file distributed with the module.  Only relevant when --xml is provided.",
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
        "-x", "--xml", action="store_true", help="Create a PDS4 .XML label file."
    )
    parser.add_argument(
        "inputs", nargs="*", help="Either VIS raw product IDs or files."
    )
    return parser


def main():
    args = arg_parser().parse_args()
    util.set_logger(args.verbose)

    if args.dburl is None:
        create(
            args.inputs,
            args.output_dir,
            None,
            args.json,
            args.xml,
            args.template,
            args.bottom,
        )
    else:
        engine = create_engine(args.dburl)
        session = sessionmaker(engine, future=True)
        create(
            args.inputs,
            args.output_dir,
            session,
            args.json,
            args.xml,
            args.template,
            args.bottom,
        )

    return


def create(
    inputs: Iterable[Union[Path, pds.VISID, RawProduct, str]],
    outdir: Path = Path.cwd(),
    session: Optional[Session] = None,
    json: bool = True,
    xml: bool = False,
    template_path: Optional[Path] = None,
    bottom_row: Optional[MutableSequence[Union[Path, str]]] = None,
):
    """
    Creates a Panorama Product in *outdir*. Returns None.

    At this time, session, xml, and template_path are ignored.

    At this time, *inputs* should be a list of file paths.  In the
    future, it could be a list of product IDs.

    If a path is provided to *outdir* the created files
    will be written there. Defaults to the current working
    directory.

    If *session* is given, information for the raw product will be
    written to the raw_products table.  If not, no database activity
    will occur.

    The *template_path* argument is passed to the write_xml() function, please see
    its documentation for details.
    """
    metadata: Dict[str, Any] = dict(
        source_products=[],
    )
    source_paths = []

    for i in inputs:
        if isinstance(i, RawProduct):
            metadata["source_products"].append(i.product_id)
            source_paths.append(i.file_path)
        elif isinstance(i, pds.VISID):
            raise NotImplementedError(
                "One day, this will fire up a db connection and get the info needed."
            )
        elif isinstance(i, (Path, str)):
            metadata["source_products"].append([str(pds.VISID(i))])
            source_paths.append(i)
        else:
            raise ValueError(
                f"an element in input is not the right type: {i} ({type(i)})"
            )

    # At this time, image pointing information is not available, so we assume that
    # the images provided are provided in left-to-right order.

    image_list = list()
    for path in source_paths:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"{p} does not exist.")
            # in future, maybe do a db lookup on the VISID.

        image_list.append(imread(str(p)))

    pano_arr = np.hstack(image_list)

    if bottom_row is not None:
        if len(bottom_row) < len(source_paths):
            bottom_row += [
                "-",
            ] * (len(source_paths) - len(bottom_row))

        bottom_list = list()
        for b in bottom_row:
            if b == "-":
                bottom_list.append(np.zeros_like(image_list[0]))
            else:
                p = Path(b)
                if not p.exists():
                    raise FileNotFoundError(f"{p} does not exist.")
                metadata["source_products"].append([str(pds.VISID(p))])
                im = imread(str(p))
                if im.shape != image_list[0].shape:
                    im = resize(im, image_list[0].shape)
                bottom_list.append(im)
        bot_arr = np.hstack(bottom_list)
        pano_arr = np.vstack((pano_arr, bot_arr))

    pp = make_pano_product(metadata, pano_arr, outdir)

    if json:
        write_json(pp.asdict(), outdir)

    if xml:
        write_xml(pp.label_dict(), outdir, template_path)

    if session is not None:
        with session.begin() as s:
            s.add(pp)

    return


def make_pano_product(
    metadata: dict,
    image: Union[ImageType, Path, None] = None,
    outdir: Path = Path.cwd(),
) -> PanoProduct:
    """
    Returns a PanoProduct created from the provided meta-data, and
    if *image* is a numpy array, it will also use write_tiff() to
    create a TIFF data product in *outdir* (defaults to current
    working directory).
    """
    pp = PanoProduct(**metadata)
    pid = pds.PanoID(pp.product_id)

    if image is not None:
        if isinstance(image, Path):
            tif_d = tif_info(image)
        else:
            desc = f"VIPER Panorama {pid}"

            logger.debug(desc)
            outpath = (outdir / str(pid)).with_suffix(".tif")

            imsave(
                str(outpath),
                image,
                check_contrast=False,
                description=desc,
                metadata=None,
            )
            tif_d = tif_info(outpath)

        pp.update(tif_d)
    else:
        pp.update({"file_byte_offset": None, "file_data_type": None})

    pp.update(
        {
            "software_name": "vipersci",
            "software_version": vipersci.__version__,
            "software_type": "Python",
            "software_program_name": __name__,
        }
    )

    return pp
