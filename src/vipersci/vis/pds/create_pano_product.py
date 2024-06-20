"""Creates PDS VIS Pano Products.

This module builds a VIS panorama data products from VIS pano record data.  At this
time, a Pano Product is produced from VIS Image Records. That metadata is the basis for
production of the PDS4 XML label file.

In order to perform the lookup of Image Records and Pano Records requires use
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
from datetime import timezone
from pathlib import Path
from typing import Union

import numpy as np
import numpy.typing as npt
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

import vipersci
from vipersci import util
from vipersci.pds import pid as pds
from vipersci.vis.create_image import tif_info
from vipersci.vis.db.pano_records import PanoRecord
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
        help="Database with a pano_products table which will be written to. "
        "If not given, no database will be written to.  Example: "
        "postgresql://postgres:NotTheDefault@localhost/visdb",
    )
    parser.add_argument(
        "-t",
        "--template",
        default="pano-template.xml",
        help="Genshi XML file template.  Will default to the pano-template.xml "
        "file distributed with the module.",
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
            pid = pds.PanoID(args.input)
        except ValueError:
            pid = None

        pr = None
        if pid is None or args.input.endswith(".json"):
            if Path(args.input).exists():
                with open(args.input) as f:
                    pr = PanoRecord(**json.load(f))
            else:
                parser.error(f"The file {args.input} does not exist.")
        else:
            # We got a valid pid, go look it up in the db.
            stmt = select(PanoRecord).where(PanoRecord.product_id == str(pid))
            result = session.scalars(stmt)
            rows = result.all()
            if len(rows) > 1:
                raise ValueError(f"There was more than 1 row returned from {stmt}")
            elif len(rows) == 0:
                raise ValueError(
                    f"No records were returned from the database for Product Id {pid}."
                )

            pr = rows[0]

        if pr is None:
            raise ValueError(f"Could not extract a PanoRecord from {args.input}")

        # If testing via sqlite, ensure datetimes are UTC aware:
        if session.get_bind().name == "sqlite":
            pr.file_creation_datetime = pr.file_creation_datetime.replace(
                tzinfo=timezone.utc
            )
            pr.start_time = pr.start_time.replace(tzinfo=timezone.utc)
            pr.stop_time = pr.stop_time.replace(tzinfo=timezone.utc)

        # I'm not sure where these are coming from, let's hard-code them for now:
        metadata = {
            "mission_phase": "TEST",
        }

        # This allows values in these dicts to override the hard-coded values above.
        metadata.update(label_dict(pr))
        metadata.update(pr.asdict())
        metadata.update(
            {
                "software_name": "vipersci",
                "software_version": vipersci.__version__,
                "software_type": "Python",
                "software_program_name": __name__,
            }
        )
        if metadata["purpose"] is None:
            metadata["purpose"] = "Science"
        else:
            metadata["purpose"] = metadata["purpose"].value.replace("_", " ").title()

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

    write_xml(metadata, args.template, args.output_dir)


def label_dict(pr: PanoRecord):
    """Returns a dictionary suitable for label generation."""
    d = dict(
        lid=f"{lids['bundle']}:data_derived:{pr.product_id}",
        mission_lid=lids["mission"],
        sc_lid=lids["spacecraft"],
        instruments=[],
        source_product_lidvids=[],
        source_product_type="data_to_raw_source_product",
    )

    instruments_dict = {}
    for ir in pr.image_records:
        _inst = ir.instrument_name.lower().replace(" ", "_")
        instruments_dict[ir.instrument_name] = {
            "name": ir.instrument_name,
            "lid": f"{lids['spacecraft']}.{_inst}",
        }
        # todo: need to figure out how to set version id here
        d["source_product_lidvids"].append(  # type: ignore
            f"urn:nasa:pds:viper_vis:data_raw:{ir.product_id}::99.99"
        )

    for inst in instruments_dict.values():
        d["instruments"].append(inst)  # type: ignore

    return d
