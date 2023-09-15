#!/usr/bin/env python
# coding: utf-8

"""Defines the VIS ldst_verification table using the SQLAlchemy ORM."""

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

from sqlalchemy import (
    Boolean,
    ForeignKey,
    String,
)
from sqlalchemy.orm import backref, mapped_column, relationship

from vipersci.vis.db import Base
from vipersci.vis.db.image_records import ImageRecord
from vipersci.vis.db.ldst import LDST


class LDSTVerification(Base):
    """An object to represent LDST Critical Tracking Verification elements for VIS."""

    __tablename__ = "ldst_verification"

    # id = mapped_column(Integer, Identity(start=1), primary_key=True)
    product_id = mapped_column(
        String, ForeignKey(ImageRecord.product_id), nullable=False, primary_key=True
    )
    image_record = relationship(
        ImageRecord, backref=backref("ldst_verification", uselist=False)
    )

    ldst_hypothesis = mapped_column(
        String,
        ForeignKey(LDST.id),
        nullable=False,
        doc="The LDST Hypothesis identifier.",
    )

    notes = mapped_column(
        String,
        nullable=True,
        doc="Any notes about the verification of this image against the LDST "
        "hypothesis.",
    )

    verified = mapped_column(
        Boolean,
        nullable=False,
        doc="True if a Scientist has indicated that this image is an image that "
        "supports the LDST Hypothesis.  If false, a Scientist has determined that "
        "this image does not support the LDST Hypothesis.",
    )

    verifier = mapped_column(
        String,
        nullable=False,
        doc="The name of the individual that reviewed this image against the LDST "
        "hypothesis.",
    )
