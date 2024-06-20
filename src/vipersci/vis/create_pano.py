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
from datetime import timezone
from pathlib import Path
from typing import Any, Dict, List, MutableSequence, Optional, Union

import numpy as np
import numpy.typing as npt
from skimage.exposure import rescale_intensity
from skimage.io import imread, imsave  # maybe just imageio here?
from skimage.transform import resize
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

import vipersci
from vipersci import util
from vipersci.pds import pid as pds
from vipersci.vis.create_image import tif_info, write_json
from vipersci.vis.db.image_records import ImageRecord
from vipersci.vis.db.junc_image_pano import JuncImagePano
from vipersci.vis.db.pano_records import PanoRecord

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
        "-o",
        "--output_dir",
        type=Path,
        default=Path.cwd(),
        help="Output directory for label. Defaults to current working directory.  "
        "Output file names are fixed based on product_id, and will be over-written.",
    )
    parser.add_argument(
        "--prefix",
        type=Path,
        default=Path.cwd(),
        help="A directory path that, if given, will be prepended to paths given via "
        "inputs or will be prepended to the file_path values returned from a database "
        "query.",
    )
    parser.add_argument(
        "-t",
        "--thumb",
        nargs="?",
        default=None,  # If not given.
        const=1024,  # If just -t with no arg is given.
        help="If provided, will also generate a JPEG thumbnail, whose largest dimension"
        "will be %(const)s unless a different integer is indicated.",
    )
    parser.add_argument(
        "inputs", nargs="+", help="Either VIS raw product IDs or files."
    )
    return parser


def main():
    args = arg_parser().parse_args()
    util.set_logger(args.verbose)

    if args.dburl is None:
        create(
            args.inputs,
            args.prefix,
            args.output_dir,
            None,
            args.json,
            args.bottom,
            args.thumb,
        )
    else:
        engine = create_engine(args.dburl)
        with Session(engine) as session:
            create(
                args.inputs,
                args.prefix,
                args.output_dir,
                session,
                args.json,
                args.bottom,
                args.thumb,
            )
            session.commit()


def create(
    inputs: MutableSequence[Union[Path, pds.VISID, ImageRecord, str]],
    prefixdir: Optional[Path] = None,
    outdir: Path = Path.cwd(),
    session: Optional[Session] = None,
    json: bool = True,
    bottom_row: Optional[MutableSequence[Union[Path, str]]] = None,
    thumb=None,
):
    """
    Creates a Panorama Product in *outdir*. Returns None.

    At this time, *inputs* should be a list of file paths or product IDs.

    If a path is provided to *outdir* the created files
    will be written there.

    If *session* is given, information for the PanoRecord will be
    written to the pano_records table.  If not, no database activity
    will occur.
    """

    metadata: Dict[str, Any] = dict(
        source_pids=[],
    )
    source_paths = []
    image_records = []

    for i, vid in enumerate(inputs):
        if isinstance(vid, str):
            temp_vid = pds.VISID(vid)
            if str(temp_vid) == vid:
                vid = temp_vid
            else:
                continue

        if isinstance(vid, pds.VISID):
            if session is not None:
                ir = session.scalars(
                    select(ImageRecord).where(ImageRecord.product_id == str(vid))
                ).first()
                if ir is None:
                    raise ValueError(f"{vid} was not found in the database.")

                inputs[i] = ir

    for inp in inputs:
        if isinstance(inp, ImageRecord):
            metadata["source_pids"].append(inp.product_id)
            source_paths.append(
                inp.file_path if prefixdir is None else prefixdir / inp.file_path
            )
            image_records.append(inp)
        elif isinstance(inp, (Path, str)):
            metadata["source_pids"].append([str(pds.VISID(inp))])
            source_paths.append(inp if prefixdir is None else prefixdir / inp)
        else:
            raise ValueError(
                f"an element in input is not the right type: {inp} ({type(inp)})"
            )

    # At this time, image pointing information is not available, so we assume that
    # the images provided are provided in left-to-right order and fake these values:
    half_width = (len(inputs) / 2) * 60
    metadata["rover_pan_min"] = -1 * half_width
    metadata["rover_pan_max"] = half_width
    metadata["rover_tilt_max"] = 15
    metadata["rover_tilt_min"] = -50 if bottom_row is None else -80

    image_list = []
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

        bottom_list = []
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

    pp = make_pano_record(metadata, pano_arr, outdir, thumb)

    if image_records and session is not None:
        bound_name = getattr(session.get_bind(), "name", None)
        purposes = set()
        start_times = []
        stop_times = []
        for ir in image_records:
            purposes.add(ir.verification_purpose)
            start_times.append(
                ir.start_time
                if bound_name != "sqlite"
                else ir.start_time.replace(tzinfo=timezone.utc)
            )
            stop_times.append(
                ir.stop_time
                if bound_name != "sqlite"
                else ir.stop_time.replace(tzinfo=timezone.utc)
            )

        purp = purposes.pop()
        if purp is not None:
            pp.purpose = purp

        pp.start_time = min(start_times)
        pp.stop_time = max(stop_times)

    if json:
        write_json(pp.asdict(), outdir)

    if session is not None:
        if image_records:
            to_add: List[Union[PanoRecord, JuncImagePano]] = [
                pp,
            ]
            for ir in image_records:
                a = JuncImagePano()
                a.image_record = ir
                a.pano_record = pp
                to_add.append(a)

            session.add_all(to_add)

        else:
            session.add(pp)


def make_pano_record(
    metadata: dict,
    image: Union[ImageType, Path, None] = None,
    outdir: Path = Path.cwd(),
    thumb: Union[int, None] = None,
) -> PanoRecord:
    """
    Returns a PanoProduct created from the provided meta-data, and
    if *image* is a numpy array, it will also use write_tiff() to
    create a TIFF data product in *outdir* (defaults to current
    working directory).
    """
    pp = PanoRecord(**metadata)
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

            if thumb is not None:
                # Scale down image to be no larger than thumb pixels
                max_dim = max(np.shape(image))
                if max_dim > thumb:
                    scale = max_dim / thumb
                    new_shape = tuple(int(x / scale) for x in np.shape(image))
                    image_th = rescale_intensity(
                        resize(image, new_shape), in_range="image", out_range="uint8"
                    )
                else:
                    image_th = image

                imsave(
                    outpath.stem + "_thumb.jpg",
                    image_th,
                    check_contrast=False,
                    description=desc,
                    metadata=None,
                )

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
