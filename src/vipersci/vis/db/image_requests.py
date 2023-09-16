#!/usr/bin/env python
# coding: utf-8

"""Defines the VIS image_requests table using the SQLAlchemy ORM."""

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

import enum
from typing import Sequence, Union

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Identity,
    Integer,
    String,
)
from sqlalchemy.orm import mapped_column, relationship, validates
from geoalchemy2 import Geometry  # type: ignore

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
    IMMEDIATE = 5


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
        DateTime, nullable=False, doc="time of request submission/update"
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

    # What follows are panorama-only parameters:
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
        elif len(value) == 1:
            legal = allowable + generalities
            if value[0] not in legal:
                raise ValueError(f"Single {name} entry must be one of {legal}.")
        else:
            if not all(v in allowable for v in value):
                raise ValueError(
                    f"Multi-element requests must be selected from:" f"{allowable}"
                )

        return ",".join(value)
