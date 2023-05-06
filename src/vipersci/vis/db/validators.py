#!/usr/bin/env python
# coding: utf-8

"""Provides functions to validate various intput data."""

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

from vipersci.pds.datetime import fromisozformat


def validate_datetime_asutc(key, value):
    if isinstance(value, datetime):
        if value.utcoffset() is None:
            raise ValueError(f"{key} must be tz aware.")
        dt = value
    elif isinstance(value, str):
        if value.endswith("Z"):
            dt = fromisozformat(value)
        else:
            dt = datetime.fromisoformat(value)
    else:
        raise ValueError(f"{key} must be a datetime or an ISO 8601 formatted string.")

    return dt.astimezone(timezone.utc)


def validate_purpose(value: str):
    s = {
        "Calibration",
        "Checkout",
        "Engineering",
        "Navigation",
        "Observation Geometry",
        "Science",
        "Supporting Observation",
    }
    if value not in s:
        raise ValueError(f"purpose must be one of {s}")
    return value
