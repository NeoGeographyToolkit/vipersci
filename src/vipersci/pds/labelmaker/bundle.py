"""Creates a PDS4 Bundle XML file from the provided Collection XML labels.
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

import logging
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd
import yaml

from vipersci import util
from vipersci.pds.labelmaker import (
    assert_unique,
    gather_info,
    get_common_label_info,
    write_xml,
)
from vipersci.pds.xml import find_text, ns

logger = logging.getLogger(__name__)

# This definition is from Appendix K.2.1.6 (Bundle_Member_Entry) in the
# https://pds.nasa.gov/datastandards/documents/dph/current/PDS4_DataProvidersHandbook_1.20.0.pdf
collection_reference_type = {
    "Browse": "bundle_has_browse_collection",
    "Calibration": "bundle_has_calibration_collection",
    "Context": "bundle_has_context_collection",
    "Data": "bundle_has_data_collection",
    "Document": "bundle_has_document_collection",
    "Geometry": "bundle_has_geometry_collection",
    "Miscellaneous": "bundle_has_miscellaneous_collection",
    "SPICE Kernel": "bundle_has_spice_kernel_collection",
    "Schema": "bundle_has_schema_collection",
}


def add_parser(subparsers):
    parser = subparsers.add_parser("bundle", help=__doc__)

    parser.add_argument(
        "-c", "--config", type=Path, help="YAML file with configuration parameters."
    )
    parser.add_argument(
        "-t", "--template", type=Path, help="Genshi XML file template. "
    )
    parser.add_argument(
        "labelfiles",
        type=Path,
        nargs="+",
        help="Path(s) to all Collection XML label files to be included in the output "
        "Bundle label file.",
    )
    parser.set_defaults(func=main)
    return parser


def main(args):
    util.set_logger(args.verbose)

    d = yaml.safe_load(args.config.read_text())

    outpath = Path("bundle.xml")
    if outpath.exists():
        raise FileExistsError(f"The {outpath} file already exists.")

    labelinfo = []
    for labelpath in args.labelfiles:
        logger.info(f"Reading {labelpath}")
        labelinfo.append(get_label_info(labelpath))

    d.update(check_and_derive(d, labelinfo))

    write_xml(d, outpath, args.template)
    logger.info(f"Wrote {outpath}")


def check_and_derive(config: dict, labelinfo: list):
    df = pd.DataFrame(labelinfo)

    # Check consistency for gathered labels:
    for x in (
        "bundle_lid",
        "investigation_name",
        "investigation_type",
        "investigation_lid",
        "host_name",
        "host_lid",
        "target_name",
        "target_type",
        "target_lid",
    ):
        assert_unique(config[x], df[x])

    # Generate values from gathered labels:
    d = gather_info(df, config["modification_details"])

    collections = []
    for label in labelinfo:
        collections.append(
            {
                "lid": label["lid"] + "::" + label["vid"],
                "type": collection_reference_type[label["collection_type"]],
            }
        )
    d["collections"] = collections

    return d


def get_label_info(path: Path) -> dict:
    root = ET.fromstring(path.read_text())

    if root.find("pds:Context_Area", ns) is not None:
        d = get_common_label_info(root, "pds:Context_Area")
    else:
        d = get_common_label_info(root, None)

    d["bundle_lid"] = ":".join(d["lid"].split(":")[:-1])
    d["collection_type"] = find_text(root, ".//pds:Collection/pds:collection_type")
    return d
