#!/usr/bin/env python
# coding: utf-8

"""Defines the VIS light records table using the SQLAlchemy ORM."""

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

from sqlalchemy import Boolean, DateTime, Identity, Integer, String
from sqlalchemy.orm import mapped_column, validates

import vipersci.vis.db.validators as vld

from vipersci.vis.db import Base


luminaire_names = {
    "navLeft": "NavLight Left",
    "navRight": "NavLight Right",
    "haz2": "HazLight Aft Port",
    "haz4": "HazLight Aft Starboard",
    "haz5": "HazLight Center Port",
    "haz6": "HazLight Center Starboard",
    "haz1": "HazLight Fore Port",
    "haz3": "HazLight Fore Starboard",
}

luminaire_shortnames = dict(
    hfp="haz1",
    hap="haz2",
    hfs="haz3",
    has="haz4",
    hcp="haz5",
    hcs="haz6",
    nl="navLeft",
    nr="navRight",
)


class LightRecord(Base):
    """An object to represent rows in the light_records table for VIS.  Each row
    represents a single state change (from 'on' to 'off' or vice-versa) for one
    light."""

    # This class is derived from SQLAlchemy's orm.DeclarativeBase
    # which means that it has a variety of class properties that are
    # then swept up into properties on the instantiated object via
    # super().__init__().

    # The table represents many of these objects, so the __tablename__ is
    # plural while the class name is singular.
    __tablename__ = "light_records"

    # The mapped_column() names below should use "snake_case" for the names that are
    # committed to the database as column names.  Furthermore, those names
    # should be similar, if not identical, to the PDS4 Class and Attribute
    # names that they represent.  Other names (like Yamcs parameter camelCase
    # names) are implemented as synonyms. Aside from the leading "id" column,
    # the remainder are in alphabetical order, since there are so many.

    id = mapped_column(Integer, Identity(start=1), primary_key=True)
    name = mapped_column(
        String, nullable=False, doc="The luminaire that was activated."
    )
    on = mapped_column(
        Boolean,
        nullable=False,
        doc="If this light, at this time, turned 'on', this column is TRUE, if the "
        "this light was detected to go from ON to OFF at this time, this column is "
        "FALSE.",
    )
    datetime = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="The time at which the luminaire was first measured to change state "
        "(via measuredState) from ON to OFF or vice-versa.",
    )

    @validates("name")
    def validate_name(self, key, value):
        if value not in luminaire_names.values():
            if value in luminaire_names:
                value = luminaire_names[value]
            else:
                raise ValueError(
                    f"The {key} ({value}) is not a luminaire name ({luminaire_names})"
                )
        return value

    @validates("datetime")
    def validate_datetime_asutc(self, key, value):
        return vld.validate_datetime_asutc(key, value)
