"""Creates a PDS4 Collection XML file from the provided XML labels.
"""

import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

from vipersci import util
from vipersci.pds.datetime import isozformat
from vipersci.pds.labelmaker import (
    assert_unique,
    gather_info,
    get_common_label_info,
    vid_max,
    write_inventory,
    write_xml,
)
from vipersci.pds.xml import ns

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


logger = logging.getLogger(__name__)


def add_parser(subparsers):
    parser = subparsers.add_parser("collection", help=__doc__)

    parser.add_argument(
        "-c", "--config", type=Path, help="YAML file with configuration parameters."
    )
    parser.add_argument(
        "--csv",
        type=Path,
        help="The collections CSV file.  If not given, one will be generated.",
    )
    parser.add_argument(
        "-t", "--template", type=Path, required=True, help="Genshi XML file template. "
    )
    parser.add_argument(
        "labelfiles",
        type=Path,
        nargs="+",
        help="Path(s) to all XML label files to be included in the output collection "
        "file.",
    )
    parser.set_defaults(func=main)
    return parser


def main(args):
    util.set_logger(args.verbose)

    d = yaml.safe_load(args.config.read_text())

    name = d["collection_lid"].split(":")[-1]
    outpath = Path(f"collection_{name}.xml")
    if outpath.exists():
        raise FileExistsError(f"The file {outpath} already exists.")

    labelinfo = []
    for labelpath in args.labelfiles:
        logger.info(f"Reading {labelpath}")
        labelinfo.append(get_label_info(labelpath))

    d.update(check_and_derive(d, labelinfo))

    if args.csv is None:
        csv_path = Path(f"collection_{name}.csv")
        if csv_path.exists():
            raise FileExistsError(f"The file {csv_path} already exists.")

        write_inventory(csv_path, labelinfo)
        logger.info(f"Wrote {csv_path}")
        d["number_of_records"] = len(labelinfo)
    else:
        csv_path = args.csv
        d["number_of_records"] = len(str.splitlines(args.csv.read_text()))

    d["collection_csv"] = csv_path
    d["file_creation_datetime"] = isozformat(
        datetime.fromtimestamp(csv_path.stat().st_mtime, timezone.utc)
    )

    write_xml(d, outpath, args.template)
    logger.info(f"Wrote {outpath}")


def check_and_derive(config: dict, labelinfo: list):
    df = pd.DataFrame(labelinfo)

    check = {
        "Browse": ("collection_lid",),
        "Data": (
            "collection_lid",
            "investigation_name",
            "investigation_type",
            "investigation_lid",
            "host_name",
            "host_lid",
            "target_name",
            "target_type",
            "target_lid",
        ),
        "Document": ("collection_lid",),
    }

    # Check consistency for gathered labels:
    for x in check[config["collection_type"]]:
        assert_unique(config[x], df[x])

    # Generate values from gathered labels:
    if config["collection_type"] == "Data":
        d = gather_info(df, config["modification_details"])
    elif config["collection_type"] in ("Document", "Browse"):
        d = {
            "vid": str(
                vid_max(config["modification_details"], pd.to_numeric(df["vid"]).max())
            )
        }
    else:
        raise NotImplementedError(
            f"Do not have a strategy for {config['collection_type']} collection types."
        )

    return d


def get_label_info(path: Path) -> dict:
    root = ET.fromstring(path.read_text())

    if root.find("pds:Observation_Area", ns) is not None:
        d = get_common_label_info(root, "pds:Observation_Area")
    else:
        d = get_common_label_info(root, None)

    d["collection_lid"] = ":".join(d["lid"].split(":")[:-1])
    return d
