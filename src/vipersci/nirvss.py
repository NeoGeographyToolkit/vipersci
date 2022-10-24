"""NIRVSS model module.

This module contains functions for simulating NIRVSS data.
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


def band_depth_H2O(temperature, ice_depth, a=0.001, b=100, c=50, d=1, e=10):
    """Returns the H2O band depth."""

    return (
        a
        * np.exp(-1 * np.absolute(temperature - b) / c)
        / np.exp(-1 * np.absolute(ice_depth - d) / e)
    )


def band_depth_OH(insolation, a=1e-3, b=150, c=0.5):
    """Returns the OH band depth."""
    return a * np.float_power(insolation - b, c)
