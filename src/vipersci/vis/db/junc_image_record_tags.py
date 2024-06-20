#!/usr/bin/env python
# coding: utf-8

"""Defines the mapping or join table connecting the image_records and
image_tags tables using the SQLAlchemy ORM."""

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

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import mapped_column, relationship

from vipersci.vis.db import Base
from vipersci.vis.db.image_records import ImageRecord
from vipersci.vis.db.image_tags import ImageTag


class JuncImageRecordTag(Base):
    """An object to represent the junction of image_tags to VIS Image Records."""

    __tablename__ = "junc_image_record_tags"

    image_record_id = mapped_column(
        Integer, ForeignKey(ImageRecord.id), nullable=False, primary_key=True
    )
    image_tag_id = mapped_column(
        Integer, ForeignKey(ImageTag.id), nullable=False, primary_key=True
    )
    comment = mapped_column(
        String,
        nullable=True,
        doc="Any extra information about the the application of the tag to the image "
        "record.",
    )

    image_record = relationship("ImageRecord", back_populates="image_tag_associations")
    image_tag = relationship("ImageTag", back_populates="image_record_associations")
