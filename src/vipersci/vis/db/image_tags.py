#!/usr/bin/env python
# coding: utf-8

"""Defines the VIS image_tags table using the SQLAlchemy ORM."""

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

from sqlalchemy import Identity, Integer, String
from sqlalchemy.orm import mapped_column, relationship

from vipersci.vis.db import Base


class ImageTag(Base):
    """An object to represent tags that can be applied to VIS Image Records."""

    __tablename__ = "image_tags"

    id = mapped_column(Integer, Identity(start=1), primary_key=True)
    name = mapped_column(String, nullable=False, doc="The name of the tag.")

    image_records = relationship(
        "ImageRecord",
        secondary="junc_image_record_tags",
        back_populates="image_tags",
        viewonly=True,
    )
    image_record_associations = relationship(
        "JuncImageRecordTag", back_populates="image_tag"
    )


# Unlike other tables, the image_tags table should not have arbitrary contents, and the
# set of tags should be uniform and constant.  The taglist below is the canonical list
# of tag names to be loaded into this table.
# Only add new tags to the bottom of the list.
taglist = [
    "Over Exposed",
    "Under Exposed",
    "Compression Artifacts",
    "Missing row(s) of pixels",
    # Image header damaged in downlink?  Not sure how we'd know.
]
