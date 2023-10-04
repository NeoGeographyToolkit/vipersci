"""Creates VIS Image Records.

This module builds VIS Image Records from input data.  A VIS Image Record
consists of a TIFF file and a JSON file containing meta-data.
The meta data can optionally be inserted into a database

For now, this program still has a variety of hard-coded elements,
that will eventually be extracted from telemetry.

The command-line version is primarily to aide testing.
"""

# Copyright 2022-2023, United States Government as represented by the
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
from datetime import datetime, timezone
import hashlib
import json
import logging
from typing import Union, Optional
from pathlib import Path

import numpy as np
import numpy.typing as npt
from skimage.io import imread, imsave  # maybe just imageio here?
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from tifftools import read_tiff

import vipersci
from vipersci.vis.db.image_records import ImageRecord
from vipersci.vis.db.image_requests import ImageRequest  # noqa
from vipersci.vis.db.junc_image_record_tags import JuncImageRecordTag  # noqa
from vipersci.vis.db.junc_image_req_ldst import JuncImageRequestLDST  # noqa
from vipersci.pds import pid as pds
from vipersci import util

logger = logging.getLogger(__name__)

ImageType = Union[npt.NDArray[np.uint16], npt.NDArray[np.uint8]]


def arg_parser():
    parser = argparse.ArgumentParser(
        description=__doc__, parents=[util.parent_parser()]
    )
    parser.add_argument(
        "-d",
        "--dburl",
        help="Database with a raw_products table which will be written to. "
        "If not given, no database will be written to.  Example: "
        "postgresql://postgres:NotTheDefault@localhost/visdb",
    )
    parser.add_argument(
        "--nojson",
        action="store_false",
        dest="json",
        help="Disables creation of .json output, which is the default.",
    )
    parser.add_argument(
        "--image",
        type=Path,
        help="Optional path to source image file which will be read and "
        "converted into a TIFF product.  If no path is given, then "
        "Only a .json file will be written and no image.",
    )
    parser.add_argument(
        "--tiff",
        type=Path,
        help="Optional pre-existing TIFF file (presumably created by this program). "
        "This file will be inspected and its information added to the output. "
        "If --image is given, this option will be ignored.",
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        type=Path,
        default=Path.cwd(),
        help="Output directory for label. Defaults to current working directory.  "
        "Output file names are fixed based on product_id, and will be over-written.",
    )
    parser.add_argument("input", type=Path, help="JSON file containing metadata.")
    return parser


def main():
    args = arg_parser().parse_args()
    util.set_logger(args.verbose)

    with open(args.input) as f:
        jsondata = json.load(f)

    if args.image is not None:
        image = imread(str(args.image))
    elif args.tiff is not None:
        image = args.tiff
    else:
        image = None

    if args.dburl is None:
        create(jsondata, image, args.output_dir, None, args.json)
    else:
        engine = create_engine(args.dburl)
        with Session(engine) as session:
            create(
                jsondata,
                image,
                args.output_dir,
                session,
                args.json,
            )

    return


def create(
    metadata: dict,
    image: Union[ImageType, Path, None] = None,
    outdir: Path = Path.cwd(),
    session: Optional[Session] = None,
    json: bool = True,
):
    """
    Creates a TIFF file / JSON file pair in *outdir* based on the provided
    meta-data.  Returns an ImageRecord.

    If *image* is a numpy array, that array will be considered the
    Array_2D_Image and will be written to a TIFF file with the same
    naming scheme as the JSON file in *outdir*.  If *image* is a
    file path to a TIFF file, the TIFF file at that path will be
    evaluated and its meta-data added to the JSON info, as if that
    file is the file that would have been written by this function.  If
    *image* is None (the default), no TIFF file will be written,
    and certain elements of the JSON info (pertaining to the
    file) will be empty.

    If a path is provided to *outdir* the JSON and optional TIFF
    file will be written there. Defaults to the current working
    directory.

    If *session* is given, information for the image record will be
    written to the image_records table.  If not, no database activity
    will occur.
    """
    # This arrangement of creating the output files first, ensures a clean
    # db insert (otherwise the outfile-writing would need to happen in the
    # context of the session).  However, if the db insert fails, the files
    # already exist on disk.  Is that a problem?  Maybe that's fine?
    rp = make_image_record(metadata, image, outdir)

    if json:
        write_json(rp.asdict(), outdir)

    if session is not None:
        session.add(rp)

    return rp


