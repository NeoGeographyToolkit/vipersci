"""Creates Raw VIS PDS Products.

This module builds "raw" VIS data products from VIS record data.  At this time,
a Raw Product is produced from a VIS Image Record and zero to many Light Records.

A VIS Image Record consists of a TIFF file and metadata (either as a JSON file or
in a database).  That metadata is the basis for production of the PDS4 XML label file.

In order to perform the lookup of Light Records for an Image Record requires use
of the database.

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
from datetime import date
from importlib import resources
import json
import logging
from typing import Union, Optional
from pathlib import Path
from warnings import warn

from genshi.template import MarkupTemplate
import numpy as np
import numpy.typing as npt
from sqlalchemy import and_, create_engine, select
from sqlalchemy.orm import Session

import vipersci
from vipersci.vis.db.image_records import ImageRecord, ProcessingStage
from vipersci.vis.db.light_records import LightRecord, luminaire_names
from vipersci.vis.create_image import tif_info
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
        required=True,
        help="Database with a raw_products table which will be written to. "
        "If not given, no database will be written to.  Example: "
        "postgresql://postgres:NotTheDefault@localhost/visdb",
    )
    parser.add_argument(
        "-t",
        "--template",
        type=Path,
        help="Genshi XML file template.  Will default to the raw-template.xml "
        "file distributed with the module.  Only relevant when --xml is provided.",
    )
    parser.add_argument(
        "--tiff",
        type=Path,
        help="Optional pre-existing TIFF file (presumably created by create_image). "
        "This file will be inspected and its information added to the output. ",
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
        help="Product ID (or TIFF file from which a Product ID can be extracted) or a "
        "JSON file containing metadata.",
    )
    return parser


def main():
    parser = arg_parser()
    args = parser.parse_args()
    util.set_logger(args.verbose)

    engine = create_engine(args.dburl)
    with Session(engine) as session:
        try:
            pid = pds.VISID(args.input)
        except ValueError:
            pid = None

        ir = None
        if pid is None or args.input.endswith(".json"):
            if Path(args.input).exists():
                with open(args.input) as f:
                    ir = ImageRecord(json.load(f))
            else:
                parser.error(f"The file {args.input} does not exist.")
        else:
            # We got a valid pid, go look it up in the db.
            stmt = select(ImageRecord).where(ImageRecord.product_id == str(pid))
            result = session.scalars(stmt)
            rows = result.all()
            if len(rows) > 1:
                raise ValueError(f"There was more than 1 row returned from {stmt}")
            elif len(rows) == 0:
                raise ValueError(
                    f"No records were returned from the database for Product Id {pid}."
                )

            ir = rows[0]

        if ir is None:
            raise ValueError(f"Could not extract an ImageRecord from {args.input}")

        # I'm not sure where these are coming from, let's hard-code them for now:
        metadata = {
            "mission_phase": "TEST",
            "bad_pixel_table_id": 0,
            "purpose": "Engineering",
        }

        # This allows values in these dicts to override the hard-coded values above.
        metadata.update(label_dict(ir, get_lights(ir, session)))
        metadata.update(ir.asdict())
        metadata.update(
            {
                "software_name": "vipersci",
                "software_version": vipersci.__version__,
                "software_type": "Python",
                "software_program_name": __name__,
            }
        )

    if args.input.endswith(".tif"):
        args.tiff = Path(args.input)

    if args.tiff is None:
        # Make up some values:
        metadata["file_byte_offset"] = 0
        metadata["file_data_type"] = "UnsignedLSB2"
    else:
        t_info = tif_info(args.tiff)

        for k, v in t_info.items():
            if hasattr(metadata, k) and metadata[k] != v:
                raise ValueError(
                    f"The value of {k} in the metadata ({metadata[k]}) does not match "
                    f"the value ({v}) in the image ({args.tiff})"
                )
        metadata.update(t_info)

    write_xml(metadata, args.output_dir, args.template)

    return


# class Creator:
#     """
#     This object can be instantiated with an output directory, *outdir*, and optional
#     *session* and *template_path* directories, which the object maintains.
#
#     This object can simply be called which results in a raw product TIFF file and JSON
#     file being created, written to disk and possibly added to the database.
#
#     This is basically a persistent version of the create() function, so that a
#     database connection can be kept alive (during a Yamcs subscription, for example),
#     and just called with new data.
#
#     All of the arguments to initialize the object are optional:  If *outdir* is not
#     given, the current working directory will be used (beware!).  If *session* is not
#     given, no writes to a database will occur.
#     """
#
#     def __init__(
#         self,
#         outdir: Path = Path.cwd(),
#         session: Optional[Session] = None,
#     ):
#         self.outdir = outdir
#         self.session = session
#
#     def __call__(self, metadata: dict, image: Union[ImageType, Path, None] = None):
#         rp = make_raw_product(metadata, image, self.outdir)
#         logger.info(f"{rp.product_id} created.")
#
#         write_json(rp.asdict(), self.outdir)
#
#         if self.session is not None:
#             with self.session.begin() as s:
#                 s.add(rp)
#
#         return rp
#
#     def from_yamcs_parameters(self, data):
#         for parameter in data.parameters:
#             logger.info(f"{parameter.generation_time} - {parameter.name}")
#             # These are hard-coded until we figure out where they come from.
#             d = {
#                 "bad_pixel_table_id": 0,
#                 "hazlight_aft_port_on": False,
#                 "hazlight_aft_starboard_on": False,
#                 "hazlight_center_port_on": False,
#                 "hazlight_center_starboard_on": False,
#                 "hazlight_fore_port_on": False,
#                 "hazlight_fore_starboard_on": False,
#                 "navlight_left_on": False,
#                 "navlight_right_on": False,
#                 "mission_phase": "TEST",
#                 "purpose": "Navigation",
#             }
#             d.update(parameter.eng_value["imageHeader"])
#             d["yamcs_name"] = parameter.name
#             d["yamcs_generation_time"] = parameter.generation_time
#
#             with io.BytesIO(parameter.eng_value["imageData"]) as f:
#                 im = imread(f)
#
#             self.__call__(d, im)


