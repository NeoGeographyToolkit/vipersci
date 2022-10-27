"""Creates Raw VIS PDS Products.

For now, this program has a variety of pre-set data,
that will eventually be extracted from telemetry.
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
from datetime import datetime, date, timezone
import hashlib
from importlib import resources
import io
import json
import logging
import sys
from typing import Union
from pathlib import Path
from warnings import warn

from genshi.template import MarkupTemplate
import numpy as np
import numpy.typing as npt
from skimage.io import imread, imsave  # maybe just imageio here?
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from tifftools import read_tiff

import vipersci
from vipersci.vis.db.raw_products import RawProduct
from vipersci.pds import pid as pds
from vipersci import util

logger = logging.getLogger(__name__)


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
        "--json",
        type=Path,
        required=True,
        help="JSON file, with raw product meta-data.",
    )
    parser.add_argument(
        "-t",
        "--template",
        type=Path,
        help="Genshi XML file template.  Will default to the raw-template.xml "
        "file distributed with the module.",
    )
    parser.add_argument(
        "--image",
        type=Path,
        help="Optional path to source image file which will be read and "
        "converted into a TIFF product.  If no path is given, then "
        "Only a .xml label will be written and no image.",
    )
    parser.add_argument(
        "--tiff",
        type=Path,
        help="Optional pre-existing TIFF file.  This file will be inspected "
        "and an .xml label will be written.  If --image is given, this will "
        "be ignored.",
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        type=Path,
        default=Path.cwd(),
        help="Output directory for label. Defaults to current working directory.",
    )
    return parser


def main():
    args = arg_parser().parse_args()
    util.set_logger(args.verbose)

    with open(args.json) as f:
        jsondata = json.load(f)

    # I'm not sure where these are coming from, let's hard-code them for now:
    metadata = {
        "mission_phase": "TEST",
        "purpose": "Navigation",
        "onboard_compression_ratio": 64,
    }

    # This allows values in jsondata to override the hard-coded values above.
    metadata.update(jsondata)

    if args.image is not None:
        image = imread(str(args.image))
    elif args.tiff is not None:
        image = args.tiff
    else:
        image = None

    if args.dburl is None:
        create(metadata, image, args.output_dir, None, args.template)
    else:
        engine = create_engine(args.dburl)
        session_maker = sessionmaker(engine, future=True)
        create(metadata, image, args.output_dir, session_maker, args.template)

    return


class Creator:
    """
    This object can be instantiated with an output directory, *outdir*, and optional
    *session* and *template_path* directories, which the object maintains.

    This object can simply be called which results in a raw product being created,
    written to disk and possibly added to the database.

    This is basically a persistent version of the create() function, so that a
    database connection can be kept alive (during a Yamcs subscription, for example),
    and just called with new data.

    All of the arguments to initialize the object are optional:  If *outdir* is not
    given, the current working directory will be used (beware!).  If *session* is not
    given, no writes to a database will occur.  If *template_path* is not given, a
    default from this library will be used.
    """

    def __init__(
        self,
        outdir: Path = Path.cwd(),
        session: Session = None,
        template_path: Path = None,
    ):
        self.outdir = outdir
        self.session = session
        self.tmpl_path = template_path

    def __call__(self, metadata: dict, image: npt.NDArray[np.uint16] = None):
        rp = make_raw_product(metadata, image, self.outdir)
        logger.info(f"{rp.product_id} created.")

        write_xml(rp.label_dict(), self.outdir, self.tmpl_path)

        if self.session is not None:
            with self.session.begin() as s:
                s.add(rp)

        return

    def from_yamcs_parameters(self, data):
        for parameter in data.parameters:
            logger.info(f"{parameter.generation_time} - {parameter.name}")
            # These are hard-coded until I figure out where they come from.
            d = {
                "bad_pixel_table_id": 0,
                "hazlight_aft_port_on": False,
                "hazlight_aft_starboard_on": False,
                "hazlight_center_port_on": False,
                "hazlight_center_starboard_on": False,
                "hazlight_fore_port_on": False,
                "hazlight_fore_starboard_on": False,
                "navlight_left_on": False,
                "navlight_right_on": False,
                "mission_phase": "TEST",
                "purpose": "Navigation",
                "onboard_compression_ratio": 64,
                "onboard_compression_type": parameter.name[-4:].upper(),
            }
            d.update(parameter.eng_value["imageHeader"])
            d["yamcs_name"] = parameter.name
            d["yamcs_generation_time"] = parameter.generation_time

            with io.BytesIO(parameter.eng_value["imageData"]) as f:
                im = imread(f)

            self.__call__(d, im)


def create(
    metadata: dict,
    image: Union[npt.NDArray[np.uint16], Path] = None,
    outdir: Path = Path.cwd(),
    session: Session = None,
    template_path: Path = None,
):
    """
    Creates a PDS4 XML label file in *outdir* based on the provided
    meta-data.  Returns None.

    If *image* is a numpy array, that array will be considered the
    Array_2D_Image and will be written to a TIFF file with the same
    naming scheme as the XML file in *outdir*.  If *image* is a
    file path to a TIFF file, the TIFF file at that path will be
    evaluated and its meta-dataadded to the XML label, as if that
    file was the File_Area_Observational for the XML label.  If
    *image* is None (the default), no TIFF file will be written,
    and certain elements of the XML label (pertaining to the
    File_Area_Observational) will be empty.

    If a path is provided to *outdir* the XML and optional TIFF
    file will be written there. Defaults to the current working
    directory.

    If *session* is given, information for the raw product will be
    written to the raw_products table.  If not, no database activity
    will occur.

    The *template_path* argument is passed to the write_xml() function, please see
    its documentation for details.
    """
    rp = make_raw_product(metadata, image, outdir)

    write_xml(rp.label_dict(), outdir, template_path)

    if session is not None:
        with session.begin() as s:
            s.add(rp)

    return


def make_raw_product(
    metadata: dict,
    image: Union[npt.NDArray[np.uint16], Path] = None,
    outdir: Path = Path.cwd(),
) -> RawProduct:
    """
    Returns a Raw_Product created from the provided meta-data, and
    if *image* is a numpy array, it will also use write_tiff() to
    create a TIFF data product in *outdir* (defaults to current
    working directory).
    """
    rp = RawProduct(**metadata)

    if image is not None:
        if isinstance(image, Path):
            tif_d = tif_info(image)
        else:
            tif_d = tif_info(write_tiff(pds.VISID(rp.product_id), image, outdir))

        for k in ("lines", "samples"):
            if getattr(rp, k) != tif_d[k]:
                raise ValueError(
                    f"The value of {k} from the TIFF ({tif_d[k]}) does not "
                    f"match the value from the metadata ({getattr(rp, k)})"
                )

        rp.update(tif_d)
    else:
        rp.update({"byte_offset": None, "data_type": None})
    rp.update(version_info(rp.product_id))

    rp.update(
        {
            "software_name": "vipersci",
            "software_version": vipersci.__version__,
            "software_type": "Python",
            "software_program_name": __name__,
        }
    )

    return rp


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

    if info["bigEndian"]:
        end = "MSB"
    else:
        end = "LSB"

    if tags[258]["data"][0] != 16:
        raise ValueError(
            f"TIFF file has {tags[258]['data'][0]} BitsPerSample " f"expecting 16."
        )
    else:
        dtype = f"Unsigned{end}2"

    d = {
        "file_path": p.name,
        "file_creation_datetime": dt,
        "md5_checksum": md5.hexdigest(),
        "byte_offset": tags[273]["data"][0],  # Tag 273 is StripOffsets
        "lines": tags[257]["data"][0],  # Tag 257 is ImageWidth,
        "samples": tags[256]["data"][0],  # Tag 256 is ImageWidth,
        "data_type": dtype,
    }
    return d


def version_info(pid: pds.VISID):
    # This should reach into a database and do something smart to figure
    # out how to populate this, but for now, hardcoding:
    d = {
        "modification_details": [
            {
                "version": 0.1,
                "date": date.today().isoformat(),
                "description": "Illegal version number for testing",
            }
        ],
        "vid": 0.1,
    }
    return d


def write_tiff(
    pid: pds.VISID, image: npt.NDArray[np.uint16], outdir: Path = Path.cwd()
) -> Path:
    """
    Returns the path where a TIFF with a name based on *pid* and the array
    *image* was written in *outdir* (defaults to current working directory).
    """
    if image.dtype != np.uint16:
        # raise ValueError(
        warn(f"The input image is not a uint16, it is {image.dtype}")

    desc = f"VIPER {pds.vis_instruments[pid.instrument]} {pid}"

    logger.info(desc)
    outpath = (outdir / str(pid)).with_suffix(".tif")

    imsave(str(outpath), image, check_contrast=False, description=desc, metadata=None)
    return outpath


def write_xml(product: dict, outdir: Path = Path.cwd(), template_path: Path = None):
    """
    Writes a PDS4 XML label in *outdir* based on the contents of
    the *product* object, which must be of type Raw_Product.

    The *template_path* can be a path to an appropriate template
    XML file, but defaults to the raw-template.xml file provided
    with this library.
    """
    if template_path is None:
        tmpl = MarkupTemplate(
            resources.read_text("vipersci.vis.pds.data", "raw-template.xml")
        )
    else:
        tmpl = MarkupTemplate(template_path.read_text())

    stream = tmpl.generate(**product)
    out_path = (outdir / product["product_id"]).with_suffix(".xml")
    out_path.write_text(stream.render())
    return


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
