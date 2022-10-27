"""Contains information and functions that reflect information in the MCSE ICD.

Contains information about how to translate bit fields to their practical
values, as well as helper functions.
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

import logging
from typing import Union


logger = logging.getLogger(__name__)


pga_gain_dict = {
    # The key is the integer value of the 3-bit parameter from the Image
    # Header.  The value is the floating point value that corresponds
    # to the 3-bit parameter.
    0: 1,
    1: 1.2,
    2: 1.4,
    3: 1.6,
    4: 2,  # 4, 5, 6, & 7 are 2x 0, 1, 2, 3
    5: 2.4,
    6: 2.8,
    7: 3.2,
}


def exposure_time(value: int):
    """Returns the exposure time in microseconds.

    The Exposure parameter is a 15 bit value, and the Exposure Step
    is a 1 bit value which is packed together so that the Exposure
    Step is the MSB of the two-byte value, defined as follows:

    The 15-bit LSB portion is "the exposure field" and the 1-bit Exposure Step
    modifies how the exposure field is interpreted.  If the Exposure Step is
    zero (0b0), the steps between exposure field values are 10 microseconds
    allowing values from 111 microseconds through ~328 microseconds.  If the
    Exposure Step is 1 (0b1), the steps between exposure field values are
    1 milisecond, from 1 milisecond to 32,768 ms.
    """

    if value <= 32768:
        return 111 + value * 10

    elif value < 65536:
        return (value - 32767) * 1000

    else:
        raise ValueError


def mcam_id(value: int):
    """Returns the camera value given the MCAM_ID.

    This is a 3-bit value  in the header.
    """

    d = {
        0: "Camera 1",
        1: "Camera 2",
        2: "Camera 3",
        3: "Camera 4",
        4: "Test image",
    }

    try:
        return d[value]
    except KeyError:
        raise ValueError(f"The value ({value}) must be in the set {d.keys()}.")


def pga_gain(value: Union[int, float]):
    """Returns the PGA Gain as a decimal value."""

    try:
        if isinstance(value, float):
            if value in pga_gain_dict.values():
                return value
            else:
                raise KeyError

        return pga_gain_dict[value]
    except KeyError:
        raise ValueError(
            f"The value ({value}) must be in the set {pga_gain_dict.keys()}."
        )
