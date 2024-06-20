"""Various helper functions for VIS PDS operations.
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
from datetime import date
from importlib import resources
from pathlib import Path

from genshi.template import MarkupTemplate

logger = logging.getLogger(__name__)

lids = {
    "bundle": "urn:nasa:pds:viper_vis",
    "mission": "urn:nasa:pds:viper",
    "spacecraft": "urn:nasa:pds:context:instrument_host:spacecraft.viper",
    "instrument": "urn:nasa:pds:context:instrument:viper.vis",
}


def version_info():
    # This should reach into a database and do something smart to figure
    # out how to populate this, but for now, hardcoding:
    d = {
        "modification_details": [
            {
                "version": 99.99,
                "date": date.today().isoformat(),
                "description": "Dumb information model forces this to be a 'valid' "
                "version instead of 0.1 for testing, which should be "
                "allowed.",
            }
        ],
        "vid": 99.99,
    }
    return d


def write_xml(
    product: dict,
    template: str,
    outdir: Path = Path.cwd(),
):
    """
    Writes a PDS4 XML label in *outdir* based on the contents of
    the *product* object, which must be of type Raw_Product.

    The *template_path* can be a path to an appropriate template
    XML file, but defaults to the raw-template.xml file provided
    with this library.
    """
    if Path(template).exists():
        tmpl = MarkupTemplate(Path(template).read_text())
    else:
        tmpl = MarkupTemplate(
            resources.read_text("vipersci.vis.pds.data", str(template))
        )

    d = version_info()
    d.update(product)

    logger.info(d)

    stream = tmpl.generate(**d)
    out_path = (outdir / product["product_id"]).with_suffix(".xml")
    out_path.write_text(stream.render())
