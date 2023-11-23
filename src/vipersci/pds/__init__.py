#!/usr/bin/env python
# coding: utf-8

"""Provides some generic PDS structures."""

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


class Purpose(enum.Enum):
    # These definitions are taken from the allowable values for
    # Product_Observational/Observation_Area/Primary_Result_Summary/purpose
    # in the PDS4 Data Dictionary.
    CALIBRATION = "Data collected to determine the relationship between measurement "
    "values and physical units."
    CHECKOUT = "Data collected during operational tests."
    ENGINEERING = "Data collected about support systems and structures, which are "
    "ancillary to the primary measurements."
    NAVIGATION = "Data collected to support navigation."
    OBSERVATION_GEOMETRY = "Data used to compute instrument observation geometry, "
    "such as SPICE kernels."
    SCIENCE = "Data collected primarily to answer questions about the targets of "
    "the investigation."
    SUPPORTING_OBSERVATION = "A science observation that was acquired to provide "
    "support for another science observation (e.g., a context image for a very "
    "high resolution observation, or an image intended to support an observation "
    "by a spectral imager)."
