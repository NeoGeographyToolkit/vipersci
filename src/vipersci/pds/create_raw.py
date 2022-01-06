"""Creates Raw VIS PDS Products.

For now, this program has a variety of pre-set data,
that will eventually be extracted from telemetry.
"""

# Copyright 2022, vipersci developers.
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
from pathlib import Path

from genshi.template import MarkupTemplate
from tifftools import read_tiff, Datatype

import vipersci
from vipersci.pds import pid as pds
from vipersci import util

logger = logging.getLogger(__name__)


def arg_parser():
    parser = argparse.ArgumentParser(
        description=__doc__,
        parents=[util.parent_parser()]
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

    d["product_id"] = str(pid)
    d["lid"] = f"urn:nasa:pds:viper_vis:raw:{pid}"
    d["mission_lid"] = "urn:nasa:pds:viper"
    d["mission_phase"] = "TEST"
    d["sc_lid"] = "urn:nasa:pds:context:instrument_host:spacecraft.viper"
    d["inst_name"] = pds.vis_instruments[pid.instrument]
    _inst = d["inst_name"].lower().replace(" ", "_")
    d[
        "inst_lid"
    ] = f"urn:nasa:pds:context:instrument_host:spacecraft.viper.{_inst}"

    # The attribute pds:purpose must be equal to one of the following values
    # 'Calibration', 'Checkout', 'Engineering', 'Navigation',
    # 'Observation Geometry', 'Science', or 'Supporting Observation'.
    d["purpose"] = "Navigation"

    d.update(version_info(pid))
    d.update(telemetry_info(pid))
    d.update(software_info())

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


def tif_info(p: Path):
    pid = pds.VISID(p.stem)
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
        "file_name": p.name,
        "file_creation_datetime": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "file_checksum": md5.hexdigest(),
        "byte_offset": tags[273]["data"][0],  # Tag 273 is StripOffsets
        "lines": tags[257]["data"][0],  # Tag 257 is ImageWidth,
        "samples": tags[256]["data"][0],  # Tag 256 is ImageWidth,
        "data_type": dtype,
    }
    return pid, d


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


def telemetry_info(pid: pds.VISID):
    st = pid.datetime().strftime("%Y-%m-%dT%H:%M:%SZ")
    comp = pds.vis_compression[pid.compression]
    if comp is None:
        cclass = "Lossless"
        cratio = 1
    elif comp is "SLoG":
        cclass = "Lossy"
        cratio = "??"
    else:
        cclass = "Lossy"
        cratio = comp

    d = {
        "start_time": st,
        "stop_time": st,
        "bad_pixel_table_id": 1,
        "exposure": 2,
        "lights": [
            {"name": "NavLight Left", "wavelength": 450},
            {"name": "NavLight Right", "wavelength": 450}
        ],
        "compression_class": cclass,
        "compression_ratio": cratio,
        "inst_temp": 30,
    }
    return d


def software_info():
    return {
        "software": [
            {
                "name": "VIS processing software",
                "version": vipersci.__version__,
                "type": "Python",
                "programs": [
                    {"name": __name__}
                ]
            }
        ],
    }


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