def get_lights(ir: ImageRecord, session: Session):
    lights = {k: False for k in luminaire_names.values()}
    stmt = select(LightRecord).where(
        and_(
            LightRecord.start_time < ir.start_time,
            ir.start_time < LightRecord.last_time,
        )
    )
    result = session.scalars(stmt)
    for row in result.all():
        lights[row.name] = True

    return lights


def label_dict(ir: ImageRecord, lights: dict):
    """Returns a dictionary suitable for label generation."""
    _inst = ir.instrument_name.lower().replace(" ", "_")
    _sclid = "urn:nasa:pds:context:instrument_host:spacecraft.viper"
    onoff = {True: "On", False: "Off", None: None}
    pid = pds.VISID(ir.product_id)
    d = dict(
        lid=f"urn:nasa:pds:viper_vis:raw:{ir.product_id}",
        mission_lid="urn:nasa:pds:viper",
        sc_lid=_sclid,
        inst_lid=f"{_sclid}.{_inst}",
        gain_number=(ir.adc_gain * ir.pga_gain),
        exposure_type="Auto" if ir.auto_exposure else "Manual",
        image_filters=list(),
        led_wavelength=453,  # nm
        luminaires={},
        compression_class=pid.compression_class(),
        onboard_compression_ratio=pds.vis_compression[pid.compression],
        onboard_compression_type="ICER",
        sample_bits=12,
        sample_bit_mask="2#0000111111111111",
    )
    for k, v in lights.items():
        d["luminaires"][k] = onoff[v]

    try:
        proc_info = ProcessingStage(ir.processing_info)
    except ValueError:
        # processing_info is some bad yamcs value, for now:
        proc_info = ProcessingStage.FLATFIELD | ProcessingStage.LINEARIZATION
        if pid.compression == "s":
            proc_info |= ProcessingStage.SLOG
        warn(
            f"processing_info ({ir.processing_info}) is not one "
            f"of {list(ProcessingStage)}, so assuming a value of {proc_info}"
        )
    if ProcessingStage.FLATFIELD in proc_info:
        d["image_filters"].append(("Onboard", "Flat field normalization."))

    if ProcessingStage.LINEARIZATION in proc_info:
        d["image_filters"].append(("Onboard", "Linearization."))

    if ProcessingStage.SLOG in proc_info:
        d["image_filters"].append(
            ("Onboard", "Sign of the Laplacian of the Gaussian, SLoG")
        )
        d["sample_bits"] = 8
        d["sample_bit_mask"] = "2#11111111"

    return d


def version_info():
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


def write_xml(
    product: dict, outdir: Path = Path.cwd(), template_path: Optional[Path] = None
):
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

    d = version_info()
    d.update(product)

    logger.info(d)

    stream = tmpl.generate(**d)
    out_path = (outdir / product["product_id"]).with_suffix(".xml")
    out_path.write_text(stream.render())
    return
