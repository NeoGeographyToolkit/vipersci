#!/usr/bin/env python
# coding: utf-8

"""Defines the VIS Raw_Product table using the SQLAlchemy ORM."""

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

from datetime import datetime, timedelta, timezone

from sqlalchemy import orm
from sqlalchemy.orm import validates
from sqlalchemy import (
    Integer, String, Column, Boolean, Float, Identity, DateTime
)
from sqlalchemy.ext.hybrid import hybrid_property

from vipersci.pds.pid import VISID, vis_instruments, vis_compression
from vipersci.vis.header import pga_gain as header_pga_gain


Base = orm.declarative_base()


class Raw_Product(Base):
    """An object to represent rows in the Raw_Products table for VIS.
    """
    # Note that SQLAlchemy will default the table name to the name of the
    # class. We want the class to provide a single instance (object) whereas
    # the table is the full table of all of these objects. To that end, we
    # use the plural for the table name and the singular for the class name.
    __tablename__ = "raw_products"

    id = Column(Integer, Identity(start=1), primary_key=True)
    adc_gain = Column(
        Integer, nullable=False, doc="ADC_GAIN from the MCSE Image Header."
    )
    auto_exposure = Column(
        Boolean, nullable=False, doc="AUTO_EXPOSURE from the MCSE Image Header."
    )
    bad_pixel_table_id = Column(
        Integer,
        nullable=False,
        # There is a Defective Pixel Map (really a list of 128 coordinates) for
        # each MCAM.  The "state" of this is managed by the ground and not
        # reflected in any Image Header information attached to an individual
        # image.  It is not clear how to obtain this information from Yamcs,
        # or even what might be recorded, so this column's value is TBD.
    )
    capture_id = Column(
        Integer, nullable=False, doc="The captureId from the command sequence."
        # TODO: learn more about captureIds to provide better doc here.
    )
    _exposure_time = Column(
        "exposure_time",
        Integer,
        nullable=False,
        doc="The exposure time in microseconds, the result of decoding the "
            "EXP_STEP and EXP paramaters from the MCSE Image Header."
    )
    file_creation_datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        doc="The time at which file_name was created."
    )
    file_path = Column(
        String,
        nullable=False,
        doc="The absolute path (POSIX style) that contains the Array_2D_Image "
            "that this metadata refers to."
    )
    # Not sure where we're getting info for these light booleans yet.
    hazlight_aft_port_on = Column(Boolean, nullable=False)
    hazlight_aft_starboard_on = Column(Boolean, nullable=False)
    hazlight_center_port_on = Column(Boolean, nullable=False)
    hazlight_center_starboard_on = Column(Boolean, nullable=False)
    hazlight_fore_port_on = Column(Boolean, nullable=False)
    hazlight_fore_starboard_on = Column(Boolean, nullable=False)
    image_id = Column(
        Integer,
        nullable=False,
        doc="The IMG_ID from the MCSE Image Header used for CCU storage and "
            "retrieval."
    )
    instrument_name = Column(
        String,
        nullable=False,
        doc="The full name of the instrument."
    )
    instrument_temperature = Column(
        Float,
        nullable=False,
        doc="The TEMPERATURE from the MCSE Image Header.  TBD how to convert "
            "this 16-bit integer into degrees C."
    )
    # There may also be another sensor in the camera body (PT1000) and
    # externally to each camera body (AD590), will need to track down their
    # Yamcs feeds.
    lines = Column(
        Integer,
        nullable=False,
        doc="The imageHeight parameter from the Yamcs imageHeader."
    )
    _lobt = Column(
        "lobt",
        Integer,
        nullable=False,
        doc="The TIME_TAG from the MCSE Image Header."
    )
    mcam_id = Column(
        Integer, nullable=False, doc="The MCAM_ID from the MCSE Image Header."
    )
    md5_checksum = Column(
        String,
        nullable=False,
        doc="The md5 checksum of the file described by file_path."
    )
    mission_phase = Column(
        String,
        nullable=False,
        # Not sure what form this will take, nor where it can be looked up.
    )
    navlight_left_on = Column(Boolean, nullable=False)
    navlight_right_on = Column(Boolean, nullable=False)
    offset = Column(
        Integer,
        nullable=False,
        doc="The OFFSET parameter from the MCSE Image Header."
    )
    onboard_compression_ratio = Column(
        Float,
        nullable=False,
        # This is a PDS img:Onboard_Compression parameter which is the ratio
        # of the size, in bytes, of the original uncompressed data object
        # to its compressed size.  This operation is done by RFSW, but not
        # sure where to get this parameter from ...?
    )
    onboard_compression_type = Column(
        String,
        nullable=False,
        # This is the PDS img:Onboard_Compression parameter.  For us this
        # is going to be ICER, Lossless, or rarely None.
    )
    output_image_mask = Column(
        Integer,
        nullable=False,
        doc="The outputImageMask from the Yamcs imageHeader."
        # TODO: learn more about outputImageMask to provide better doc here.
    )
    output_image_type = Column(
        String,
        nullable=False,
        doc="The outputImageType from the Yamcs imageHeader."
        # TODO: learn more about outputImageType to provide better doc here.
    )
    _pid = Column(
        "product_id", String, nullable=False, doc="The PDS Product ID."
    )
    padding = Column(
        Integer,
        nullable=False,
        doc="The padding parameter from the Yamcs imageHeader."
    )
    pga_gain = Column(
        Float,
        nullable=False,
        doc="The translated floating point multiplier derived from PGA_GAIN "
            "from the MCSE Image Header."
    )
    processing_info = Column(
        Integer,
        nullable=False,
        doc="The processingInfo parameter from the Yamcs imageHeader."
        # TODO: learn more about processingInfo to provide better doc here.
    )
    purpose = Column(
        String,
        nullable=False,
        doc="This is the value for the PDS "
            "Observation_Area/Primary_Result_Summary/purpose parameter, it "
            "has a restricted set of allowable values."
    )
    samples = Column(
        Integer,
        nullable=False,
        doc="The imageWidth parameter from the Yamcs imageHeader."
    )
    software_name = Column(String, nullable=False)
    software_version = Column(String, nullable=False)
    software_type = Column(String, nullable=False)
    software_program_name = Column(String, nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    stereo = Column(
        Boolean,
        nullable=False,
        doc="The stereo parameter from the Yamcs imageHeader."
        # TODO: learn more about stereo to provide better doc here.
    )
    stop_time = Column(DateTime(timezone=True), nullable=False)
    voltage_ramp = Column(
        Integer,
        nullable=False,
        doc="The VOLTAGE_RAMP parameter from the MCSE Image Header."
    )

    def __init__(self, **kwargs):
        if kwargs.keys() >= {"start_time", "lobt"}:
            if (
                datetime.fromtimestamp(kwargs["lobt"], tz=timezone.utc) !=
                kwargs["start_time"]
            ):
                raise ValueError(
                    f"The start_time {kwargs['start_time']} does not equal "
                    f"the lobt {kwargs['lobt']}"
                )

        if "product_id" in kwargs:
            pid = VISID(kwargs["product_id"])

            if "lobt" in kwargs:
                dt = datetime.fromtimestamp(kwargs["lobt"], tz=timezone.utc )
                if pid.datetime() != dt:
                    raise ValueError(
                        f"The product_id datetime ({pid.datetime()}) and the "
                        f"provided lobt ({dt}) disagree."
                    )

            if "start_time" in kwargs and pid.datetime() != kwargs["start_time"]:
                raise ValueError(
                    f"The product_id datetime ({pid.datetime()}) and the "
                    f"provided start_time ({kwargs['start_time']}) disagree."
                )

            if (
                "instrument_name" in kwargs and not (
                    vis_instruments[pid.instrument] == kwargs["instrument_name"] or
                    pid.instrument == kwargs["instrument_name"]
                )
            ):
                raise ValueError(
                    f"The product_id instrument code ({pid.instrument}) and "
                    f"the provided instrument_name "
                    f"({kwargs['instrument_name']}) disagree."
                )

            if (
                "onboard_compression_ratio" in kwargs and not (
                    vis_compression[pid.compression] == kwargs[
                        "onboard_compression_ratio"
                    ] or
                    pid.compression == kwargs["onboard_compression_ratio"]
                )
            ):
                raise ValueError(
                    f"The product_id compression code ({pid.compression}) and "
                    f"the provided onboard_compression_ratio "
                    f"({kwargs['onboard_compression_ratio']}) disagree."
                )

            # Final cleanup so that super() works later.
            del kwargs["product_id"]
        elif (
                ("start_time" in kwargs or "lobt" in kwargs) and
                kwargs.keys() >= {
                    "instrument_name", "onboard_compression_ratio"
                }
        ):
            pid = VISID(kwargs)
        else:
            raise ValueError(
                "Either product_id must be given, or each of start_time, "
                "instrument_name, and onboard_compression_ratio."
            )

        after_super_init_keys = ("exposure_time", )
        after_super_init = {}
        for k in after_super_init_keys:
            if k in kwargs:
                after_super_init[k] = kwargs[k]
                del kwargs[k]

        super().__init__(**kwargs)

        self._pid = str(pid)
        for k, v in after_super_init.items():
            setattr(self, k, v)

        return

    @hybrid_property
    def product_id(self):
        return self._pid

    @product_id.setter
    def product_id(self, pid):
        # vid = VISID(pid)
        # self._pid = str(vid)
        # self.start_time = vid.datetime()
        # self.instrument_name = vis_instruments[vid.instrument]
        # self.compression_ratio = vis_compression[vid.compression]
        raise NotImplementedError("product_id cannot be set directly.")

    @validates('pga_gain')
    def validate_pga_gain(self, key, value):
        return header_pga_gain(value)

    @validates('mcam_id')
    def validate_mcam_id(self, key, value: int):
        s = {0, 1, 2, 3, 4}
        if value not in s:
            raise ValueError(f"mcam_id must be one of {s}")
        return value

    @hybrid_property
    def lobt(self):
        return self._lobt

    @lobt.setter
    def lobt(self, lobt):
        self._lobt = lobt
        self.start_time = datetime.fromtimestamp(lobt, tz=timezone.utc)

    @hybrid_property
    def exposure_time(self):
        return self._exposure_time

    @exposure_time.setter
    def exposure_time(self, value: int):
        """Takes an exposure time in microseconds."""
        self._exposure_time = value
        self.stop_time = self.start_time + timedelta(microseconds=value)

    @validates("purpose")
    def validate_purpose(self, key, value: str):
        s = {
            "Calibration",
            "Checkout",
            "Engineering",
            "Navigation",
            "Observation Geometry",
            "Science",
            "Supporting Observation"
        }
        if value not in s:
            raise ValueError(f"purpose must be one of {s}")
        return value

    @validates("onboard_compression_type")
    def validate_onboard_compression_type(self, key, value: str):
        s = {"ICER", "Lossless", "None"}
        if value not in s:
            raise ValueError(f"onboard_compression_type must be one of {s}")
        return value
