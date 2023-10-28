#!/usr/bin/env python
# coding: utf-8

"""Program to instantiate all the VIS tables in a database.

If a table already exists, no CREATE TABLE statement will be issued to
the database.
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
import csv
import logging

from geoalchemy2 import load_spatialite  # type: ignore
from sqlalchemy import create_engine, insert, inspect, select
from sqlalchemy.event import listen
from sqlalchemy.orm import Session

from vipersci import util

from vipersci.vis.db.image_records import ImageRecord
from vipersci.vis.db.image_requests import ImageRequest
from vipersci.vis.db.image_stats import ImageStats
from vipersci.vis.db.image_tags import ImageTag, taglist
from vipersci.vis.db.junc_image_pano import JuncImagePano
from vipersci.vis.db.junc_image_record_tags import JuncImageRecordTag
from vipersci.vis.db.junc_image_req_ldst import JuncImageRequestLDST
from vipersci.vis.db.ldst import LDST
from vipersci.vis.db.light_records import LightRecord
from vipersci.vis.db.pano_records import PanoRecord
from vipersci.vis.db.ptu_records import PanRecord, TiltRecord

# As new tables are defined, their Classes must be imported above, and
# then also added to this tuple:
tables = (
    ImageRecord,
    ImageRequest,
    ImageStats,
    ImageTag,
    JuncImagePano,
    JuncImageRecordTag,
    JuncImageRequestLDST,
    LDST,
    LightRecord,
    PanoRecord,
    PanRecord,
    TiltRecord,
)

logger = logging.getLogger(__name__)


def arg_parser():
    parser = argparse.ArgumentParser(
        description=__doc__, parents=[util.parent_parser()]
    )
    parser.add_argument(
        "-d",
        "--dburl",
        default="postgresql://postgres:NotTheDefault@localhost/visdb",
        help="Something like  %(default)s",
    )
    parser.add_argument(
        "-l", "--ldst", help="Path to semi-colon CSV file with LDST info."
    )
    return parser


def main():
    args = arg_parser().parse_args()
    util.set_logger(args.verbose)

    engine = create_engine(args.dburl)
    if args.dburl.startswith("sqlite://"):
        # This required because we have spatialite tables in the db:
        listen(engine, "connect", load_spatialite)

    # Create tables
    for t in tables:
        logger.info(f"Attempting to create {t.__tablename__}.")
        t.metadata.create_all(engine)

    with Session(engine) as session:
        # Establish image_tags
        scalars = session.scalars(select(ImageTag))
        results = scalars.all()
        if len(results) == 0:
            session.execute(insert(ImageTag), [{"name": x} for x in taglist])
            session.commit()
        elif len(results) == len(taglist):
            for i, row in enumerate(results):
                if row.name != taglist[i]:
                    raise ValueError(
                        f"Row {i} in the database has id {row.id} and tag {row.name} "
                        f"but should have {taglist[i]} from {taglist}."
                    )
        else:
            raise ValueError(
                f"The {ImageTag.__tablename__} table already contains the following "
                f"{len(results)} entries: {[r.name for r in results]}, but should "
                f"contain these {len(taglist)} entries: {taglist}"
            )

        # Set up LDST table
        if args.ldst is not None:
            with open(args.ldst, newline="") as csvfile:
                ldst_rows = list()
                reader = csv.reader(csvfile, delimiter=";")
                next(reader)  # Skip first line.
                next(reader)  # Skip second line.
                for row in reader:
                    ldst_rows.append(row)

            scalars = session.scalars(select(LDST))
            results = scalars.all()
            if len(results) == 0:
                session.execute(
                    insert(LDST), [{"id": x, "description": y} for (x, y) in ldst_rows]
                )
                session.commit()
            elif len(results) == len(ldst_rows):
                for i, row in enumerate(results):
                    if row.id != ldst_rows[i][0] or row.description != ldst_rows[i][1]:
                        raise ValueError(
                            f"Row {i} in the database has these values: {row} "
                            f"but should have {ldst_rows[i]}"
                        )
            else:
                raise ValueError(
                    f"The {LDST.__tablename__} table already contains the following "
                    f"{len(results)} entries: {results}, but should contain "
                    f"{len(ldst_rows)} entries."
                )

    # Check table names exists via inspect
    ins = inspect(engine)
    print("The following tables are now present in the database:")
    for t in ins.get_table_names():
        print(f"  {t}")
