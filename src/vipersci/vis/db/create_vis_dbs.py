#!/usr/bin/env python
# coding: utf-8

"""Program to instantiate all the VIS tables in a database.

If a table already exists, no CREATE TABLE statement will be issued to
the database.
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
import logging

from sqlalchemy import create_engine, inspect

from vipersci import util

from vipersci.vis.db.raw_products import RawProduct

# As new tables are defined, their Classes must be imported above, and
# then also added to this tuple:
tables = (RawProduct,)

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
    return parser


def main():
    args = arg_parser().parse_args()
    util.set_logger(args.verbose)

    engine = create_engine(args.dburl)

    # Create tables
    for t in tables:
        logger.info(f"Attempting to create {t.__tablename__}.")
        t.metadata.create_all(engine)

    # Check table names exists via inspect
    ins = inspect(engine)
    print("The following tables are now present in the database:")
    for t in ins.get_table_names():
        print(f"  {t}")
