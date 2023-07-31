#!/usr/bin/env python
"""This module contains an alternate form of the vipersci.pds.datetime.isozformat()
function suitable for testing with SQLite databases which do not retain timezone
information.
"""

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

import datetime


def isozformat(date_time, sep="T", timespec="auto"):
    """
    This function is meant to be patched in place of vipersci.pds.datetime.isozformat()
    via unittest.mock.patch's 'new=' argument as follows:

        with patch(
            "vipersci.vis.db.image_records.isozformat",
            new=datetime_sqlite.isozformat
        )

    It should only be patched in when needed to test load-from-database functionality.
    If used more frequently, could allow bugs to propagate.

    For more information about isozformat, please see vipersci.pds.datetime.isozformat()
    """
    if date_time.utcoffset() == datetime.timedelta():
        return date_time.replace(tzinfo=None).isoformat(sep, timespec) + "Z"
    elif date_time.utcoffset() is None:
        # This elif is the difference from the original function: it will take a naive
        # datetime and assumes that it is a UTC datetime
        return date_time.isoformat(sep, timespec) + "Z"
    else:
        raise ValueError(
            "The datetime object is either naive (not timezone aware), "
            "or has a non-zero offset from UTC.  Maybe you just want "
            "the datetime object's isoformat() function?"
        )
