#!/usr/bin/env python
# coding: utf-8

"""Defines the VIS image_requests table using the SQLAlchemy ORM."""

# Copyright 2023, United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All rights reserved.
#
# Copyright (c) 2023, Million Concepts
# All rights reserved.
#
# This code is licensed under the Apache License, Version 2.0 (the "License");
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
#
#
# The ImageRequest class below is a derived work based on the ImageRequest class from
# https://github.com/MillionConcepts/viper-vis-orchestrator/blob/main/viper_orchestrator/visintent/tracking/tables.py
# as of commit 897585605a7ace3b2f0886f1fd02776b3cd7245f (2023-09-24)
# written by Michael St. Clair.  That code is licensed under the BSD 3-Clause
# License:
#
# BSD 3-Clause License
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import enum
from datetime import datetime
from typing import Sequence, Union

from geoalchemy2 import Geometry  # type: ignore
from sqlalchemy import Boolean, DateTime, Enum, Identity, Integer, String
from sqlalchemy.orm import mapped_column, relationship, validates

from vipersci.pds.datetime import isozformat
from vipersci.pds.pid import vis_instruments
from vipersci.vis.db import Base
from vipersci.vis.db.light_records import luminaire_names


class Status(enum.Enum):
    """
    This describes the status of an Image Request.
    """

    WORKING = 1
    READY_FOR_VIS = 2
    READY_FOR_PLANNING = 3
    PLANNED = 4
    NOT_PLANNED = 5
    IMMEDIATE = 6
    ACQUIRED = 7
    NOT_AQUIRED = 8
    NOT_OBTAINABLE = 9


class CameraType(enum.Enum):
    NAVCAM = 1
    AFTCAM = 2
    HAZCAM = 3


class CompressionType(enum.Enum):
    LOSSLESS = 1
    LOSSY = 2


class ImageMode(enum.Enum):
    # These are just for the NavCams and AftCams.
    LEFT = 1
    RIGHT = 2
    STEREO = 3
    PANORAMA = 4  # Only NavCams
    CALIBRATION = 5  # Only NavCams: initiates "standard" calibration sequence.


class RoverWaitFor(enum.Enum):
    DOWNLINK = 1
    VIS_VERIFICATION = 2
    DOWNLINK_AND_VIS = 3


class ImageRequest(Base):
    """An object to represent rows in the image_requests table for VIS."""

    __tablename__ = "image_requests"

    id = mapped_column(Integer, Identity(start=1), primary_key=True)
    title = mapped_column(String, nullable=False, doc="Short title for request.")
    justification = mapped_column(
        String, nullable=False, doc="Full description of request intent."
    )

    # TODO: determine whether to dynamically or statically update
    status = mapped_column(
        Enum(Status), nullable=False, default="WORKING", doc="request status"
    )
    users = mapped_column(String, nullable=False, doc="requesting user(s)")
    # note: autofilled; this will also track edit time / backfill time.
    request_time = mapped_column(
        DateTime(timezone=True), nullable=False, doc="time of request submission/update"
    )
    # all remaining fields may be null for backfilled requests. they are
    # intended for use in ops.
    target_location_point = mapped_column(
        Geometry(geometry_type="POINT", srid=910101),
        doc="If provided by the user the specific location of the image target point.",
    )
    target_location = mapped_column(
        String,
        doc="One-line description of what this should be an image "
        "of. May simply be coordinates from MMGIS.",
    )
    rover_location_point = mapped_column(
        Geometry(geometry_type="POINT", srid=910101),
        doc="If provided by the user the specific location of the rover for this "
        "image.",
    )
    rover_location = mapped_column(
        String,
        doc="One-line description of where the rover should be when "
        "the image is taken. May simply be coordinates from MMGIS.",
    )
    rover_orientation = mapped_column(
        String,
        default="any",
        doc="One-line description of desired rover orientation",
    )
    rover_wait_for = mapped_column(
        Enum(RoverWaitFor), doc="Details of a rover stop request."
    )
    # TODO: how do we handle attached images? are we responsible for file
    #  management?

    camera_type = mapped_column(Enum(CameraType), doc="Primary camera request.")
    imaging_mode = mapped_column(Enum(ImageMode), doc="Imaging mode to be used.")
    hazcams = mapped_column(
        String,
        doc="If camera_type is HAZCAM, this field should contain one or more hazcams.",
    )

    compression = mapped_column(
        Enum(CompressionType), doc="desired compression for image"
    )
    luminaires = mapped_column(
        String, default="default", doc="requested active luminaires"
    )
    exposure_time = mapped_column(String, default="default")

    # Start panorama-only parameters:
    caltarget_required = mapped_column(
        Boolean, default=True, doc="acquire caltarget image?"
    )
    aftcam_pair = mapped_column(
        Boolean, default=False, doc="acquire additional aftcam pair?"
    )
    chin_down_navcam_pair = mapped_column(
        Boolean, default=False, doc="acquire chin-down navcam pair?"
    )
    slices = mapped_column(Integer, doc="The total number of slices.")
    # needed only for non-360 panos, if blank, assume first_slice is "1" and
    # last slice is the number of slices, a.k.a a 360 pano.
    first_slice_index = mapped_column(Integer, doc="First slice of pano, >= 1.")
    last_slice_index = mapped_column(Integer, doc="Last slice of pano, <= slices.")
    # End panorama-only parameters.

    # These establish the many-to-many relationship between ImageRequests and LDST
    # hypotheses.  The junction table allows the relation to be marked "critical"
    # or not.
    ldst_hypotheses = relationship(
        "LDST",
        secondary="junc_image_request_ldst",
        back_populates="image_requests",
        viewonly=True,
    )
    ldst_associations = relationship(
        "JuncImageRequestLDST", back_populates="image_request"
    )

    # This establishes a many ImageRequests to one ImageRecord relationship.
    image_records = relationship("ImageRecord", back_populates="image_request")

    # legal values for things.
    # could do some of these as enum columns but very annoying for things that
    # start with numbers, generally more complicated, etc.

    # TODO: do we want a non-pano image request to be able to handle a series?

    luminaire_generalities = ("default", "none")

    @validates("luminaires")
    def validate_luminaires(self, _, value: Union[Sequence[str], str]):
        return self.validate_listing(
            "luminaires",
            ("default", "none"),
            tuple(luminaire_names.keys()),
            value,
            limit=4,
        )

    @validates("hazcams")
    def validate_hazcams(self, _, value: Union[Sequence[str], str]):
        return self.validate_listing(
            "hazcams",
            ("Any",),
            tuple(filter(lambda x: x.startswith("h"), vis_instruments.keys())),
            value,
        )

    @staticmethod
    def validate_listing(
        name: str,
        generalities: tuple,
        allowable: tuple,
        value: Union[Sequence[str], str],
        limit=None,
    ):
        if len(value) == 0:
            raise ValueError(
                f"At least '{generalities[0]}' must be specified for {name}."
            )

        if isinstance(value, str):
            value = value.split(",")

        if limit is not None and len(value) > limit:
            raise ValueError(f"Maximum {limit} {name}s per request.")

        if len(value) == 1:
            legal = allowable + generalities
            if value[0] not in legal:
                raise ValueError(f"Single {name} entry must be one of {legal}.")
        else:
            if not all(v in allowable for v in value):
                raise ValueError(
                    f"Multi-element requests must be selected from:" f"{allowable}"
                )

        return ",".join(value)

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
