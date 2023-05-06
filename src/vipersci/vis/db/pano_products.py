#!/usr/bin/env python
# coding: utf-8

"""Defines the VIS pano_products table using the SQLAlchemy ORM."""

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

from datetime import datetime, timezone

# from typing import List
import xml.etree.ElementTree as ET

from sqlalchemy import (
    DateTime,
    Identity,
    Integer,
    String,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeBase, mapped_column, validates

from vipersci.pds.pid import PanoID
from vipersci.pds.xml import ns
from vipersci.pds.datetime import fromisozformat, isozformat
import vipersci.vis.db.validators as vld


class Base(DeclarativeBase):
    pass


class PanoProduct(Base):
    """An object to represent rows in the pano_products table for VIS."""

    # This class is derived from SQLAlchemy's orm.DeclarativeBase
    # which means that it has a variety of class properties that are
    # then swept up into properties on the instantiated object via
    # super().__init__().

    # The table represents many of these objects, so the __tablename__ is
    # plural while the class name is singular.
    __tablename__ = "pano_products"

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
    instrument_name = mapped_column(
        String,
        nullable=False,
        doc="The full name of the instrument of the earliest source product.",
    )
    lines = mapped_column(
        Integer,
        nullable=False,
        doc="The number of lines or rows in the Pano Product image.",
    )
    _pid = mapped_column(
        "product_id", String, nullable=False, unique=True, doc="The PDS Product ID."
    )
    purpose = mapped_column(
        String,
        nullable=False,
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
    # source_products: Mapped[List["RawProduct"]] =
    # relationship(back_populates="panorama")
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

        elif self.start_time is not None and self.instrument_name is not None:
            pid = PanoID(
                self.start_time.date(), self.start_time.time(), self.instrument_name
            )
        else:
            got = dict()
            for k in (
                "product_id",
                "start_time",
                "instrument_name",
            ):
                v = getattr(self, k)
                if v is not None:
                    got[k] = v

            raise ValueError(
                "Either product_id must be given, or each of start_time, "
                f"and instrument_name. Got: {got}"
            )

        self._pid = str(pid)

        # Is this really a good idea?  Not sure.  This instance variable plus
        # label_dict() and update() allow other key/value pairs to be carried around
        # in this object, which is handy.  If these are well enough known, perhaps
        # they should just be pre-defined properties and not left to chance?
        self.labelmeta = otherargs

        return

    @hybrid_property
    def product_id(self):
        return self._pid

    @product_id.inplace.setter
    def _product_id_setter(self, pid):
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
    def validate_purpose(self, key, value: str):
        return vld.validate_purpose(value)

    def asdict(self):
        d = {}

        for c in self.__table__.columns:
            if isinstance(getattr(self, c.name), datetime):
                d[c.name] = isozformat(getattr(self, c.name))
            else:
                d[c.name] = getattr(self, c.name)

        d.update(self.labelmeta)

        return d

    @classmethod
    def from_xml(cls, text: str):
        """
        Returns an instantiated PanoProduct object from parsing the provided *text*
        as XML.
        """
        d = {}

        def _find_text(root, xpath, unit_check=None):
            element = root.find(xpath, ns)
            if element is not None:
                if unit_check is not None:
                    if element.get("unit") != unit_check:
                        raise ValueError(
                            f"The {xpath} element does not have units of "
                            f"{unit_check}, has {element.get('unit')}"
                        )
                el_text = element.text
                if el_text:
                    return el_text
                else:
                    raise ValueError(
                        f"The XML {xpath} element contains no information."
                    )
            else:
                raise ValueError(f"XML text does not have a {xpath} element.")

        root = ET.fromstring(text)
        lid = _find_text(
            root, "./pds:Identification_Area/pds:logical_identifier"
        ).split(":")

        if lid[3] != "viper_vis":
            raise ValueError(
                f"XML text has a logical_identifier which is not viper_vis: {lid[3]}"
            )

        if lid[4] != "panoramas":
            raise ValueError(
                f"XML text has a logical_identifier which is not panoramas: {lid[4]}"
            )
        d["product_id"] = lid[5]

        d["file_creation_datetime"] = fromisozformat(
            _find_text(root, ".//pds:creation_date_time")
        )
        d["file_path"] = _find_text(root, ".//pds:file_name")

        osc = root.find(".//pds:Observing_System_Component[pds:type='Instrument']", ns)
        d["instrument_name"] = _find_text(osc, "pds:name")

        aa = root.find(".//pds:Axis_Array[pds:axis_name='Line']", ns)
        d["lines"] = int(_find_text(aa, "./pds:elements"))
        d["file_md5_checksum"] = _find_text(root, ".//pds:md5_checksum")
        d["mission_phase"] = _find_text(root, ".//msn:mission_phase_name")
        d["offset"] = _find_text(root, ".//img:analog_offset")

        d["purpose"] = _find_text(root, ".//pds:purpose")

        aa = root.find(".//pds:Axis_Array[pds:axis_name='Sample']", ns)
        d["samples"] = int(_find_text(aa, "./pds:elements"))

        sw = root.find(".//proc:Software", ns)
        d["software_name"] = _find_text(sw, "./proc:name")
        d["software_version"] = _find_text(sw, "./proc:software_version_id")
        d["software_program_name"] = _find_text(sw, "./proc:Software_Program/proc:name")

        # Start times must be on the whole second, which is why we don't use
        # fromisozformat() here.
        d["start_time"] = datetime.strptime(
            _find_text(root, ".//pds:start_date_time"), "%Y-%m-%dT%H:%M:%SZ"
        ).replace(tzinfo=timezone.utc)

        d["stop_time"] = fromisozformat(_find_text(root, ".//pds:stop_date_time"))

        return cls(**d)

    def label_dict(self):
        """Returns a dictionary suitable for label generation."""
        _inst = self.instrument_name.lower().replace(" ", "_")
        _sclid = "urn:nasa:pds:context:instrument_host:spacecraft.viper"
        d = dict(
            lid=f"urn:nasa:pds:viper_vis:panoramas:{self.product_id}",
            mission_lid="urn:nasa:pds:viper",
            sc_lid=_sclid,
            inst_lid=f"{_sclid}.{_inst}",
        )

        d.update(self.asdict())

        return d

    def update(self, other):
        for k, v in other.items():
            if k in self.__table__.columns or k in self.__mapper__.synonyms:
                setattr(self, k, v)
            else:
                self.labelmeta[k] = v
