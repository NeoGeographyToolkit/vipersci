"""MSolo model module.

This module contains functions for simulating MSolo data.
"""

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

import numpy as np

from vipersci.nirvss import band_depth_H2O


def mass20(temperature, ice_depth, a=1e-6, b=150, c=30, d=1, e=10):
    """Returns the simulated mass 20 signal intensity in amps."""

    return band_depth_H2O(temperature, ice_depth, a, b, c, d, e)


def mass40(temperature, a=5e-7, b=100, c=20):
    """Returns the simulated mass 40 signal intensity in amps."""
    # A*Exp(-1*abs(Tsurf-B)/C)
    return a * np.exp(-1 * np.absolute(temperature - b) / c)
