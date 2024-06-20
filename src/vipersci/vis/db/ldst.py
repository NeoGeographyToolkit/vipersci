#!/usr/bin/env python
# coding: utf-8

"""Defines the VIS ldst table using the SQLAlchemy ORM."""

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

from sqlalchemy import String
from sqlalchemy.orm import mapped_column, relationship

from vipersci.vis.db import Base


class LDST(Base):
    """An object to represent LDST hypothesis info for VIS use."""

    __tablename__ = "ldst"

    id = mapped_column(String, primary_key=True)

    description = mapped_column(
        String, nullable=False, doc="A short descriptive name for this LDST hypothesis."
    )

    image_requests = relationship(
        "ImageRequest",
        secondary="junc_image_request_ldst",
        back_populates="ldst_hypotheses",
        viewonly=True,
    )
    image_request_associations = relationship(
        "JuncImageRequestLDST", back_populates="ldst"
    )