def check_bit_depth(pid: pds.VISID, bit_depth: Union[int, str, np.dtype]):
    """If the provided *bit_depth* is incompatible with *pid* a ValueError will be
    raised.

    The *bit_depth* will attempt to be converted to a valid integer value the bit
    depth of the PDS TIFF file.  The *bit_depth* argument can be an integer, a
    numpy dtype, and even a string compatible with the PDS4
    Array_2D_Image/Element_Array/data_type attribute.
    """

    bd = None
    if isinstance(bit_depth, int):
        bd = bit_depth
    elif isinstance(bit_depth, str):
        bd = int(bit_depth[-1]) * 8
    elif isinstance(bit_depth, np.dtype):
        if bit_depth == np.uint16:
            bd = 16
        elif bit_depth == np.uint8:
            bd = 8

    if bd is None:
        raise ValueError(f"Cannot determine a bit-depth from {bit_depth}")

    if pid.compression == "s":
        if bd != 8:
            raise ValueError(
                f"This is a SLoG product ({pid}), but this image is not 8-bit, "
                f"it is {bit_depth}"
            )
    else:
        if bd != 16:
            raise ValueError(
                f"This product ({pid}) should be 16-bit, but it is {bit_depth}"
            )
    return


def make_image_record(
    metadata: dict,
    image: Union[ImageType, Path, None] = None,
    outdir: Path = Path.cwd(),
) -> ImageRecord:
    """
    Returns an ImageRecord created from the provided meta-data, and
    if *image* is a numpy array, it will also use write_tiff() to
    create a TIFF file in *outdir* (defaults to current
    working directory).
    """
    ir = ImageRecord(**metadata)
    pid = pds.VISID(ir.product_id)

    if image is not None:
        if isinstance(image, Path):
            tif_d = tif_info(image)
        else:
            tif_d = tif_info(write_tiff(pid, image, outdir))

        for k in ("lines", "samples"):
            if getattr(ir, k) != tif_d[k]:
                raise ValueError(
                    f"The value of {k} from the TIFF ({tif_d[k]}) does not "
                    f"match the value from the metadata ({getattr(ir, k)})"
                )

        check_bit_depth(pid, tif_d["file_data_type"])

        ir.update(tif_d)
    else:
        ir.update(
            {
                "file_byte_offset": None,
                # "file_creation_datetime": None,
                "file_data_type": None,
                "file_md5_checksum": None,
                "file_path": None,
            }
        )

    ir.update(
        {
            "software_name": "vipersci",
            "software_version": vipersci.__version__,
            "software_program_name": __name__,
        }
    )

    return ir


def tif_info(p: Path) -> dict:
    """
    Returns a dict containing meta-data from the TIFF file at the
    provided path, *p*.
    """
    dt = datetime.fromtimestamp(p.stat().st_mtime, timezone.utc)

    md5 = hashlib.md5()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5.update(chunk)

    info = read_tiff(str(p))
    tags = info["ifds"][0]["tags"]

    end = "MSB" if info["bigEndian"] else "LSB"

    d = {
        "file_byte_offset": tags[273]["data"][0],  # Tag 273 is StripOffsets
        "file_creation_datetime": dt,
        # Tag 258 is bits per pixel:
        "file_data_type": f"Unsigned{end}{int(tags[258]['data'][0] / 8)}",
        "file_md5_checksum": md5.hexdigest(),
        "file_path": p.name,
        "lines": tags[257]["data"][0],  # Tag 257 is ImageWidth,
        "samples": tags[256]["data"][0],  # Tag 256 is ImageWidth,
    }
    return d


def write_json(product: dict, outdir: Path = Path.cwd()):
    """
    Convenience function to write *product* as a JSON file in
    *outdir*.
    """
    out_path = (outdir / product["product_id"]).with_suffix(".json")
    with out_path.open("w") as f:
        json.dump(product, f, indent=2, sort_keys=True)


def write_tiff(pid: pds.VISID, image: ImageType, outdir: Path = Path.cwd()) -> Path:
    """
    Returns the path where a TIFF with a name based on *pid* and the array
    *image* was written in *outdir* (defaults to current working directory).
    """

    check_bit_depth(pid, image.dtype)

    desc = f"VIPER {pds.vis_instruments[pid.instrument]} {pid}"

    logger.debug(desc)
    outpath = (outdir / str(pid)).with_suffix(".tif")

    imsave(str(outpath), image, check_contrast=False, description=desc, metadata=None)
    return outpath
