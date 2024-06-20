#!/usr/bin/env python
# coding: utf-8

"""Defines the VIS pano_records table using the SQLAlchemy ORM."""

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

from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, Identity, Integer, String
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import mapped_column, relationship, validates

import vipersci.vis.db.validators as vld
from vipersci.pds import Purpose
from vipersci.pds.datetime import isozformat
from vipersci.pds.pid import PanoID, VISID
from vipersci.vis.db import Base


class PanoRecord(Base):
    """An object to represent rows in the pano_records table for VIS."""

    # This class is derived from SQLAlchemy's orm.DeclarativeBase
    # which means that it has a variety of class properties that are
    # then swept up into properties on the instantiated object via
    # super().__init__().

    # The table represents many of these objects, so the __tablename__ is
    # plural while the class name is singular.
    __tablename__ = "pano_records"

    # The mapped_column() names below should use "snake_case" for the names that are
    # committed to the database as column names.  Furthermore, those names
    # should be similar, if not identical, to the PDS4 Class and Attribute
    # names that they represent.  Other names are implemented as synonyms.
    # Aside from the leading "id" column, the remainder are in alphabetical order.

    id = mapped_column(Integer, Identity(start=1), primary_key=True)
    file_creation_datetime = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="The time at which file_name was created.",
    )
    file_md5_checksum = mapped_column(
        String,
        nullable=False,
        doc="The md5 checksum of the file described by file_path.",
    )
    file_path = mapped_column(
        String,
        nullable=False,
        doc="The absolute path (POSIX style) that contains the Array_2D_Image "
        "that this metadata refers to.",
    )
    # The image_records and image_record_associations allow a many PanoRecord to many
    # ImageRecord relationship.
    image_records = relationship(
        "ImageRecord",
        secondary="junc_image_pano",
        back_populates="pano_records",
        viewonly=True,
    )
    image_record_associations = relationship(
        "JuncImagePano", back_populates="pano_record"
    )
    lines = mapped_column(
        Integer,
        nullable=False,
        doc="The number of lines or rows in the Pano Product image.",
    )
    rover_pan_min = mapped_column(
        Float,
        nullable=False,
        doc="The minimum or leftmost pan angle of this panorama in degrees, where "
        "zero is the rover forward (+x) direction. "
        "This angle is relative to the rover frame.",
    )
    rover_pan_max = mapped_column(
        Float,
        nullable=False,
        doc="The maximum or rightmost pan angle of this panorama in degrees, where "
        "zero is the rover forward (+x) direction.  "
        "This angle is relative to the rover frame.",
    )
    rover_tilt_min = mapped_column(
        Float,
        nullable=False,
        doc="The minimum or lower tilt angle of this panorama in degrees, "
        "where zero is the rover level plane.  "
        "This tilt angle is relative to the rover frame.",
    )
    rover_tilt_max = mapped_column(
        Float,
        nullable=False,
        doc="The maximum or upper tilt angle of this panorama in degrees, "
        "where zero is the rover level plane.  "
        "This tilt angle is relative to the rover frame.",
    )
    _pid = mapped_column(
        "product_id", String, nullable=False, unique=True, doc="The PDS Product ID."
    )
    purpose = mapped_column(
        Enum(Purpose),
        nullable=True,
        doc="This is the value for the PDS "
        "Observation_Area/Primary_Result_Summary/purpose parameter, it "
        "has a restricted set of allowable values.",
    )
    samples = mapped_column(
        Integer,
        nullable=False,
        doc="The number of samples or columns in the Pano Product Image.",
    )
    software_name = mapped_column(String, nullable=False)
    software_version = mapped_column(String, nullable=False)
    software_program_name = mapped_column(String, nullable=False)
    start_time = mapped_column(DateTime(timezone=True), nullable=False)
    stop_time = mapped_column(DateTime(timezone=True), nullable=False)

    def __init__(self, **kwargs):
        # If present, product_id needs some special handling:
        if "product_id" in kwargs:
            pid = PanoID(kwargs["product_id"])
            del kwargs["product_id"]
        else:
            pid = False

        ppargs = dict()
        otherargs = dict()
        for k, v in kwargs.items():
            if k in self.__table__.columns or k in self.__mapper__.synonyms:
                ppargs[k] = v
            else:
                otherargs[k] = v

        # Instantiate early, so that the parent orm_declarative Base can
        # resolve all of the synonyms.
        super().__init__(**ppargs)

        # Ensure product_id consistency
        if pid:
            if "start_time" in kwargs and pid.datetime() != self.start_time:
                raise ValueError(
                    f"The product_id datetime ({pid.datetime()}) and the "
                    f"provided start_time ({kwargs['start_time']}) disagree."
                )

        elif "source_pids" in kwargs:
            source_pids = list(map(VISID, kwargs["source_pids"]))
            instruments = set([p.instrument for p in source_pids])
            inst = "pan"
            if len(instruments) == 1:
                inst = instruments.pop()

            source_pids.sort()
            st = source_pids[0].datetime()
            if self.start_time is None:
                self.start_time = st
            else:
                st = self.start_time

            pid = PanoID(st.date(), st.time(), inst)
        else:
            got = {}
            for k in (
                "product_id",
                "start_time",
            ):
                v = getattr(self, k)
                if v is not None:
                    got[k] = v

            if "source_pids" in kwargs:
                got["source_pids"] = kwargs["source_pids"]

            raise ValueError(
                "Either product_id must be given, or a list of source product IDs. "
                f"Got: {got}"
            )

        self._pid = str(pid)

        # Is this really a good idea?  Not sure.  This instance variable plus
        # label_dict() and update() allow other key/value pairs to be carried around
        # in this object, which is handy.  If these are well enough known, perhaps
        # they should just be pre-defined properties and not left to chance?
        self.labelmeta = otherargs

    @hybrid_property
    def product_id(self):
        return self._pid

    @product_id.inplace.setter
    def _product_id_setter(self, _):
        # In this class, the source of product_id information really is what
        # based on the source products, and so this should not be monkeyed with.
        # So at this time, this can only be set when this object is instantiated.
        raise NotImplementedError(
            "product_id cannot be set directly after instantiation."
        )

    @validates(
        "file_creation_datetime",
        "start_time",
        "stop_time",
    )
    def validate_datetime_asutc(self, key, value):
        return vld.validate_datetime_asutc(key, value)

    @validates("purpose")
    def validate_purpose(self, _, value: str):
        return vld.validate_purpose(value)

    def asdict(self):
        d = {}

        for c in self.__table__.columns:
            if isinstance(getattr(self, c.name), datetime):
                d[c.name] = isozformat(getattr(self, c.name))
            else:
                d[c.name] = getattr(self, c.name)

        if hasattr(self, "labelmeta"):
            d.update(self.labelmeta)

        return d

    @classmethod
    def from_xml(cls, text: str):
        """
        Returns an instantiated PanoProduct object from parsing the provided *text*
        as XML.
        """
        raise NotImplementedError()

    def update(self, other):
        for k, v in other.items():
            if k in self.__table__.columns or k in self.__mapper__.synonyms:
                setattr(self, k, v)
            else:
                self.labelmeta[k] = v
