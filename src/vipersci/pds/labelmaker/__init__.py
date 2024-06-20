"""Helps to build PDS4 Bundle and Collection XML labels and files.
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

import csv
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from genshi.template import MarkupTemplate

from vipersci.pds.datetime import fromisozformat, isozformat
from vipersci.pds.xml import find_text, ns

logger = logging.getLogger(__name__)


def get_common_label_info(element: ET.Element, area="pds:Observation_Area"):
    """
    Returns a dict of information harvested from *element* which contains
    PDS4 label information.

    The *area* argument contains the XML element which contains elements
    like start_date_time.  This is likely either 'pds:Observation_Area' (the
    default) or 'pds:Context_Area'.
    """
    if area is not None:
        osc = element.find(".//pds:Observing_System_Component[pds:type='Host']", ns)

        host_name = find_text(osc, "pds:name")
        host_lid = find_text(osc, "pds:Internal_Reference/pds:lid_reference")

        instruments = {}
        for i in element.findall(
            ".//pds:Observing_System_Component[pds:type='Instrument']", ns
        ):
            instruments[find_text(i, "pds:name")] = find_text(
                i, "pds:Internal_Reference/pds:lid_reference"
            )

        purposes = []
        for p in element.findall(
            f"./{area}/pds:Primary_Result_Summary/pds:purpose", ns
        ):
            purposes.append(p.text)

        processing_levels = []
        for p in element.findall(
            f"./{area}/pds:Primary_Result_Summary/pds:processing_level", ns
        ):
            processing_levels.append(p.text)
    else:
        host_name = None
        host_lid = None
        instruments = None
        purposes = None
        processing_levels = None

    lid = find_text(element, "./pds:Identification_Area/pds:logical_identifier")
    d = {
        "lid": lid,
        "vid": find_text(element, "./pds:Identification_Area/pds:version_id"),
        "start_date_time": (
            None
            if area is None
            else fromisozformat(
                find_text(element, f"./{area}/pds:Time_Coordinates/pds:start_date_time")
            )
        ),
        "stop_date_time": (
            None
            if area is None
            else fromisozformat(
                find_text(element, f"./{area}/pds:Time_Coordinates/pds:stop_date_time")
            )
        ),
        "investigation_name": (
            None
            if area is None
            else find_text(element, f"./{area}/pds:Investigation_Area/pds:name")
        ),
        "investigation_type": (
            None
            if area is None
            else find_text(element, f"./{area}/pds:Investigation_Area/pds:type")
        ),
        "investigation_lid": (
            None
            if area is None
            else find_text(
                element,
                f"./{area}/pds:Investigation_Area/pds:Internal_Reference/"
                "pds:lid_reference",
            )
        ),
        "host_name": host_name,
        "host_lid": host_lid,
        "target_name": (
            None
            if area is None
            else find_text(element, ".//pds:Target_Identification/pds:name")
        ),
        "target_type": (
            None
            if area is None
            else find_text(element, ".//pds:Target_Identification/pds:type")
        ),
        "target_lid": (
            None
            if area is None
            else find_text(
                element,
                ".//pds:Target_Identification/pds:Internal_Reference/pds:lid_reference",
            )
        ),
        "instruments": instruments,
        "purposes": purposes,
        "processing_levels": processing_levels,
    }

    return d


def get_lidvid(element: ET.Element):
    return {
        "lid": find_text(element, "./pds:Identification_Area/pds:logical_identifier"),
        "vid": find_text(element, "./pds:Identification_Area/pds:version_id"),
    }


def get_lidvidfile(path: Path) -> dict:
    """
    Returns a dict with three keys: 'lid', 'vid', and 'productfile' whose values
    are extracted from the XML file at *path*.

    This is a convenience function to read a PDS4 XML file and extract the following "
    values:
    ./pds:Identification_Area/pds:logical_identifier,
    ./pds:Identification_Area/pds:version_id, and
    ./pds:File_Area_Observational/pds:File/pds:file_name .
    """
    logger.info(f"Reading {path}")

    root = ET.fromstring(path.read_text())

    d = get_lidvid(root)
    for fxpath in (
        "./pds:File_Area_Observational/pds:File/pds:file_name",
        "./pds:Document/pds:Document_Edition/pds:Document_File/pds:file_name",
        "./pds:File_Area_Browse/pds:File/pds:file_name",
    ):
        element = root.find(fxpath, ns)
        if element is not None:
            el_text = element.text
            if el_text:
                d["productfile"] = el_text
                break
    else:
        d["productfile"] = None

    return d


def gather_info(df, modification_details: List[Dict]):
    """
    Returns a dict of information harvested from the provided pandas dataframe, *df*.

    The dataframe is primarily derived from a list of dicts produced by the
    get_common_label_info() function.
    """
    d = {
        "vid": str(vid_max(modification_details, pd.to_numeric(df["vid"]).max())),
        "instruments": {},
        "purposes": set(),
        "processing_levels": set(),
        "start_date_time": isozformat(df["start_date_time"].min()),
        "stop_date_time": isozformat(df["stop_date_time"].max()),
    }

    for inst_dict in df["instruments"].dropna().tolist():
        d["instruments"].update(inst_dict)

    for p in df["purposes"].dropna().tolist():
        d["purposes"].update(set(p))

    for pl in df["processing_levels"].dropna().tolist():
        d["processing_levels"].update(set(pl))

    return d


def assert_unique(value, series: pd.Series):
    """
    If the *series* has only a single unique value and that value is identical
    to *value* then this function silently returns.  Otherwise it will raise
    a ValueError.

    If the *series* has more than one unique value, this function will raise a
    ValueError.  If the *series* has a single unique value, but it is not equivalent
    to *value*, this function will raise a ValueError.
    """
    s = series.dropna()
    if s.nunique() == 1:
        col_val = s.unique()[0]
        if value != col_val:
            raise ValueError(
                f"The series has a unique value ({col_val}) which does not match the "
                f"provided value ({value}) for {series.name}."
            )
    else:
        raise ValueError(
            f"The series has more than one unique value of {series.name}: "
            f"{series.unique()} "
        )


def vid_max(modification_details: List[Dict], max_product_vid: Optional[float] = None):
    """
    Returns the maximum VID from the *modification_details* list, and if
    *max_product_vid* is not None, then this maximum VID is checked to at least
    be greater than *max_product_vid*, otherwise a ValueError is raised.
    """
    mod_vids = []
    for detail in modification_details:
        mod_vids.append(float(detail["version"]))
    max_mod_vid = max(mod_vids)
    if max_product_vid is not None:
        if max_mod_vid < max_product_vid:
            raise ValueError(
                f"The largest version in the configuration file is {max_mod_vid} but "
                f"the largest version amongst the labels is {max_product_vid} ."
            )
    return max_mod_vid


def write_inventory(path: Path, labels: List[Dict], member="P"):
    """
    Writes a PDS4 collection inventory CSV file to *path* based on the list of
    dicts in *labels*.

    Those dictionaries should have a 'lid' and a 'vid' keyword. The value of *member*
    indicates whether the label is a Primary (P) member or a Secondary (S) member of
    the collection.  If the dictionaries in *labels* have a "member" key, that value
    will be used instead of *member* for that output row.
    """
    with open(path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)

        for label in labels:
            lidvid = label["lid"] + "::" + label["vid"]
            m = label.get("member", member)
            writer.writerow([m, lidvid])


def write_xml(metadata: dict, outpath: Path, template_path: Path):
    """
    Convenience function to write an XML file at *outpath* that is the
    result of taking the information in *metadata* and populating the XML
    template at *template_path* with that information.

    This function uses the genshi markup library: https://genshi.edgewall.org
    """
    tmpl = MarkupTemplate(template_path.read_text())
    logger.debug(metadata)

    stream = tmpl.generate(**metadata)
    outpath.write_text(stream.render())
