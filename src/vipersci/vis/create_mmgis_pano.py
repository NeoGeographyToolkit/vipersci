"""Creates a panorama file and JSON stream suitable for use in MMGIS.
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
from pathlib import Path
from typing import Optional, Union

import numpy as np
import numpy.typing as npt
from skimage.exposure import equalize_adapthist, rescale_intensity
from skimage.io import imread, imsave  # maybe just imageio here?
from skimage.transform import resize
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from vipersci import util
from vipersci.pds import pid as pds
from vipersci.vis.db.pano_records import PanoRecord

logger = logging.getLogger(__name__)

ImageType = Union[npt.NDArray[np.uint16], npt.NDArray[np.uint8]]


def arg_parser():
    parser = argparse.ArgumentParser(
        description=__doc__, parents=[util.parent_parser()]
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
        "-m",
        "--mapserver",
        help="URL that will respond to requests when given an event_time and "
        "a crs_code.  Alternately, if a float is provided, this will be used as "
        "the rover yaw (zero==north) for testing.",
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
    parser.add_argument("input", help="Either VIS Pano product IDs or a JSON file.")
    return parser


def main():
    args = arg_parser().parse_args()
    util.set_logger(args.verbose)

    create_args = [args.input, args.prefix, args.output_dir, args.mapserver]

    if args.dburl is None:
        create_args.append(None)
        create(*create_args)
    else:
        engine = create_engine(args.dburl)
        with Session(engine) as session:
            create_args.append(session)
            create(*create_args)

            session.commit()

    return


def create(
    info: Union[Path, pds.PanoID, PanoRecord, str],
    prefixdir: Optional[Path] = None,
    outdir: Path = Path.cwd(),
    mapserver: Optional[str] = None,
    session: Optional[Session] = None,
    thumbsize=(None, 93),
):
    """
    Creates an MMGIS Panorama in *outdir*. Returns None.

    At this time, *input* should be a list of file paths or product IDs.

    If a path is provided to *outdir* the created files
    will be written there.

    If *session* is given, information for the PanoRecord will be
    written to the pano_records table.  If not, no database activity
    will occur.
    """

    # vid = None
    # pano = {}
    # source_path = Path()

    if isinstance(info, str):
        temp_vid = pds.PanoID(info)
        if str(temp_vid) == info:
            info = temp_vid

    if isinstance(info, pds.PanoID):
        if session is not None:
            pr = session.scalars(
                select(PanoRecord).where(PanoRecord.product_id == str(info))
            ).first()
            if pr is None:
                raise ValueError(f"{info} was not found in the database.")

            info = pr
        else:
            raise ValueError(f"Without a database session, can't lookup {info}")

    if isinstance(info, PanoRecord):
        # vid = pds.PanoID(info.product_id)
        source_path = (
            Path(info.file_path) if prefixdir is None else prefixdir / info.file_path
        )
        pano = info.asdict()
    elif isinstance(info, (Path, str)):
        # vid = pds.PanoID(info)
        with open(info) as f:
            pano = json.load(f)
        source_path = (
            Path(pano["file_path"])
            if prefixdir is None
            else prefixdir / pano["file_path"]
        )
    else:
        raise ValueError(
            f"an element in input is not the right type: {info} ({type(info)})"
        )

    if mapserver is None:
        yaw = 0.0
    else:
        try:
            yaw = float(mapserver)
        except ValueError:
            raise NotImplementedError("mapserver queries are not yet implemented.")

    # Convert to PNG
    image = equalize_adapthist(imread(str(source_path)))
    image8 = rescale_intensity(image, in_range="image", out_range="uint8").astype(
        "uint8"
    )

    outpath = outdir / Path(longname(source_path)).with_suffix(".png").name

    imsave(str(outpath), image8, check_contrast=False)

    d = mmgis_data(pano, yaw)
    # Decided not to include the URL key in the JSON this program outputs
    # as the process that takes these data and publishes them are what
    # should set that.
    # d["url"] = "not/sure/what/the/path/should/be/to/" + outpath.name

    # Make JPG thumbnail
    if thumbsize is not None:
        scale: float = 1
        if isinstance(thumbsize, int):
            max_dim = max(np.shape(image8))
            if max_dim > thumbsize:
                scale = max_dim / thumbsize
        elif len(thumbsize) == 2:
            if thumbsize[0] is not None:
                raise ValueError(
                    "Not sure how to handle a non-None first element for thumbsize."
                )
            scale = np.shape(image8)[1] / thumbsize[1]

        new_shape = tuple(int(x / scale) for x in np.shape(image8))

        image8 = rescale_intensity(
            resize(image8, new_shape), in_range="image", out_range="uint8"
        )
        outthumb = outpath.with_name(outpath.stem + "_thumb.jpeg")
        imsave(outthumb, image8, check_contrast=False)

    with open(outpath.stem + ".json", "w") as f:
        json.dump(d, f, indent=2, sort_keys=True)


def longname(path):
    """Returns a longer iso8601-esque filename."""
    # YYYY-MM-DDTHH-mm-ss.SSS-pan
    vid = pds.PanoID(path.name)
    vdt = vid.datetime()
    return (
        vdt.date().isoformat() + "T" + vdt.time().isoformat().replace(":", "-") + "-pan"
    )


def mmgis_data(pano_data: dict, yaw=0.0):
    d = {
        "azmax": yaw + pano_data["rover_pan_max"],
        "azmin": yaw + pano_data["rover_pan_min"],
        "columns": pano_data["samples"],
        "elmax": pano_data["rover_tilt_max"],
        "elmin": pano_data["rover_tilt_min"],
        "isPanoramic": True,
        "name": pano_data["product_id"],
        "rows": pano_data["lines"],
    }
    return d
