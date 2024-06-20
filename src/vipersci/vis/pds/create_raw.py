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
import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Union
from warnings import warn

import numpy as np
import numpy.typing as npt
from geoalchemy2 import load_spatialite  # type: ignore
from sqlalchemy import and_, create_engine, select
from sqlalchemy.event import listen
from sqlalchemy.orm import Session

import vipersci
from vipersci import util
from vipersci.pds import pid as pds
from vipersci.pds.datetime import isozformat
from vipersci.vis.create_image import tif_info
from vipersci.vis.db.image_records import ImageRecord, ProcessingStage
from vipersci.vis.db.light_records import (
    LightRecord,
    luminaire_names,
    luminaire_shortnames,
)
from vipersci.vis.pds import lids, write_xml

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
        default="raw-template.xml",
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
    if args.dburl.startswith("sqlite://"):
        listen(engine, "connect", load_spatialite)

    with Session(engine) as session:
        try:
            pid = pds.VISID(args.input)
        except ValueError:
            pid = None

        ir = None
        if pid is None or args.input.endswith(".json"):
            if Path(args.input).exists():
                with open(args.input) as f:
                    ir = ImageRecord(**json.load(f))
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
        }

        # This allows values in these dicts to override the hard-coded values above.
        metadata.update(label_dict(ir, get_lights(ir)))
        if args.dburl.startswith("sqlite://"):
            for c in ir.__table__.columns:
                dt = getattr(ir, c.name)
                if isinstance(dt, datetime) and dt.tzinfo is None:
                    setattr(ir, c.name, dt.replace(tzinfo=timezone.utc))

        metadata.update(ir.asdict())
        metadata.update(
            {
                "software_name": "vipersci",
                "software_version": vipersci.__version__,
                "software_type": "Python",
                "software_program_name": __name__,
            }
        )
        if metadata["verification_purpose"] is None:
            metadata["purpose"] = "Science"
        else:
            metadata["purpose"] = (
                metadata["verification_purpose"].value.replace("_", " ").title()
            )

    if args.input.endswith(".tif"):
        args.tiff = Path(args.input)

    if args.tiff is not None:
        t_info = tif_info(args.tiff)
    else:
        t_info = tif_info(Path(ir.file_path))

    for k, v in t_info.items():
        if hasattr(metadata, k):
            if metadata[k] != v:
                raise ValueError(
                    f"The value of {k} in the metadata ({metadata[k]}) does not match "
                    f"the value ({v}) in the image ({args.tiff})"
                )
        else:
            if isinstance(v, datetime):
                metadata[k] = isozformat(v)
            else:
                metadata[k] = v

    write_xml(metadata, args.template, args.output_dir)


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


def get_lights(ir: ImageRecord, session: Union[Session, None] = None):
    # If session is given, values in the ImageRecord are ignored.
    lights = {k: False for k in luminaire_names.values()}
    for short in luminaire_shortnames:
        light_name = luminaire_names[luminaire_shortnames[short]]
        light_col = getattr(ir, f"light_on_{short}")
        if session is not None:
            prev_stmt = (
                select(LightRecord)
                .where(
                    and_(
                        LightRecord.name == light_name,
                        LightRecord.datetime < ir.start_time,
                    )
                )
                .order_by(LightRecord.datetime.desc())
            )
            prev_light = session.scalars(prev_stmt).first()

            if (
                prev_light is not None
                and prev_light.on
                and ir.start_time - prev_light.datetime < timedelta(seconds=10)
            ):
                lights[light_name] = True
        elif light_col is not None:
            lights[light_name] = light_col

    return lights


def label_dict(ir: ImageRecord, lights: dict):
    """Returns a dictionary suitable for label generation."""
    # _inst = ir.instrument_name.lower().replace(" ", "_")
    onoff = {True: "On", False: "Off", None: None}
    pid = pds.VISID(ir.product_id)
    d = dict(
        data_quality="",
        lid=f"{lids['bundle']}:data_raw:{ir.product_id}",
        mission_lid=lids["mission"],
        sc_lid=lids["spacecraft"],
        inst_lid=f"{lids['instrument']}",
        gain_number=(ir.adc_gain * ir.pga_gain),
        exposure_type="Auto" if ir.auto_exposure else "Manual",
        image_filters="",
        led_wavelength=453,  # nm
        luminaires={},
        compression_class=pid.compression_class(),
        observational_intent={},
        onboard_compression_ratio=ir.icer_byte_quota / (2048 * 2048 * 2),
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

    im_filt = []
    if ProcessingStage.FLATFIELD in proc_info:
        im_filt.append("Flat field normalization.")

    if ProcessingStage.LINEARIZATION in proc_info:
        im_filt.append("Linearization.")

    if ProcessingStage.SLOG in proc_info:
        im_filt.append("Sign of the Laplacian of the Gaussian, SLoG.")
        d["sample_bits"] = 8
        d["sample_bit_mask"] = "2#11111111"

    if len(im_filt) > 0:
        d["image_filters"] = " ".join(im_filt)

    if ir.image_request is not None:
        d["observational_intent"]["goal"] = ir.image_request.justification
        d["observational_intent"]["task"] = ir.image_request.title
        d["observational_intent"][
            "activity_id"
        ] = f"Image Request {ir.image_request.id}"
        d["observational_intent"]["target_id"] = ir.image_request.target_location

    if ir.verified is not None:
        if ir.verified:
            d["data_quality"] += "Image manually verified."
        else:
            d["data_quality"] += "Image determined to have errors."

        if ir.verification_notes is not None:
            d["data_quality"] += " " + ir.verification_notes

    return d
