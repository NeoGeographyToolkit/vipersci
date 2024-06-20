"""Extracts a "publishable" set of bundle and collection files when pointed at
a bundle directory.
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
import csv
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from shutil import copy2

from vipersci import util
from vipersci.pds.labelmaker import get_lidvidfile
from vipersci.pds.xml import find_text, ns

logger = logging.getLogger(__name__)


def arg_parser():
    parser = argparse.ArgumentParser(
        description=__doc__, parents=[util.parent_parser()]
    )
    parser.add_argument(
        "source_directory",
        type=Path,
        help="A directory that contains created Bundle files.",
    )
    parser.add_argument(
        "build_directory",
        type=Path,
        help="Path to a directory where the bundle files will be installed.",
    )
    return parser


def main():
    parser = arg_parser()
    args = parser.parse_args()
    util.set_logger(args.verbose)

    args.build_directory.mkdir(exist_ok=True)

    copy2(args.source_directory / "bundle.xml", args.build_directory)

    bundle = ET.fromstring((args.build_directory / "bundle.xml").read_text())
    readme = bundle.find("./pds:File_Area_Text/pds:File/pds:file_name", ns)
    if readme is not None:
        copy2(args.source_directory / readme.text, args.build_directory)

    for bme in bundle.findall(".//pds:Bundle_Member_Entry", ns):
        try:
            lidvid_ref = find_text(bme, "pds:lidvid_reference")
            col_lid, col_vid = lidvid_ref.split("::")
        except ValueError:
            col_lid = find_text(bme, "pds:lid_reference")
            col_vid = None

        if find_text(bme, "pds:member_status") == "Primary":
            col_name = col_lid.split(":")[-1]
            src_col_dir = args.source_directory / col_name
            if src_col_dir.exists() is False:
                raise FileNotFoundError(f"{src_col_dir} does not exist.")

            bld_col_dir = args.build_directory / col_name
            bld_col_dir.mkdir(exist_ok=True)

            col_label_file = f"collection_{col_name}.xml"
            copy2(src_col_dir / col_label_file, bld_col_dir)
            collection = ET.fromstring((bld_col_dir / col_label_file).read_text())
            this_col_lid = find_text(
                collection, "./pds:Identification_Area/pds:logical_identifier"
            )
            if col_lid != this_col_lid:
                raise ValueError(
                    f"The collection lid ({this_col_lid}) does not match the "
                    f"collection lid that the bundle file has ({col_lid})."
                )
            if col_vid is not None:
                this_col_vid = find_text(
                    collection, "./pds:Identification_Area/pds:version_id"
                )
                if this_col_vid != col_vid:
                    raise ValueError(
                        f"The collection vid ({this_col_vid}) for {col_lid} does not "
                        f"match the collection vid that the bundle file "
                        f"has ({col_vid})."
                    )
            inventory = find_text(
                collection, "./pds:File_Area_Inventory/pds:File/pds:file_name"
            )
            copy2(src_col_dir / inventory, bld_col_dir)
            col_lidvids = set()
            with open(str(src_col_dir / inventory), newline="") as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    if row[0] == "P":
                        col_lidvids.add(row[1])

            # At this point we have a list of product lidvids that we need to find
            # in this directory or elsewhere.
            for p in src_col_dir.rglob("*.xml"):
                f = get_lidvidfile(p)
                f_lidvid = f["lid"] + "::" + f["vid"]
                if f_lidvid in col_lidvids:
                    dest_path = bld_col_dir / p.relative_to(src_col_dir)
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    copy2(p, dest_path)
                    copy2(p.with_name(f["productfile"]), dest_path.parent)
                    col_lidvids.remove(f_lidvid)
                if len(col_lidvids) == 0:
                    break

            if len(col_lidvids) != 0:
                raise ValueError(f"Could not find the following lidvids: {col_lidvids}")
