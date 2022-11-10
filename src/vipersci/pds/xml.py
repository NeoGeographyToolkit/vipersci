#!/usr/bin/env python
"""This module contains functions and data structures to enable
processing of PDS4 XML.
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

im_version = "1.18.0.0"

dd = dict(
    pds="PDS4_PDS_1I00",
    disp="PDS4_DISP_1I00_1510",
    img="PDS4_IMG_1I00_1860",
    msn="PDS4_MSN_1I00_1300",
    proc="PDS4_PROC_1I00_1210",
)

ns = {}
for k in dd.keys():
    ns[k] = f"http://pds.nasa.gov/pds4/{k}/v1"
