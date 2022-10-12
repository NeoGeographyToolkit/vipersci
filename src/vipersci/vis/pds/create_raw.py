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
from datetime import datetime, date
import hashlib
from importlib import resources
import logging
import sys
from typing import Union
from pathlib import Path

from genshi.template import MarkupTemplate
import numpy as np
import numpy.typing as npt
from skimage.io import imsave
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tifftools import read_tiff, Datatype


import vipersci
from vipersci.vis.db.raw_products import Raw_Product
from vipersci.pds import pid as pds
from vipersci import util

logger = logging.getLogger(__name__)


def arg_parser():
    parser = argparse.ArgumentParser(
        description=__doc__,
        parents=[util.parent_parser()]
    )
    parser.add_argument(
        "-d", "--dburl",
        default="postgresql://postgres:NotTheDefault@localhost/visdb",
        help="Database with a raw_products table which will be written to. "
             "Default: %(default)s"
    )
    parser.add_argument(
        "-t", "--template",
        type=Path,
        help="Genshi XML file template.  Will default to the raw-template.xml "
             "file distributed with the module."
    )
    parser.add_argument(
        "--tiff",
        type=Path,
        help="Path to TIFF file that this label is to be created for."
    )
    parser.add_argument(
        "-o", "--output_dir",
        type=Path,
        default=Path.cwd(),
        help="Output directory for label."
    )
    return parser


def main():
    args = arg_parser().parse_args()
    util.set_logger(args.verbose)

    # Eventually, this will be replaced by data gathered from the
    # telemetry stream.  For now, we fake

    pid, d = tif_info(args.tiff)

    d.update(version_info(pid))
    d.update(telemetry_info(pid))

    # loader = TemplateLoader()
    # tmpl = loader.load(str(args.input))
    if args.template is None:
        tmpl = MarkupTemplate(resources.read_text(
            "vipersci.pds.data.template", "raw-template.xml"
        ))
    else:
        tmpl = MarkupTemplate(args.template.read_text())
    stream = tmpl.generate(**d)
    out_path = args.output_dir / args.tiff.with_suffix(".xml")
    out_path.write_text(stream.render())


def create(
    metadata: dict,
    image: Union[npt.NDArray[np.uint16], Path] = None,
    outdir: Path = Path.cwd(),
    dburl: str = None,
    template_path: Path = None
):
    if "product_id" not in metadata:
        metadata["product_id"] = pds.VISID(metadata)

    if isinstance(image, Path):
        # Should we bother to test filename patterns against the pid?
        tif_d = tif_info(image)
    else:
        tif_d = tif_info(write_tiff(metadata["product_id"], image, outdir))

    for k in ("lines", "samples"):
        if metadata[k] != tif_d[k]:
            raise ValueError(
                f"The value of {k} from the TIFF ({tif_d[k]}) does not "
                f"match the value from the metadata ({metadata[k]})"
            )

    metadata.update(tif_d)
    metadata.update(version_info(metadata["product_id"]))

    metadata.update({
        "software_name": "vipersci",
        "software_version": vipersci.__version__,
        "software_type": "Python",
        "software_program_name": __name__
    })

    # Other items that I'm not sure where they come from, hard-coding for now:
    metadata["mission_phase"] = "TEST"

    # The attribute pds:purpose must be equal to one of the following values
    # 'Calibration', 'Checkout', 'Engineering', 'Navigation',
    # 'Observation Geometry', 'Science', or 'Supporting Observation'.
    metadata["purpose"] = "Navigation"

    if dburl is not None:
        db_insert(metadata)

    write_xml(metadata, outdir, template_path)

    return


def db_insert(metadata: dict, dburl: str):
    rp = Raw_Product(**metadata)

    engine = create_engine(dburl)

    session_maker = sessionmaker(engine, future=True)
    with session_maker.begin() as session:
        session.add(rp)
        session.commit()

    return


def tif_info(p: Path):
    dt = datetime.utcfromtimestamp(p.stat().st_mtime)

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

    if tags[258]["datatype"] != 3:
        raise ValueError(
            f"TIFF file has datatype {Datatype[tags[258]['datatype']]} "
            f"expecting UINT16 - unsigned short."
        )
    else:
        dtype = f"Unsigned{end}2"

    d = {
        "file_path": p.name,
        "file_creation_datetime": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "md5_checksum": md5.hexdigest(),
        "byte_offset": tags[273]["data"][0],  # Tag 273 is StripOffsets
        "lines": tags[257]["data"][0],  # Tag 257 is ImageWidth,
        "samples": tags[256]["data"][0],  # Tag 256 is ImageWidth,
        "data_type": dtype,
    }
    return d


def version_info(pid: pds.VISID):
    # This should reach into a database and do something smart to figure
    # out how to populate this, but again, for now, hardcoding:
    d = {
        "modification_details": [
            {
                "version": 0.1,
                "date": date.today().isoformat(),
                "description": "Illegal version number for testing"
            }
        ],
        "vid": 0.1
    }
    return d


def write_tiff(
        pid: pds.VISID, image: npt.NDArray[np.uint16], outdir: Path = Path.cwd()
):
    if image.dtype != np.uint16:
        raise ValueError(
            f"The input image is not a uint16, it is {image.dtype}"
        )

    desc = f"VIPER {pds.vis_instruments[pid.instrument]} {pid}"

    logger.info(desc)
    outpath = (outdir / str(pid)).with_suffix(".tif")

    imsave(
        str(outpath),
        image,
        check_contrast=False,
        description=desc,
        metadata=None
    )
    return outpath


def write_xml(
    metadata: dict,
    outdir: Path = Path.cwd(),
    template_path: Path = None
):
    metadata["lid"] = f"urn:nasa:pds:viper_vis:raw:{metadata['product_id']}"
    metadata["mission_lid"] = "urn:nasa:pds:viper"
    metadata["sc_lid"] = "urn:nasa:pds:context:instrument_host:spacecraft.viper"
    _inst = pds.vis_instruments[
        metadata["product_id"].instrument
    ].lower().replace(" ", "_")
    metadata["inst_lid"] = f"urn:nasa:pds:context:instrument_host:spacecraft.viper.{_inst}"

    if template_path is None:
        tmpl = MarkupTemplate(resources.read_text(
            "vipersci.pds.data.template", "raw-template.xml"
        ))
    else:
        tmpl = MarkupTemplate(template_path.read_text())
    stream = tmpl.generate(**metadata)
    out_path = (outdir / str(metadata["product_id"])).with_suffix(".xml")
    out_path.write_text(stream.render())
    return


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
