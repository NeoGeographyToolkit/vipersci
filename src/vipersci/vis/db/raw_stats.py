#!/usr/bin/env python
# coding: utf-8

"""Defines the VIS raw_stats table using the SQLAlchemy ORM."""

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

from sqlalchemy import (
    Float,
    ForeignKey,
    Identity,
    Integer,
    String,
)
from sqlalchemy.orm import backref, mapped_column, relationship

from vipersci.vis.db import Base
from vipersci.vis.db.raw_products import RawProduct


class RawStats(Base):
    """An object to represent rows in the raw_stats table for VIS."""

    __tablename__ = "raw_stats"

    id = mapped_column(Integer, Identity(start=1), primary_key=True)
    product_id = mapped_column(
        String, ForeignKey(RawProduct.product_id), nullable=False
    )
    raw_product = relationship(RawProduct, backref=backref("stats", uselist=False))

    blur = mapped_column(
        Float, nullable=False, doc="Blur metric from skimage.measure.blur_effect()."
    )
    mean = mapped_column(Float, nullable=False, doc="Image mean.")
    std = mapped_column(Float, nullable=False, doc="Image standard deviation.")
