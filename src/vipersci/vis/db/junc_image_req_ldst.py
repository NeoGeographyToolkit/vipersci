#!/usr/bin/env python
# coding: utf-8

"""Defines the mapping or join table connecting the image_requests and
ldst tables using the SQLAlchemy ORM."""

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

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import mapped_column, relationship

from vipersci.vis.db import Base
from vipersci.vis.db.image_requests import ImageRequest
from vipersci.vis.db.ldst import LDST


class JuncImageRequestLDST(Base):
    """An object to represent the junction of image_requests to LDST hypotheses."""

    __tablename__ = "junc_image_request_ldst"

    image_request_id = mapped_column(
        Integer, ForeignKey(ImageRequest.id), nullable=False, primary_key=True
    )
    ldst_id = mapped_column(
        String, ForeignKey(LDST.id), nullable=False, primary_key=True
    )
    critical = mapped_column(
        Boolean,
        doc="If true, indicates that this ImageRequest is critical for this LDST "
        "hypothesis.",
    )
    evaluation = mapped_column(
        Boolean,
        nullable=True,
        doc="True if a Scientist has indicated that the acquired images for the "
        "indicated ImageRequest supports the LDST Hypothesis.  If false, a Scientist "
        "has determined that the images do not support the LDST Hypothesis.",
    )
    evaluation_notes = mapped_column(
        String,
        nullable=True,
        doc="Any notes about the evaluation of the ImageRequest's images against the "
        "LDST hypothesis.",
    )
    evaluator = mapped_column(
        String,
        nullable=True,
        doc="The name of the individual that reviewed the acquired images against the "
        "LDST hypothesis.",
    )

    image_request = relationship("ImageRequest", back_populates="ldst_associations")
    ldst = relationship("LDST", back_populates="image_request_associations")
